# Import Odoo libs
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ExceptionRule(models.Model):
    _name = "exception.rule"
    _inherit = ["exception.rule", "mail.thread"]

    """
    Rewrite Exception Rule fields for adding the Tracking.
    """
    # COLUMNS #####
    name = fields.Char("Exception Name", required=True, translate=True, tracking=True)
    description = fields.Text(translate=True, tracking=True)
    sequence = fields.Integer(
        help="Gives the sequence order when applying the test", tracking=True
    )
    model = fields.Selection(
        selection=[], string="Apply on", required=True, tracking=True
    )
    exception_type = fields.Selection(
        selection=[
            ("by_domain", "By domain"),
            ("by_py_code", "By python code"),
            ("by_method", "By method"),
        ],
        required=True,
        default="by_py_code",
        help="By python code: allow to define any arbitrary check\n"
        "By domain: limited to a selection by an odoo domain:\n"
        "           performance can be better when exceptions"
        "           are evaluated with several records\n"
        "By method: allow to select an existing check method",
        tracking=True,
    )
    domain = fields.Char(tracking=True)
    method = fields.Selection(
        selection=[],
        readonly=True,
        tracking=True,
        help="If methods are added via modules they would show here to run the "
        "exception rule check when the method is triggered.",
    )
    active = fields.Boolean(default=True, tracking=True)
    code = fields.Text(
        "Python Code",
        help="Python code executed to check if the exception apply or "
        "not. Use failed = True to block the exception",
        tracking=True,
    )
    is_blocking = fields.Boolean(
        help="When checked the exception can not be ignored", tracking=True
    )
    # END #########

    def _valid_field_parameter(self, field, name):
        # EXTENDS models
        return name == "tracking" or super()._valid_field_parameter(field, name)

    @api.model
    def _get_view(self, view_id=None, view_type="form", **options):
        arch, view = super()._get_view(view_id, view_type, **options)
        for node in arch.xpath("//field[@name='code']"):
            if (
                self.user_has_groups("ol_exception.group_exception_python")
                and self.exception_type == "by_py_code"
            ):
                node.set("invisible", "0")
        return arch, view

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if (
                self.user_has_groups("base_exception.group_exception_rule_manager")
                and not self.user_has_groups("ol_exception.group_exception_python")
                and vals.get("exception_type") == "by_py_code"
            ):
                raise UserError(
                    _(
                        "You do not have permissions to add python code to exceptions. "
                        "Please see your administrator for access."
                    )
                )

        return super().create(vals_list)

    def write(self, vals):
        res = super().write(vals)
        if (
            self.user_has_groups("base_exception.group_exception_rule_manager")
            and not self.user_has_groups("ol_exception.group_exception_python")
            and self.exception_type == "by_py_code"
        ):
            raise UserError(
                _(
                    "You do not have permissions to add python code to exceptions. "
                    "Please see your administrator for access."
                )
            )
        return res
