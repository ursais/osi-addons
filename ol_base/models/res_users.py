# Import Odoo libs
from odoo import models, _
from odoo.exceptions import UserError
from odoo.addons.base.models.res_users import check_identity


class ResUsers(models.Model):
    _inherit = "res.users"

    @check_identity
    def api_key_wizard(self):
        if not self.user_has_groups("ol_base.dev_team"):
            raise UserError(_("You do not have access to this functionality!"))
        return super().api_key_wizard()
