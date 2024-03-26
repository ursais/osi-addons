# Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
# Copyright (C) Thinkopen Solutions <http://www.tkobr.com>.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models, api


class ResGroups(models.Model):
    _inherit = 'res.groups'

    login_calendar_id = fields.Many2one('resource.calendar',
                                        'Allow Login Calendar',
                                        company_dependent=True,
                                        help='''The user will be only allowed
                                        to login in the calendar defined here.
                                        \nNOTE: The users will be allowed to
                                        login using a merge/union of all
                                        calendars to wich one belongs.''')
    multiple_sessions_block = fields.Boolean('Block Multiple Sessions',
                                             company_dependent=True,
                                             help='''Select this to prevent
                                             users of this group to start more
                                             than one session.''')
    interval_number = fields.Integer('Default Session Duration',
                                     company_dependent=True,
                                     help='''This define the timeout for the
                                     users of this group.\nNOTE: The system
                                     will get the lowest timeout of all user
                                     groups.''')
    interval_type = fields.Selection([('minutes', 'Minutes'),
                                      ('hours', 'Hours'),
                                      ('work_days', 'Work Days'),
                                      ('days', 'Days'), ('weeks', 'Weeks'),
                                      ('months', 'Months')],
                                     'Interval Unit', company_dependent=True)

    @api.model
    def search_read(
            self, domain=None, fields=None, offset=0,
            limit=None, order=None):
        res = super(ResGroups, self).search_read(
            domain, fields, offset, limit, order)
        if res:
            res_obj = self.env['res.groups']

            for a in res:
                rec_val = res_obj.search([('id', '=', a['id'])])
                old_name = a['name']
                new_name = ''
                if rec_val.category_id and rec_val.category_id.name:
                    new_name = rec_val.category_id.name
                final_name = new_name + '/' + old_name
                # Update new updated name when group is res.groups
                a.update({'name': final_name})
        return res
