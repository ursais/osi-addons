# Import Odoo libs
from odoo import _, models
from odoo.exceptions import UserError


class MrpBom(models.Model):
    """
    Extend BoM to inform user scaffold BoM will be automatically built therefore
    any changes to the BoM that the ECO created can't be done.
    """

    _inherit = "mrp.bom"

    # METHODS #####

    def write(self, vals):
        """
        Block updates to BoM if it's part of an open ECO.
        We only care if the BoM is not active since revised BoM's are in archive states.
        """
        # Fields that are always safe to update even under ECO control
        safe_fields = {"active", "code", "sequence"}

        # If vals contains *only* safe fields, skip blocking
        if set(vals.keys()).issubset(safe_fields):
            return super().write(vals)

        for bom in self:
            # Only care about inactive BoMs linked to open ECOs with rebuild scaffold
            if not bom.active and bom.eco_ids.filtered(
                lambda e: e.state in ["progress", "confirmed"]
                and e.rebuild_scaffold_bom
            ):
                raise UserError(
                    "This BoM is controlled by an open ECO with 'Rebuild Scaffolding BoM' enabled.\n"
                    "Structural changes are blocked until you apply changes or close the ECO."
                )

        return super().write(vals)

    # END #########
