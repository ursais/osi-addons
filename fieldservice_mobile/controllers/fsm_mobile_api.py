# Copyright (C) 2026 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import http
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.http import request

_logger = logging.getLogger(__name__)


class FSMMobileAPI(http.Controller):
    """HTTP API used by the Field Service mobile application."""

    @http.route(
        "/fsm/sync",
        type="jsonrpc",
        auth="user",
        methods=["POST"],
        readonly=False,
    )
    def fsm_sync(self, mutations=None, **kwargs):
        """
        Apply a batch of offline mutations in a single DB transaction.

        JSON-RPC params (single mutation)::

            {
                "order_id": 12,
                "order": {"stage_id": 5, "resolution": "..."},
                "clocks": [
                    {
                        "stage_id": 6,
                        "start_datetime": "2026-07-24 15:00:00",
                        "duration": 0.5,
                        "total_duration": 1.0
                    }
                ],
                "signature": {
                    "signed_by": "Jane Doe",
                    "signature": "<base64 png>",
                    "signed_on": "2026-07-24 16:00:00"
                }
            }

        Or a batch::

            {"mutations": [ {...}, {...} ]}
        """
        return request.env["fsm.order"].fsm_mobile_sync_batch(
            mutations=mutations, **kwargs
        )

    @http.route(
        "/fsm/pull",
        type="jsonrpc",
        auth="user",
        methods=["POST"],
        readonly=True,
    )
    def fsm_pull(
        self, since=None, fields=None, limit=80, offset=0, include_workers=True
    ):
        """
        Pull orders assigned to the current technician, filtered by write_date.

        JSON-RPC params::

            {
                "since": "2026-07-24 00:00:00",
                "fields": ["id", "name", "stage_id", "write_date"],
                "limit": 80,
                "offset": 0,
                "include_workers": true
            }
        """
        return request.env["fsm.order"].fsm_mobile_pull_delta(
            since=since,
            fields=fields,
            limit=limit,
            offset=offset,
            include_workers=include_workers,
        )

    @http.route(
        "/fsm/photo",
        type="http",
        auth="user",
        methods=["POST"],
        csrf=False,
        readonly=False,
    )
    def fsm_photo(self, order_id=None, name=None, **kwargs):
        """
        Multipart photo upload that creates ``ir.attachment`` directly.

        Form fields:
        - ``order_id`` (required): fsm.order id
        - ``name`` (optional): file name
        - file field: ``ufile``, ``file``, ``photo`` or ``attachment``
        """
        try:
            order_id = order_id or kwargs.get("res_id")
            if not order_id:
                return self._json_http_error("order_id is required.", status=400)

            upload = (
                request.httprequest.files.get("ufile")
                or request.httprequest.files.get("file")
                or request.httprequest.files.get("photo")
                or request.httprequest.files.get("attachment")
            )
            if not upload:
                return self._json_http_error(
                    "Missing multipart file field "
                    "(ufile, file, photo or attachment).",
                    status=400,
                )

            filename = name or upload.filename or "photo.bin"
            raw_bytes = upload.read()
            mimetype = getattr(upload, "content_type", None) or getattr(
                upload, "mimetype", None
            )
            result = request.env["fsm.order"].fsm_mobile_create_photo_attachment(
                order_id=order_id,
                name=filename,
                raw_bytes=raw_bytes,
                mimetype=mimetype,
            )
            return request.make_json_response(result)
        except (AccessError, UserError, ValidationError) as exc:
            return self._json_http_error(str(exc), status=400)
        except Exception:  # noqa: BLE001 - return safe JSON for mobile clients
            _logger.exception("FSM mobile photo upload failed")
            return self._json_http_error(
                "Unexpected error while uploading photo.", status=500
            )

    @staticmethod
    def _json_http_error(message, status=400):
        return request.make_json_response(
            {"ok": False, "error": message},
            status=status,
        )
