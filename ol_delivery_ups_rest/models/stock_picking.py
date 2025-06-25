# Import Odoo libs
from odoo import fields, models, api


class StockPicking(models.Model):
    _inherit = "stock.picking"
    
    ### COLUMNS #######
    is_ups_delivery = fields.Boolean(
        string="Is UPS Delivery", compute="_compute_is_ups_delivery", default=False, store=True
    )
    ups_request_log = fields.Text("UPS API Request Log", readonly=True, copy=False)
    ups_response_log = fields.Text("UPS API Response Log", readonly=True, copy=False)
    ## END COLUMNS ###

    @api.depends("carrier_id", "carrier_id.delivery_type")
    def _compute_is_ups_delivery(self):
        for picking in self:
            picking.is_ups_delivery = picking.carrier_id and picking.carrier_id.delivery_type in ["ups_rest", "ups"]
