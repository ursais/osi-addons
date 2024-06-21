# Import Odoo libs
from odoo import fields, models


class DeliveryCarrierMultiplier(models.Model):
    """

    New Object Delivery Carrier Multiplier

    Shipment Method Table to hold Masterdata for Shipment Method and Multiplier.
    The Table needs to hold Shipment Method and multiplier for each individual Company,
    so each line needs to have a Company Identifier.

    """

    _name = "delivery.carrier.multiplier"
    _description = "Shipment Method Master Data"
    _rec_name = "carrier"

    # COLUMNS ###

    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)
    carrier = fields.Char(string="Inbound Ship Method", required="1")
    multiplier = fields.Float(
        string="Cost Multiplier",
        default="1",
        help="""The multiplier is used on price reviews to calculate an estimated
          shipping cost for the product (Multiplier * Product Weight)""",
    )

    # END #######
