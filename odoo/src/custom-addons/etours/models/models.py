# -*- coding: utf-8 -*-

from odoo import models, fields


class etours(models.Model):
    _name = 'etours.etours'
    _description = 'etours.etours'

    name = fields.Char()
    value = fields.Integer()
    value2 = fields.Float(compute="_value_pc", store=True)
    description = fields.Text()
