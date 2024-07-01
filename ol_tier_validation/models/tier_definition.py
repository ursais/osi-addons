# Import Odoo libs
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class TierDefinition(models.Model):
    _inherit = ["mail.thread", "mail.activity.mixin", "portal.mixin", "tier.definition"]
    _name = "tier.definition"

    """
    Add tracking to fields
    """
    # COLUMNS ###

    python_code = fields.Text(
        string="Tier Definition Expression",
        help="Write Python code that defines when this tier confirmation "
        "will be needed. The result of executing the expresion must be "
        "a boolean.",
        default="""# Available locals:\n#  - rec: current record\nTrue""",
        tracking=True,
    )
    reviewer_expression = fields.Text(
        string="Review Expression",
        help="Write Python code that defines the reviewer. "
        "The result of executing the expression must be a res.users "
        "recordset.",
        default="# Available locals:\n#  - rec: current record\n"
        "#  - Expects a recordset of res.users\nrec.env.user",
        tracking=True,
    )
    has_tier_group = fields.Boolean(compute="_compute_has_tier_group")

    # END #######
    # METHODS ###
    def _compute_has_tier_group(self):
        for rec in self:
            rec.has_tier_group = self.env["res.users"].has_group(
                "ol_tier_validation.group_tier_validation_python"
            )

    @api.model
    def create(self, vals):
        self.check_user_permissions(vals)
        return super().create(vals)

    def write(self, vals):
        self.check_user_permissions(vals)
        return super().write(vals)

    def check_user_permissions(self, vals):
        """
        If python_code or reviewer_expression is set/changed
        and user does not have the correct permissions
        raise UserError
        """
        tier_python_group = self.env["res.users"].has_group(
            "ol_tier_validation.group_tier_validation_python"
        )
        if (
            "python_code" in vals or "reviewer_expression" in vals
        ) and not tier_python_group:
            raise ValidationError(
                _(
                    """You do not have permissions to add python code to tier
                      validations. Please see your administrator for access."""
                )
            )

    # END #######
