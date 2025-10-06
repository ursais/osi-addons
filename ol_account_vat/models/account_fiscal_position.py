# Import Odoo libs
from odoo import api, models, fields


class AccountFiscalPosition(models.Model):
    """Inherit Fiscal Position for field/method changes."""

    _inherit = "account.fiscal.position"
    # COLUMNS #####

    b2b =fields.Boolean("B2B")
    vat_delivery_match = fields.Boolean(
        string="VAT ID Matches Delivery Country",
    )

    # END #########

    # METHODS ######
    @api.model
    def _get_fiscal_position(self, partner, delivery=None):
        """
        Determine the most appropriate fiscal position based on partner type,
        VAT match status, and fiscal position configuration flags.

        Logic:
        --------
        1. Start from standard Odoo fiscal position logic (super call).
        2. Get all auto-apply fiscal positions.
        3. For non-company partners (B2C):
            - Exclude all positions where 'b2b' is True.
        4. For companies (B2B):
            - Determine if VAT country matches delivery country.
            - If not matching, exclude positions with 'vat_delivery_match' = True.
        5. If multiple fiscal positions remain, select the one with the
           highest score based on:
              vat_required (weight 4) +
              b2b (weight 2) +
              vat_delivery_match (weight 1)
           If tied, Python’s max() preserves order, effectively using sequence.
        6. If no positions match, fallback to the fiscal position from super().

        Returns:
            recordset (account.fiscal.position): The most suitable fiscal position.
        """

        # Get default fiscal position from super
        default_fp = super()._get_fiscal_position(partner, delivery=delivery)

        # Safety check
        if not partner or not delivery:
            return default_fp

        # Helper scoring function
        def _score(fp):
            return (4 * int(fp.vat_required)) + (2 * int(fp.b2b)) + int(fp.vat_delivery_match)

        # Fetch all auto-apply fiscal positions once
        fiscals = self.search([("auto_apply", "=", True)])

        partner_company = partner.commercial_partner_id
        is_company = partner_company.is_company

        # --- B2C (not a company) ---
        if not is_company:
            fiscals = fiscals.filtered(lambda fp: not fp.b2b)

        # --- B2B (company) ---
        else:
            # Check if VAT prefix matches delivery country code
            vat_match = (
                partner.vat
                and delivery.country_id
                and partner.vat[:2].upper() == delivery.country_id.code.upper()
            )
            if not vat_match:
                fiscals = fiscals.filtered(lambda fp: not fp.vat_delivery_match)

        # If no fiscal positions found, fallback to default
        if not fiscals:
            return default_fp

        # Pick fiscal position with highest score
        return max(fiscals, key=_score)
    # END ##########
