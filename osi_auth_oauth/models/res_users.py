# Copyright (C) 2023 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json

from odoo import api, models
from odoo.exceptions import AccessDenied, UserError

from odoo.addons.auth_signup.models.res_users import SignupError


class ResUsers(models.Model):
    _inherit = "res.users"

    @api.model
    def _auth_oauth_signin(self, provider, validation, params):
        """retrieve and sign in the user corresponding to provider and validated access token
        :param provider: oauth provider id (int)
        :param validation: result of validation of access token (dict)
        :param params: oauth parameters (dict)
        :return: user login (str)
        :raise: AccessDenied if signin failed

        This method can be overridden to add alternative signin methods.
        """
        oauth_uid = validation["email"]
        try:
            oauth_user = self.search(
                [("oauth_uid", "=", oauth_uid), ("oauth_provider_id", "=", provider)]
            )
            if not oauth_user:
                # OSI, 10/02/2019 BK -- Retrieve login from Odoo for external user
                oauth_user = self.search([("login", "=", validation["email"])])
                if not oauth_user:
                    raise AccessDenied()
            assert len(oauth_user) == 1
            oauth_user.write({"oauth_access_token": params["access_token"]})
            return oauth_user.login
        except AccessDenied as access_denied_exception:
            if self.env.context.get("no_user_creation"):
                return None
            state = json.loads(params["state"])
            token = state.get("t")
            values = self._generate_signup_values(provider, validation, params)
            try:
                _, login, _ = self.signup(values, token)
                return login
            except (SignupError, UserError):
                raise access_denied_exception
