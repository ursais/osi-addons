# Import Odoo libs
from odoo import api, fields, models


class ProductCreateWizardLine(models.TransientModel):
    """Line object on the wizard that contains the attribute/value configs."""

    _name = "product.create.wizard.line"
    _description = "Wizard Attribute Line"

    # COLUMNS ##########

    wizard_id = fields.Many2one(
        comodel_name="product.create.wizard",
        required=True,
        ondelete="cascade",
    )
    attribute_id = fields.Many2one(
        comodel_name="product.attribute",
        required=True,
    )
    value_ids = fields.Many2many(
        comodel_name="product.attribute.value",
        string="Values",
    )
    used_in_sale_description = fields.Boolean(
        string="Show in Sale Description",
        default=True,
    )
    is_qty_required = fields.Boolean(string="Qty Required")
    default_val = fields.Many2one(
        comodel_name="product.attribute.value",
        string="Default Value",
    )
    required = fields.Boolean(
        string="Required",
        default=True,
        help="Is this attribute required?",
    )
    multi = fields.Boolean(
        string="Multi",
        help="Allow selection of multiple values for this attribute?",
    )
    custom = fields.Boolean(
        string="Custom",
        help="Allow custom values for this attribute?",
    )

    # END ##########
    # METHODS ######

    @api.onchange("value_ids")
    def _onchange_value_ids(self):
        # If default_val is set and no longer in value_ids, clear it
        if self.default_val:
            new_ids = self.value_ids.ids
            if self.default_val.id not in new_ids:
                self.default_val = False

    # END ##########
