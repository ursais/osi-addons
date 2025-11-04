# Copyright (C) 2024 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class SaleOrder(models.Model):
    """
    Extend Sale Order model to receive job costing data from opportunities.
    
    When a sale order is created from an opportunity with job costing data,
    this data will be available on the sale order for further processing.
    """
    _inherit = 'sale.order'

    # Job Costing Fields from Opportunity
    jcs_budget_amount = fields.Monetary(
        string='Budget Amount',
        currency_field='currency_id',
        help='Budget amount from opportunity',
        tracking=True,
    )
    
    jcs_estimated_cost = fields.Monetary(
        string='Estimated Cost',
        currency_field='currency_id',
        help='Estimated cost from opportunity',
        tracking=True,
    )
    
    jcs_job_type = fields.Char(
        string='Job Type',
        help='Job type from opportunity',
        tracking=True,
    )
    
    jcs_start_date = fields.Date(
        string='Expected Start Date',
        help='Expected start date from opportunity',
        tracking=True,
    )
    
    jcs_end_date = fields.Date(
        string='Expected End Date',
        help='Expected end date from opportunity',
        tracking=True,
    )
    
    jcs_duration_days = fields.Integer(
        string='Expected Duration (Days)',
        help='Expected duration in days from opportunity',
    )
    
    jcs_notes = fields.Text(
        string='Job Costing Notes',
        help='Job costing notes from opportunity',
    )
    
    jcs_requires_job_costing = fields.Boolean(
        string='Requires Job Costing',
        help='Indicates if this sale order requires job costing',
        tracking=True,
    )

    @api.model
    def create(self, vals):
        """
        Override create to copy job costing data from opportunity if available.
        
        Args:
            vals: Dictionary of field values
            
        Returns:
            sale.order: Created record
        """
        # If opportunity_id is provided, copy job costing data
        if 'opportunity_id' in vals and vals.get('opportunity_id'):
            opportunity = self.env['crm.lead'].browse(vals['opportunity_id'])
            if opportunity.jcs_requires_job_costing:
                vals.update({
                    'jcs_budget_amount': opportunity.jcs_budget_amount,
                    'jcs_estimated_cost': opportunity.jcs_estimated_cost,
                    'jcs_job_type': opportunity.jcs_job_type,
                    'jcs_start_date': opportunity.jcs_start_date,
                    'jcs_end_date': opportunity.jcs_end_date,
                    'jcs_duration_days': opportunity.jcs_duration_days,
                    'jcs_notes': opportunity.jcs_notes,
                    'jcs_requires_job_costing': opportunity.jcs_requires_job_costing,
                })
        
        return super(SaleOrder, self).create(vals)
