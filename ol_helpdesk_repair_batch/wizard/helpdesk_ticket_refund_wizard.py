# Import Odoo libs
from odoo import _, api, fields, models


class RepairCreditNoteWizard(models.TransientModel):
    _name = "repair.credit.note.wizard"
    _description = "Repair Credit Note Wizard"

    ticket_id = fields.Many2one(
        comodel_name="helpdesk.ticket",
        required=True,
    )
    line_ids = fields.One2many(
        comodel_name="repair.credit.note.wizard.line",
        inverse_name="wizard_id",
        string="Credit Note Lines",
    )
    original_sale_order_ids = fields.Many2many(
        comodel_name="sale.order",
        string="Original Sale Orders",
        help="Original Sale Orders where the systems were originally sold, populated by the Import from Sale Order wizard.",
    )
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Customer",
    )
    restock_fee = fields.Float(
        string="Restock Fee %",
        default=".15",
        help="This restock fee will be auto applied to each line, reducing it's price by the fee's percentage.",
    )

    def action_add_from_sale_orders(self):
        sale_orders = self.ticket_id.original_sale_order_ids.filtered(
            lambda so: so.invoice_ids
        )
        self.original_sale_order_ids = [(6, 0, sale_orders.ids)]
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }

    @api.onchange("original_sale_order_ids")
    def _onchange_original_sale_orders(self):
        lines = []
        for sale_order in self.original_sale_order_ids:
            for invoice in sale_order.invoice_ids.filtered(
                lambda inv: inv.move_type == "out_invoice" and inv.state == "posted"
            ):
                for line in invoice.invoice_line_ids:
                    if not line.product_id:
                        continue
                    lines.append(
                        (
                            0,
                            0,
                            {
                                "product_id": line.product_id.id,
                                "quantity": line.product_uom_qty,
                                "price_unit": -line.price_unit,
                                "tax_ids": [(6, 0, line.tax_ids.ids)],
                                "account_id": line.account_id.id,
                                "discount": -self.restock_fee,
                            },
                        )
                    )

        self.line_ids = lines

    def action_add_from_repairs(self):
        self.ensure_one()
        product_quantities = {}

        repairs = self.ticket_id.repair_batch_ids.mapped("repair_ids").filtered(
            lambda r: r.state == "done"
        )
        for repair in repairs:
            for move in repair.move_ids.filtered(
                lambda m: m.repair_line_type == "remove"
            ):
                product_id = move.product_id.id
                product_quantities[product_id] = (
                    product_quantities.get(product_id, 0) + move.product_uom_qty
                )

        lines_to_add = []
        for product_id, qty in product_quantities.items():
            product = self.env["product.product"].browse(product_id)
            account_id = (
                product.property_account_income_id.id
                or product.categ_id.property_account_income_categ_id.id
            )
            existing_line = next(
                (
                    l
                    for l in self.line_ids
                    if l.product_id.id == product_id and l.price_unit == 0.0
                ),
                None,
            )
            if existing_line:
                existing_line.quantity += qty
            else:
                lines_to_add.append(
                    (
                        0,
                        0,
                        {
                            "product_id": product.id,
                            "name": f"Refund (Repair): {product.display_name}",
                            "quantity": qty,
                            "price_unit": 0.0,
                            "tax_ids": [],
                            "account_id": account_id,
                        },
                    )
                )

        self.line_ids += lines_to_add

    def action_confirm(self):
        self.ensure_one()
        move_vals = {
            "move_type": "out_refund",
            "partner_id": self.ticket_id.partner_id.id,
            "invoice_date": fields.Date.context_today(self),
            "invoice_origin": self.ticket_id.name,
            "helpdesk_ticket_id": self.ticket_id.id,
            "team_id": self.env.user.sale_team_id.id or False,
            "user_id": self.env.user.id,
            "sale_type_id": self.env.ref(
                "ol_helpdesk_repair_batch.rma_return_sale_type"
            ).id,
            "invoice_line_ids": [
                (
                    0,
                    0,
                    {
                        "product_id": line.product_id.id,
                        "name": line.name,
                        "quantity": line.quantity,
                        "price_unit": line.price_unit,
                        "tax_ids": [(6, 0, line.tax_ids.ids)],
                        "analytic_account_id": line.analytic_account_id.id,
                        "account_id": line.account_id.id,
                    },
                )
                for line in self.line_ids
            ],
        }

        credit_note = self.env["account.move"].create(move_vals)

        return {
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "view_mode": "form",
            "res_id": credit_note.id,
        }


class RepairCreditNoteWizardLine(models.TransientModel):
    _name = "repair.credit.note.wizard.line"
    _description = "Credit Note Line"

    wizard_id = fields.Many2one(
        comodel_name="repair.credit.note.wizard",
        required=True,
    )
    product_id = fields.Many2one(
        comodel_name="product.product",
        required=True,
    )
    name = fields.Char(
        required=True,
    )
    quantity = fields.Float(
        required=True,
        default=1.0,
    )
    price_unit = fields.Float(
        required=True,
    )
    tax_ids = fields.Many2many(
        comodel_name="account.tax",
    )
    account_id = fields.Many2one(
        comodel_name="account.account",
        required=True,
    )
    discount = fields.Float(
        string="Discount (%)",
        digits="Discount",
        default=0.0,
    )
