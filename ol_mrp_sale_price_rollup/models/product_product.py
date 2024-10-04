# Import Odoo libs
from odoo import api, fields, models
from odoo.tools import float_round
from odoo.exceptions import UserError


class ProductProduct(models.Model):
    """
    Inherit Product model to override specific methods related
    to Bill of Materials (BoM).
    """

    _inherit = "product.product"

    # Define a new field to store the list price derived from the BoM
    bom_lst_price = fields.Float(
        "BoM List Price",
        digits="Product Price",
        help="This is the sum of the sales prices from all components on BoM",
    )

    # METHODS ##########

    """
    The methods below are similar to the compute cost from BoM methods.
    They provide functionality to compute the sale price of products based on their
    Bill of Materials (BoM) and associated attributes.
    """

    def _get_non_config_set_bom_lines(self):
        """
        Compute the total price for BoM lines that are not configurable sets.

        This method calculates the total price of all BoM lines that do not have
        a configurable set. It includes the recursive computation of child BoMs
        and their associated products.
        """
        self.ensure_one()
        current_bom = self.env["mrp.bom"]._bom_find(self)[self]
        additional_total = 0

        for bom_line in current_bom.bom_line_ids:
            if bom_line.child_bom_id:
                # If there is a child BoM, iterate through its lines
                # and compute the total price
                for child_bom_line in bom_line.child_bom_id.bom_line_ids:
                    additional_total += (
                        child_bom_line.product_id.uom_id._compute_price(
                            child_bom_line.product_id.lst_price,
                            child_bom_line.product_uom_id,
                        )
                        * child_bom_line.product_qty
                    )
            else:
                # If there is no child BoM, compute the price directly from
                # the current BoM line
                additional_total += (
                    bom_line.product_id.uom_id._compute_price(
                        bom_line.product_id.lst_price, bom_line.product_uom_id
                    )
                    * bom_line.product_qty
                )
        return additional_total

    def _get_bom_sale_price(self):
        """
        Calculate the sale price from the BoM, including attribute value extras.

        This method sums up the BoM total price and any extra prices associated
        with the product's attributes.
        """
        for product in self:
            # Get BoM components for the product
            bom = self.env["mrp.bom"]._bom_find(self)[self]
            bom_components = bom.bom_line_ids.mapped("product_id.id") if bom else []

            # Get attribute values where product_id is either not set or not a BoM component
            attribute_value_obj = self.env["product.attribute.value"]
            value_ids = product.product_template_attribute_value_ids.mapped(
                "product_attribute_value_id"
            ).filtered(
                lambda l: not l.product_id or l.product_id.id not in bom_components
            )

            # Get extra prices for the filtered attribute values
            extra_prices = attribute_value_obj.get_attribute_value_extra_prices(
                product_tmpl_id=product.product_tmpl_id.id, pt_attr_value_ids=value_ids
            )

            # Calculate additional price from non-config BoM lines
            additional_total = product._get_non_config_set_bom_lines()
            self.bom_lst_price = additional_total
            self.price_extra = sum(extra_prices.values())

            # Return total price
            return additional_total + sum(extra_prices.values())

    @api.onchange("lst_price")
    def _set_product_lst_price(self):
        """
        Override method to adjust product list price based on user input.

        This method recalculates and updates the product's list price whenever the
        'lst_price' field is changed. It adjusts for any extra pricing and converts
        the price based on the specified unit of measure.
        """
        for product in self.filtered(lambda l: not l.config_ok):
            if self._context.get("uom"):
                value = (
                    self.env["uom.uom"]
                    .browse(self._context["uom"])
                    ._compute_price(product.lst_price, product.uom_id)
                )
            else:
                value = product.lst_price
            value -= product.price_extra
            product.write({"list_price": value})

    @api.depends("list_price", "price_extra")
    @api.depends_context("uom")
    def _compute_product_lst_price(self):
        """
        Compute the product list price, considering extra prices and the BoM.

        This method calculates the list price of the product, taking into account
        any additional costs from product attributes and the BoM structure.
        """
        rec = super()._compute_product_lst_price()
        for product in self.filtered(lambda l: l.config_ok):
            additional_total = product._get_bom_sale_price()
            product.lst_price = additional_total
            if self.env.context.get("from_product_template", False):
                product.product_tmpl_id.list_price = additional_total
        return rec

    def button_bom_sale_price(self):
        """
        Button method on the product form to trigger price computation.

        This method is linked to a button in the product form view, and when clicked,
        it triggers the recomputation of the BoM sale price.
        """
        self._compute_product_lst_price()

    def action_bom_sale_price(self):
        """
        Compute the BoM sale prices for products.

        This method finds all relevant BoMs for the current products and triggers the
        computation of sale prices based on these BoMs.
        """
        boms_to_recompute = self.env["mrp.bom"].search(
            [
                "|",
                ("product_id", "in", self.ids),
                "&",
                ("product_id", "=", False),
                ("product_tmpl_id", "in", self.mapped("product_tmpl_id").ids),
            ]
        )
        raise UserError(boms_to_recompute)
        for product in self:
            product._set_sale_price_from_bom(boms_to_recompute)

    def _set_sale_price_from_bom(self, boms_to_recompute=False):
        """
        Set the BoM list price for the product.

        This method calculates and sets the list price of the product based on its
        associated BoM. It handles both normal and byproduct cases.
        """
        self.ensure_one()
        bom = self.env["mrp.bom"]._bom_find(self)[self]
        raise UserError(bom)
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
        """
        Compute the sale price based on the BoM, including child BoMs and byproducts.

        This method computes the total sale price for a product based on its BoM.
        It takes into account all BoM lines, including nested child BoMs and any byproducts
        that affect the pricing.
        """
        self.ensure_one()
        if not bom:
            return 0
        if not boms_to_recompute:
            boms_to_recompute = []
        total = 0

        for line in bom.bom_line_ids:
            if line._skip_bom_line(self):
                continue

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

        # Handle cost allocation for byproducts
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
