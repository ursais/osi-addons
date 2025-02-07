# Import Odoo libs
from odoo import api, fields, models


class MrpAssemblyCheck(models.Model):
    _name = "mrp.assembly.check"
    _description = "A check to be shown on the traveler"
    _order = "priority"

    # COLUMNS #####

    name = fields.Char(
        string="Check Name",
        required=True,
    )
    type = fields.Selection(
        string="Check type",
        required=True,
        selection=[
            ("output", "Output QA"),
            ("input", "Next Stage Input QA"),
            ("both", "Both Output and Next Stage Input QA"),
            ("note", "Note"),
        ],
    )
    priority = fields.Integer(
        string="Sort Order",
        required=True,
    )
    text = fields.Char(
        string="Check Text",
        required=True,
    )
    stage_id = fields.Many2one(
        comodel_name="mrp.assembly.stage",
        string="Assembly Stage",
    )
    classification_id = fields.Many2one(
        comodel_name="product.attribute.classification",
        string="BoM Classification",
    )
    product_ids = fields.Many2many(
        comodel_name="product.product",
        string="Linked Products",
    )
    template_ids = fields.Many2many(
        comodel_name="product.template",
        string="Linked Templates",
    )
    products_count = fields.Integer(
        string="Product Count",
        compute="_compute_products_count",
    )
    templates_count = fields.Integer(
        string="Template Count",
        compute="_compute_products_count",
    )
    repair_check = fields.Boolean(
        string="Repair Check",
        default=True,
        help="Should this check show up on the Repair Traveler?",
    )
    assembly_check = fields.Boolean(
        string="Assembly Check",
        default=True,
        help="Should this check show up on the Assembly Traveler?",
    )

    # END #########
    # METHODS #####

    @api.constrains(
        "stage_id",
        "product_ids",
        "classification_id",
        "template_ids",
    )
    def onchange_references(self):
        """
        Don't allow this check to be attached to both option and products
        """
        if self.classification_id and (self.product_ids or self.template_ids):
            raise ValueError(
                "Can't assign a check with both classification and products"
            )

    def _compute_products_count(self):
        for check in self:
            check.products_count = len(check.product_ids)
            check.templates_count = len(check.template_ids)

    @api.model
    def get_all_checks(self, stage, stage_classifications, line_products, all_products):
        """
        Get all checks associated with the given stage, classifications, and products
        """
        # checks linked only to stage
        all_checks = self.search(
            [
                ("stage_id", "=", stage.id),
                ("classification_id", "=", False),
                ("product_ids", "=", False),
                ("template_ids", "=", False),
            ]
        )

        # checks linked to product in bom and this stage
        all_checks |= self.search(
            [
                ("stage_id", "=", stage.id),
                "|",
                ("product_ids", "in", all_products.ids),
                ("template_ids", "in", all_products.mapped("product_tmpl_id.id")),
            ]
        )

        # checks linked to classification this stage's  bom lines and this stage
        all_checks |= self.search(
            [
                ("stage_id", "=", stage.id),
                ("classification_id", "in", stage_classifications.ids),
            ]
        )

        # checks linked to product in stage but not to any stage
        all_checks |= self.search(
            [
                ("stage_id", "=", False),
                "|",
                ("product_ids", "in", line_products.ids),
                ("template_ids", "in", line_products.mapped("product_tmpl_id.id")),
            ]
        )

        # checks linked to classification in stage but not to any stage
        all_checks |= self.search(
            [
                ("stage_id", "=", False),
                ("classification_id", "in", stage_classifications.ids),
            ]
        )

        # sort checks
        all_checks = all_checks.sorted(lambda r: r.priority)

        return all_checks

    @api.onchange("stage_id")
    def update_repair_check(self):
        if self.stage_id.name == "disabled":
            self.repair_check = False

    # END #########
