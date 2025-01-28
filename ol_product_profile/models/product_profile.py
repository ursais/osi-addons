# Import Odoo libs
from odoo import api, fields, models
import odoo.addons.product_profile.models.product_profile as product_profile_module


# Store the original fields to exclude function to prevent recursion error
original_get_profile_fields_to_exclude = (
    product_profile_module.get_profile_fields_to_exclude
)


# Inherit original fields to exclude method to add a new field.
def custom_get_profile_fields_to_exclude():
    # Call the original function to get default fields
    fields_to_exclude = original_get_profile_fields_to_exclude()

    # Add your custom fields to the exclusion list
    fields_to_exclude.append("has_products")

    return fields_to_exclude


# Apply the monkey-patch
product_profile_module.get_profile_fields_to_exclude = (
    custom_get_profile_fields_to_exclude
)


class ProductProfile(models.Model):
    """Add fields to product profiles."""

    _inherit = "product.profile"

    # DEFAULT METHODS #####

    def _get_default_uom_id(self):
        return self.env.ref("uom.product_uom_unit")

    # END ##########
    # COLUMNS #####

    has_products = fields.Boolean(
        string="Has Products",
        compute="_compute_has_products",
    )
    uom_id = fields.Many2one(
        "uom.uom",
        string="Unit of Measure",
        default=_get_default_uom_id,
    )
    uom_po_id = fields.Many2one(
        "uom.uom",
        "Purchase UoM",
    )
    route_ids = fields.Many2many(
        "stock.route",
        "stock_route_product_profile",
        "product_profile_id",
        "route_id",
        string="Routes",
        domain=[("product_selectable", "=", True)],
        depends_context=["company", "allowed_companies"],
    )
    invoice_policy = fields.Selection(
        selection=[
            ("order", "Ordered quantities"),
            ("delivery", "Delivered quantities"),
        ],
        string="Invoicing Policy",
        help="Ordered Quantity: Invoice quantities ordered by the customer.\n"
        "Delivered Quantity: Invoice quantities delivered to the customer.",
    )
    tracking = fields.Selection(
        [
            ("serial", "By Unique Serial Number"),
            ("lot", "By Lots"),
            ("none", "No Tracking"),
        ],
        string="Tracking",
        required=True,
        default="none",
        compute="_compute_tracking",
        store=True,
        readonly=False,
        precompute=True,
        help="Ensure the traceability of a storable product in your warehouse.",
    )

    # END ##########
    # METHODS ##########

    def _compute_has_products(self):
        # If any products have the profile assigned then helper field has_products
        # is true so certain fields can be readonly to the user.
        for rec in self:
            rec.has_products = False
            products = self.env["product.product"].search([("profile_id", "=", rec.id)])
            if products:
                rec.has_products = True

    @api.depends("detailed_type")
    def _compute_tracking(self):
        self.filtered(
            lambda t: not t.tracking
            or t.detailed_type in ("consu", "service")
            and t.tracking != "none"
        ).tracking = "none"

    # END ##########
