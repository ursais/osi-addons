# Copyright 2011 Akretion (http://www.akretion.com).
# @author Benoît GUILLOT <benoit.guillot@akretion.com>
# @author Raphaël VALYI <raphael.valyi@akretion.com>
# Copyright 2015 Savoir-faire Linux
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AttributeSet(models.Model):
    _name = "attribute.set"
    _description = "Attribute Set"

    name = fields.Char(required=True, translate=True)

    attribute_ids = fields.Many2many(
        comodel_name="attribute.attribute",
        string="Attributes",
        relation="rel_attribute_set",
        column1="attribute_set_id",
        column2="attribute_id",
    )
    model_id = fields.Many2one("ir.model", "Model", required=True, ondelete="cascade")
    model = fields.Char(
        related="model_id.model",
        string="Model Name",
        store=True,
        help="This is a technical field in order to build filters on this one to avoid"
        "access on ir.model",
    )
