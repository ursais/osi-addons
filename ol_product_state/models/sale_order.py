# Import Odoo libs
from odoo import models, _
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    """
    Add validation error if confirming SO and product can't be manufactured.
    """

    _inherit = "sale.order"

    def action_confirm(self):
        """
        This adds a validation error if any of the products on the sale order can't be
        manufactured or isn't allowed to be a component on a manufacturing order.
        The purpose is to catch them before the sale order gets confirmed and not
        downstream later.
        """
        errors = []

        for order in self:
            for line in order.order_line.filtered(lambda l: l.bom_id):
                finished_product = line.product_id

                def format_product(prod):
                    return "[%s] %s" % (
                        prod.default_code or "No Code",
                        prod.name,
                    )

                if not finished_product.mrp_ok:
                    errors.append(
                        _("Product %s is not allowed to be manufactured.")
                        % format_product(finished_product)
                    )

                for component in line.bom_id.bom_line_ids.mapped("product_id"):
                    if not component.mrp_component_ok:
                        errors.append(
                            _(
                                "Component %s is not allowed to be a component on a manufacturing order."
                            )
                            % format_product(component)
                        )

        if errors:
            raise ValidationError(
                _(
                    "Cannot confirm Sale Order due to the following product configurations:\n\n"
                )
                + "\n".join(errors)
            )

        return super().action_confirm()
