# Copyright (C) 2018 - 2021, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    avg_price = fields.Float(string="Avg Price", type="float")
    calculate_from_date = fields.Date(string="Calculate From")
    std_cost = fields.Float(string="Std Cost", type="float")

    @api.onchange("calculate_from_date")
    def onchange_calculate_from_date(self):
        # Recompute avg price
        if self.product_id:
            self.avg_price = self.product_id.calc_prod_avg_purchase_price(
                self.product_id, self.calculate_from_date
            )
            self.std_cost = self.product_id.standard_price
        return

    @api.onchange("product_id")
    def onchange_product_id(self):
        if self.product_id:
            super(PurchaseOrderLine, self).onchange_product_id()
            self.avg_price = self.product_id.avg_price
            self.calculate_from_date = (
                self.product_id.calculate_from_date
                or self.product_id.product_tmpl_id.calculate_from_date
            )
            self.std_cost = self.product_id.standard_price
        return

    @api.onchange("product_qty", "product_uom")
    def _onchange_quantity(self):
        if not self.product_id:
            return

        result = super(PurchaseOrderLine, self)._onchange_quantity()

        if self.product_id.uom_id.id != self.product_uom.id:
            self.std_cost = self.product_id.uom_id._compute_price(
                self.product_id.standard_price, to_unit=self.product_uom
            )
            self.avg_price = self.product_id.uom_id._compute_price(
                self.product_id.avg_price, to_unit=self.product_uom
            )

        # When it's on the default UOM the value is set correctly
        else:
            self.std_cost = self.product_id.standard_price
            self.avg_price = self.product_id.avg_price

        return result

    @api.model
    def create(self, vals):

        # Update avg_price field explicitly since it is set as "readonly",
        # otherwise it won't be saved.
        for product in self.env["product.product"].browse(vals["product_id"]):
            vals["avg_price"] = product.avg_price
            vals["calculate_from_date"] = (
                product.calculate_from_date
                or product.product_tmpl_id.calculate_from_date
            )
            vals["std_cost"] = product.standard_price

        return super(PurchaseOrderLine, self).create(vals)

    def write(self, vals):
        # Update avg_price field explicitly since it is set as "readonly",
        # otherwise it won't be saved.
        if "product_id" in vals:
            for product in self.env["product.product"].browse(vals["product_id"]):
                vals.update(
                    {
                        "avg_price": product.avg_price,
                        "calculate_from_date": product.calculate_from_date
                        or product.product_tmpl_id.calculate_from_date,
                        "std_cost": product.standard_price,
                    }
                )

        if "product_uom" in vals:

            new_uom = vals.get("product_uom")

            if self.product_id.uom_id.id != new_uom:
                avg_price = self.product_id.uom_id._compute_price(
                    self.product_id.avg_price, self.env["uom.uom"].browse(new_uom)
                )
                std_cost = self.product_id.uom_id._compute_price(
                    self.product_id.standard_price, self.env["uom.uom"].browse(new_uom)
                )

            # When it's on the default UOM the value is set correctly.
            else:
                std_cost = self.product_id.standard_price
                avg_price = self.product_id.avg_price

            vals.update({"avg_price": avg_price, "std_cost": std_cost})

        return super(PurchaseOrderLine, self).write(vals)
