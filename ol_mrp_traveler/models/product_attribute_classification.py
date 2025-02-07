# Import Odoo libs
from odoo import fields, models


class ProductAttributeClassification(models.Model):
    """
    Add traveler connected info to the classification
    """

    _inherit = "product.attribute.classification"
    _order = "name"

    def _compute_default_stage(self):
        return self.env.ref("ol_mrp_traveler.undefined_stage", raise_if_not_found=False)

    # COLUMNS #####

    stage_id = fields.Many2one(
        comodel_name="mrp.assembly.stage",
        string="Stage",
        default=_compute_default_stage,
        required=True,
    )
    check_ids = fields.One2many(
        comodel_name="mrp.assembly.check",
        string="Assembly Checks",
        inverse_name="classification_id",
    )

    # END #########

    _sql_constraints = [
        ("name_uniq", "unique(name)", "Option Title must be unique!"),
    ]
