# Import Odoo libs
from odoo import api, fields, models
from odoo.tools import float_round


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
        help="This is the sum of the sales price of all BoM Components",
    )
    attr_val_lst_price = fields.Float(
        "Values Extra Price",
        digits="Product Price",
        help="This is the sum of the sales price of all attribute values",
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
            attribute_value_obj = self.env["product.attribute.value"]
            value_ids = product.product_template_attribute_value_ids.mapped(
                "product_attribute_value_id"
            ).filtered(lambda l: not l.product_id)
            extra_prices = attribute_value_obj.get_attribute_value_extra_prices(
                product_tmpl_id=product.product_tmpl_id.id, pt_attr_value_ids=value_ids
            )
            additional_total = product._get_non_config_set_bom_lines()
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

    @api.depends("list_price", "price_extra", "bom_lst_price")
    @api.depends_context("uom")
    def _compute_product_lst_price(self):
        """Override method to insert set price from bom"""
        res = super()._compute_product_lst_price()
        to_uom = None
        if "uom" in self._context:
            to_uom = self.env["uom.uom"].browse(self._context["uom"])

        for product in self:
            if to_uom:
                list_price = product.uom_id._compute_price(product.list_price, to_uom)
            else:
                list_price = product.list_price

            product.lst_price = list_price + product.price_extra

        return res

    def write(self, vals):
        res = super().write(vals)
        if "lst_price" in vals or "price_extra" in vals or "list_price" in vals:
            for product in self:
                product._set_sale_price_from_bom()
                product._set_approved_total_cost_from_bom()
        return res

    def button_bom_sale_price(self):
        """
        Button method on the product form to trigger price computation.

        This method is linked to a button in the product form view, and when clicked,
        it triggers the recomputation of the BoM sale price.
        """
        self._compute_product_lst_price()
        self._set_approved_total_cost_from_bom()

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

        for product in self:
            product._set_sale_price_from_bom(boms_to_recompute)
            product._set_approved_total_cost_from_bom(boms_to_recompute)

    def _set_sale_price_from_bom(self, boms_to_recompute=False):
        """
        Set the BoM list price for the product.

        This method calculates and sets the list price of the product based on its
        associated BoM. It handles both normal and byproduct cases.
        """
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
        sale_total = 0

        for line in bom.bom_line_ids:
            if line._skip_bom_line(self):
                continue

            if line.child_bom_id and line.child_bom_id in boms_to_recompute:
                child_sale_total = line.product_id._compute_bom_sale_price(
                    line.child_bom_id, boms_to_recompute=boms_to_recompute
                )
                sale_total += (
                    line.product_id.uom_id._compute_price(
                        child_sale_total, line.product_uom_id
                    )
                    * line.product_qty
                )
            else:
                sale_total += (
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
                return sale_total * byproduct_cost_share / 100 / product_uom_qty
        else:
            byproduct_cost_share = sum(bom.byproduct_ids.mapped("cost_share"))
            if byproduct_cost_share:
                sale_total *= float_round(
                    1 - byproduct_cost_share / 100, precision_rounding=0.0001
                )
            return bom.product_uom_id._compute_price(
                sale_total / bom.product_qty, self.uom_id
            )

    def _set_approved_total_cost_from_bom(self, boms_to_recompute=False):
        """
        Set the BoM total cost for the product.

        This method calculates and sets the total cost of the product based on its
        associated BoM. It handles both normal and byproduct cases.
        """
        self.ensure_one()
        bom = self.env["mrp.bom"]._bom_find(self)[self]
        if bom:
            self.approved_total_cost = self._compute_bom_custom_cost(
                bom, boms_to_recompute=boms_to_recompute
            )
        else:
            bom = self.env["mrp.bom"].search(
                [("byproduct_ids.product_id", "=", self.id)],
                order="sequence, product_id, id",
                limit=1,
            )
            if bom:
                cost = self._compute_bom_custom_cost(
                    bom, boms_to_recompute=boms_to_recompute, byproduct_bom=True
                )
                if cost:
                    self.approved_total_cost = cost

    def _compute_bom_custom_cost(
        self,
        bom,
        boms_to_recompute=False,
        byproduct_bom=False,
    ):
        """
        Compute the total cost based on the BoM, including child BoMs and byproducts.

        This method computes the total cost for a product based on its BoM.
        It takes into account all BoM lines, including nested child BoMs and any byproducts
        that affect the pricing.
        """
        self.ensure_one()
        if not bom:
            return 0
        if not boms_to_recompute:
            boms_to_recompute = []
        cost_total = 0

        for line in bom.bom_line_ids:
            if line._skip_bom_line(self):
                continue
            if line.child_bom_id and line.child_bom_id in boms_to_recompute:
                child_cost_total = line.product_id._compute_bom_custom_cost(
                    line.child_bom_id, boms_to_recompute=boms_to_recompute
                )
                cost_total += (
                    line.product_id.uom_id._compute_price(
                        child_cost_total, line.product_uom_id
                    )
                    * line.product_qty
                )
            else:
                cost_total += (
                    line.product_id.uom_id._compute_price(
                        line.product_id.approved_total_cost, line.product_uom_id
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
                return cost_total * byproduct_cost_share / 100 / product_uom_qty
        else:
            byproduct_cost_share = sum(bom.byproduct_ids.mapped("cost_share"))
            if byproduct_cost_share:
                cost_total *= float_round(
                    1 - byproduct_cost_share / 100, precision_rounding=0.0001
                )
            return bom.product_uom_id._compute_price(
                cost_total / bom.product_qty, self.uom_id
            )

    def _compute_product_price_extra(self):
        """
        This overrides the price extra compute to properly handle different configuration scenarios such as
        extra price only,
        extra prices with qty,
        bom's with compute from bom,
        bom's with qty and compute from bom,
        extra prices with boms and qty.
        """
        standard_products = self.filtered(lambda product: not product.bom_ids)
        config_products = self - standard_products

        if standard_products:
            super()._compute_product_price_extra()

        for product in config_products:
            attribute_value_obj = self.env["product.attribute.value"]
            value_ids = (
                product.product_template_attribute_value_ids.product_attribute_value_id
            )

            # Get extra prices from attribute values
            extra_prices = attribute_value_obj.get_attribute_value_extra_prices(
                product_tmpl_id=product.product_tmpl_id.id, pt_attr_value_ids=value_ids
            )

            # Get BoM components for this product variant
            bom = self.env["mrp.bom"]._bom_find(product)[product]
            bom_component_product_ids = (
                bom.bom_line_ids.mapped("product_id.id") if bom else []
            )

            attr_val_lst_price = 0.0  # Initialize attribute value list price

            # Calculate attr_val_lst_price based on attribute value prices and quantities
            for attr_value_id, price in extra_prices.items():
                matching_records = product.product_attribute_value_qty_ids.filtered(
                    lambda l: l.attr_value_id.id == attr_value_id
                )

                attr_value = self.env["product.attribute.value"].browse(attr_value_id)
                if (
                    attr_value.product_id
                    and attr_value.product_id.id in bom_component_product_ids
                ):
                    # Skip as it’s accounted for in BoM
                    continue

                if matching_records:
                    additional_qty = sum(matching_records.mapped("qty"))
                    attr_val_lst_price += (
                        price * additional_qty if additional_qty else price
                    )
                else:
                    attr_val_lst_price += price

            # Set attr_val_lst_price as an informative field
            # product.attr_val_lst_price = attr_val_lst_price
            self.env.cr.execute(
                "update product_product set attr_val_lst_price=%s where id=%s",
                (
                    attr_val_lst_price,
                    product.id,
                ),
            )

            # Final calculation for price_extra
            total_price_extra = product.bom_lst_price + attr_val_lst_price
            if bom.type == "phantom":
                total_price_extra = attr_val_lst_price

            # Directly assign to override any existing value
            product.price_extra = total_price_extra

        return None


# END #########
