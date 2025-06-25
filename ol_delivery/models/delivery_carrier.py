from odoo import models, api, fields, _
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import UserError
from odoo.addons.ol_base.models.tools import get_closest_next_workday_by_delta
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'
    
    # COLUMNS #######
    account_required = fields.Boolean(string="Shipping Account Required", help="The carrier shorthand of the delivery method we receive from the e-commerce platform", default=False)
    message_carrier = fields.Char(
        string="Carrier shorthand",
        help="The carrier shorthand of the delivery method we receive from the e-commerce platform",
        copy=False,
        required=False,
    )

    message_code = fields.Char(
        string="Carrier code",
        help="The carrier code of the delivery method we receive from the e-commerce platform",
        copy=False,
        required=False,
    )
    shipping_buffer = fields.Integer(
        string="Shipping Buffer",
        help="The number of buffer days before carrier pickup",
        company_dependent=True,
    )
    # END #########
    
    _sql_constraints = [
        (
            'uniq_message_code_and_carrier',
            'UNIQUE(company_id, message_code, message_carrier)',
            'Cannot have the same code and carrier for multiple delivery methods in the same company',
        )
    ]
    
    def get_package_type(self, weight, volume, default_package_type):
        return default_package_type
    
    def _convert_weight(self, weight, unit='KGS'):
        weight_uom_id = self.env['product.template']._get_weight_uom_id_from_ir_config_parameter()
        if unit == 'KGS':
            return weight_uom_id._compute_quantity(weight, self.env.ref('uom.product_uom_kgm'), round=False)
        elif unit == 'LBS':
            return weight_uom_id._compute_quantity(weight, self.env.ref('uom.product_uom_lb'), round=False)
        else:
            raise ValueError
    
    def rate_shipment(self, order):
        """
        If a `Delivery Account Number` was provided we don't want to calculate the delivery price
        """

        self.ensure_one()

        if order.delivery_account_number:

            return {
                'success': True,
                'price': 0.0,
                'carrier_price': 0.0,
                'error_message': False,
                'warning_message': _(
                    f'The shipping cost is 0.0 since a Delivery Account Number ({order.delivery_account_number}) was provided'
                ),
            }

        # If no `Delivery Account Number` was provided continue with the core workflow
        return super().rate_shipment(order)