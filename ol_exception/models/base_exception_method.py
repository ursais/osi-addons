# Import Odoo libs
from odoo import _, fields, models


class BaseExceptionMethod(models.AbstractModel):
    """
    Override base exception method to remove ignored exceptions if
    no longer part of exception list.
    """

    _inherit = "base.exception.method"

    # COLUMNS #####

    # This field is use for avoid send multip email of exception's
    to_send_exception_email = fields.Boolean(
        string="Send exception email",
        default=True,
        copy=False,
    )

    # END #########
    # METHODS ######

    def detect_exceptions(self):
        # Run the standard OCA detection
        all_exception_ids = super().detect_exceptions()

        detected_keys = {
            (rec.id, rule.id) for rec in self for rule in rec.exception_ids
        }

        for record in self:
            # --- Cleanup stale ignores ---
            if "ignored_exception_ids" in record._fields:
                stale_ignores = record.ignored_exception_ids.filtered(
                    lambda ign: (ign.res_id, ign.exception_rule_id.id)
                    not in detected_keys
                )
                if stale_ignores:
                    stale_ignores.sudo().with_context(
                        skip_detect_exceptions=True
                    ).unlink()

            # --- Email notifications ---
            if record.exception_ids:
                exception_ids = record.exception_ids.filtered(lambda e: e.template_id)
                for exception in exception_ids:
                    exception.template_id.send_mail(record.id, force_send=True)
                if exception_ids:
                    record.write({"to_send_exception_email": False})

        return all_exception_ids

    # END ##########
