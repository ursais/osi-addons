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

    name = fields.Char(tracking=True)
    description = fields.Text(tracking=True)
    sequence = fields.Integer(tracking=True)
    model = fields.Selection(tracking=True)
    exception_type = fields.Selection(
        tracking=True,
    )
    domain = fields.Char(tracking=True)
    method = fields.Selection(
        tracking=True,
    )
    active = fields.Boolean(tracking=True)
    code = fields.Text(
        tracking=True,
    )
    is_blocking = fields.Boolean(tracking=True)

    # END #########
    # METHODS #####

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

    # END #########
