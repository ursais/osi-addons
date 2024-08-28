# Copyright (C) 2022 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from markupsafe import Markup

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class BlanketOrderLine(models.Model):
    _inherit = "sale.blanket.order.line"

    partner_id = fields.Many2one(store=True)

    @api.onchange(
        "original_uom_qty",
        "ordered_uom_qty",
    )
    def _onchange_uom_qty(self):
        for line in self:
            if line.original_uom_qty < line.ordered_uom_qty:
                raise UserError(
                    _("Updated 'Original QTY' should not be less than 'Ordered QTY'!")
                )

    def _update_line_quantity(self, values):
        orders = self.mapped("order_id")
        for order in orders:
            order_lines = self.filtered(lambda x: x.order_id == order)
            msg = Markup("<b>%s</b><ul>") % _("The Original quantity has been updated.")
            for line in order_lines:
                if (
                    "product_id" in values
                    and values["product_id"] != line.product_id.id
                ):
                    # tracking is meaningless if the product is changed as well.
                    continue
                msg += Markup("<li> %s: <br/>") % line.product_id.display_name
                changes = []
                if "original_uom_qty" in values:
                    changes.append(
                        _("Original Quantity: %(old_qty)s -> %(new_qty)s")
                        % {
                            "old_qty": line.original_uom_qty,
                            "new_qty": values["original_uom_qty"],
                        }
                    )
                if "date_schedule" in values:
                    changes.append(
                        _("Scheduled Date: %(old_schedule)s -> %(new_schedule)s")
                        % {
                            "old_schedule": line.date_schedule,
                            "new_schedule": values["date_schedule"],
                        }
                    )
                if "price_unit" in values:
                    changes.append(
                        _("Price: %(old_price)s -> %(new_price)s")
                        % {
                            "old_price": line.price_unit,
                            "new_price": values["price_unit"],
                        }
                    )
                msg += Markup("<br/>".join(changes)) + Markup("<br/>")
            msg += Markup("</ul>")
            order.message_post(body=msg)

    def create(self, values):
        res = super().create(values)
        compute_mps = False
        for line in res:
            if line.order_id.state != "draft":
                compute_mps = True
        if compute_mps:
            res.mapped("order_id").action_mps_replenish(self.ids)
        return res

    def write(self, values):
        tracking_field_list = [
            "original_uom_qty",
            "date_schedule",
            "price_unit",
        ]
        if (
            any(field in values for field in tracking_field_list)
            and self.order_id.state != "draft"
        ):
            self._update_line_quantity(values)

        if "product_id" in values and self.ordered_uom_qty > 0:
            raise UserError(
                _(
                    "You cannot change product which"
                    " 'Ordered QTY' should greater than 0!"
                )
            )
        return super().write(values)

    def unlink(self):
        """
        If the line is being deleted, we first want to recompute MPS by
        setting qty to zero then run the action_mps_replenish method.
        If multiple lines are being removed, we are only runing the replenish
        method once for all.
        """
        compute_mps = False
        for line in self:
            if line.ordered_uom_qty == 0.0:
                line.write({"original_uom_qty": 0.0})
                compute_mps = True
        if compute_mps:
            self.order_id.action_mps_replenish(self.ids)
        return super().unlink()
