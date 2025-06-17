# Import Odoo libs
from odoo import _, fields, models


class StockWarehouse(models.Model):
    """Inherit warehouse to add RMA fields and generate rma operations when enabled."""

    _inherit = "stock.warehouse"

    # COLUMNS ######

    lot_rma_id = fields.Many2one(
        comodel_name="stock.location",
        string="RMA Location",
    )
    rma_sup_out_type_id = fields.Many2one(
        comodel_name="stock.picking.type",
        string="RMA Supplier out Type",
        readonly=True,
    )
    rma_sup_in_type_id = fields.Many2one(
        comodel_name="stock.picking.type",
        string="RMA Supplier in Type",
        readonly=True,
    )
    rma_in_this_wh = fields.Boolean(
        string="RMA in this Warehouse",
        help="If set, it will create RMA location, picking types and routes "
        "for this warehouse.",
    )
    rma_supplier_in_pull_id = fields.Many2one(
        comodel_name="stock.rule",
        string="RMA Supplier In Rule",
    )
    rma_supplier_out_pull_id = fields.Many2one(
        comodel_name="stock.rule",
        string="RMA Supplier Out Rule",
    )

    # END ##########
    # METHODS ######

    def _get_rma_types(self):
        return [
            self.rma_sup_out_type_id,
            self.rma_sup_in_type_id,
        ]

    def _rma_types_available(self):
        self.ensure_one()
        rma_types = self._get_rma_types()
        for r_type in rma_types:
            if not r_type:
                return False
        return True

    def write(self, vals):
        if "rma_in_this_wh" in vals:
            if vals.get("rma_in_this_wh"):
                for wh in self:
                    # RMA location:
                    if not wh.lot_rma_id:
                        wh.lot_rma_id = self.env["stock.location"].create(
                            {
                                "name": "RMA",
                                "usage": "internal",
                                "location_id": wh.view_location_id.id,
                                "company_id": wh.company_id.id,
                                "return_location": True,
                            }
                        )
                    # RMA types
                    if not wh._rma_types_available():
                        wh._create_rma_picking_types()
                    else:
                        for r_type in wh._get_rma_types():
                            if r_type:
                                r_type.active = True
                    # RMA rules:
                    wh._create_or_update_rma_pull()
            else:
                for wh in self:
                    for r_type in wh._get_rma_types():
                        if r_type:
                            r_type.active = False
                # Unlink rules:
                self.mapped("rma_supplier_in_pull_id").unlink()
                self.mapped("rma_supplier_out_pull_id").unlink()
        return super().write(vals)

    def _create_rma_picking_types(self):
        picking_type_obj = self.env["stock.picking.type"]
        sequence_obj = self.env["ir.sequence"]
        customer_loc, supplier_loc = self._get_partner_locations()

        for wh in self:
            company_id = wh.company_id.id

            # Find an existing picking type to reuse color/sequence info
            other_pick_type = picking_type_obj.search(
                [("warehouse_id", "=", wh.id)],
                order="sequence desc",
                limit=1,
            )
            color = other_pick_type.color if other_pick_type else 0
            max_sequence = other_pick_type.sequence if other_pick_type else 0

            # Create unique sequence for RMA OUT
            seq_out = sequence_obj.create(
                {
                    "name": f"{wh.name} RMA OUT",
                    "prefix": f"{wh.code}/SRMA/OUT/",
                    "padding": 5,
                    "company_id": company_id,
                }
            )

            # Create RMA Supplier Out picking type
            rma_sup_out_type_id = picking_type_obj.create(
                {
                    "name": _("Supplier RMA Deliveries"),
                    "warehouse_id": wh.id,
                    "company_id": company_id,
                    "code": "outgoing",
                    "use_create_lots": True,
                    "use_existing_lots": False,
                    "sequence_id": seq_out.id,
                    "default_location_src_id": wh.lot_rma_id.id,
                    "default_location_dest_id": supplier_loc.id,
                    "sequence": max_sequence,
                    "color": color,
                    "sequence_code": "Customer → RMA",
                }
            )

            # Create unique sequence for RMA IN
            seq_in = sequence_obj.create(
                {
                    "name": f"{wh.name} RMA IN",
                    "prefix": f"{wh.code}/SRMA/IN/",
                    "padding": 5,
                    "company_id": company_id,
                }
            )

            # Create RMA Supplier In picking type
            rma_sup_in_type_id = picking_type_obj.create(
                {
                    "name": _("Supplier RMA Receipts"),
                    "warehouse_id": wh.id,
                    "company_id": company_id,
                    "code": "incoming",
                    "use_create_lots": True,
                    "use_existing_lots": False,
                    "sequence_id": seq_in.id,
                    "default_location_src_id": supplier_loc.id,
                    "default_location_dest_id": wh.lot_rma_id.id,
                    "sequence": max_sequence,
                    "color": color,
                    "sequence_code": "Supplier → RMA",
                }
            )

            # Link picking types to warehouse
            wh.write(
                {
                    "rma_sup_out_type_id": rma_sup_out_type_id.id,
                    "rma_sup_in_type_id": rma_sup_in_type_id.id,
                }
            )

        return True

    def get_rma_rules_dict(self):
        self.ensure_one()
        rma_rules = dict()
        customer_loc, supplier_loc = self._get_partner_locations()
        rma_rules["rma_supplier_in"] = {
            "name": self._format_rulename(self, supplier_loc, self.lot_rma_id.name),
            "action": "pull",
            "warehouse_id": self.id,
            "company_id": self.company_id.id,
            "location_src_id": supplier_loc.id,
            "location_dest_id": self.lot_rma_id.id,
            "procure_method": "make_to_stock",
            "route_id": self.env.ref("ol_rma_supplier.route_rma_supplier").id,
            "picking_type_id": self.rma_sup_in_type_id.id,
            "active": True,
        }
        rma_rules["rma_supplier_out"] = {
            "name": self._format_rulename(self, self.lot_rma_id, supplier_loc.name),
            "action": "pull",
            "warehouse_id": self.id,
            "company_id": self.company_id.id,
            "location_src_id": self.lot_rma_id.id,
            "location_dest_id": supplier_loc.id,
            "procure_method": "make_to_stock",
            "route_id": self.env.ref("ol_rma_supplier.route_rma_supplier").id,
            "picking_type_id": self.rma_sup_out_type_id.id,
            "active": True,
        }
        return rma_rules

    def _create_or_update_rma_pull(self):
        rule_obj = self.env["stock.rule"]
        for wh in self:
            rules_dict = wh.get_rma_rules_dict()
            if wh.rma_supplier_in_pull_id:
                wh.rma_supplier_in_pull_id.write(rules_dict["rma_supplier_in"])
            else:
                wh.rma_supplier_in_pull_id = rule_obj.create(
                    rules_dict["rma_supplier_in"]
                )

            if wh.rma_supplier_out_pull_id:
                wh.rma_supplier_out_pull_id.write(rules_dict["rma_supplier_out"])
            else:
                wh.rma_supplier_out_pull_id = rule_obj.create(
                    rules_dict["rma_supplier_out"]
                )
        return True

    # END ##########
