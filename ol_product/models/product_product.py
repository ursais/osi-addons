# Import Python libs
import base64
from collections import defaultdict

# Import Odoo Libs
from odoo import api, models


class ProductProduct(models.Model):
    """
    Reporting functions
    """

    _inherit = "product.product"

    # METHODS #####

    def get_label_barcode(self):
        """
        Get a base64 encoded picture of the barcode for this product
        """
        self.ensure_one()

        barcode = self.env["ir.actions.report"].barcode(
            "Code128", self.default_code, width=600, height=160
        )

        # turn the barcode string into base64 encoding ready to be put into <img src="..." />
        return base64.b64encode(barcode)

    def get_supplier_code(self, supplier=None):
        """
        Get the supplier's sku if given, otherwise take the first one
        """
        self.ensure_one()

        seller_ids = self.seller_ids

        if supplier:
            seller_ids = seller_ids.filtered(lambda s: s.partner_id == supplier)

        if not seller_ids or not seller_ids[0].product_code:
            return self.default_code

        return seller_ids[0].product_code

    def get_systems_data_containing_these_components(
        self, company=False, include_inactive_options=False
    ):

        product_template_data = defaultdict(set)

        if not self:
            return product_template_data

        company = company or self.env.company
        query = f"""
            SELECT
                DISTINCT ptav.product_tmpl_id AS product_tmpl_id,
                component.id AS product_id,
                pav.company_id AS company_id
            FROM
                product_attribute_value pav
            JOIN product_product component ON
                component.id = pav.product_id
            JOIN product_template_attribute_value ptav ON
                ptav.product_attribute_value_id = pav.id
            JOIN product_template pt ON
                pt.id = ptav.product_tmpl_id
            LEFT JOIN product_template_company_display_rel company_rel ON
                company_rel.product_template_id = pt.id
            WHERE
                -- The components the systems need to contain
                component.id IN %(product_ids)s
                -- The Product Attribute Value must be for the correct company
                AND pav.company_id = %(company_id)s
                -- The System is enabled for the given company or is global
                AND (company_rel.company_id = %(company_id)s OR company_rel.company_id IS NULL)
                -- Ex/Include inactive options
                {"" if include_inactive_options else "AND ptav.ptav_active = TRUE"}
            """

        query_args = {"product_ids": tuple(self.ids), "company_id": company.id}
        self.env.cr.execute(query, query_args)
        results = self.env.cr.dictfetchall()

        for res in results:
            product_template_data[res["product_id"]].add(res["product_tmpl_id"])

        return product_template_data

    def is_stockable(self):
        """
        Check if this product should have stock values or not
        """

        if self.has_configurable_attributes or self.type != "product":
            # Product should not have stock values
            # a.k.a Systems, Services, Virtual, Consumable
            return False

        return True

    def get_related_phantom_bom_ids(self):
        # Find all Phantom Boms
        all_phantom_boms = self.env["mrp.bom"].search([("type", "=", "phantom")])

        # We only need Products or Consumables
        valid_product_variants = self.filtered(lambda p: p.type in ["consu", "product"])

        # Find all Phantom Bom Lines with this product_id
        # `mrp.bom.line``product_id` refers to `product.product`
        mrp_bom_lines = self.env["mrp.bom.line"].search(
            [
                ("product_id", "in", valid_product_variants.ids),
                ("bom_id", "in", all_phantom_boms.ids),
            ]
        )

        # Get the `mrp.bom` from the `mrp.bom.line`
        phantom_boms = mrp_bom_lines.mapped("bom_id")
        return phantom_boms

    @api.depends(lambda self: (self._rec_name,) if self._rec_name else ())
    def _compute_display_name(self):
        """Change display name to just show internal reference and name."""
        for product in self:
            product.display_name = f"[{product.default_code}] {product.name}"

    # END #########
