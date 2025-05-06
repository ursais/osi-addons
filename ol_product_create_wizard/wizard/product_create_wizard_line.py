# Import Odoo libs
from odoo import fields, models


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
