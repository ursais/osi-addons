# Import Odoo libs
from odoo import _, models
from odoo.exceptions import UserError


class AccountMove(models.Model):
    """Inherit Account Move for field/method changes."""

    _inherit = "account.move"

    # METHODS ######

    def unlink(self):
        """
        Restrict deletion of account.move to only the system user
        and users with the special permission.
        Users should cancel account moves instead of deleting to adhere
        to Onlogic Accounting policy.
        """
        for move in self:
            # Allow deletion if the user is the system user to be safe
            # and not impact system operations
            if self.env.uid == 1:
                continue

            # Restrict deletion
            if not self.env.user.has_group("ol_account.group_account_move_delete"):
                raise UserError(
                    _(
                        "You are not allowed to delete account moves. "
                        "Please cancel them instead."
                    )
                )
            if move.state != "draft":
                raise UserError(
                    _(
                        "Only draft account moves can be deleted. "
                        "For posted moves, cancel them instead."
                    )
                )
        return super(AccountMove, self).unlink()

    # END ##########
