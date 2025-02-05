# Import Odoo libs
from odoo import _, models, fields, api
from odoo.exceptions import ValidationError


class ProductOperationsCategory(models.Model):
    _name = "product.operations.category"
    _description = "Product Operations Category"
    _parent_name = "parent_id"
    _parent_store = True
    _rec_name = "complete_name"
    _order = "complete_name"

    # COLUMNS ##########

    name = fields.Char(
        string="Name",
        index=True,
        required=True,
    )
    complete_name = fields.Char(
        string="Complete Name",
        compute="_compute_complete_name",
        store=True,
        recursive=True,
    )
    parent_id = fields.Many2one(
        comodel_name="product.operations.category",
        string="Parent Category",
        index=True,
        ondelete="cascade",
    )
    parent_path = fields.Char(
        index=True,
        unaccent=False,
    )
    child_id = fields.One2many(
        comodel_name="product.operations.category",
        inverse_name="parent_id",
        string="Child Categories",
    )
    product_count = fields.Integer(
        string="# Products",
        compute="_compute_product_count",
        help="The number of products under this category (Does not consider the children categories)",
    )

    # END ##########
    # METHODS ##########

    @api.depends("name", "parent_id.complete_name")
    def _compute_complete_name(self):
        for category in self:
            if category.parent_id:
                category.complete_name = "%s / %s" % (
                    category.parent_id.complete_name,
                    category.name,
                )
            else:
                category.complete_name = category.name

    def _compute_product_count(self):
        read_group_res = self.env["product.template"].read_group(
            [("operations_category_id", "child_of", self.ids)],
            ["operations_category_id"],
            ["operations_category_id"],
        )
        group_data = dict(
            (data["operations_category_id"][0], data["operations_category_id_count"])
            for data in read_group_res
        )
        for categ in self:
            product_count = 0
            for sub_operations_category_id in categ.search(
                [("id", "child_of", categ.ids)]
            ).ids:
                product_count += group_data.get(sub_operations_category_id, 0)
            categ.product_count = product_count

    @api.constrains("parent_id")
    def _check_category_recursion(self):
        if not self._check_recursion():
            raise ValidationError(_("You cannot create recursive categories."))
        return True

    @api.model
    def name_create(self, name):
        record = self.create({"name": name})
        return record.id, record.display_name

    # END ##########
