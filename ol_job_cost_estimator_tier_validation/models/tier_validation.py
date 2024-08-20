# Import Odoo libs
from odoo import models


class TierValidation(models.AbstractModel):
    """
    Override allow to remove reviews method.
    This method determines when reviews are reset.
    We are adding the ability to have states in both From/To
    definitions to trigger validation.
    """

    _inherit = "tier.validation"

    # METHODS #########

    def _allow_to_remove_reviews(self, values):
        """Method for deciding whether the elimination of revisions is necessary."""
        res = super()._allow_to_remove_reviews(values)
        self.ensure_one()
        state_to = values.get(self._state_field)
        if not state_to:
            return False
        state_from = self[self._state_field]
        # If you change to _cancel_state reset reviews
        if state_to in (self._cancel_state):
            return True
        # If it is changed to _state_from and it was not in _state_from
        # Added OR if it is in both _state_from and _state_from then reset reviews,
        # otherwise its going it will stay approved through stages
        if (state_to in self._state_from and state_from not in self._state_from) or (
            state_to in self._state_from and state_from in self._state_from
        ):
            return True
        return res

    # END #########
