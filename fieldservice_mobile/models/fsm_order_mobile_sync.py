# Copyright (C) 2026 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError


class FSMOrder(models.Model):
    _inherit = "fsm.order"

    # Fields the mobile app may push in a sync batch.
    _FSM_MOBILE_SYNC_ORDER_FIELDS = frozenset(
        {
            "stage_id",
            "description",
            "resolution",
            "todo",
            "date_start",
            "date_end",
            "priority",
            "tag_ids",
            "equipment_ids",
            "equipment_id",
        }
    )

    # Default fields returned by the delta pull endpoint.
    _FSM_MOBILE_PULL_FIELDS = (
        "id",
        "name",
        "write_date",
        "scheduled_date_start",
        "scheduled_date_end",
        "request_early",
        "request_late",
        "date_start",
        "date_end",
        "location_id",
        "mobile",
        "phone",
        "priority",
        "person_id",
        "person_ids",
        "stage_id",
        "stage_name",
        "custom_color",
        "tag_ids",
        "type",
        "team_id",
        "description",
        "todo",
        "resolution",
        "equipment_id",
        "equipment_ids",
        "message_ids",
        "fsm_stage_history_ids",
        "duration",
        "signed_by",
        "signed_on",
        "require_signature",
        "payment_state",
    )

    @api.model
    def _fsm_mobile_get_person(self, user=None):
        """Return the fsm.person linked to the given (or current) user."""
        user = user or self.env.user
        return self.env["fsm.person"].search(
            [("partner_id", "=", user.partner_id.id)], limit=1
        )

    def _fsm_mobile_ensure_assigned(self, person=None):
        """Raise if the order is not assigned to the technician."""
        self.ensure_one()
        person = person or self._fsm_mobile_get_person()
        if not person:
            raise AccessError(
                self.env._("No Field Service worker is linked to the current user.")
            )
        if self.person_id != person and person not in self.person_ids:
            raise AccessError(
                self.env._(
                    "You can only sync orders assigned to you " "(order %(order)s).",
                    order=self.display_name,
                )
            )
        return person

    @api.model
    def _fsm_mobile_filter_order_vals(self, order_vals):
        """Keep only whitelisted writable fields from the mobile payload."""
        if not order_vals:
            return {}
        if not isinstance(order_vals, dict):
            raise ValidationError(self.env._("order values must be a dictionary."))
        return {
            key: value
            for key, value in order_vals.items()
            if key in self._FSM_MOBILE_SYNC_ORDER_FIELDS
        }

    def _fsm_mobile_apply_clocks(self, clocks):
        """Create or update fsm.stage.history lines (mobile clock punches)."""
        self.ensure_one()
        if not clocks:
            return self.env["fsm.stage.history"]
        if not isinstance(clocks, list):
            raise ValidationError(self.env._("clocks must be a list."))

        History = self.env["fsm.stage.history"]
        created_or_updated = History.browse()
        for clock in clocks:
            if not isinstance(clock, dict):
                raise ValidationError(
                    self.env._("Each clock entry must be a dictionary.")
                )
            vals = {
                "order_id": self.id,
                "stage_id": clock.get("stage_id"),
                "start_datetime": clock.get("start_datetime"),
                "duration": clock.get("duration", 0.0),
                "total_duration": clock.get("total_duration", 0.0),
            }
            if not vals["stage_id"] or not vals["start_datetime"]:
                raise ValidationError(
                    self.env._("Each clock entry requires stage_id and start_datetime.")
                )
            clock_id = clock.get("id")
            if clock_id:
                history = History.browse(int(clock_id)).exists()
                if not history or history.order_id != self:
                    raise UserError(
                        self.env._(
                            "Clock %(clock_id)s does not belong to order %(order)s.",
                            clock_id=clock_id,
                            order=self.display_name,
                        )
                    )
                history.write(
                    {
                        "stage_id": vals["stage_id"],
                        "start_datetime": vals["start_datetime"],
                        "duration": vals["duration"],
                        "total_duration": vals["total_duration"],
                    }
                )
                created_or_updated |= history
            else:
                created_or_updated |= History.create(vals)
        return created_or_updated

    def _fsm_mobile_apply_signature(self, signature):
        """Apply customer signature fields (same effect as the sign wizard)."""
        self.ensure_one()
        if not signature:
            return
        if not isinstance(signature, dict):
            raise ValidationError(self.env._("signature must be a dictionary."))
        signed_by = signature.get("signed_by")
        signature_data = signature.get("signature")
        if not signed_by or not signature_data:
            raise ValidationError(
                self.env._("signature requires signed_by and signature data.")
            )
        signed_on = signature.get("signed_on") or fields.Datetime.now()
        self.write(
            {
                "signed_by": signed_by,
                "signed_on": signed_on,
                "signature": signature_data,
            }
        )
        self.message_post(
            body=self.env._("Order signed by %s", signed_by),
            message_type="comment",
            subtype_xmlid="mail.mt_comment",
        )

    def _fsm_mobile_sync_one(self, order_vals=None, clocks=None, signature=None):
        """Apply order vals, clocks and signature on this order."""
        self.ensure_one()
        person = self._fsm_mobile_ensure_assigned()
        vals = self._fsm_mobile_filter_order_vals(order_vals)
        if vals:
            self.write(vals)
        histories = self._fsm_mobile_apply_clocks(clocks)
        self._fsm_mobile_apply_signature(signature)
        return {
            "order_id": self.id,
            "write_date": fields.Datetime.to_string(self.write_date),
            "person_id": person.id,
            "clock_ids": histories.ids,
            "signed_by": self.signed_by or False,
            "signed_on": (
                fields.Datetime.to_string(self.signed_on) if self.signed_on else False
            ),
        }

    @api.model
    def fsm_mobile_sync_batch(self, mutations=None, **kwargs):
        """
        Apply one or more mobile mutations in the current DB transaction.

        Accepts either:
        - mutations: list of {order_id, order?, clocks?, signature?}
        - or a single mutation as kwargs: order_id, order, clocks, signature
        """
        if mutations is None:
            if not kwargs.get("order_id"):
                raise ValidationError(
                    self.env._("Provide mutations or a single order_id payload.")
                )
            mutations = [kwargs]
        if not isinstance(mutations, list) or not mutations:
            raise ValidationError(self.env._("mutations must be a non-empty list."))

        results = []
        for mutation in mutations:
            if not isinstance(mutation, dict):
                raise ValidationError(self.env._("Each mutation must be a dictionary."))
            order_id = mutation.get("order_id")
            if not order_id:
                raise ValidationError(self.env._("Each mutation requires order_id."))
            order = self.browse(int(order_id)).exists()
            if not order:
                raise UserError(
                    self.env._(
                        "FSM order %(order_id)s was not found.", order_id=order_id
                    )
                )
            results.append(
                order._fsm_mobile_sync_one(
                    order_vals=mutation.get("order") or mutation.get("order_vals"),
                    clocks=mutation.get("clocks"),
                    signature=mutation.get("signature"),
                )
            )
        return {"ok": True, "results": results}

    @api.model
    def fsm_mobile_pull_delta(
        self, since=None, fields=None, limit=80, offset=0, include_workers=True
    ):
        """
        Return orders assigned to the current technician changed after ``since``.

        Domain:
        - person_id = current user's fsm.person (and optionally person_ids)
        - write_date > since (when provided)
        """
        person = self._fsm_mobile_get_person()
        if not person:
            raise AccessError(
                self.env._("No Field Service worker is linked to the current user.")
            )

        domain = [("person_id", "=", person.id)]
        if include_workers:
            domain = [
                "|",
                ("person_id", "=", person.id),
                ("person_ids", "in", person.ids),
            ]
        if since:
            domain.append(("write_date", ">", since))

        # ``fields`` is the JSON-RPC param name (shadows odoo.fields here).
        pull_fields = list(fields or self._FSM_MOBILE_PULL_FIELDS)
        for required in ("id", "write_date", "person_id"):
            if required not in pull_fields:
                pull_fields.append(required)

        # Drop unknown fields so optional modules don't break the pull.
        model_fields = self._fields
        pull_fields = [name for name in pull_fields if name in model_fields]

        limit = min(max(int(limit or 80), 1), 500)
        offset = max(int(offset or 0), 0)
        orders = self.search(
            domain, order="write_date asc, id asc", limit=limit, offset=offset
        )
        records = orders.read(pull_fields)
        return {
            "ok": True,
            "person_id": person.id,
            "since": since or False,
            "count": len(records),
            "records": records,
        }

    @api.model
    def fsm_mobile_create_photo_attachment(
        self, order_id, name, raw_bytes, mimetype=None
    ):
        """Create an ir.attachment for an order photo from raw binary bytes."""
        order = self.browse(int(order_id)).exists()
        if not order:
            raise UserError(
                self.env._("FSM order %(order_id)s was not found.", order_id=order_id)
            )
        order._fsm_mobile_ensure_assigned()
        if not raw_bytes:
            raise ValidationError(self.env._("Photo content is empty."))
        if not name:
            name = "photo.bin"

        vals = {
            "name": name,
            "datas": base64.b64encode(raw_bytes),
            "res_model": "fsm.order",
            "res_id": order.id,
            "type": "binary",
        }
        if mimetype:
            vals["mimetype"] = mimetype
        # Portal workers lack ir.attachment create ACL; access was already
        # validated by _fsm_mobile_ensure_assigned() (same pattern as
        # create_fsm_attachment).
        attachment = self.env["ir.attachment"].sudo().create(vals)
        return {
            "ok": True,
            "attachment_id": attachment.id,
            "order_id": order.id,
            "name": attachment.name,
            "mimetype": attachment.mimetype,
        }
