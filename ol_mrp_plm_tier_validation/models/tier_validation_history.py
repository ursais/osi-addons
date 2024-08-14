# Import Odoo libs
from odoo import fields, models


class TierValidationHistory(models.Model):
    """
    New object for tier review history on eco's.
    """

    _name = "tier.validation.history"

    # COLUMNS ###

    eco_id = fields.Many2one("mrp.eco", string="ECO")
    definition_id = fields.Many2one("tier.definition", string="Tier Definition")
    requested_by = fields.Many2one("res.users", string="Requested By")
    name = fields.Char(related="definition_id.name")
    eco_stage_id = fields.Many2one("mrp.eco.stage", string="ECO Stage")
    todo_by = fields.Char(string="Todo by")
    done_by = fields.Many2one("res.users", string="Done By")
    reviewed_date = fields.Date(string="Approval Date")
    comment = fields.Char()
    status = fields.Selection(
        [
            ("waiting", "Waiting"),
            ("pending", "Pending"),
            ("rejected", "Rejected"),
            ("approved", "Approved"),
        ],
    )

    # END #######
