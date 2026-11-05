"""Authenticated file transport; backups never travel in WebSocket frames."""

import asyncio
import json
import logging
import time
from uuid import uuid4

from aiohttp import web
from homeassistant.components.http import HomeAssistantView
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.http import KEY_HASS

from .backup import MAX_BACKUP_BYTES, get_manager, read_backup
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


def json_response(data, *, status=200):
    return web.json_response(data, status=status, headers={"Cache-Control": "no-store"})


class BackupView(HomeAssistantView):
    url = f"/api/{DOMAIN}/backup"
    name = f"api:{DOMAIN}:backup"
    requires_auth = True
    extra_urls = [f"/api/{DOMAIN}/backup/{{action}}"]

    @staticmethod
    def manager(request):
        user = request["hass_user"]
        if not user.is_admin:
            raise web.HTTPForbidden(
                text="Nur HA-Administratoren dürfen Datensicherungen verwalten."
            )
        return get_manager(request.app[KEY_HASS])

    async def get(self, request, action=None):
        manager = self.manager(request)
        try:
            if action == "status":
                previous = await manager.fallback.async_load()
                return json_response(
                    {
                        "lists": manager.targets(),
                        "fallback_available": previous is not None,
                    }
                )
            if action == "previous":
                previous = await manager.fallback.async_load()
                if previous is None:
                    raise ValueError("Keine Rückfallsicherung vorhanden.")
                raw = previous["backup"].encode("utf-8")
            elif action is None:
                raw = await manager.backup()
            else:
                raise web.HTTPNotFound()
            stamp = time.strftime("%Y-%m-%d-%H%M%S", time.gmtime())
            return web.Response(
                body=raw,
                content_type="application/json",
                headers={
                    "Content-Disposition": f'attachment; filename="easy-shopping-{"previous-" if action else ""}{stamp}.json"',
                    "Cache-Control": "no-store",
                },
            )
        except (HomeAssistantError, OSError, ValueError, TypeError) as err:
            _LOGGER.warning("Backup download failed: %s", err)
            return json_response({"error": str(err)}, status=400)

    async def post(self, request, action=None):
        manager = self.manager(request)
        try:
            raw = bytearray()
            async for chunk in request.content.iter_chunked(64 * 1024):
                raw.extend(chunk)
                if len(raw) > MAX_BACKUP_BYTES:
                    raise ValueError("Die Sicherung darf maximal 100 MiB groß sein.")
            if action == "preview":
                payload = await asyncio.to_thread(read_backup, bytes(raw))
                token = uuid4().hex
                manager.staged = {
                    "token": token,
                    "user": request["hass_user"].id,
                    "expires": time.monotonic() + 600,
                    "payload": payload,
                }
                return json_response(
                    {
                        "token": token,
                        "created_at": payload["created_at"],
                        "app_version": payload["app_version"],
                        "lists": [
                            {
                                "entry_id": item["entry_id"],
                                "name": item["name"],
                                "source_entity_id": item["source_entity_id"],
                                "items": len(item["snapshot"]["items"]),
                            }
                            for item in payload["lists"]
                        ],
                        "markets": len(payload["catalog"]["supermarkets"]),
                        "catalogs": len(payload["catalog"]["catalogs"]),
                        "targets": manager.targets(),
                    }
                )
            data = json.loads(raw)
            if not isinstance(data, dict):
                raise ValueError("Ungültige Anfrage.")
            if action == "restore":
                staged = manager.staged
                if (
                    not staged
                    or staged["token"] != data.get("token")
                    or staged["user"] != request["hass_user"].id
                    or staged["expires"] < time.monotonic()
                    or data.get("confirm") is not True
                ):
                    raise ValueError(
                        "Die Vorschau ist abgelaufen oder nicht bestätigt. Bitte Datei erneut auswählen."
                    )
                # Consume the preview before the first await to prevent double submission.
                manager.staged = None
                await manager.restore(staged["payload"], data.get("mapping"))
                return json_response({"restored": True, "source_paused": True})
            if action == "resume":
                if data.get("confirm") is not True or not isinstance(
                    data.get("entry_ids"), list
                ):
                    raise ValueError("Bitte den Quellabgleich ausdrücklich bestätigen.")
                await manager.resume(data["entry_ids"])
                return json_response({"resumed": True})
            raise web.HTTPNotFound()
        except (
            HomeAssistantError,
            OSError,
            ValueError,
            TypeError,
            KeyError,
            RecursionError,
        ) as err:
            _LOGGER.warning("Backup %s failed: %s", action, err)
            return json_response({"error": str(err)}, status=400)
