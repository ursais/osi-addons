# Import Odoo libs
from odoo import api, fields, models
from odoo.tools import float_round


class ProductProduct(models.Model):
    """Inherit Product for Method Overriding."""

    _inherit = "product.product"

    bom_lst_price = fields.Float(
        "BoM List Price",
        digits="Product Price",
        help="This is the sum of the extra price of all attributes",
    )

    # METHODS ##########
    """ The methods below are very similar to the compute cost from bom methods """

    def _get_non_config_set_bom_lines(self):
        self.ensure_one()
        attribute_value =  self.env["product.attribute.value"]
        current_bom = self.env["mrp.bom"]._bom_find(self)[self]
        additional_total = 0
        for bom_line in current_bom.bom_line_ids:
            if bom_line.child_bom_id:
                for child_bom_line in bom_line.child_bom_id.bom_line_ids:
                    additional_total +=  (
                        child_bom_line.product_id.uom_id._compute_price(
                            child_bom_line.product_id.lst_price, child_bom_line.product_uom_id
                        )
                        * child_bom_line.product_qty)
            elif not bom_line.child_bom_id:
                additional_total +=  (
                    bom_line.product_id.uom_id._compute_price(
                        bom_line.product_id.lst_price, bom_line.product_uom_id
                    )
                    * bom_line.product_qty)
        return additional_total

    def _get_bom_sale_price(self):
        for product in self:
            attribute_value_obj = self.env["product.attribute.value"]
            value_ids = product.product_template_attribute_value_ids.mapped("product_attribute_value_id").filtered(lambda l:not l.product_id)
            extra_prices = attribute_value_obj.get_attribute_value_extra_prices(
                product_tmpl_id=product.product_tmpl_id.id, pt_attr_value_ids=value_ids
            )
            additional_total = product._get_non_config_set_bom_lines()
            return additional_total + sum(extra_prices.values())

    @api.onchange('lst_price')
    def _set_product_lst_price(self):
        """Override Method to bypass update Product lst Price"""
        for product in self.filtered(lambda l: not l.config_ok):
            if self._context.get('uom'):
                value = self.env['uom.uom'].browse(self._context['uom'])._compute_price(product.lst_price, product.uom_id)
            else:
                value = product.lst_price
            value -= product.price_extra
            product.write({'list_price': value})

    @api.depends('list_price', 'price_extra')
    @api.depends_context('uom')
    def _compute_product_lst_price(self):
        rec = super()._compute_product_lst_price()
        for product in self.filtered(lambda l:l.config_ok):
            additional_total = product._get_bom_sale_price()
            product.lst_price = additional_total
            if self.env.context.get("from_product_template",False):
                product.product_tmpl_id.list_price = additional_total
        return rec

    def button_bom_sale_price(self):
        """Button method on the product form."""
        self._compute_product_lst_price()

    def action_bom_sale_price(self):
        """Get the bom's to compute."""
        boms_to_recompute = self.env["mrp.bom"].search(
            [
                "|",
                ("product_id", "in", self.ids),
                "&",
                ("product_id", "=", False),
                ("product_tmpl_id", "in", self.mapped("product_tmpl_id").ids),
            ]
        )

        for product in self:
            product._set_sale_price_from_bom(boms_to_recompute)

    def _set_sale_price_from_bom(self, boms_to_recompute=False):
        """ets the bom_lst_price."""
        self.ensure_one()
        bom = self.env["mrp.bom"]._bom_find(self)[self]
        if bom:
            self.bom_lst_price = self._compute_bom_sale_price(
                bom, boms_to_recompute=boms_to_recompute
            )
        else:
            bom = self.env["mrp.bom"].search(
                [("byproduct_ids.product_id", "=", self.id)],
                order="sequence, product_id, id",
                limit=1,
            )
            if bom:
                price = self._compute_bom_sale_price(
                    bom, boms_to_recompute=boms_to_recompute, byproduct_bom=True
                )
                if price:
                    self.bom_lst_price = price

    def _compute_bom_sale_price(
        self,
        bom,
        boms_to_recompute=False,
        byproduct_bom=False,
    ):
        """Cycle through the BoM and child BoM's to compute the sale price."""
        self.ensure_one()
        if not bom:
            return 0
        if not boms_to_recompute:
            boms_to_recompute = []
        total = 0

        # Leaving commented incase this is needed in the future,
        # This code will add operation costs into the sales price if desired.
        # for opt in bom.operation_ids:
        #     if opt._skip_operation_line(self):
        #         continue
        #     duration_expected = (
        #         opt.workcenter_id._get_expected_duration(self)
        #         + opt.time_cycle * 100 / opt.workcenter_id.time_efficiency
        #     )
        #     total += (duration_expected / 60) * opt._total_cost_per_hour()

        for line in bom.bom_line_ids:
            if line._skip_bom_line(self):
                continue

            # Compute recursive if line has `child_line_ids`
            if line.child_bom_id and line.child_bom_id in boms_to_recompute:
                child_total = line.product_id._compute_bom_sale_price(
                    line.child_bom_id, boms_to_recompute=boms_to_recompute
                )
                total += (
                    line.product_id.uom_id._compute_price(
                        child_total, line.product_uom_id
                    )
                    * line.product_qty
                )
            else:
                total += (
                    line.product_id.uom_id._compute_price(
                        line.product_id.lst_price, line.product_uom_id
                    )
                    * line.product_qty
                )

        # Ensure byproduct costs are part of the pricing
        if byproduct_bom:
            byproduct_lines = bom.byproduct_ids.filtered(
                lambda b: b.product_id == self and b.cost_share != 0
            )
            product_uom_qty = 0
            for line in byproduct_lines:
                product_uom_qty += line.product_uom_id._compute_quantity(
                    line.product_qty, self.uom_id, round=False
                )
            byproduct_cost_share = sum(byproduct_lines.mapped("cost_share"))
            if byproduct_cost_share and product_uom_qty:
                return total * byproduct_cost_share / 100 / product_uom_qty
        else:
            byproduct_cost_share = sum(bom.byproduct_ids.mapped("cost_share"))
            if byproduct_cost_share:
                total *= float_round(
                    1 - byproduct_cost_share / 100, precision_rounding=0.0001
                )
            return bom.product_uom_id._compute_price(
                total / bom.product_qty, self.uom_id
            )

    # END #########
