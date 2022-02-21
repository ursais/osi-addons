from odoo import api, models


class StockLocation(models.Model):
    _inherit = "stock.location"

    @api.model
    def _search(
        self,
        args,
        offset=0,
        limit=None,
        order=None,
        count=False,
        access_rights_uid=None,
    ):
        context = self._context or {}
        if context.get("product_id") or context.get("lot_id"):
            quants = self.env["stock.quant"].search(
                [
                    ("product_id", "=", context.get("product_id")),
                    ("lot_id", "=", context.get("lot_id")),
                    ("location_id.name", "like", "stock"),
                ]
            )
            locations = quants.mapped("location_id")
            if not locations:
                company_id = context.get("default_company_id") or self.env.company.id
                warehouse = self.env["stock.warehouse"].search(
                    [("company_id", "=", company_id)], limit=1
                )
                if warehouse:
                    locations = warehouse.lot_stock_id
            args += [("id", "in", locations.ids)]
        return super(StockLocation, self)._search(
            args, offset, limit, order, count=count, access_rights_uid=access_rights_uid
        )


class StockScrap(models.Model):
    _inherit = "stock.scrap"

    @api.onchange("product_id")
    def _onchange_product_id(self):
        self.location_id = False
        self.lot_id = False
        return super()._onchange_product_id()

    @api.onchange("lot_id")
    def _onchange_lot_id(self):
        self.location_id = False
