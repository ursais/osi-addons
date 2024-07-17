# Copyright 2011 Akretion (http://www.akretion.com).
# @author Benoît GUILLOT <benoit.guillot@akretion.com>
# @author Raphaël VALYI <raphael.valyi@akretion.com>
# Copyright 2015 Savoir-faire Linux
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AttributeGroup(models.Model):
    _name = "attribute.group"
    _description = "Attribute Group"
    _order = "sequence"

    name = fields.Char(required=True, translate=True)

    sequence = fields.Integer(
        "Sequence in Set", help="The Group order in his attribute's Set"
    )

    attribute_ids = fields.One2many(
        "attribute.attribute", "attribute_group_id", "Attributes"
    )

    model_id = fields.Many2one("ir.model", "Model", required=True, ondelete="cascade")
