# -*- coding: utf-8 -*-

from odoo import models, fields

class EstimateJobType(models.Model):
    _name = 'estimate.job.type'
    _description = 'Estimate Job Type'

    name = fields.Char(
        string='Name',
        required=True,
    )
    code = fields.Char(
        string='Code',
        required=True,
    )
    job_type = fields.Selection(
        selection=[
            ('material','Material'),
            ('labour','Labour'),
            ('overhead','Overhead')],
        string='Type',
        required=True,
    )
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
