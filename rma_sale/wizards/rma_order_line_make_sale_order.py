# Copyright 2020 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import _, api, exceptions, fields, models


class RmaLineMakeSaleOrder(models.TransientModel):
    _name = "rma.order.line.make.sale.order"
    _description = "Make Sales Order from RMA Line"

    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Customer",
        required=False,
    )
    item_ids = fields.One2many(
        comodel_name="rma.order.line.make.sale.order.item",
        inverse_name="wiz_id",
        string="Items",
        readonly=False,
    )

    sale_order_id = fields.Many2one(
        comodel_name="sale.order",
        string="Sales Order",
        required=False,
        domain=[("state", "=", "draft")],
    )

    @api.model
    def _prepare_item(self, line):
        free_of_charge_rma_sale = line.operation_id.free_of_charge_rma_sale
        return {
            "line_id": line.id,
            "product_id": line.product_id.id,
            "name": line.product_id.name,
            "product_qty": line.qty_to_sell,
            "rma_id": line.rma_id.id,
            "out_warehouse_id": line.out_warehouse_id.id,
            "product_uom_id": line.uom_id.id,
            "free_of_charge": free_of_charge_rma_sale,
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
        customers = lines.mapped("partner_id")
        if len(customers) == 1:
            res["partner_id"] = customers.id
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
    def _prepare_sale_order(self, line):
        if not self.partner_id:
            raise exceptions.Warning(_("Enter a customer."))
        customer = self.partner_id
        auto = self.env["account.fiscal.position"].search(
            [("auto_apply", "=", True), ("country_id", "=", customer.country_id.id)],
            limit=1,
        )
        fiscal_position = False
        if customer.property_account_position_id:
            fiscal_position = customer.property_account_position_id
        elif auto:
            fiscal_position = auto
        data = {
            "origin": line.name,
            "partner_id": customer.id,
            "warehouse_id": line.out_warehouse_id.id,
            "company_id": line.company_id.id,
            "fiscal_position_id": fiscal_position.id if fiscal_position else False,
        }

        return data

    @api.model
    def _prepare_sale_order_line(self, so, item):
        product = item.product_id
        vals = {
            "name": item.name,
            "order_id": so.id,
            "product_id": product.id,
            "product_uom": product.uom_po_id.id,
            "product_uom_qty": item.product_qty,
            "rma_line_id": item.line_id.id,
        }
        if item.free_of_charge:
            vals["price_unit"] = 0.0
        return vals

    def _post_process_sale_order(self, item, sale_line):
        line = item.line_id
        if line.operation_id.auto_confirm_rma_sale:
            sale_line.order_id.action_confirm()

    def make_sale_order(self):
        res = []
        sale_obj = self.env["sale.order"]
        so_line_obj = self.env["sale.order.line"]
        sale = False

        for item in self.item_ids:
            line = item.line_id
            if item.product_qty <= 0.0:
                raise exceptions.Warning(_("Enter a positive quantity."))

            if self.sale_order_id:
                sale = self.sale_order_id
            if not sale:
                po_data = self._prepare_sale_order(line)
                sale = sale_obj.create(po_data)
                sale.name = sale.name + " - " + line.name

            so_line_data = self._prepare_sale_order_line(sale, item)
            sale_line = so_line_obj.create(so_line_data)
            self._post_process_sale_order(item, sale_line)
            res.append(sale.id)

        action = self.env.ref("sale.action_orders")
        result = action.sudo().read()[0]
        result["domain"] = "[('id','in', [" + ",".join(map(str, res)) + "])]"
        return result


class RmaLineMakeSaleOrderItem(models.TransientModel):
    _name = "rma.order.line.make.sale.order.item"
    _description = "RMA Line Make Sale Order Item"

    wiz_id = fields.Many2one(
        comodel_name="rma.order.line.make.sale.order", string="Wizard"
    )
    line_id = fields.Many2one(
        comodel_name="rma.order.line", string="RMA Line", compute="_compute_line_id"
    )
    rma_id = fields.Many2one(
        comodel_name="rma.order", related="line_id.rma_id", readonly=False
    )
    product_id = fields.Many2one(comodel_name="product.product", string="Product")
    name = fields.Char(string="Description")
    product_qty = fields.Float(string="Quantity to sell", digits="Product UoS")
    product_uom_id = fields.Many2one(comodel_name="uom.uom", string="UoM")
    out_warehouse_id = fields.Many2one(
        comodel_name="stock.warehouse", string="Outbound Warehouse"
    )
    free_of_charge = fields.Boolean(string="Free of Charge")

    def _compute_line_id(self):
        rma_line_obj = self.env["rma.order.line"]
        for rec in self:
            if not self.env.context["active_ids"]:
                return
            rma_line_ids = self.env.context["active_ids"] or []
            lines = rma_line_obj.browse(rma_line_ids)
            rec.line_id = lines[0]

    @api.onchange("product_id")
    def onchange_product_id(self):
        if self.product_id:
            self.name = self.product_id.name
