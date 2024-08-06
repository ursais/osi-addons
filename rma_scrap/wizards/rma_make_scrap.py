# Copyright 2022 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).


from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class RmaMakeScrap(models.TransientModel):
    _name = "rma_make_scrap.wizard"
    _description = "Wizard to create scrap from rma lines"

    item_ids = fields.One2many(
        comodel_name="rma_make_scrap_item.wizard",
        inverse_name="wiz_id",
        string="Items",
    )

    @api.returns("rma.order.line")
    def _prepare_item(self, line):
        values = {
            "product_id": line.product_id.id,
            "product_qty": line.product_qty,
            "location_id": line.location_id.id,
            "scrap_location_id": line.operation_id.scrap_location_id.id,
            "uom_id": line.uom_id.id,
            "qty_to_scrap": line.qty_to_scrap,
            "line_id": line.id,
            "rma_id": line.rma_id and line.rma_id.id or False,
        }
        return values

    @api.model
    def default_get(self, fields_list):
        context = self._context.copy()
        res = super().default_get(fields_list)
        rma_line_obj = self.env["rma.order.line"]
        rma_line_ids = self.env.context["active_ids"] or []
        active_model = self.env.context["active_model"]

        if not rma_line_ids:
            return res
        assert active_model == "rma.order.line", "Bad context propagation"

        items = []
        lines = rma_line_obj.browse(rma_line_ids)
        for line in lines:
            items.append([0, 0, self._prepare_item(line)])
        res["item_ids"] = items
        context.update({"items_ids": items})
        return res

    def _create_scrap(self):
        scraps = []
        for item in self.item_ids:
            line = item.line_id
            if line.state != "approved":
                raise ValidationError(_("RMA %s is not approved") % line.name)
            scrap = self._prepare_scrap(item)
            scraps.append(scrap)
            item.line_id.scrap_ids |= scrap
        return scraps

    def action_create_scrap(self):
        self._create_scrap()
        return self.item_ids[0].line_id.action_view_scrap_transfers()

    @api.model
    def _prepare_scrap(self, item):
        line = item.line_id
        scrap = self.env["stock.scrap"].create(
            {
                "name": line.rma_id.id and line.rma_id.name or line.name,
                "origin": line.name,
                "product_id": item.line_id.product_id.id,
                "scrap_qty": item.qty_to_scrap,
                "product_uom_id": item.line_id.product_id.product_tmpl_id.uom_id.id,
                "location_id": item.location_id.id,
                "scrap_location_id": item.scrap_location_id.id,
                "rma_line_id": line.id,
                "create_date": fields.Datetime.now(),
                "company_id": line.company_id.id,
                "is_rma_scrap": True,
            }
        )
        return scrap


class RmaMakeScrapItem(models.TransientModel):
    _name = "rma_make_scrap_item.wizard"
    _description = "Items to Scrap"

    wiz_id = fields.Many2one("rma_make_scrap.wizard", string="Wizard", required=True)
    line_id = fields.Many2one(
        "rma.order.line", string="RMA order Line", ondelete="cascade", required=True
    )
    rma_id = fields.Many2one("rma.order", related="line_id.rma_id", string="RMA Group")
    product_id = fields.Many2one("product.product", string="Product", required=True)
    product_qty = fields.Float(
        related="line_id.product_qty",
        string="Quantity Ordered",
        copy=False,
        digits="Product Unit of Measure",
    )
    company_id = fields.Many2one("res.company", related="line_id.company_id")
    location_id = fields.Many2one(
        "stock.location",
        string="Source Location",
        required=True,
        domain="[('usage', '=', 'internal'),"
        "('company_id', 'in', [company_id, False])]",
    )
    scrap_location_id = fields.Many2one(
        "stock.location",
        string="Scrap Location",
        required=True,
        domain="[('scrap_location', '=', True)]",
    )
    qty_to_scrap = fields.Float(
        string="Quantity To Scrap", digits="Product Unit of Measure"
    )
    uom_id = fields.Many2one("uom.uom", string="Unit of Measure")
