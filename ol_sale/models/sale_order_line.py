# Import Odoo libs
from odoo import api, fields, models
from odoo.addons.ol_base.tools import get_product_description
from odoo.tools import float_compare
from odoo.addons.sale.models.sale_order_line import SaleOrderLine


# Monkey patch the Invoice Status compute on sale order line to add the two new statuses
@api.depends(
    "state",
    "product_uom_qty",
    "qty_delivered",
    "qty_to_invoice",
    "qty_invoiced",
)
def _compute_invoice_status(self):
    precision = self.env["decimal.precision"].precision_get("Product Unit of Measure")
    for line in self:
        if line.state != "sale":
            line.invoice_status = "no"

        elif (
            line.qty_to_invoice
            and float_compare(
                line.qty_invoiced, line.product_uom_qty, precision_digits=precision
            )
            == 1
        ):
            line.invoice_status = "invoiced"
        elif (
            line.product_uom_qty
            and float_compare(
                line.qty_to_invoice, line.product_uom_qty, precision_digits=precision
            )
            == 0
        ):
            line.invoice_status = "to invoice"

        elif (
            line.state == "sale"
            and line.product_id.invoice_policy == "order"
            and line.product_uom_qty >= 0.0
            and float_compare(
                line.qty_delivered, line.product_uom_qty, precision_digits=precision
            )
            == 1
        ):
            line.invoice_status = "upselling"
        elif (
            line.qty_invoiced
            and float_compare(
                line.qty_invoiced, line.product_uom_qty, precision_digits=precision
            )
            == -1
        ):
            line.invoice_status = "partially invoiced"
        elif line.invoice_lines and all(
            move.payment_state == "paid"
            for move in line.invoice_lines.mapped("move_id")
        ):
            line.invoice_status = "full paid"
        elif (
            float_compare(
                line.qty_invoiced, line.product_uom_qty, precision_digits=precision
            )
            >= 0
        ):
            line.invoice_status = "invoiced"

        else:
            line.invoice_status = "no"


SaleOrderLine._compute_invoice_status = _compute_invoice_status


class SaleOrderLine(models.Model):
    """
    Add new fields to Sale Order Line
    """

    _inherit = "sale.order.line"

    # COLUMNS #####

    product_state_id = fields.Many2one(related="product_template_id.product_state_id")
    invoice_status = fields.Selection(
        selection_add=[
            ("partially invoiced", "Partially Invoiced"),
            ("full paid", "Full Paid"),
        ]
    )

    # END #########
    # METHODS #####

    def update_crm_tag_sale_order(self):
        """
        Update the CRM tags on the related sale order based on the product's state.
        - If the product's state is 'Prototype', the 'Engineering Prototype' tag is
        added to the sale order.
        - If the method is called during a product removal (from_unlink context),
        the tag is removed.
        - Ensures the sale order tags are consistent with the product's state.
        """

        # Retrieve the 'Engineering Prototype' tag reference
        tag_engineering_prototype = self.env.ref(
            "ol_sale.crm_tag_engineering_prototype"
        )

        # Get the current tags on the related sale order
        prototype_state_id = self.env.ref("ol_sale.product_state_prototype").id

        for line in self:
            order = line.order_id
            if not order:
                continue

            tag_ids = order.tag_ids.ids

            # Add the tag if the product's state is 'Prototype'
            if line.product_template_id.product_state_id.id == prototype_state_id:
                if line._context.get("from_unlink"):
                    if tag_engineering_prototype.id in tag_ids:
                        tag_ids.remove(tag_engineering_prototype.id)
                        order.tag_ids = [(6, 0, tag_ids)]
                else:
                    if tag_engineering_prototype.id not in tag_ids:
                        tag_ids.append(tag_engineering_prototype.id)
                        order.tag_ids = [(6, 0, tag_ids)]

            # Remove the tag if the product's state is no longer 'Prototype'
            elif tag_engineering_prototype.id in tag_ids:
                tag_ids.remove(tag_engineering_prototype.id)
                order.tag_ids = [(6, 0, tag_ids)]

    def _update_bom(self, rec):
        """
        Update the Bill of Materials (BoM) for a order line based on the
        selected product. This method searches for a BoM that matches the product
        or its template and assigns it to the order line if applicable.

        :param rec: The order line record being processed.
        """
        if not rec.product_id:
            return  # No product selected, nothing to update

        product = rec.product_id
        product_tmpl_id = product.product_tmpl_id.id

        # Search for a BoM that matches either the specific product or its template
        product_bom = self.env["mrp.bom"].search(
            [
                "|",
                ("product_id", "=", product.id),
                ("product_tmpl_id", "=", product_tmpl_id),
            ],
            limit=1,  # Only retrieve the first matching BoM
        )

        # If a matching BoM is found, assign it to the order line unless a
        # non-scaffolding BoM is already assigned
        if product_bom and (not rec.bom_id or rec.bom_id.scaffolding_bom):
            rec.bom_id = product_bom.id
        # If no BoM is found but the order line has a BoM assigned, remove it
        elif not product_bom and rec.bom_id:
            rec.bom_id = False

    @api.onchange("product_id")
    def _onchange_product_id_set_description_bom(self):
        """
        Automatically update the BoM on the order line when the product is changed.
        This ensures that the correct BoM is always associated with the selected
        product. Also set the bom_id
        """
        for rec in self:
            if rec.product_id:
                rec.name = get_product_description(rec.product_id)
                rec._update_bom(rec)

    @api.model_create_multi
    def create(self, vals):
        """
        Override create method to include attribute values in the name
        of the record based on product attribute line settings.
        Also set the bom_id if it's not being set in vals.
        """
        res = super().create(vals)
        for rec in res.filtered(
            lambda l: l.display_type not in ("line_section", "line_note")
        ):
            rec.name = get_product_description(rec.product_id)
            rec.update_crm_tag_sale_order()
            # Update the BoM for the order line if not already being set
            if "bom_id" not in vals:
                rec._update_bom(rec)
        return res

    def write(self, vals):
        """
        Override the write method to Re-evaluate and update the
        BoM based on the new product selection.
        """
        res = super().write(vals)

        for rec in self:
            # If 'product_id' is being updated, set bom_id on the line
            if vals.get("product_id"):
                # Update the BoM for the order line
                rec._update_bom(rec)

            rec.update_crm_tag_sale_order()
        return res

    def unlink(self):
        # Update CRM tag sale order with context indicating the unlink operation
        self.with_context(from_unlink=True).update_crm_tag_sale_order()
        return super().unlink()

    def get_line_serial_numbers(self):
        """
        Get a list of serial numbers for this sale line
        """
        self.ensure_one()

        return self.move_ids.move_line_ids.mapped("lot_id.name")

    def action_duplicate_line(self):
        """Method that allows a user to duplicate the sale order line."""
        for line in self:
            values = line.copy_data(
                {
                    "order_id": line.order_id.id,
                    "config_session_id": (
                        line.config_session_id.id if line.config_session_id else False
                    ),
                    "bom_id": line.bom_id.id if line.bom_id else False,
                }
            )
            self.create(values)

    # END #########
