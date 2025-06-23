# Import Odoo libs
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class SaleOrderInspectionWizard(models.TransientModel):
    _name = "sale.order.inspection.wizard"
    _description = "Sale Order Inspection Wizard"

    # COLUMNS ##########

    order_id = fields.Many2one(
        comodel_name="sale.order",
        required=True,
    )
    order_inspection_ids = fields.Many2many(
        comodel_name="sale.order.inspection",
        string="Order Inspections",
        domain=lambda self: self._domain_inspections(),
    )
    reason = fields.Text(
        string="Reason",
        required=True,
    )

    # END ##########
    # METHODS ######

    @api.model
    def default_get(self, default_fields):
        values = super().default_get(default_fields)

        # Get the active sale order from context
        sale_id = self.env["sale.order"].browse(self._context.get("active_id"))

        # Prepopulate fields on the wizard/form with values from the sale order
        values.update(
            {
                "order_id": sale_id.id,
                "order_inspection_ids": sale_id.order_inspection_ids,
            }
        )
        return values

    def _domain_inspections(self):
        # Return a domain for filtering inspections:
        # - Include inspections with no group restriction (group_ids is False)
        # - Or where the user's group matches one of the inspection's group_ids
        user_groups = self.env.user.groups_id.ids
        return ["|", ("group_ids", "=", False), ("group_ids", "in", user_groups)]

    def confirm(self):
        # Ensure only one record is being processed
        self.ensure_one()

        # Get inspections already linked to the order
        existing = self.order_id.order_inspection_ids

        # Determine removed and added inspections
        removed = existing - self.order_inspection_ids
        added = self.order_inspection_ids - existing

        # Determine which inspections are being removed by the user
        removed = existing - self.order_inspection_ids

        # For each removed inspection, check if the user has the right permissions
        for insp in removed:
            # If the inspection has group restrictions and user isn't in
            # any of those groups
            if insp.group_ids and not (insp.group_ids & self.env.user.groups_id):
                raise UserError(
                    _("You can't remove inspections that you don't have access to.")
                )

        # Save the new list of inspections to the order
        self.order_id.order_inspection_ids = self.order_inspection_ids

        # Build descriptive message
        parts = []
        if added:
            added_names = ", ".join(added.mapped("name"))
            parts.append("<b>Added:</b> %s" % added_names)
        if removed:
            removed_names = ", ".join(removed.mapped("name"))
            parts.append("<b>Removed:</b> %s" % removed_names)

        msg = "<br/>".join(
            [
                "<b>Order Inspection Change</b>",
                "Applied by <b>%s</b>" % self.env.user.name,
                *parts,
                "Reason: %s" % self.reason,
            ]
        )

        self.order_id.message_post(body=msg, body_is_html=True)

        # Trigger exception checks
        self._trigger_related_exception_checks()

    def _trigger_related_exception_checks(self):
        """Triggers base.exception logic on sale, delivery and manufacturing orders."""
        sale = self.order_id

        # Trigger sale order exception detection
        sale.detect_exceptions()
        if sale.state == "sale":
            sale.with_context(raise_exception=False)._check_exception()

        # Trigger stock.picking exceptions (deliveries)
        pickings = sale.picking_ids.filtered(
            lambda p: p.state in ["waiting", "confirmed", "assigned"]
        )
        pickings.with_context(raise_exception=False)._check_exception()

        # Trigger manufacturing order exceptions
        # You might want to filter only relevant MOs depending on your flow
        manufacturing_orders = sale.mrp_production_ids.filtered(
            lambda p: p.state in ["draft", "confirmed"]
        )
        manufacturing_orders.with_context(raise_exception=False)._check_exception()

    # END #######
