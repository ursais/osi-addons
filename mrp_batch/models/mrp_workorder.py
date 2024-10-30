# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError

class MrpWorkorder(models.Model):
    _inherit = "mrp.workorder"
    
    mrp_batch_id = fields.Many2one(related="production_id.mrp_batch_id")