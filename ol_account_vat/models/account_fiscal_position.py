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
              If not matching, exclude positions with 'vat_delivery_match' = True.
        5. If multiple fiscal positions remain, select the one with the
           highest score based on:
              vat_required (weight 4) +
              b2b (weight 2) +
              vat_delivery_match (weight 1)
           If tied, Python’s max() preserves order, effectively using sequence.
        6. If no positions match, fallback to the fiscal position from super().
        """

        # === Step 1: Get default fiscal position ===
        default_fp = super()._get_fiscal_position(partner, delivery=delivery)

        # === Step 2: Safety checks ===
        if not partner:
            return default_fp

        partner_company = partner.commercial_partner_id
        is_company = partner_company.is_company
        delivery = delivery or partner

        # === Step 3: Get all auto-apply fiscal positions ===
        fiscals = self.search([
            ("auto_apply", "=", True),
            ("company_id", "=", self.env.company.id),
        ])

        # === Step 4: Define scoring function ===
        def _score(fp):
            return (4 * int(fp.vat_required)) + (2 * int(fp.b2b)) + int(fp.vat_delivery_match)

        # === Step 5: Handle B2C logic ===
        if not is_company:
            fiscals = fiscals.filtered(lambda fp: not fp.b2b)

            if not (partner.vat or getattr(delivery, "vat", False)):
                fiscals = fiscals.filtered(
                    lambda fp: (
                        not fp.vat_delivery_match
                        and fp.vat_required
                        and (
                            fp.country_id.code
                            in [partner.country_id.code, delivery.country_id.code]
                        )
                    )
                )

        # === Step 6: Handle B2B logic ===
        else:
            vat_match = False
            if partner.vat and delivery.country_id and delivery.country_id.code:
                try:
                    vat_prefix = partner.vat[:2].upper()
                    vat_match = vat_prefix == delivery.country_id.code.upper()
                except Exception:
                    vat_match = False

            if vat_match:
                not_intra_fiscals = fiscals.filtered(
                    lambda l: (
                        partner.country_id.code in l.country_group_id.country_ids.mapped("code")
                        or partner.country_id.code == l.country_id.code
                    )
                )
                if not not_intra_fiscals:
                    fiscals = fiscals.filtered(lambda l: not l.country_group_id and not l.country_id)
            else:
                fiscals = fiscals.filtered(lambda fp: not fp.vat_delivery_match)

        # === Step 7: Special handling for Netherlands (NL) ===
        if (
            (partner.country_id and partner.country_id.code == "NL")
            or (delivery.country_id and delivery.country_id.code == "NL")
        ):
            fiscals = fiscals.filtered(
                lambda fp: (
                    not fp.vat_delivery_match
                    and not fp.vat_required
                    and not fp.b2b
                    and fp.country_id.code == "NL"
                )
            )

        # === Step 8: Fallback if nothing matches ===
        if not fiscals:
            return default_fp

        # === Step 9: Pick the best fiscal position by score ===
        best_fp = max(fiscals, key=_score)
        return best_fp
