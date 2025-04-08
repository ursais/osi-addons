# Import Odoo libs
from odoo import fields, models


class ResPartner(models.Model):
    """
    Adding fields to Partner.
    """

    _inherit = "res.partner"

    # COLUMNS ##########

    approved_vendor = fields.Boolean(
        default=False,
        help="Indicates if the vendor is approved for purchasing.",
    )
    default_shipping_notes = fields.Text(
        string="Default Shipping Notes",
        company_dependent=True,
    )
    supplier_delivery_method_id = fields.Many2one(
        comodel_name="delivery.carrier",
        string="Supplier Delivery Method",
        company_dependent=True,
    )
    default_incoterms_id = fields.Many2one(
        comodel_name="account.incoterms",
        string="Default Incoterms",
    )
    default_supplier_contact_ids = fields.Many2many(
        comodel_name="res.partner",
        relation="partner_supplier_contact_rel",
        column1="partner_id",
        column2="contact_id",
        string="Default Purchasing Contacts",
    )

    # END ##########
