# Import Odoo libs
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class StockPicking(models.Model):
    """
    Inherit Stock Picking Object to add Credit Limit.
    """

    _inherit = "stock.picking"

    # COLUMNS #####

    credit_hold = fields.Boolean("Credit Hold", related="sale_id.credit_hold")

    # END #########
    # METHODS #####

    def action_assign(self):
        for picking in self:
            if picking.sale_id and picking.sale_id.credit_hold:
                raise UserError(
                    _("Delivery cannot be confirmed due to customer's credit hold.")
                )
        return super().action_assign()

    def button_validate(self):
        for picking in self:
            if picking.sale_id and picking.sale_id.credit_hold:
                raise UserError(
                    _("Delivery cannot be confirmed due to customer's credit hold.")
                )
        return super().button_validate()

    # END #########
