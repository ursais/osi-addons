# Import Odoo libs
from odoo import _, api, fields, models
from collections import defaultdict


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
        string="Sale Orders to Refund",
        help="Original Sale Orders where the systems were originally sold, populated by the Import from Sale Order wizard.",
    )
    original_repair_order_ids = fields.Many2many(
        comodel_name="repair.order",
        string="Repair Orders to Refund",
    )
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Customer",
    )
    restock_fee = fields.Float(
        string="Restock Fee %",
        default=0.15,
        help="This restock fee will be auto applied to each line, reducing its price by the fee's percentage.",
    )

    @api.onchange("restock_fee")
    def _onchange_restock_fee(self):
        if self.restock_fee:
            self.line_ids.write({"discount":self.restock_fee * 100})


    def action_add_from_sale_orders(self):
        sale_orders = self.ticket_id.original_sale_order_ids.filtered(
            lambda so: so.invoice_ids
        )
        self.original_sale_order_ids = [(6, 0, sale_orders.ids)]
        self._onchange_original_sale_orders()
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }

    @api.onchange("original_sale_order_ids")
    def _onchange_original_sale_orders(self):
        grouped_lines = defaultdict(
            lambda: {
                "quantity": 0.0,
                "tax_ids": set(),
                "account_id": None,
                "price_unit": 0.0,
                "name": "",
                "discount": 0.0,
            }
        )

        for sale_order in self.original_sale_order_ids:
            for invoice in sale_order.invoice_ids.filtered(
                lambda inv: inv.move_type == "out_invoice" and inv.state == "posted"
            ):
                for line in invoice.invoice_line_ids:
                    if not line.product_id:
                        continue
                    key = (line.product_id.id, round(line.price_unit, 2))
                    entry = grouped_lines[key]
                    entry["quantity"] += line.quantity
                    entry["tax_ids"].update(line.tax_ids.ids)
                    entry["account_id"] = line.account_id.id
                    entry["price_unit"] = line.price_unit  # keep original price
                    entry["discount"] = (
                        self.restock_fee * 100
                    )  # negative discount for restock fee
                    entry["name"] = (
                        line.name or line.product_id.display_name
                    ) + f" (Restock Fee: {int(self.restock_fee * 100)}%)"

        self.line_ids = [
            (
                0,
                0,
                {
                    "product_id": product_id,
                    "name": entry["name"],
                    "quantity": entry["quantity"],
                    "price_unit": entry["price_unit"],
                    "tax_ids": [(6, 0, list(entry["tax_ids"]))],
                    "account_id": entry["account_id"],
                    "discount": entry["discount"],
                },
            )
            for (product_id, _), entry in grouped_lines.items()
        ]

    def action_add_from_repairs(self):
        repair_orders = self.ticket_id.repair_ids.filtered(lambda r: r.state == "done")
        self.original_repair_order_ids = [(6, 0, repair_orders.ids)]
        self._onchange_original_repair_orders()
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }

    @api.onchange("original_repair_order_ids")
    def _onchange_original_repair_orders(self):
        grouped_lines = defaultdict(
            lambda: {
                "quantity": 0.0,
                "tax_ids": set(),
                "account_id": None,
                "price_unit": 0.0,
                "name": "",
                "discount": 0.0,
            }
        )

        for repair in self.original_repair_order_ids.filtered(
            lambda r: r.state == "done"
        ):
            for move in repair.move_ids.filtered(
                lambda m: m.repair_line_type == "remove"
            ):
                product = move.product_id
                if not product:
                    continue
                key = (product.id, round(product.lst_price, 2))  # or other price logic

                entry = grouped_lines[key]
                entry["quantity"] += move.product_uom_qty
                entry["tax_ids"].update(product.taxes_id.ids)
                entry["account_id"] = (
                    product.property_account_income_id.id
                    or product.categ_id.property_account_income_categ_id.id
                )
                entry["price_unit"] = product.lst_price
                entry["discount"] = self.restock_fee * 100
                entry["name"] = (
                    f"Refund (Repair): {product.display_name} (Restock Fee: {int(self.restock_fee * 100)}%)"
                )

        self.line_ids = [
            (
                0,
                0,
                {
                    "product_id": product_id,
                    "name": entry["name"],
                    "quantity": entry["quantity"],
                    "price_unit": entry["price_unit"],
                    "tax_ids": [(6, 0, list(entry["tax_ids"]))],
                    "account_id": entry["account_id"],
                    "discount": entry["discount"],
                },
            )
            for (product_id, _), entry in grouped_lines.items()
        ]

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
                        "account_id": line.account_id.id,
                        "discount": line.discount,
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
