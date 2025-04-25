# Import Odoo libs
from odoo import fields, models


class SaleBookingLine(models.Model):
    _name = "sale.booking.line"
    _description = "Sales Booking Line"

    # COLUMNS ###

    booking_id = fields.Many2one(
        comodel_name="sale.booking",
        string="Sale Booking",
        required=True,
        ondelete="cascade",
    )
    origin = fields.Char(
        string="Sale/Blanket Order",
        related="booking_id.origin",
        store=True,
    )
    sale_order_id = fields.Many2one(
        comodel_name="sale.order",
        string="Sale Order",
    )
    sale_order_currency_id = fields.Many2one(
        string="Sale Order Currency",
        comodel_name="res.currency",
        related="sale_order_id.pricelist_id.currency_id",
    )
    sale_order_line_id = fields.Integer(
        string="Sale Order Line",
    )
    sale_blanket_order_id = fields.Many2one(
        comodel_name="sale.blanket.order",
        string="Sale Blanket Order",
    )
    sale_blanket_order_currency_id = fields.Many2one(
        string="Sale Blanket Order Currency",
        comodel_name="res.currency",
        related="sale_blanket_order_id.pricelist_id.currency_id",
    )
    sale_blanket_order_line_id = fields.Integer(
        string="Sale Blanket Order Line",
    )
    name = fields.Text(
        string="Description",
        required=True,
    )
    invoice_lines = fields.Many2many(
        comodel_name="account.move.line",
        relation="sale_booking_line_invoice_rel",
        column1="booking_line_id",
        column2="invoice_line_id",
        string="Invoice Lines",
        copy=False,
    )
    invoice_status = fields.Selection(
        [
            ("upselling", "Upselling Opportunity"),
            ("invoiced", "Fully Invoiced"),
            ("to invoice", "To Invoice"),
            ("no", "Nothing to Invoice"),
        ],
        string="Invoice Status",
        readonly=True,
    )
    price_unit = fields.Float(
        "Unit Price",
        required=True,
        digits="Product Price",
        default=0.0,
    )
    original_price_unit = fields.Float(
        "Product Price",
        required=True,
        digits="Product Price",
        default=0.0,
    )
    product_lst_price = fields.Float(
        "Variant Price",
        required=True,
        digits="Product Public Price",
        default=0.0,
    )
    price_subtotal = fields.Monetary(
        string="Subtotal",
        readonly=True,
        currency_field="sale_order_currency_id",
    )
    price_tax = fields.Float(
        string="Total Tax",
        readonly=True,
    )
    price_total = fields.Monetary(
        string="Total",
        readonly=True,
        currency_field="sale_order_currency_id",
    )
    tax_id = fields.Many2many(
        comodel_name="account.tax",
        string="Taxes",
    )
    product_id = fields.Many2one(
        comodel_name="product.product",
        string="Product",
    )
    product_uom_qty = fields.Float(
        string="Quantity",
        digits="Product Unit of Measure",
        required=True,
        default=1.0,
    )
    product_uom = fields.Many2one(
        comodel_name="uom.uom",
        string="Unit of Measure",
    )
    is_delivery = fields.Boolean(
        string="Is a Delivery",
        default=False,
    )
    product_qty = fields.Float(
        string="Product Qty",
        digits="Product Unit of Measure",
    )
    product_free_qty = fields.Float(string="Qty Unallocated")
    product_qty_onhand = fields.Float(string="Qty On Hand")
    product_qty_incoming = fields.Float(string="Qty Incoming")
    product_qty_draft = fields.Float(string="Draft PO Qty")

    prev_price_total = fields.Monetary(
        string="Previous Total",
        currency_field="sale_order_currency_id",
        readonly=True,
    )
    prev_price_subtotal = fields.Monetary(
        string="Previous Subtotal",
        currency_field="sale_order_currency_id",
        readonly=True,
    )
    prev_price_tax = fields.Monetary(
        string="Previous Total Tax",
        currency_field="sale_order_currency_id",
        readonly=True,
    )
    line_amount = fields.Monetary(
        string="Booking Line Amount",
        currency_field="sale_order_currency_id",
        required=True,
        readonly=True,
    )
    line_amount_untaxed = fields.Monetary(
        string="Booking Line Amount Untaxed",
        currency_field="sale_order_currency_id",
        required=True,
        readonly=True,
    )

    # END #######
