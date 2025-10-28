# Import Odoo libs
from odoo import fields, models, api
from odoo.exceptions import ValidationError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    ### COLUMNS #######
    is_ups_delivery = fields.Boolean(
        string="Is UPS Delivery",
        compute="_compute_is_ups_delivery",
        default=False,
        store=True,
    )
    ups_request_log = fields.Text("UPS API Request Log", readonly=True, copy=False)
    ups_response_log = fields.Text("UPS API Response Log", readonly=True, copy=False)

    forward_agent = fields.Many2one(
        comodel_name="res.partner",
        string="Forward Agent",
        help="Set a specific forward agent for UPS shipping requests",
    )
    ## END COLUMNS ###

    @api.depends("carrier_id", "carrier_id.delivery_type")
    def _compute_is_ups_delivery(self):
        for picking in self:
            picking.is_ups_delivery = (
                picking.carrier_id
                and picking.carrier_id.delivery_type in ["ups_rest", "ups"]
            )

    @api.onchange("forward_agent")
    def _onchange_forward_agent(self):
        if self.forward_agent and not self.forward_agent.vat:
            raise ValidationError("The forward agent requires a Tax Number set!")
