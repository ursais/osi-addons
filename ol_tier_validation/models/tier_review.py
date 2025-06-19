# Import Odoo libs
from odoo import models, _
from odoo.exceptions import ValidationError


class TierReview(models.Model):
    """Override method to provide more descriptive error."""

    _inherit = "tier.review"

    # METHODS ###

    def _get_reviewers(self):
        """
        Overriding this method to provide a better error so the user knows
        what field needs to be set.
        """

        if self.reviewer_field_id:
            resource = self.env[self.model].browse(self.res_id)
            reviewer_field = getattr(resource, self.reviewer_field_id.name, False)
            if not reviewer_field or not reviewer_field._name == "res.users":
                field_label = self.reviewer_field_id.field_description
                raise ValidationError(
                    _(
                        "A Tier Validation is needed however the field '%s' must be"
                        " set to a valid 'User' record in order to proceed."
                    )
                    % field_label
                )
        return super()._get_reviewers()

    # END #######
