# -*- coding: utf-8 -*-
# Powered by Kanak Infosystems LLP.
# © 2020 Kanak Infosystems LLP. (<https://www.kanakinfosystems.com>).

import base64
import requests

from odoo import api, models
from odoo.addons.auth_signup.models.res_users import SignupError
from odoo.exceptions import AccessDenied, UserError


class ResUsers(models.Model):
    _inherit = "res.users"

    @api.model
    def _get_microsoft_photo(self, provider_id, params):
        provider = self.env['auth.oauth.provider'].sudo().browse(provider_id)
        url = "%s/v1.0/users/%s/photo/$value" % (provider.data_endpoint, params['user_id'])
        headers = {
            'Authorization': 'Bearer %s' % params["access_token"]
        }
        try:
            response = requests.get(url, headers=headers, data={})
            if response.status_code == 200:
                return base64.b64encode(response.content)
        except:
            pass
        return False

    @api.model
    def _microsoft_generate_signup_values(self, provider_id, params):
        email = params.get("email")
        name = params.get("name", email)
        oauth_uid = params["user_id"]
        return {
            "name": name,
            "login": email,
            "email": email,
            "oauth_provider_id": provider_id,
            "oauth_uid": oauth_uid,
            "oauth_access_token": params["access_token"],
            "active": True,
            "image_1920": self._get_microsoft_photo(provider_id, params)
        }

    @api.model
    def _microsoft_auth_oauth_signin(self, provider_id, params):
        try:
            users = self.sudo().search([("oauth_uid", "=", params["user_id"]), ("oauth_provider_id", "=", provider_id)], limit=1)
            if not users:
                users = self.sudo().search([("login", "=", params.get("email"))], limit=1)
            if not users:
                raise AccessDenied()

            assert len(users.ids) == 1

            users.sudo().write({
                "oauth_access_token": params["access_token"]
            })
            return users.login
        except AccessDenied as access_denied_exception:
            if self._context and self._context.get("no_user_creation"):
                return None

            values = self._microsoft_generate_signup_values(provider_id, params)
            try:
                login, _ = self.signup(values)
                return login
            except (SignupError, UserError):
                raise access_denied_exception

    @api.model
    def microsoft_auth_oauth(self, provider_id, params):
        access_token = params.get("access_token")
        login = self._microsoft_auth_oauth_signin(provider_id, params)
        if not login:
            raise AccessDenied()
        return (self.env.cr.dbname, login, access_token)
