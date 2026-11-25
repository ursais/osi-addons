# Copyright (C) 2020 Open Source Integrators
# Copyright (C) 2020 Serpent Consulting Services Pvt. Ltd.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class FSMOrder(models.Model):
    _inherit = "fsm.order"

    @api.depends("date_start", "date_end", "fsm_stage_history_ids")
    def _compute_duration(self):
        for rec in self:
            if rec.fsm_stage_history_ids and rec.date_end:
                stage_rec = self.env["fsm.stage.history"].search(
                    [("order_id", "=", rec.id)], order="id desc", limit=1
                )
                rec.duration = stage_rec.total_duration
            elif not rec.date_end:
                rec.duration = 0.0

    @api.depends("sale_id.transaction_ids.state")
    def _compute_payment_state(self):
        for rec in self:
            payment_state = "not_paid"
            paid_payment_check_list = [
                True if paym.state == "done" else False
                for paym in rec.sale_id.transaction_ids
            ]
            if rec.sale_id.transaction_ids:
                if all(paid_payment_check_list):
                    payment_state = "paid"
                elif rec.sale_id.transaction_ids.filtered(
                    lambda r: r.state == "pending"
                ):
                    payment_state = "pending"
            rec.payment_state = payment_state

    duration = fields.Float(
        string="Actual duration",
        compute="_compute_duration",
        help="Actual duration in hours",
        store=True,
    )
    fsm_stage_history_ids = fields.One2many(
        "fsm.stage.history", "order_id", string="Stage History"
    )
    payment_state = fields.Selection(
        [("not_paid", "Not Paid"), ("paid", "Paid"), ("pending", "Pending")],
        compute="_compute_payment_state",
        store=True,
    )

    @api.model
    def create_fsm_attachment(self, name, datas, res_model, res_id):
        if res_model == "fsm.order":
            attachment = (
                self.env["ir.attachment"]
                .sudo()
                .create(
                    {
                        "name": name,
                        "datas": datas,
                        "res_model": res_model,
                        "res_id": res_id,
                    }
                )
            )
            return attachment.id
        return False

    @api.model
    def generate_so_payment_link(self, fsm_order_id):
        order = self.env["fsm.order"].browse(fsm_order_id)
        if not order.sale_id:
            return {
                "payment_status": False,
                "message": "The sale order is not found related to this FSO.",
            }
        payment_link_id = (
            self.env["payment.link.wizard"]
            .with_context(
                default_res_model="sale.order", default_res_id=order.sale_id.id
            )
            .sudo()
            .create(
                {
                    "res_model": "sale.order",
                    "res_id": order.sale_id.id,
                    "amount": order.sale_id.amount_total,
                    "currency_id": order.sale_id.currency_id.id,
                    "partner_id": order.sale_id.partner_id.id,
                }
            )
        )
        return {"payment_status": True, "payment_link": payment_link_id.link}

    def mobile_post_log_note(self, body):
        """Post a chatter log note; portal-safe via sudo after write ACL check."""
        self.ensure_one()
        self.check_access("write")
        if not body or not str(body).strip():
            return False
        message = self.sudo().message_post(
            body=str(body).strip(),
            message_type="comment",
            subtype_xmlid="mail.mt_note",
            author_id=self.env.user.partner_id.id,
        )
        return message.id

    def get_mobile_stage_history(self):
        """Return stage history rows with readable stage names for mobile."""
        self.ensure_one()
        self.check_access("read")
        histories = (
            self.env["fsm.stage.history"]
            .sudo()
            .search([("order_id", "=", self.id)], order="id asc")
        )
        result = []
        for hist in histories:
            stage = hist.stage_id
            result.append(
                {
                    "id": hist.id,
                    "start_datetime": hist.start_datetime,
                    "stage_id": [stage.id, stage.display_name] if stage else False,
                    "duration": hist.duration or 0.0,
                    "total_duration": hist.total_duration or 0.0,
                }
            )
        return result

    def get_mobile_log_notes(self, offset=0, limit=10):
        """Return log notes on this order; portal-safe message read."""
        self.ensure_one()
        self.check_access("read")
        domain = [
            ("model", "=", "fsm.order"),
            ("res_id", "=", self.id),
            ("body", "!=", False),
            ("body", "!=", ""),
            "|",
            ("message_type", "=", "comment"),
            "&",
            ("message_type", "=", "notification"),
            ("subtype_id.name", "=", "Note"),
        ]
        messages = (
            self.env["mail.message"]
            .sudo()
            .search(domain, order="id desc", offset=offset, limit=limit)
        )
        result = []
        for msg in messages:
            author = msg.author_id
            result.append(
                {
                    "id": msg.id,
                    "author_id": [author.id, author.display_name] if author else False,
                    "body": msg.body or "",
                    "date": msg.date,
                }
            )
        return result
