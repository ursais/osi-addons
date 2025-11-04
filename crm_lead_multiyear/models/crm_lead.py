# Copyright (C) 2024 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    x_multiyear = fields.Boolean(
        string='Multi-Year',
        default=False,
        help='Indicates if this is a multi-year project'
    )
    x_number_of_years = fields.Integer(
        string='Number of Years',
        help='Number of years for the multi-year project (1-20)'
    )

    @api.constrains('x_number_of_years')
    def _check_number_of_years(self):
        """
        Validate that number of years is between 1 and 20 when multi-year is selected
        """
        for lead in self:
            if lead.x_multiyear and lead.x_number_of_years:
                if lead.x_number_of_years < 1 or lead.x_number_of_years > 20:
                    raise ValidationError(
                        _('Number of years must be between 1 and 20.')
                    )

    @api.onchange('x_project_type')
    def _onchange_project_type(self):
        """
        Reset multi-year fields when project type changes away from
        eligible types
        """
        eligible_types = ['Monitoring', 'Test and Inspection', 'Renew - Test and Inspection']
        if hasattr(self, 'x_project_type') and self.x_project_type:
            if self.x_project_type not in eligible_types:
                self.x_multiyear = False
                self.x_number_of_years = False

    @api.model
    def _get_multiyear_required_domain(self):
        """
        Returns list of project types that require multi-year fields
        """
        return ['Monitoring', 'Test and Inspection', 'Renew - Test and Inspection']

    def _check_multiyear_required(self):
        """
        Check if multi-year fields are required based on project type
        """
        if not hasattr(self, 'x_project_type') or not self.x_project_type:
            return False
        eligible_types = self._get_multiyear_required_domain()
        return self.x_project_type in eligible_types

    @api.constrains('x_multiyear', 'x_number_of_years')
    def _check_multiyear_required_fields(self):
        """
        Validate that multi-year fields are filled when required.
        Note: This constraint only checks x_multiyear and x_number_of_years
        to avoid issues if x_project_type doesn't exist.
        """
        for lead in self:
            if lead._check_multiyear_required():
                if not lead.x_multiyear:
                    raise ValidationError(
                        _('Multi-Year field is required for project type: %s') % lead.x_project_type
                    )
                if lead.x_multiyear and not lead.x_number_of_years:
                    raise ValidationError(
                        _('Number of Years is required when Multi-Year is selected.')
                    )

    @api.onchange('x_multiyear')
    def _onchange_x_multiyear(self):
        """
        Reset number of years when multi-year is unchecked
        """
        if not self.x_multiyear:
            self.x_number_of_years = False
