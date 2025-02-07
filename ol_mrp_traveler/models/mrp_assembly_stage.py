# Import Odoo libs
from odoo import fields, models


class MrpAssemblyStage(models.Model):
    _name = "mrp.assembly.stage"
    _description = "A Step in the Assembly Process"
    _order = "sequence"

    # COLUMNS #####

    name = fields.Char(string="Stage Title")
    sequence = fields.Integer(string="Stage Order")
    show_on_traveler = fields.Boolean(
        string="Show On Traveler",
        default=True,
    )
    show_on_repair_traveler = fields.Boolean(
        string="Show On Repair Traveler",
        default=False,
    )
    show_when_empty = fields.Boolean(
        string="Show, Even if empty",
        default=False,
    )

    check_ids = fields.One2many(
        comodel_name="mrp.assembly.check",
        string="Assembly Checks",
        inverse_name="stage_id",
    )

    classification_ids = fields.One2many(
        comodel_name="product.attribute.classification",
        string="BoM Options",
        inverse_name="stage_id",
    )

    # END #########

    _sql_constraints = [
        ("name_uniq", "unique(name)", "Stage Title must be unique!"),
    ]
