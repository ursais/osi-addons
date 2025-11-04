# Copyright (C) 2024 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class CrmLead(models.Model):
    """
    Extend CRM Lead model to add monitoring-related fields.
    
    Adds:
    - monitoring_included: Boolean field to indicate if monitoring is included
    - monitoring_sales_associate_id: Sales associate assigned for monitoring
    """
    _inherit = 'crm.lead'

    monitoring_included = fields.Boolean(
        string='Monitoring Included',
        default=False,
        help='Check this box if monitoring is included in this opportunity.'
    )
    
    monitoring_sales_associate_id = fields.Many2one(
        'res.users',
        string='Monitoring Sales Associate',
        help='Sales associate responsible for monitoring this opportunity.'
    )
