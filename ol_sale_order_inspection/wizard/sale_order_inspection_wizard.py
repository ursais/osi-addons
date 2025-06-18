# Import Odoo libs
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class SaleOrderInspectionWizard(models.TransientModel):
    _name = "sale.order.inspection.wizard"
    _description = "Sale Order Inspection Wizard"

    # COLUMNS ##########
    order_id = fields.Many2one("sale.order", required=True)
    order_inspection_ids = fields.Many2many(
        "sale.order.inspection",
        string="Order Inspections",
        domain=lambda self: self._domain_inspections(),
    )
    reason = fields.Text("Reason", required=True)

    # END ##########

    # METHODS ###

    @api.model
    def default_get(self, default_fields):
        values = super().default_get(default_fields)
        sale_id = self.env["sale.order"].browse(self._context.get("active_id"))
        values.update(
            {
                "order_id": sale_id.id,
                "order_inspection_ids": sale_id.order_inspection_ids,
            }
        )

        return values

    def _domain_inspections(self):
        user_groups = self.env.user.groups_id.ids
        return ["|", ("group_ids", "=", False), ("group_ids", "in", user_groups)]

    def confirm(self):
        self.ensure_one()
        existing = self.order_id.order_inspection_ids
        removed = existing - self.order_inspection_ids
        for insp in removed:
            if insp.group_ids and not (insp.group_ids & self.env.user.groups_id):
                raise UserError(
                    _("You can't remove inspections that you don't have access to.")
                )

        self.order_id.order_inspection_ids = self.order_inspection_ids
        msg = (
            """Order Hold Change <br/> <b> %s </b> Applied by <b>%s </b> <br/> Reason: %s """
            % (
                ", ".join(self.order_inspection_ids.mapped("name")),
                self.env.user.name,
                self.reason,
            )
        )

        self.order_id.message_post(body=msg, body_is_html=True)

    # END #######
