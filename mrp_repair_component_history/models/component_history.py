# Import Odoo libs
from odoo import fields, models


class ComponentHistory(models.Model):
    _name = "component.history"
    _description = "Component History"
    _rec_name = "lot_id"
    _order = "create_date desc"

    # COLUMNS ###

    lot_id = fields.Many2one(
        comodel_name="stock.lot",
        string="Serial Number",
        required=True,
        index=True,
    )
    product_id = fields.Many2one(
        comodel_name="product.product",
        string="Component",
        required=True,
    )
    qty_changed = fields.Float(
        string="Quantity",
        required=True,
    )
    change_type = fields.Selection(
        [
            ("manufactured", "Manufactured"),
            ("add", "Added"),
            ("remove", "Removed"),
            ("recycle", "Recycled"),
        ],
        string="Change Type",
        required=True,
    )
    component_lot_ids = fields.Many2many(
        comodel_name="stock.lot",
        string="Component Serial Numbers",
    )
    source_id = fields.Reference(
        [
            ("mrp.production", "Manufacturing Order"),
            ("repair.order", "Repair Order"),
        ],
        string="Source Document",
        required=True,
    )

    # END #######
    # METHODS #######

    def name_get(self):
        return [
            (record.id, f"{record.product_id.display_name} ({record.change_type})")
            for record in self
        ]

    # END #######
