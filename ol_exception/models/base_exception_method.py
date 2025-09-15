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
        rules_info = (
            self.env["exception.rule"]
            .sudo()
            ._get_rules_info_for_domain(self._rule_domain())
        )

        rules_to_remove = {}
        rules_to_add = {}
        detected_keys = set()  # Track all triggered (even if ignored)

        # Preload ignored exceptions
        ignored = self.env["exception.ignore"].search(
            [
                ("res_model", "=", self._name),
                ("res_id", "in", self.ids),
            ]
        )
        ignored_map = {(r.res_id, r.exception_rule_id.id) for r in ignored}

        for rule_info in rules_info:
            main_records = self._get_main_records()

            # Evaluate all exceptions for this rule
            all_records_with_exception = self._detect_exceptions(rule_info)

            # Track all detected exceptions (including ignored ones)
            detected_keys |= {
                (rec.id, rule_info.id) for rec in all_records_with_exception
            }

            # Filter out ignored exceptions
            records_with_exception = all_records_with_exception.filtered(
                lambda r: (r.id, rule_info.id) not in ignored_map
            )

            # Determine which exceptions to add or remove
            records_with_rule_in_exceptions = main_records.filtered(
                lambda r: rule_info.id in r.exception_ids.ids
            )
            to_remove = records_with_rule_in_exceptions - records_with_exception
            to_add = records_with_exception - records_with_rule_in_exceptions

            rules_to_remove.setdefault(rule_info.id, main_records.browse())
            rules_to_add.setdefault(rule_info.id, main_records.browse())
            rules_to_remove[rule_info.id] |= to_remove
            rules_to_add[rule_info.id] |= to_add

        # Apply changes to exception_ids
        for rule_id, records in rules_to_remove.items():
            records.write({"exception_ids": [(3, rule_id)]})

        for rule_id, records in rules_to_add.items():
            records.write({"exception_ids": [(4, rule_id)]})

        # Per-record handling
        for record in self:
            # Reset flag if no exceptions left
            if not record.exception_ids and not record.to_send_exception_email:
                record.write({"to_send_exception_email": True})

            if record.to_send_exception_email and record.exception_ids:
                # Send one email per rule that has a template
                for exception in record.exception_ids.filtered(lambda r: r.template_id):
                    email_values = {}

                    # Collect all users from groups defined on the rule
                    groups = exception.user_group_ids
                    if groups:
                        emails = (
                            groups.mapped("users")
                            .filtered(lambda u: u.email)
                            .mapped("email")
                        )
                        if emails:
                            email_values["email_to"] = ",".join(emails)

                    # Send the template with email_values override
                    exception.template_id.send_mail(
                        record.id, force_send=True, email_values=email_values
                    )

                # Only disable email flag if we actually sent something
                if record.exception_ids.filtered(lambda r: r.template_id):
                    record.write({"to_send_exception_email": False})

            # Cleanup stale ignores
            if "ignored_exception_ids" in record._fields:
                stale_ignores = record.ignored_exception_ids.filtered(
                    lambda ign: (ign.res_id, ign.exception_rule_id.id)
                    not in detected_keys
                )
                stale_ignores.sudo().with_context(skip_detect_exceptions=True).unlink()

        return True

    # END ##########
