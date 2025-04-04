# Import Odoo libs
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    """
    Add new fields to Sale Order
    """

    _inherit = "sale.order"

    # COLUMNS #####
    original_request_date = fields.Date(
        string="Original Customer Requested Date",
        copy=False,
    )
    original_commitment_date = fields.Datetime(
        string="Original Shipment Commitment Date",
        copy=False,
    )
    account_manager_id = fields.Many2one(
        comodel_name="res.users",
        related="partner_id.account_manager_id",
        string="Account Manager",
        store=True,
    )
    end_user = fields.Many2one(comodel_name="res.partner")
    integrator = fields.Many2one(comodel_name="res.partner")
    delivery_note = fields.Text(string="Delivery Note")
    mrp_note = fields.Text(string="Manufacturing Note")

    # This field is populated via Integrations, but also used in emails
    is_guest_checkout = fields.Boolean(
        string="Guest checkout",
        copy=False,
    )

    # END #########

    # METHODS #########

    def action_confirm(self):
        """
        Inherit method for set up value for original_request_date and original_commitment_date
        """

        # First check for original request date and raise validation error if not set
        for rec in self:
            if not rec.original_request_date:
                raise ValidationError(
                    _(
                        "Original Customer Requested Date is required to confirm the order."
                    )
                )

        # Call the parent method once for all records
        res = super().action_confirm()

        # Update original_commitment_date for each record after confirmation
        for rec in self:
            rec.original_commitment_date = self.commitment_date or self.expected_date
        return res

    @api.onchange("partner_id")
    def _onchange_partner_id_sale_order_tag_ids(self):
        self.tag_ids = self.partner_id.sale_order_tag_ids



    def get_quote_report_data(self):
        """Get the Sale Order related report data"""

        data = {}
        for order in self:
            order_data = order.get_report_data()
            data[order.id] = order_data
        return data

    def get_report_data(self):
        """Collect order information into a dict, that can be used in reports"""

        self.ensure_one()

        order_data = {
            'product_lines': [],
        }

        product_lines = self.order_line.filtered(lambda l: not l.is_delivery)

        for sale_order_line in product_lines:

            # TODO: NC : "sale_order_line.quote_config_id" Field not found
            quote_config = sorted_quote_lines = False
            # quote_config = sale_order_line.quote_config_id or False
            #
            # if quote_config:
            #     quote_lines = quote_config.quote_config_line_ids.filtered(
            #         lambda l: l.description_type != 'hide'
            #     )
            #     sorted_quote_lines = quote_lines.sorted(key=lambda q: q.sequence)
            #     # self.print_quote_data_for_debug(quote_config, sorted_quote_lines)
            # else:
            #     sorted_quote_lines = False

            order_line_data = {
                'order_line': sale_order_line,
                'quote_config': quote_config,
                'quote_lines': sorted_quote_lines,
            }

            order_data['product_lines'].append(order_line_data)

        # Set the shipping lines
        shipping_lines = self.order_line.filtered(lambda l: l.is_delivery)

        order_data['shipping_lines'] = shipping_lines
        order_data['product_subtotal_amount'] = sum(product_lines.mapped('price_subtotal'))
        order_data['shipping_subtotal_amount'] = sum(shipping_lines.mapped('price_subtotal'))

        return order_data

    # END #########
