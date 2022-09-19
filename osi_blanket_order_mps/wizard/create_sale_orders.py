# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class BlanketOrderWizard(models.TransientModel):
    _inherit = "sale.blanket.order.wizard"

    order_option = fields.Selection(
        [
            (
                "no_line",
                "Create Empty Order - Create Empty Sales Order so "
                "lines can be added manually.",
            ),
            ("line", "Use Existing Lines - Bring Lines Over to New Sales Order"),
            ("update_only", "Only Update Lines - Don't Create Sales Order"),
        ],
        string="Create Options",
        default="no_line",
        required=True,
    )
    dup_sale_order_id = fields.Many2one("sale.order")

    @api.model
    def _default_lines(self):
        super()._default_lines()
        blanket_order_line_obj = self.env["sale.blanket.order.line"]
        blanket_order_line_ids = self.env.context.get("active_ids", False)
        active_model = self.env.context.get("active_model", False)

        if active_model == "sale.blanket.order":
            bo_lines = self._default_order().line_ids
        else:
            bo_lines = blanket_order_line_obj.browse(blanket_order_line_ids)

        self._check_valid_blanket_order_line(bo_lines)

        lines = [
            (
                0,
                0,
                {
                    "blanket_line_id": bol.id,
                    "product_id": bol.product_id.id,
                    "date_schedule": bol.date_schedule,
                    "remaining_uom_qty": bol.remaining_uom_qty,
                    "price_unit": bol.price_unit,
                    "product_uom": bol.product_uom,
                    "qty": 0.0,
                    "partner_id": bol.partner_id,
                    "new_qty": bol.original_uom_qty,
                },
            )
            for bol in bo_lines.filtered(lambda l: l.remaining_uom_qty != 0.0)
        ]
        return lines

    line_ids = fields.One2many(
        "sale.blanket.order.wizard.line",
        "wizard_id",
        string="Lines",
        default=_default_lines,
    )

    def create_sale_order(self):
        res = super().create_sale_order()
        self.blanket_order_id.sudo().action_mps_replenish(
            self.blanket_order_id.line_ids
        )
        return res

    def mrp_create_sale_order(self):
        if self.order_option == "line":
            self.create_sale_order()
        elif self.order_option == "no_line":
            self.create_empty_order()
        elif self.order_option == "update_only":
            self.update_blanket_order()

    def create_empty_order(self):
        currency_id = 0
        pricelist_id = 0
        user_id = 0
        payment_term_id = 0
        if len(self.line_ids.filtered(lambda l: l.qty != 0.0)) == 0:
            raise UserError(_("Please enter a quantity for at least one line."))
        elif self.dup_sale_order_id:
            for line in self.line_ids.filtered(lambda l: l.qty != 0.0):
                if line.qty > line.remaining_uom_qty:
                    raise UserError(
                        _("You can't order more than the remaining quantities")
                    )
                line.blanket_line_id.write(
                    {"empty_ordered_uom_qty": line.empty_ordered_uom_qty + line.qty}
                )
            sale_order = self.dup_sale_order_id.copy(
                {
                    "origin": self.blanket_order_id.name,
                    "blanket_order_id2": self.blanket_order_id.id,
                    "user_id": user_id,
                }
            )
        else:
            for line in self.line_ids.filtered(lambda l: l.qty != 0.0):
                if line.qty > line.remaining_uom_qty:
                    raise UserError(
                        _("You can't order more than the remaining quantities")
                    )
                if currency_id == 0:
                    currency_id = line.blanket_line_id.order_id.currency_id.id
                elif currency_id != line.blanket_line_id.order_id.currency_id.id:
                    currency_id = False
                if pricelist_id == 0:
                    pricelist_id = line.blanket_line_id.pricelist_id.id
                elif pricelist_id != line.blanket_line_id.pricelist_id.id:
                    pricelist_id = False
                if user_id == 0:
                    user_id = line.blanket_line_id.user_id.id
                elif user_id != line.blanket_line_id.user_id.id:
                    user_id = False
                if payment_term_id == 0:
                    payment_term_id = line.blanket_line_id.payment_term_id.id
                elif payment_term_id != line.blanket_line_id.payment_term_id.id:
                    payment_term_id = False
                line.blanket_line_id.write(
                    {"empty_ordered_uom_qty": line.empty_ordered_uom_qty + line.qty}
                )
            if not currency_id:
                raise UserError(
                    _(
                        "Can not create Sale Order from Blanket "
                        "Order lines with different currencies."
                    )
                )
            sale_order = self.env["sale.order"].create(
                {
                    "partner_id": self.blanket_order_id.partner_id.id,
                    "origin": self.blanket_order_id.name,
                    "user_id": user_id,
                    "currency_id": currency_id,
                    "pricelist_id": pricelist_id,
                    "payment_term_id": payment_term_id,
                    "analytic_account_id": self.blanket_order_id.analytic_account_id.id,
                    "blanket_order_id2": self.blanket_order_id.id,
                }
            )
        self.blanket_order_id.sudo().action_mps_replenish(
            self.blanket_order_id.line_ids
        )
        return {
            "domain": [("id", "in", sale_order.id)],
            "name": _("Sales Orders"),
            "view_type": "form",
            "view_mode": "tree,form",
            "res_model": "sale.order",
            "context": {"from_sale_order": True},
            "type": "ir.actions.act_window",
        }

    def update_blanket_order(self):
        for line in self.line_ids.filtered(
            lambda l: l.blanket_line_id.original_uom_qty != l.new_qty
            or l.blanket_line_id.date_schedule != l.date_schedule
        ):
            if line.new_qty < (line.empty_ordered_uom_qty + line.ordered_uom_qty):
                raise UserError(
                    _(
                        "You can't update the original qty with less than "
                        "the sum of already ordered quantities."
                    )
                )
            line.blanket_line_id.write(
                {"original_uom_qty": line.new_qty, "date_schedule": line.date_schedule}
            )
        self.blanket_order_id.sudo().action_mps_replenish(
            self.blanket_order_id.line_ids
        )


class BlanketOrderWizardLine(models.TransientModel):
    _inherit = "sale.blanket.order.wizard.line"

    empty_ordered_uom_qty = fields.Float(
        string="Empty Order Qty",
        related="blanket_line_id.empty_ordered_uom_qty",
    )
    ordered_uom_qty = fields.Float(
        string="Ordered Qty",
        related="blanket_line_id.ordered_uom_qty",
    )
    original_uom_qty = fields.Float(
        string="Original Qty",
        related="blanket_line_id.original_uom_qty",
    )
    new_qty = fields.Float(
        string="New Qty",
    )
