# Import Odoo libs
from odoo import api, models, fields


class AccountFiscalPosition(models.Model):
    """Inherit Fiscal Position for field/method changes."""

    _inherit = "account.fiscal.position"
    # COLUMNS #####

    ignore_for_domestic_deliveries = fields.Boolean(
        string="Ignore for Domestic Deliveries",
    )
    # END #########

    # METHODS ######
    @api.model
    def _get_fiscal_position(self, partner, delivery=None):
        """
            Retrieve the appropriate fiscal position based on the partner and optional delivery address.

            This method extends the base implementation by adding logic to exclude fiscal positions 
            marked as "ignore_for_domestic_deliveries" if the delivery address is domestic 
            (i.e., matches the company's country).

            Args:
                partner (res.partner): The partner for whom the fiscal position is being determined.
                delivery (res.partner, optional): An optional delivery address. If not provided,
                    the partner's country is used.

            Returns:
                account.fiscal.position: A filtered fiscal position record or records based on 
                domestic delivery rules.
        """
        fiscal_position = super()._get_fiscal_position(partner, delivery=delivery)
        country_id = self.env.company.country_id

        delivery_country_id = delivery.country_id if delivery else partner.country_id
        if delivery_country_id == country_id:
            fiscal_position = fiscal_position.filtered(
                lambda l: not l.ignore_for_domestic_deliveries
            )

        return fiscal_position

    # END ##########
