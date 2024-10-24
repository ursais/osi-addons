# See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class IrActionsClient(models.Model):

    _inherit = "ir.actions.client"

    reload_time = fields.Integer("Auto Reload Time")

    def _get_readable_fields(self):
        return super()._get_readable_fields() | {"reload_time"}


class IrActionsActWindowExtend(models.Model):

    _inherit = "ir.actions.act_window"

    reload_time = fields.Integer("Auto Reload Time")

    def _get_readable_fields(self):
        return super()._get_readable_fields() | {"reload_time"}
