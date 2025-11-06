# Copyright (C) 2024 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, models


class MailTemplate(models.Model):
    """
    Inherit mail template to add sale_order to invoice email context.

    This ensures the sale_order variable is available in invoice email templates,
    allowing templates to reference sale_order.name directly.
    """

    _inherit = "mail.template"

    @api.model
    def _get_invoice_sale_order(self, invoice):
        """
        Get the first sale order associated with an invoice.

        Args:
            invoice: account.move record

        Returns:
            sale.order record or False if no sale order found
        """
        if not invoice or invoice.move_type not in ("out_invoice", "out_refund"):
            return False

        # Get sale orders from invoice lines
        sale_orders = invoice.invoice_line_ids.sale_line_ids.order_id
        if sale_orders:
            return sale_orders[0]
        return False

    def _render_template(self, template_txt, model, res_ids, post_process=False):
        """
        Override to add sale_order to context for invoice email templates.

        This method adds the sale_order variable to the template rendering context
        so that templates can reference sale_order.name directly.
        """
        # Call parent first
        result = super()._render_template(
            template_txt, model, res_ids, post_process=post_process
        )

        # Only process invoice templates
        if model != "account.move":
            return result

        # Add sale_order to context and re-render if needed
        # Check if template uses sale_order variable
        if "sale_order" in template_txt:
            invoices = self.env[model].browse(res_ids)
            for invoice in invoices:
                if not invoice.exists():
                    continue

                sale_order = self._get_invoice_sale_order(invoice)

                # Build context with sale_order
                ctx = {
                    "object": invoice,
                    "sale_order": sale_order,
                }

                # Re-render template with updated context
                rendered = self.env["ir.qweb"]._render(
                    template_txt, ctx, raise_if_not_found=False
                )
                if rendered and invoice.id in result:
                    result[invoice.id] = rendered

        return result
