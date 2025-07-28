# Import Odoo libs
from odoo import _, fields, models
from odoo.exceptions import ValidationError


class BaseException(models.AbstractModel):
    """
    Override base exception to add an ignored exception field which
    populates when the exceptions are ignored and can only be applied if the
    user has the security group on the exception rule or no groups are set.
    """

    _inherit = "base.exception"

    # COLUMNS ######

    ignored_exception_ids = fields.One2many(
        "exception.ignore",
        "res_id",
        string="Ignored Exceptions",
        domain=lambda self: [("res_model", "=", self._name)],
    )

    # END ##########
    # METHODS ######

    def action_ignore_exceptions(self):
        # Preload ignored map for performance
        all_ignored = self.env["exception.ignore"].search(
            [("res_model", "=", self._name), ("res_id", "in", self.ids)]
        )
        ignored_map = {(r.res_id, r.exception_rule_id.id) for r in all_ignored}

        for rec in self:
            if any(rec.exception_ids.mapped("is_blocking")):
                raise ValidationError(
                    _("Some exceptions are blocking and cannot be ignored.")
                )

            for exception in rec.exception_ids:
                key = (rec.id, exception.id)

                if key in ignored_map:
                    # Already ignored, just make sure it's not in exception_ids
                    if exception in rec.exception_ids:
                        rec.write({"exception_ids": [(3, exception.id)]})
                    continue

                # Check permission to ignore
                if exception.allowed_group_ids and not (
                    set(exception.allowed_group_ids.ids)
                    & set(self.env.user.groups_id.ids)
                ):
                    continue  # user not in any allowed group

                # Add ignore record
                self.env["exception.ignore"].create(
                    {
                        "res_model": rec._name,
                        "res_id": rec.id,
                        "exception_rule_id": exception.id,
                    }
                )

                # Remove from exception_ids
                rec.write({"exception_ids": [(3, exception.id)]})

        return True

    def _check_exception(self):
        """Exclude ignored exceptions from raising errors"""
        if not self.env.context.get("check_exception", True):
            return True

        exception_ids = self.detect_exceptions()
        if not exception_ids:
            return True

        # Bulk preload ignored rules
        ignored = self.env["exception.ignore"].search(
            [("res_model", "=", self._name), ("res_id", "in", self.ids)]
        )
        ignored_map = {(r.res_id, r.exception_rule_id.id) for r in ignored}

        to_raise = []
        for rec in self:
            for eid in rec.exception_ids.ids:
                if (rec.id, eid) not in ignored_map:
                    to_raise.append(eid)

        if to_raise and self.env.context.get("raise_exception", True):
            exceptions = self.env["exception.rule"].browse(to_raise)
            raise ValidationError("\n".join(exceptions.mapped("name")))

        return True

    # END ##########
