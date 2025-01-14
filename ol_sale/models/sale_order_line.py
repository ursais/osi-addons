# Import Odoo libs
from odoo import api, fields, models
from odoo.addons.ol_base.tools import get_product_description


class SaleOrderLine(models.Model):
    """
    Add new fields to Sale Order Line
    """

    _inherit = "sale.order.line"

    # COLUMNS #####

    product_state_id = fields.Many2one(related="product_template_id.product_state_id")

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
        tag_ids = self.order_id.tag_ids.ids

        # Check if the related sale order exists and the product's state is 'Prototype'
        if (
            self.order_id
            and self.product_template_id.product_state_id.id
            == self.env.ref("ol_sale.product_state_prototype").id
        ):
            if self._context.get("from_unlink"):
                # If the method is called from a product unlink operation, remove the tag
                tag_ids.remove(tag_engineering_prototype.id)
                self.order_id.tag_ids = [(6, 0, tag_ids)]
            else:
                # Otherwise, add the 'Engineering Prototype' tag to the sale order
                self.order_id.tag_ids = [(6, 0, tag_engineering_prototype.ids)]
        # If the product's state is no longer 'Prototype' and the tag is present, remove it
        elif (
            self.product_template_id.product_state_id.id != tag_engineering_prototype.id
            and tag_engineering_prototype.id in self.order_id.tag_ids.ids
        ):
            tag_ids.remove(tag_engineering_prototype.id)
            self.order_id.tag_ids = [(6, 0, tag_ids)]

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
        for rec in res.filtered(lambda l: l.display_type not in ('line_section', 'line_note')):
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

    # END #########
