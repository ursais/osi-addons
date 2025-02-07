# Import Odoo libs
from odoo import fields, models


class MrpBomLine(models.Model):
    _inherit = "mrp.bom.line"

    # COLUMNS #####

    assembly_stage_id = fields.Many2one(
        string="Assembly Stage",
        comodel_name="mrp.assembly.stage",
        compute="_compute_assembly_stage_id",
    )
    customer_selection_name = fields.Char(
        string="Customer Selection Name",
        compute="_compute_assembly_stage_id",
    )

    # END COLUMNS ###

    def _compute_assembly_stage_id(self):
        for line in self:
            stage, customer_selection_name = line.get_traveler_data()
            line.assembly_stage_id = stage
            line.customer_selection_name = customer_selection_name

    def get_traveler_data(self):
        """
        The main purpose of this function is to get overridden from other modules
        and to provide a bareone logic to get Assembly Satges from MRP BOM Lines
        """
        self.ensure_one()
        return self.classification_id.stage_id, self.classification_id.name
