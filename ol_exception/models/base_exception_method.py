# Import Odoo libs
from odoo import _, models


class BaseExceptionMethod(models.AbstractModel):
    """
    Override base exception method to remove ignored exceptions if
    no longer part of exception list.
    """

    _inherit = "base.exception.method"

    # METHODS ######

    def detect_exceptions(self):
        rules_info = (
            self.env["exception.rule"]
            .sudo()
            ._get_rules_info_for_domain(self._rule_domain())
        )
        all_exception_ids = []
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

            if records_with_exception:
                all_exception_ids.append(rule_info.id)

        # Apply changes to exception_ids
        for rule_id, records in rules_to_remove.items():
            records.write({"exception_ids": [(3, rule_id)]})
        for rule_id, records in rules_to_add.items():
            records.write({"exception_ids": [(4, rule_id)]})

        # Cleanup: Remove ignore records for exceptions no longer triggered
        for record in self:
            if "ignored_exception_ids" not in record._fields:
                continue

            stale_ignores = record.ignored_exception_ids.filtered(
                lambda ign: (ign.res_id, ign.exception_rule_id.id) not in detected_keys
            )
            stale_ignores.sudo().with_context(skip_detect_exceptions=True).unlink()

        return all_exception_ids

    # END ##########
