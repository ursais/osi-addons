# See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models
from odoo.exceptions import AccessDenied, UserError

from odoo.addons.auth_signup.models.res_users import SignupError


class ResUsers(models.Model):
    _inherit = "res.users"

    microsoft_refresh_token = fields.Char()

    @api.model
    def _microsoft_generate_signup_values(self, provider, params):
        email = params.get("email")
        return {
            "name": params.get("name", email),
            "login": email,
            "groups_id": [(6, 0, [self.env.ref("base.group_user").id])],
            "email": email,
            "oauth_provider_id": provider,
            "oauth_uid": params["user_id"],
            "company_id": self.env.ref("base.main_company").id,
            "oauth_access_token": params["access_token"],
            "active": True,
            "microsoft_refresh_token": params["microsoft_refresh_token"],
        }

    @api.model
    def _microsoft_auth_oauth_signin(self, provider, params):
        try:
            oauth_uid = params["user_id"]
            users = self.sudo().search(
                [("oauth_uid", "=", oauth_uid), ("oauth_provider_id", "=", provider)],
                limit=1,
            )
            if not users:
                users = self.sudo().search(
                    [("login", "ilike", params.get("email"))], limit=1
                )
            if not users:
                raise AccessDenied()
            assert len(users.ids) == 1
            users.sudo().write(
                {
                    "oauth_access_token": params["access_token"],
                    "microsoft_refresh_token": params["microsoft_refresh_token"],
                }
            )
            return users.login
        except AccessDenied as access_denied_exception:
            if self._context and self._context.get("no_user_creation"):
                return None
            values = self._microsoft_generate_signup_values(provider, params)
            try:
                self = self.with_company(self.env.ref("base.main_company"))
                login, _ = self.with_context(mail_create_nosubscribe=True).signup(
                    values
                )
                return login
            except (SignupError, UserError):
                raise access_denied_exception

    @api.model
    def microsoft_auth_oauth(self, provider, params):
        access_token = params.get("access_token")
        login = self._microsoft_auth_oauth_signin(provider, params)
        if not login:
            raise AccessDenied()
        return self._cr.dbname, login, access_token
