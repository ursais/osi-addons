# Import Odoo libs
from odoo import _, models


class ExceptionRuleConfirm(models.AbstractModel):
    """
    Override confirm on exception popup wizard, removing auto setting
    ignore_exception bool and compute ignored exceptions instead.
    """

    _inherit = "exception.rule.confirm"

    def action_confirm(self):
        self.ensure_one()

        if self.ignore:
            if self.related_model_id:
                record = self.env[self.related_model_id._name].browse(
                    self.related_model_id.id
                )
                # Don't set the ignore exception on record
                self.related_model_id.ignore_exception = False

                # Compute the ignored exceptions
                record.action_ignore_exceptions()

        return {"type": "ir.actions.act_window_close"}
