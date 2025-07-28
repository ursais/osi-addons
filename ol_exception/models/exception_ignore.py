# Import Odoo libs
from odoo import fields, models
from odoo.exceptions import ValidationError


class ExceptionIgnore(models.Model):
    """
    New object that tracks which exceptions have been ignored on the record.
    This allows security group control on the exception rules.
    """

    _name = "exception.ignore"
    _description = "Per-Exception Ignore Flag"
    _rec_name = "exception_rule_id"

    # COLUMNS ######

    res_model = fields.Char(required=True)
    res_id = fields.Integer(required=True)
    exception_rule_id = fields.Many2one(
        "exception.rule", required=True, ondelete="cascade"
    )
    user_id = fields.Many2one(
        "res.users",
        default=lambda self: self.env.uid,
    )

    # END ##########
    # CONSTRAINT ###

    _sql_constraints = [
        (
            "unique_ignore",
            "unique(res_model, res_id, exception_rule_id)",
            "Ignore entry already exists.",
        )
    ]

    # END ##########
    # METHODS ######

    def unlink(self):
        """Check if user can delete ignored exceptions. Sudo can always delete."""
        if not self.env.su and not self.env.user._is_superuser():
            for record in self:
                for group in record.exception_rule_id.allowed_group_ids:
                    if group.id not in self.env.user.groups_id.ids:
                        raise ValidationError(
                            "You do not have the rights to clear this exception."
                        )
        return super().unlink()

    # END ##########
