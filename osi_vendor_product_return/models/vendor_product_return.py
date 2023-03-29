# Copyright (C) 2017 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class VendorProductReturn(models.Model):
    _name = "vendor.product.return"
    _description = "Vendor Product Return"

    @api.depends("return_line.last_price_unit")
    def _compute_amount_all(self):
        """Compute the total amounts of the Return."""
        for return_order in self:
            amount_total = sum(
                line.last_price_unit * line.quantity
                for line in return_order.return_line
            )
            return_order.amount_total = amount_total

    @api.depends("delivery_picking_ids")
    def _compute_picking_count(self):
        for rec in self:
            rec.picking_count = len(rec.delivery_picking_ids.ids)

    @api.depends("vendor_refunds_ids")
    def _compute_vendor_refund_count(self):
        for rec in self:
            rec.vendor_refund_count = len(rec.vendor_refunds_ids.ids)

    name = fields.Char(
        string="Return Reference",
        required=True,
        copy=False,
        readonly=True,
        index=True,
        default="New",
    )
    state = fields.Selection(
        [("draft", "Draft"), ("done", "Done")],
        default="draft",
        tracking=True,
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Vendor",
        required=True,
        domain=[("supplier_rank", ">", 0)],
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    reference = fields.Char(
        "Vendor RMA Number",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    order_date = fields.Datetime(
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        default=fields.Datetime.now,
    )
    is_create_refund = fields.Boolean(
        "Create Refund",
        default=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    reason_return_id = fields.Many2one(
        "return.reason",
        "Reason for Return",
        readonly=True,
        states={"draft": [("readonly", False)]},
        ondelete="restrict",
    )
    source_location_id = fields.Many2one(
        "stock.location",
        string="Source Location",
        required=True,
        domain=[("active", "=", True), ("usage", "=", "internal")],
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    destination_location_id = fields.Many2one(
        "stock.location",
        string="Destination Location",
        required=True,
        domain=[("active", "=", True), ("usage", "=", "supplier")],
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    return_line = fields.One2many(
        "vendor.product.return.line",
        "return_id",
        string="Return Lines",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    amount_total = fields.Monetary(
        string="Total",
        store=True,
        readonly=True,
        compute="_compute_amount_all",
        # tracking=True
    )
    currency_id = fields.Many2one(
        "res.currency",
        related="company_id.currency_id",
        string="Currency",
        readonly=True,
        required=False,
    )
    delivery_picking_ids = fields.One2many(
        "stock.picking",
        "vendor_return_id",
        string="Delivery",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    picking_count = fields.Integer(compute="_compute_picking_count", string="Delivery")
    vendor_refunds_ids = fields.One2many(
        "account.move",
        "vendor_return_id",
        string="Vendor Refunds Bill",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    vendor_refund_count = fields.Integer(
        compute="_compute_vendor_refund_count", string="Bill"
    )

    @api.model
    def create(self, vals):
        if vals.get("name", "New") == "New":
            vals["name"] = (
                self.env["ir.sequence"].next_by_code("vendor.product.return") or "New"
            )
        return super(VendorProductReturn, self).create(vals)

    def _get_picking_type_id(self):
        warehouse_id = self.env["stock.warehouse"].search(
            [("company_id", "=", self.company_id.id)]
        )
        picking_type_id = self.env["stock.picking.type"].search(
            [
                ("code", "=", "outgoing"),
                ("warehouse_id", "in", warehouse_id.ids),
            ],
            limit=1,
        )
        return picking_type_id.id

    @api.model
    def _prepare_picking(self):
        return {
            "picking_type_id": self._get_picking_type_id(),
            "partner_id": self.partner_id.id,
            "date": self.order_date,
            "is_return_supplier": True,
            "location_id": self.source_location_id.id,
            "location_dest_id": self.destination_location_id.id,
            "vendor_return_id": self.id,
        }

    def _product_qty_by_location(self, product, warehouse_stock_location):
        # update context with source location
        ctx = dict(self._context)
        ctx.update({"location": warehouse_stock_location})

        # get product quantity on hand
        qty = product._compute_quantities_dict(
            self._context.get("lot_id"),
            self._context.get("owner_id"),
            self._context.get("package_id"),
            self._context.get("from_date"),
            self._context.get("to_date"),
        )

        qty_wh = 0.0

        if product.id in qty:
            qty_wh = qty[product.id]["qty_available"]

        return qty_wh

    def _create_picking(self):
        picking = False
        for return_product in self:

            # check quantity based on source location
            for line in return_product.return_line:
                # get quantity on hand based on source location
                qty = self._product_qty_by_location(
                    line.product_id, return_product.source_location_id.id
                )
                if qty <= 0.0 and not line.product_id.type == "consu":
                    raise ValidationError(
                        _(
                            "Not enough quantity on hand to return."
                            "\n Product Name = %(name)s"
                            "\n Quantity On Hand = %(qty)s"
                            "\n Return Quantity = %(quantity)s"
                        )
                        % {
                            "name": line.product_id.name,
                            "qty": qty,
                            "quantity": line.quantity,
                        }
                    )

            # check product type
            if any(
                [
                    ptype in ["product", "consu"]
                    for ptype in return_product.return_line.mapped("product_id.type")
                ]
            ):

                # prepare picking values
                res = return_product._prepare_picking()
                res.update({"origin": return_product.name})

                # create stock picking Delivery order
                picking = self.env["stock.picking"].create(res)

                # create stock moves
                return_product.return_line.filtered(
                    lambda r: r.product_id.type in ["product", "consu"]
                )._create_stock_moves(picking, return_product)
                picking.action_assign()

        return picking

    def _get_journal(self):

        journal_pool = self.env["account.journal"]
        company_id = self.env.company.id

        # set journal domain
        journal_domain = [
            ("type", "=", "purchase"),
            ("company_id", "=", company_id),
        ]

        # search purchase refund journal
        journal = journal_pool.search(journal_domain, limit=1)

        return journal.id

    def _prepare_invoice_dict(self, partner):

        # get journal
        journal_id = self._get_journal()

        # prepare dict
        inv_dict = {
            "partner_id": partner.id,
            "invoice_date": fields.Date.context_today(self),
            "payment_reference": "none",
            "move_type": "in_refund",
            "journal_id": journal_id,
            "user_id": self.env.user.id,
            "is_return_supplier": True,
            "ref": self.reference,
            "vendor_return_id": self.id,
        }

        return inv_dict

    def _create_vendor_bill(self):
        for return_product in self:
            # browse partner record
            partner = return_product.partner_id

            # prepare invoice dict
            inv_dict = self._prepare_invoice_dict(partner)
            inv_dict.update({"invoice_origin": return_product.name})

            # create vendor bill
            vendor_bill = self.env["account.move"].create(inv_dict)

            inv_line_list = []
            for line in return_product.return_line:

                # set vendor bill line description
                description = ""
                if line.product_id.default_code:
                    description = "[" + line.product_id.default_code + "] "

                description += line.product_id.name

                # set account
                accounts = line.product_id.product_tmpl_id.get_product_accounts(
                    vendor_bill.fiscal_position_id
                )

                account = accounts["stock_input"]

                if not account:
                    raise ValidationError(
                        _(
                            """Please update Product stock input account or
                            Product's category stock input account."""
                        )
                    )

                # set invoice line dict
                inv_line_list.append(
                    (
                        0,
                        0,
                        {
                            "product_id": line.product_id.id,
                            "quantity": line.quantity,
                            "name": description,
                            "account_id": account.id,
                            "product_uom_id": line.uom_id.id,
                            "move_id": vendor_bill.id,
                            "analytic_distribution": line.analytic_distribution,
                            # "analytic_account_id": line.account_analytic_id.id,
                            "price_unit": abs(line.last_price_unit),
                        },
                    )
                )

            # update vendor bill line if its there
            if inv_line_list:
                vendor_bill.write({"invoice_line_ids": inv_line_list})

            # Put the reason in the chatter
            subject = _("Product Return to Vendor bill refund")
            body = return_product.reason_return_id.display_name
            vendor_bill.message_post(body=body, subject=subject)

        return True

    def create_delivery_order(self):
        for return_product in self:
            if not return_product.return_line.ids:
                raise ValidationError(
                    _("You can not confirm return without return lines.")
                )

            # create delivery order
            return_product._create_picking()

            # check condition for creating refund
            if return_product.is_create_refund:
                # create vendor refund bill
                return_product._create_vendor_bill()

            # set state equal to done
            return_product.write({"state": "done"})

        return True

    def action_picking_view(self):
        pickings = self.mapped("delivery_picking_ids")
        action = self.env.ref("stock.action_picking_tree_ready").read()[0]
        if len(pickings) > 1:
            action["domain"] = [("id", "in", pickings.ids)]
        elif len(pickings) == 1:
            action["views"] = [(self.env.ref("stock.view_picking_form").id, "form")]
            action["res_id"] = pickings.ids[0]
        else:
            action = {"type": "ir.actions.act_window_close"}
        return action

    def action_refunds_bill_view(self):
        bills = self.mapped("vendor_refunds_ids")
        action = self.env.ref("account.action_move_in_refund_type").read()[0]
        if len(bills) > 1:
            action["domain"] = [("id", "in", bills.ids)]
        elif len(bills) == 1:
            action["views"] = [(self.env.ref("account.view_move_form").id, "form")]
            action["res_id"] = bills.ids[0]
        else:
            action = {"type": "ir.actions.act_window_close"}
        return action


class VendorProductReturnLine(models.Model):
    _name = "vendor.product.return.line"
    _inherit = "analytic.mixin"
    _description = "Vendor Product Return Line"

    @api.depends("quantity", "last_price_unit")
    def _compute_amount(self):
        """Compute the amounts of the Return line."""
        for line in self:
            line.update({"price_total": line.last_price_unit * line.quantity})

    return_id = fields.Many2one("vendor.product.return", string="return_product ID")
    product_id = fields.Many2one("product.product", string="Product", required=True)
    tracking = fields.Selection(
        [("serial", "Serial"), ("lot", "Lot"), ("none", "None")],
        default="none",
        related="product_id.tracking",
        string="Tracking",
    )
    quantity = fields.Float(default=1.0)
    uom_id = fields.Many2one("uom.uom", string="Unit of Measure")
    price_unit = fields.Float("Std Cost", digits="Product Price")
    last_price_unit = fields.Float("Unit Price", digits="Product Price")
    company_id = fields.Many2one(
        "res.company",
        related="return_id.company_id",
        string="Company",
        store=True,
        readonly=True,
    )
    qty_done = fields.Float("Done Qty")
    price_total = fields.Monetary(
        compute="_compute_amount",
        string="Sub Total",
        readonly=True,
        store=True,
    )
    currency_id = fields.Many2one(
        related="return_id.currency_id",
        store=True,
        string="Currency",
        readonly=True,
    )

    @api.onchange("product_id")
    def _onchange_product(self):
        if self.product_id:
            # restrict to source location
            if not self.return_id.source_location_id:
                self.product_id = False
                warning = {
                    "title": _("Warning!"),
                    "message": _("You must first select a source location!"),
                }
                return {"warning": warning}

            # set UoM and Standard Price
            self.uom_id = self.product_id.uom_po_id.id
            self.price_unit = self.product_id.standard_price

            # set stock move pool
            move_obj = self.env["stock.move"]

            # last vendor price for product
            # check vendor has last stock move
            vendor_stock_moves_id = move_obj.search(
                [
                    ("partner_id", "=", self.return_id.partner_id.id),
                    ("state", "=", "done"),
                    ("product_id", "=", self.product_id.id),
                ],
                order="id desc",
                limit=1,
            )
            if vendor_stock_moves_id:
                self.last_price_unit = vendor_stock_moves_id.price_unit
            else:
                # check last product price in other vendors
                vendor_stock_moves_id = move_obj.search(
                    [
                        ("state", "=", "done"),
                        ("product_id", "=", self.product_id.id),
                    ],
                    order="id desc",
                    limit=1,
                )
                if vendor_stock_moves_id:
                    self.last_price_unit = vendor_stock_moves_id.price_unit

            # check Unit Price is equal to zero then update with product cost price
            if self.last_price_unit == 0.0:
                self.last_price_unit = self.product_id.standard_price

    def _create_stock_moves(self, picking, return_product):
        # set variables
        moves = self.env["stock.move"]
        done = moves.browse()

        for line in self:
            # prepare stock move values
            template = {
                "name": line.product_id.name or "",
                "product_id": line.product_id.id,
                "product_uom": line.uom_id.id,
                "product_uom_qty": line.quantity,
                "date": line.return_id.order_date,
                "location_id": line.return_id.source_location_id.id,
                "location_dest_id": line.return_id.destination_location_id.id,
                "picking_id": picking.id,
                "partner_id": line.return_id.partner_id.id,
                "move_dest_ids": False,
                "state": "draft",
                "company_id": line.return_id.company_id.id,
                "price_unit": line.last_price_unit,
                "picking_type_id": line.return_id._get_picking_type_id(),
                "group_id": False,
                "origin": return_product.name,
            }

            done += moves.create(template)

        return done

    def open_pack_return_operation(self):
        # copy context
        context = self._context
        ctx = context.copy()
        assert len(self) == 1
        # get form view id
        form_view_id = self.env.ref(
            "osi_vendor_product_return.view_pack_operation_return_lot_form"
        ).id
        # set variable
        if self.tracking == "serial":
            only_create = True
        else:
            only_create = False
        ctx.update({"only_create": only_create})
        # search stock pack return operation id
        res_id = self.env["stock.pack.return.operation"].search(
            [("return_line_id", "=", self.id)], limit=1
        )
        res_id = res_id.id
        return {
            "name": _("Lot Details"),
            "type": "ir.actions.act_window",
            "view_type": "form",
            "res_model": "stock.pack.return.operation",
            "views": [[form_view_id, "form"]],
            "view_mode": "form",
            "target": "new",
            "res_id": res_id,
            "context": ctx,
        }


class StockPackReturnOperation(models.Model):
    _name = "stock.pack.return.operation"
    _description = "Stock Pack Return Operation"

    product_qty = fields.Float("Quantity")
    qty_done = fields.Float("Quantity")
    product_id = fields.Many2one("product.product", string="Product")
    product_uom_id = fields.Many2one("uom.uom", string="UoM")
    return_operation_line = fields.One2many(
        "stock.pack.return.operation.line",
        "stock_pack_return_id",
        string="Pack Return Operation",
    )
    state = fields.Selection(
        [("progress", "In Progress"), ("done", "Done")],
        default="progress",
    )
    return_line_id = fields.Many2one(
        "vendor.product.return.line", string="Return Line ID"
    )

    @api.onchange("return_operation_line")
    def _onchange_packlots(self):

        # update Done quantity
        self.qty_done = sum([x.qty_done for x in self.return_operation_line])

    @api.model
    def default_get(self, fields):

        context = self._context

        # call super method
        res = super(StockPackReturnOperation, self).default_get(fields)

        # update return_product values
        for line in self.env["vendor.product.return.line"].browse(
            context.get("active_ids", [])
        ):
            res.update(
                {
                    "product_qty": line.quantity - line.qty_done,
                    "qty_done": line.qty_done,
                    "product_id": line.product_id and line.product_id.id,
                    "product_uom_id": line.uom_id and line.uom_id.id,
                    "return_line_id": line.id,
                }
            )
        return res

    def save(self):

        # update return line Done quantity
        self.return_line_id.write(
            {"qty_done": sum([x.qty_done for x in self.return_operation_line])}
        )

        return True


class StockPackReturnOperationLine(models.Model):
    _name = "stock.pack.return.operation.line"
    _description = "Stock Pack Return Operation Line"

    qty_done = fields.Float("Done", default=1.0)
    production_lot_id = fields.Many2one("stock.lot", string="Lot/Serial Number")
    stock_pack_return_id = fields.Many2one(
        "stock.pack.return.operation", string="Stock Pack Operation"
    )
