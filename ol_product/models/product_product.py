# Import Python libs
import base64

# Import Odoo Libs
from odoo import models


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

    # END #########
