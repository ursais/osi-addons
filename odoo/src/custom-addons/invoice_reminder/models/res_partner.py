# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
import datetime

class FollowupLine(models.Model):
    _inherit = 'account_followup.followup.line'

    recurrence_interval = fields.Integer("Recurrence Interval")
    end_limit = fields.Integer("End Limit")

class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _compute_followup_lines(self):
        """ returns the followup plan of the current user's company (of given in context directly)
        in the form of a dictionary with
         * keys being the different possible levels of followup for account.move.line's (None or IDs of account_followup.followup.line)
         * values being a tuple of 3 elements corresponding respectively to
           - the oldest date that any line in that followup level should be compared to in order to know if it is ready for the next level
           - the followup ID of the next level
           - the delays in days of the next level
        """
        followup_id = 'followup_id' in self.env.context and self.env.context['followup_id'] or self.env['account_followup.followup'].search([('company_id', '=', self.env.user.company_id.id)]).id
        if not followup_id:
            return {}

        current_date = fields.Date.today()
        self.env.cr.execute(
            "SELECT id, delay "\
            "FROM account_followup_followup_line "\
            "WHERE followup_id=%s "\
            "ORDER BY delay", (followup_id,))

        previous_level = None
        fups = {}
        for line in self.env['account_followup.followup.line'].search([('company_id', '=', self.env.user.company_id.id)], order="delay asc"):
            delay = datetime.timedelta(days=line.delay)
            delay_in_days = line.delay
            for d in range(line.delay, line.end_limit, line.recurrence_interval):
                delay = datetime.timedelta(days=d)
                delay_in_days = d
                fups[previous_level] = (current_date - delay, line.id, delay_in_days)
                previous_level = line.id
        if previous_level:
            fups[previous_level] = (current_date - delay, previous_level, delay_in_days)
        return fups
