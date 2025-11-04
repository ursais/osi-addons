# Copyright (C) 2024 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class CrmLead(models.Model):
    """
    Extend CRM Lead/Opportunity model to add job costing data points.
    
    These fields will be visible conditionally based on lead type and
    will flow to JCS when creating a job costing record from an opportunity.
    """
    _inherit = 'crm.lead'

    # Job Costing Fields
    jcs_budget_amount = fields.Monetary(
        string='Budget Amount',
        currency_field='company_currency_id',
        help='Estimated budget amount for job costing',
        tracking=True,
    )
    
    jcs_estimated_cost = fields.Monetary(
        string='Estimated Cost',
        currency_field='company_currency_id',
        help='Estimated cost for this opportunity',
        tracking=True,
    )
    
    jcs_job_type = fields.Char(
        string='Job Type',
        help='Type or category of job for costing purposes',
        tracking=True,
    )
    
    jcs_start_date = fields.Date(
        string='Expected Start Date',
        help='Expected start date for the job',
        tracking=True,
    )
    
    jcs_end_date = fields.Date(
        string='Expected End Date',
        help='Expected end date for the job',
        tracking=True,
    )
    
    jcs_duration_days = fields.Integer(
        string='Expected Duration (Days)',
        compute='_compute_jcs_duration_days',
        store=True,
        help='Expected duration of the job in days',
    )
    
    jcs_notes = fields.Text(
        string='Job Costing Notes',
        help='Additional notes for job costing purposes',
    )
    
    jcs_requires_job_costing = fields.Boolean(
        string='Requires Job Costing',
        default=False,
        help='Check this box if this opportunity requires job costing',
        tracking=True,
    )

    @api.depends('jcs_start_date', 'jcs_end_date')
    def _compute_jcs_duration_days(self):
        """
        Compute the duration in days based on start and end dates.
        
        Returns:
            None: Updates jcs_duration_days field
        """
        for lead in self:
            if lead.jcs_start_date and lead.jcs_end_date:
                if lead.jcs_end_date >= lead.jcs_start_date:
                    delta = lead.jcs_end_date - lead.jcs_start_date
                    lead.jcs_duration_days = delta.days
                else:
                    lead.jcs_duration_days = 0
            else:
                lead.jcs_duration_days = 0

    def action_new_job_costing(self):
        """
        Action to create a new job costing record from this opportunity.
        
        This method prepares the data from the opportunity and creates
        a job costing record with the relevant fields populated.
        
        Returns:
            dict: Action dictionary to open the job costing form
        """
        self.ensure_one()
        
        # Prepare values for job costing creation
        jcs_values = self._prepare_jcs_values()
        
        # Check if job costing model exists
        # If a custom job costing model exists, use it; otherwise return a warning
        job_costing_model = self.env.get('job.costing')
        if not job_costing_model:
            # Fallback: Create analytic account or project if available
            # This is a placeholder - actual implementation depends on JCS structure
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Job Costing System',
                    'message': 'Job costing data prepared. Integration with JCS required.',
                    'type': 'warning',
                    'sticky': False,
                }
            }
        
        # Create job costing record
        job_costing = job_costing_model.create(jcs_values)
        
        return {
            'name': 'Job Costing',
            'type': 'ir.actions.act_window',
            'res_model': 'job.costing',
            'view_mode': 'form',
            'res_id': job_costing.id,
            'target': 'current',
        }

    def _prepare_jcs_values(self):
        """
        Prepare values dictionary for job costing creation.
        
        This method can be overridden by other modules to add additional
        fields or modify the values being passed to JCS.
        
        Returns:
            dict: Dictionary of values for job costing creation
        """
        self.ensure_one()
        return {
            'opportunity_id': self.id,
            'name': self.name or 'Job Costing from %s' % self.name,
            'budget_amount': self.jcs_budget_amount,
            'estimated_cost': self.jcs_estimated_cost,
            'job_type': self.jcs_job_type,
            'start_date': self.jcs_start_date,
            'end_date': self.jcs_end_date,
            'duration_days': self.jcs_duration_days,
            'notes': self.jcs_notes,
            'partner_id': self.partner_id.id if self.partner_id else False,
        }

    @api.model
    def create(self, vals):
        """
        Override create to handle job costing data initialization.
        
        Args:
            vals: Dictionary of field values
            
        Returns:
            crm.lead: Created record
        """
        lead = super(CrmLead, self).create(vals)
        
        # If job costing is required and start/end dates are set, compute duration
        if lead.jcs_requires_job_costing and lead.jcs_start_date and lead.jcs_end_date:
            lead._compute_jcs_duration_days()
        
        return lead

    def write(self, vals):
        """
        Override write to handle job costing data updates.
        
        Args:
            vals: Dictionary of field values to update
            
        Returns:
            bool: True if write successful
        """
        result = super(CrmLead, self).write(vals)
        
        # If dates are updated, recompute duration
        if 'jcs_start_date' in vals or 'jcs_end_date' in vals:
            self._compute_jcs_duration_days()
        
        return result
