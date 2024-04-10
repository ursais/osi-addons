# Copyright (C) 2020 Open Source Integrators
# Copyright (C) 2020 Serpent Consulting Services Pvt. Ltd.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

PAYMENT_STATE_SELECTION = [
        ('not_paid', 'Not Paid'),
        ('in_payment', 'In Payment'),
        ('paid', 'Paid'),
        ('partial', 'Partially Paid'),
        ('reversed', 'Reversed'),
        ('invoicing_legacy', 'Invoicing App Legacy'),
]


class FSMOrder(models.Model):
    _inherit = "fsm.order"

    @api.depends("date_start", "date_end")
    def _compute_duration(self):
        res = super()._compute_duration()
        for rec in self:
            if rec.fsm_stage_history_ids and rec.date_end:
                stage_rec = self.env["fsm.stage.history"].search(
                    [("order_id", "=", rec.id)], order="id desc", limit=1
                )
                rec.duration = stage_rec.total_duration
            elif not rec.date_end:
                rec.duration = 0.0
        return res

    @api.depends("invoice_ids.payment_state")
    def _compute_payment_state(self):
        for rec in self:
            rec.payment_state = "not_paid"
            for invoice in rec.invoice_ids:
                rec.payment_state = invoice.payment_state

    duration = fields.Float(
        string="Actual duration",
        compute=_compute_duration,
        help="Actual duration in hours",
        store=True,
    )
    fsm_stage_history_ids = fields.One2many(
        "fsm.stage.history", "order_id", string="Stage History"
    )
    payment_state = fields.Selection(PAYMENT_STATE_SELECTION, string="Payment State", compute="_compute_payment_state", store=True)

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

    @api.model
    def get_so_invoice(self):
        invoice_rec = self.env["account.move"].sudo().search([
            ("invoice_origin", "=", self.sale_id.name),
            ("partner_id", "=", self.sale_id.partner_id.id)],
            order='id desc', limit=1
        )
        return invoice_rec

    @api.model
    def generate_invoice_payment_link(self, fsm_order_id):
        order = self.env["fsm.order"].browse(fsm_order_id)
        if not order.sale_id:
            return {'payment_status': False, 'message': 'The sale order is not found related to this FSO.'}
    
        invoice_rec = order.get_so_invoice()
        if not invoice_rec:
            sale_advance_payment_obj = self.env["sale.advance.payment.inv"].sudo()
            advc_payment_wiz = sale_advance_payment_obj.with_context(
                {
                    "active_model": "sale.order",
                    "active_id": order.sale_id.id,
                    "active_ids": order.sale_id.ids,
                }
            ).create(
                {
                    "advance_payment_method": "delivered",
                    "amount": order.sale_id.amount_total,
                }
            )
            advc_payment_wiz.sudo().create_invoices()
            invoice_rec = order.get_so_invoice()
        if invoice_rec:
            payment_link_id = (self.env['payment.link.wizard']
            .with_context(
                default_res_model='account.move',
                default_res_id=invoice_rec.id
            )
            .sudo().create({
                'res_model': 'account.move',
                'res_id': invoice_rec.id,
                'amount': invoice_rec.amount_total,
                'currency_id': invoice_rec.currency_id.id,
                'partner_id': invoice_rec.partner_id.id,
                'description': order.sale_id.name,
            }))
            return {
                'payment_status': True,
                'payment_link': payment_link_id.link
            }
