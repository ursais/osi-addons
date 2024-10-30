# Copyright 2017-2022 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from datetime import datetime

from odoo import _, api, exceptions, fields, models
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DF


class RmaLineMakePurchaseOrder(models.TransientModel):
    _name = "rma.order.line.make.purchase.order"
    _description = "Make Purchases Order from RMA Line"

    partner_id = fields.Many2one(
        comodel_name="res.partner",
        required=False,
        readonly=True,
    )
    item_ids = fields.One2many(
        comodel_name="rma.order.line.make.purchase.order.item",
        inverse_name="wiz_id",
        string="Items",
    )
    purchase_order_id = fields.Many2one(
        comodel_name="purchase.order",
        string="Purchases Order",
        required=False,
        domain=[("state", "=", "draft")],
    )

    @api.model
    def _prepare_item(self, line):
        return {
            "line_id": line.id,
            "rma_line_id": line.id,
            "product_id": line.product_id.id,
            "name": line.product_id.name,
            "product_qty": line.qty_to_purchase,
            "rma_id": line.rma_id.id,
            "product_uom_id": line.uom_id.id,
        }

    @api.model
    def default_get(self, fields_list):
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
        suppliers = lines.mapped("partner_id")
        if len(suppliers) == 1:
            res["partner_id"] = suppliers.id
        else:
            raise exceptions.Warning(
                _(
                    "Only RMA lines from the same partner can be processed at "
                    "the same time"
                )
            )
        res["item_ids"] = items
        return res

    @api.model
    def _prepare_purchase_order(self, item):
        if not self.partner_id:
            raise exceptions.Warning(_("Enter a supplier."))
        supplier = self.partner_id
        data = {
            "origin": "",
            "partner_id": supplier.id,
            "company_id": item.line_id.company_id.id,
        }
        return data

    @api.model
    def _prepare_purchase_order_line(self, po, item):
        product = item.product_id
        vals = {
            "name": product.name,
            "order_id": po.id,
            "product_id": product.id,
            "price_unit": item.line_id.price_unit,
            "date_planned": datetime.today().strftime(DF),
            "product_uom": product.uom_po_id.id,
            "product_qty": item.product_qty,
            "rma_line_id": item.line_id.id,
        }
        if item.free_of_charge:
            vals["price_unit"] = 0.0
        return vals

    def create_purchase_order(self):
        res = []
        purchase_obj = self.env["purchase.order"]
        po_line_obj = self.env["purchase.order.line"]

        for item in self.item_ids:
            if item.product_qty <= 0.0:
                raise exceptions.Warning(_("Enter a positive quantity."))

            purchase = self.purchase_order_id
            if not purchase:
                po_data = self._prepare_purchase_order(item)
                purchase = purchase_obj.create(po_data)

            po_line_data = self._prepare_purchase_order_line(purchase, item)
            po_line_obj.create(po_line_data)
            res.append(purchase.id)

        action = self.env.ref("purchase.purchase_rfq")
        result = action.sudo().read()[0]
        result["domain"] = "[('id','in', [" + ",".join(map(str, res)) + "])]"
        return result


class RmaLineMakePurchaseOrderItem(models.TransientModel):
    _name = "rma.order.line.make.purchase.order.item"
    _description = "RMA Line Make Purchase Order Item"

    wiz_id = fields.Many2one(
        comodel_name="rma.order.line.make.purchase.order", string="Wizard"
    )
    line_id = fields.Many2one(comodel_name="rma.order.line", string="RMA Line")
    rma_id = fields.Many2one(
        comodel_name="rma.order", related="line_id.rma_id", string="RMA Order"
    )
    product_id = fields.Many2one(comodel_name="product.product", string="Product")
    name = fields.Char(string="Description")
    product_qty = fields.Float(
        string="Quantity to purchase",
        digits="Product Unit of Measure",
    )
    product_uom_id = fields.Many2one(comodel_name="uom.uom", string="UoM")
    free_of_charge = fields.Boolean(string="Free of Charge")
    rma_line_id = fields.Many2one(
        comodel_name="rma.order", string="RMA", ondelete="set null"
    )
