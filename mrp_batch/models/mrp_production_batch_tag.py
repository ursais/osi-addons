# -*- coding: utf-8 -*-

from odoo import fields, models


class MrpProductionBatchtag(models.Model):
    _name = "mrp.production.batch.tag"
    _description = "Manufacturing Batch Tags"
  
    name = fields.Char(string="Name",required=True)
    color = fields.Integer(string="Color")
