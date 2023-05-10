# Copyright (C) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class CustomerProductReturn(models.Model):
    _name = "customer.product.return"
    _description = "Customer Product Return"

    @api.depends("return_line.last_price_unit")
    def _compute_amount_all(self):
        """Compute the total amounts of the Return."""
        for return_order in self:
            amount_total = sum(
                line.last_price_unit * line.quantity
                for line in return_order.return_line
            )
            return_order.amount_total = amount_total

    @api.depends("picking_ids")
    def _compute_picking_count(self):
        for rec in self:
            rec.picking_count = len(rec.picking_ids.ids)

    @api.depends("customer_refund_ids")
    def _compute_customer_refund_count(self):
        for rec in self:
            rec.customer_refund_count = len(rec.customer_refund_ids.ids)

    name = fields.Char(
        string="Return Reference",
        required=True,
        copy=False,
        readonly=True,
        index=True,
        default="New",
    )
    state = fields.Selection([("draft", "Draft"), ("done", "Done")], default="draft")
    partner_id = fields.Many2one(
        "res.partner",
        string="Customer",
        required=True,
        domain=[("customer_rank", ">", 0)],
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    reference = fields.Char(readonly=True, states={"draft": [("readonly", False)]})
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
    reason_return = fields.Text(
        "Reason for Return", readonly=True, states={"draft": [("readonly", False)]}
    )
    source_location_id = fields.Many2one(
        "stock.location",
        string="Source Location",
        required=True,
        domain=[("active", "=", True), ("usage", "=", "customer")],
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    destination_location_id = fields.Many2one(
        "stock.location",
        string="Destination Location",
        required=True,
        domain=[("active", "=", True), ("usage", "=", "internal")],
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
        "customer.product.return.line",
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
        tracking=True,
    )
    currency_id = fields.Many2one(
        "res.currency",
        related="company_id.currency_id",
        string="Currency",
        readonly=True,
        required=True,
    )
    picking_ids = fields.One2many(
        "stock.picking",
        "customer_return_id",
        string="Delivery",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    picking_count = fields.Integer(compute="_compute_picking_count", string="Delivery")
    customer_refund_ids = fields.One2many(
        "account.move",
        "customer_return_id",
        string="Bills",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    customer_refund_count = fields.Integer(
        compute="_compute_customer_refund_count", string="Bill"
    )

    def _valid_field_parameter(self, field, name):
        # I can't even
        return name == "tracking" or super()._valid_field_parameter(field, name)

    @api.model
    def create(self, vals):
        if vals.get("name", "New") == "New":
            vals["name"] = (
                self.env["ir.sequence"].next_by_code("customer.product.return") or "New"
            )
        return super(CustomerProductReturn, self).create(vals)

    def _get_picking_type_id(self):
        warehouse_id = self.env["stock.warehouse"].search(
            [("company_id", "=", self.company_id.id)]
        )

        picking_type_id = self.env["stock.picking.type"].search(
            [
                ("code", "=", "incoming"),
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
            "is_return_customer": True,
            "location_id": self.source_location_id.id,
            "location_dest_id": self.destination_location_id.id,
            "customer_return_id": self.id,
        }

    def _create_picking(self):
        picking = False
        for return_product in self:
            if any(
                [
                    ptype in ["product", "consu"]
                    for ptype in return_product.return_line.mapped("product_id.type")
                ]
            ):
                # prepare picking values
                res = return_product._prepare_picking()
                res.update({"origin": self.name})

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
            ("type", "=", "sale"),
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
            "move_type": "out_refund",
            "journal_id": journal_id,
            "user_id": self.env.user.id,
            "is_return_customer": True,
            "customer_return_id": self.id,
        }

        return inv_dict

    def _create_customer_bill(self):
        for return_product in self:

            # browse partner record
            partner = return_product.partner_id

            # prepare invoice dict
            inv_dict = self._prepare_invoice_dict(partner)
            inv_dict.update({"invoice_origin": return_product.name})

            # create customer bill
            customer_bill = self.env["account.move"].create(inv_dict)
            inv_line_list = []

            for line in return_product.return_line:

                # set customer bill line description
                description = ""
                if line.product_id.default_code:
                    description = "[" + line.product_id.default_code + "] "

                description += line.product_id.name

                # set account
                accounts = line.product_id.product_tmpl_id.get_product_accounts(
                    customer_bill.fiscal_position_id
                )
                if customer_bill.move_type in ("out_invoice", "out_refund"):
                    account = accounts["income"]
                else:
                    account = accounts["expense"]

                if not account:

                    raise ValidationError(
                        _(
                            "Please update Product stock input \
                                account or Product's category stock accounts."
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
                            "move_id": customer_bill.id,
                            "analytic_distribution": line.analytic_distribution,
                            # "analytic_account_id": line.account_analytic_id.id,
                            "price_unit": line.last_price_unit,
                        },
                    )
                )

            # update customer bill line if its available
            if inv_line_list:
                customer_bill.write({"invoice_line_ids": inv_line_list})

            # Put the reason in the chatter
            subject = _("Product Return from Customer bill refund")
            body = return_product.reason_return
            customer_bill.message_post(body=body, subject=subject)

        return True

    def create_incoming_order(self):
        for return_product in self:

            if not return_product.return_line.ids:
                raise ValidationError(
                    _("You can not confirm return without return lines.")
                )

            # create delivery order

            return_product._create_picking()

            # create customer refund bill
            if return_product.is_create_refund:
                return_product._create_customer_bill()

            # set state equal to done
            return_product.write({"state": "done"})

        return True

    def action_picking_view(self):
        pickings = self.mapped("picking_ids")
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
        bills = self.mapped("customer_refund_ids")
        action = self.env.ref("account.action_move_out_refund_type").read()[0]
        if len(bills) > 1:
            action["domain"] = [("id", "in", bills.ids)]
        elif len(bills) == 1:
            action["views"] = [(self.env.ref("account.view_move_form").id, "form")]
            action["res_id"] = bills.ids[0]
        else:
            action = {"type": "ir.actions.act_window_close"}
        return action


class CustomerProductReturnLine(models.Model):
    _name = "customer.product.return.line"
    _inherit = "analytic.mixin"
    _description = "Customer Product Return Line"

    @api.depends("quantity", "last_price_unit")
    def _compute_amount(self):
        """Compute the amounts of the Return line."""
        for line in self:
            line.update({"price_total": line.last_price_unit * line.quantity})

    return_id = fields.Many2one("customer.product.return", string="Return Product ID")
    product_id = fields.Many2one("product.product", required=True)
    type = fields.Selection(
        default="none",
        related="product_id.tracking",
        string="Tracking",
        store=True,
    )
    quantity = fields.Float(default=1.0)
    uom_id = fields.Many2one("uom.uom", string="Unit of Measure")
    price_unit = fields.Float("Std Cost", digits=("Product Price"))
    last_price_unit = fields.Float("Unit Price", digits=("Product Price"))
    company_id = fields.Many2one(
        "res.company",
        related="return_id.company_id",
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
            moves = self.env["stock.move"]

            # last customer price for product
            # check customer has last stock move
            customer_stock_moves_id = moves.search(
                [
                    ("partner_id", "=", self.return_id.partner_id.id),
                    ("state", "=", "done"),
                    ("product_id", "=", self.product_id.id),
                ],
                order="id desc",
                limit=1,
            )

            if customer_stock_moves_id:
                self.last_price_unit = customer_stock_moves_id.price_unit
            else:
                # check last product price in other customers
                customer_stock_moves_id = moves.search(
                    [
                        ("state", "=", "done"),
                        ("product_id", "=", self.product_id.id),
                    ],
                    order="id desc",
                    limit=1,
                )
                if customer_stock_moves_id:
                    self.last_price_unit = customer_stock_moves_id.price_unit

            # check Unit Price is equal to zero then update with product cost price
            if self.last_price_unit == 0.0:
                self.last_price_unit = self.product_id.standard_price

    def _create_stock_moves(self, picking, return_product):
        # set variables
        moves = self.env["stock.move"]
        done = self.env["stock.move"].browse()

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
                "price_unit": line.price_unit,
                "picking_type_id": line.return_id._get_picking_type_id(),
                "group_id": False,
                "origin": return_product.name,
            }

            done += moves.create(template)

        return done
