# Copyright 2017 ForgeFlow
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class RmaLineMakeSupplierRma(models.TransientModel):
    _name = "rma.order.line.make.supplier.rma"
    _description = "RMA Line Make Supplier RMA"

    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Supplier",
        required=True,
    )
    item_ids = fields.One2many(
        comodel_name="rma.order.line.make.supplier.rma.item",
        inverse_name="wiz_id",
        string="Items",
    )
    supplier_rma_id = fields.Many2one(
        comodel_name="rma.order", string="Supplier RMA Order Group"
    )

    @api.model
    def _get_default_operation(self):
        """Dropshipping is the most common use case of this wizard, thus
        trying to default to a dropshipping operation first."""
        operation = self.env["rma.operation"].search(
            [("type", "=", "supplier"), ("supplier_to_customer", "=", True)], limit=1
        )
        if not operation:
            operation = self.env["rma.operation"].search(
                [("type", "=", "supplier")], limit=1
            )
        return operation

    @api.model
    def _prepare_item(self, line):
        operation = self._get_default_operation()
        return {
            "line_id": line.id,
            "product_id": line.product_id.id,
            "name": line.name,
            "product_qty": line.qty_to_supplier_rma,
            "uom_id": line.uom_id.id,
            "operation_id": operation.id if operation else False,
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
        suppliers = lines.mapped(
            lambda r: r.supplier_address_id.parent_id or r.supplier_address_id
        )
        if len(suppliers) > 1:
            raise ValidationError(
                _(
                    "Only RMA lines from the same supplier can be "
                    "processed at the same time"
                )
            )
        res["partner_id"] = suppliers.id
        res["item_ids"] = items
        return res

    @api.model
    def _prepare_supplier_rma(self, company):
        if not self.partner_id:
            raise ValidationError(_("Enter a supplier."))
        return {
            "partner_id": self.partner_id.id,
            "type": "supplier",
            "company_id": company.id,
        }

    @api.model
    def _prepare_supplier_rma_line(self, rma, item):
        if item.operation_id:
            operation = item.operation_id
        else:
            operation = self._get_default_operation()
        if not operation.in_route_id or not operation.out_route_id:
            route = self.env["stock.route"].search(
                [("rma_selectable", "=", True)], limit=1
            )
            if not route:
                raise ValidationError(_("Please define an RMA route"))
        if not operation.in_warehouse_id or not operation.out_warehouse_id:
            warehouse = self.env["stock.warehouse"].search(
                [
                    ("company_id", "=", self.rma_id.company_id.id),
                    ("lot_rma_id", "!=", False),
                ],
                limit=1,
            )
            if not warehouse:
                raise ValidationError(
                    _("Please define a warehouse with a default RMA location")
                )
        data = {
            "partner_id": self.partner_id.id,
            "description": self.supplier_rma_id.description,
            "type": "supplier",
            "origin": item.line_id.rma_id.name,
            "customer_address_id": item.line_id.delivery_address_id.id
            or item.line_id.partner_id.id,
            "delivery_address_id": self.partner_id.id,
            "product_id": item.line_id.product_id.id,
            "customer_rma_id": item.line_id.id,
            "product_qty": item.product_qty,
            "rma_id": rma.id if rma else False,
            "uom_id": item.line_id.uom_id.id,
            "operation_id": operation.id,
            "receipt_policy": operation.receipt_policy,
            "delivery_policy": operation.delivery_policy,
            "supplier_to_customer": operation.supplier_to_customer,
            "in_warehouse_id": operation.in_warehouse_id.id or warehouse.id,
            "out_warehouse_id": operation.out_warehouse_id.id or warehouse.id,
            "in_route_id": operation.in_route_id.id or route.id,
            "out_route_id": operation.out_route_id.id or route.id,
            "location_id": (
                operation.location_id.id
                or operation.in_warehouse_id.lot_rma_id.id
                or warehouse.lot_rma_id.id
            ),
        }
        return data

    def make_supplier_rma(self):
        self = self.with_context(supplier=True, customer=False)
        rma_obj = self.env["rma.order"]
        rma_line_obj = self.env["rma.order.line"]
        rma = False

        for item in self.item_ids:
            line = item.line_id
            if item.product_qty <= 0.0:
                raise ValidationError(_("Enter a positive quantity."))

            if self.supplier_rma_id:
                rma = self.supplier_rma_id
            if not rma and len(self.item_ids) > 1:
                rma_data = self._prepare_supplier_rma(line.company_id)
                rma = rma_obj.create(rma_data)

            rma_line_data = self._prepare_supplier_rma_line(rma, item)
            rec = rma_line_obj.create(rma_line_data)
            # Ensure that configuration on the operation is applied (like
            #  policies).
            # TODO MIG: in v16 the usage of such onchange can be removed in
            #  favor of (pre)computed stored editable fields for all policies
            #  and configuration in the RMA operation.
            rec._onchange_operation_id()
        action = self.env.ref("rma.action_rma_supplier_lines")
        rma_lines = self.item_ids.mapped("line_id.supplier_rma_line_ids").ids
        result = action.sudo().read()[0]
        result["domain"] = [("id", "in", rma_lines)]
        return result


class RmaLineMakeRmaOrderItem(models.TransientModel):
    _name = "rma.order.line.make.supplier.rma.item"
    _description = "RMA Line Make Supplier RMA Item"

    wiz_id = fields.Many2one(
        "rma.order.line.make.supplier.rma",
        string="Wizard",
        required=True,
        ondelete="cascade",
        readonly=True,
    )
    line_id = fields.Many2one(
        "rma.order.line", string="RMA Line", required=True, ondelete="cascade"
    )
    rma_id = fields.Many2one(
        "rma.order", related="line_id.rma_id", string="RMA Order", readonly=True
    )
    product_id = fields.Many2one(
        "product.product", related="line_id.product_id", readonly=True
    )
    name = fields.Char(related="line_id.name", readonly=True)
    uom_id = fields.Many2one("uom.uom", string="UoM", readonly=True)
    product_qty = fields.Float(string="Quantity", digits="Product UoS")
    operation_id = fields.Many2one(
        comodel_name="rma.operation",
        string="Operation",
        domain=[("type", "=", "supplier")],
    )
