# Copyright (C) 2019 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models
from odoo.osv import expression


class AnalyticSegmentOne(models.Model):
    _name = "analytic.segment.one"
    _description = "Analytic Segment One"
    _order = 'name,code'

    code = fields.Char('Code')
    name = fields.Char('Name')
    description = fields.Text('Description')

    @api.multi
    def name_get(self):
        result = []
        for segment in self:
            name = '[%s] %s' % (segment.code, segment.name)
            result.append((segment.id, name))
        return result

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|',
                      ('code', '=ilike', name + '%'),
                      ('name', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        segments = self.search(domain + args, limit=limit)
        return segments.name_get()


class AnalyticSegmentTwo(models.Model):
    _name = "analytic.segment.two"
    _description = "Analytic Segment Two"
    _order = 'name,code'

    code = fields.Char('Code')
    name = fields.Char('Name')
    description = fields.Text('Description')

    @api.multi
    def name_get(self):
        result = []
        for segment in self:
            name = '[%s] %s' % (segment.code, segment.name)
            result.append((segment.id, name))
        return result

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|',
                      ('code', '=ilike', name + '%'),
                      ('name', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        segments = self.search(domain + args, limit=limit)
        return segments.name_get()
