# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    """Extend settings to add ESD configuration parameters."""
    _inherit = 'res.config.settings'

    esd_no_po_lead_time = fields.Integer(
        string='No Purchase Order Lead Time (days)',
        default=999,
        config_parameter='ol_sale_lead_time.no_po_lead_time',
        help='Lead time used when component has no vendor pricelist'
    )

    esd_default_mfg_lead_time = fields.Integer(
        string='Default Manufacturing Lead Time (days)',
        default=5,
        config_parameter='ol_sale_lead_time.default_mfg_lead_time',
        help='Additional days for standard manufacturing orders'
    )

    esd_rush_order_lead_time = fields.Integer(
        string='Rush Order Lead Time (days)',
        default=2,
        config_parameter='ol_sale_lead_time.rush_order_lead_time',
        help='Additional days for rush manufacturing orders'
    )

    esd_mfg_security_lead_time = fields.Integer(
        string='Manufacturing Security Lead Time (days)',
        default=1,
        config_parameter='ol_sale_lead_time.mfg_security_lead_time',
        help='Buffer time added to all manufacturing orders'
    )

    esd_max_bom_depth = fields.Integer(
        string='Max BoM Depth',
        default=5,
        config_parameter='ol_sale_lead_time.max_bom_depth',
        help='Maximum nested BoM levels to prevent infinite loops'
    )

    esd_calculation_timeout = fields.Integer(
        string='Calculation Timeout (seconds)',
        default=30,
        config_parameter='ol_sale_lead_time.calculation_timeout',
        help='Maximum time allowed for ESD calculation'
    )
