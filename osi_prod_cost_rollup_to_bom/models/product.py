# Copyright (C) 2021, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging
from datetime import datetime

from odoo import _, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_is_zero

_logger = logging.getLogger(__name__)


class ProductProduct(models.Model):
    _inherit = "product.product"

    std_cost_update_date = fields.Datetime(
        string="Standard Cost Update Date",
        copy=False,
        help="Last time the standard cost was performed on this product.",
    )

    def action_bom_cost(self):

        real_time_products = self.filtered(
            lambda p: p.valuation == "real_time" and p.valuation == "fifo"
        )
        if real_time_products:
            raise UserError(
                _(
                    "The costing method on some products %s is FIFO.\
                    The cost will be computed during manufacturing process.\
                    Use Standard Costing to update BOM cost manually."
                )
                % (real_time_products.mapped("display_name"))
            )

        else:
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
                if product.cost_method == "standard":
                    if product.product_tmpl_id.product_variant_count == 1:
                        new_price = product._get_price_from_bom(boms_to_recompute)

                        if not float_is_zero(
                            new_price - product.standard_price, precision_rounding=2
                        ):
                            product._change_standard_price(new_price)
                            product.product_tmpl_id.std_cost_update_date = (
                                datetime.now()
                            )
                            _logger.info(
                                "Product : %s Standard Price: %s ",
                                product.default_code,
                                str(product.product_tmpl_id.standard_price),
                            )
                    else:
                        new_price = product._get_price_from_bom(boms_to_recompute)
                        if type(new_price) == float and not float_is_zero(
                            new_price - product.standard_price, precision_rounding=2
                        ):
                            product._change_standard_price(new_price)
                            product.std_cost_update_date = datetime.now()
                            _logger.info(
                                "Product : %s Standard Price: %s ",
                                product.default_code,
                                str(product.standard_price),
                            )

    def _get_price_from_bom(self, boms_to_recompute=False):
        self.ensure_one()
        bom = self.env["mrp.bom"]._bom_find(product=self)
        # product has not changed
        return self.with_context(cost_all=True)._compute_bom_price(
            bom, boms_to_recompute=boms_to_recompute
        )

    def _compute_bom_price(self, bom, boms_to_recompute=False):
        self.ensure_one()
        if not boms_to_recompute:
            boms_to_recompute = []
        total = 0
        for opt in bom.operation_ids:
            duration_expected = (
                opt.workcenter_id.time_start
                + opt.workcenter_id.time_stop
                + opt.time_cycle
            )
            total += (duration_expected / 60) * opt.workcenter_id.costs_hour

        for line in bom.bom_line_ids:
            if line._skip_bom_line(self):
                continue

            # Compute recursive if line has `child_line_ids` and the  \
            # product has not been computed recently
            if (
                line.child_bom_id
                and (
                    line.child_bom_id in boms_to_recompute
                    or self.env.context.get("cost_all", True)
                )
                and (
                    not bom.std_cost_update_date
                    or not line.product_id.std_cost_update_date
                    or line.child_bom_id._update_bom(bom.std_cost_update_date)
                )
            ):
                child_total = line.product_id._compute_bom_price(
                    line.child_bom_id, boms_to_recompute=boms_to_recompute
                )

                total += (
                    line.product_id.uom_id._compute_price(
                        child_total, line.product_uom_id
                    )
                    * line.product_qty
                )
                if line.product_id.product_tmpl_id.product_variant_count == 1:
                    if not float_is_zero(
                        child_total - line.product_id.standard_price,
                        precision_rounding=2,
                    ):
                        line.product_id._change_standard_price(child_total)

                        line.product_id.product_tmpl_id.std_cost_update_date = (
                            datetime.now()
                        )
                        _logger.info(
                            "Product : %s Standard Price: %s ",
                            line.product_id.default_code,
                            str(line.product_id.product_tmpl_id.standard_price),
                        )
                else:
                    if not float_is_zero(
                        child_total - line.product_id.standard_price,
                        precision_rounding=2,
                    ):
                        line.product_id._change_standard_price(child_total)
                        line.product_id.std_cost_update_date = datetime.now()
                        _logger.info(
                            "Product : %s Standard Price: %s ",
                            line.product_id.default_code,
                            str(line.product_id.standard_price),
                        )
            else:
                ctotal = (
                    line.product_id.uom_id._compute_price(
                        line.product_id.standard_price, line.product_uom_id
                    )
                    * line.product_qty
                )

                total += ctotal

        bom.std_cost_update_date = datetime.now()
        if bom.product_qty > 0:
            return bom.product_uom_id._compute_price(
                total / bom.product_qty, self.uom_id
            )


class ProductTemplate(models.Model):
    _inherit = "product.template"

    std_cost_update_date = fields.Datetime(
        string="Standard Cost Update Date",
        copy=False,
        help="Last time the standard cost was performed on this product.",
    )
