# Import Odoo libs
from odoo import api, fields, models


class ComponentHistory(models.Model):
    _name = "component.history"
    _description = "Component History"
    _rec_name = "lot_id"
    _order = "date desc"

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
    invisible = fields.Boolean(
        string="Invisible",
        default=False,
        help="Used to track historical component changes.",
    )
    date = fields.Datetime(string="Date")

    # END #######
    # METHODS #######

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for new_record in res:
            # Only process for "remove" or "recycle" types
            if new_record.change_type in ("remove", "recycle"):
                # Set New Record to be invisible since it was removed.
                new_record.invisible = True

                # Find the most recent non-invisible "add" or "manufactured" entry
                existing = self.search(
                    [
                        ("lot_id", "=", new_record.lot_id.id),
                        ("product_id", "=", new_record.product_id.id),
                        ("change_type", "in", ["manufactured", "add"]),
                        ("invisible", "=", False),
                    ],
                    order="create_date desc",
                    limit=1,
                )

                if existing:
                    if existing.qty_changed == new_record.qty_changed:
                        # Exact match → Mark previous as invisible
                        existing.invisible = True
                    else:
                        # Partial match → Mark previous as invisible and create a new reduced one
                        existing.invisible = True
                        self.create(
                            {
                                "lot_id": existing.lot_id.id,
                                "product_id": existing.product_id.id,
                                "qty_changed": existing.qty_changed
                                - new_record.qty_changed,
                                "change_type": existing.change_type,
                                "source_id": existing.source_id.id or False,
                                "invisible": False,
                            }
                        )

        return res

    def name_get(self):
        return [
            (record.id, f"{record.product_id.display_name} ({record.change_type})")
            for record in self
        ]

    # END #######
