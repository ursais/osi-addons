# Import Odoo libs
from odoo import fields, models, api
from odoo.addons.product_configurator_sale.models.sale import SaleOrderLine


@api.depends(
    "config_session_id",
    "company_id",
)
def _compute_price_unit(self):
    """
    Replaced this method from product_configurator_sale.
    In product_configurator_sale whenever tax changes it also triggers super() call to this method
    which is changing price_unit back to the one OOTB method evaluates, and removes the one user manually updated.
    Hence, removed 'tax_id' from depends and ine 'else' condition we are not calling super() so it won't update price_unit
    """
    result = None
    for line in self:
        if line.config_session_id:
            account_tax_obj = self.env["account.tax"]
            line.price_unit = account_tax_obj._fix_tax_included_price_company(
                line.config_session_id.price,
                line.product_id.taxes_id,
                line.tax_id,
                line.company_id,
            )
        else:
            pass
    return result


SaleOrderLine._compute_price_unit = _compute_price_unit


class SaleOrderLine(models.Model):
    """
    Extend sale.order.line with additional fields
    """

    _inherit = "sale.order.line"

    # COLUMNS ##########

    locked = fields.Boolean(
        string="Locked",
        related="order_id.locked",
    )

    # END ##########
