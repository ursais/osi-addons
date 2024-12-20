# See LICENSE file for full copyright and licensing details.

import json
import urllib

from odoo import fields, models
from odoo.http import request


class AuthOauthProvider(models.Model):
    """Class defining the configuration values of an OAuth2 provider"""

    _inherit = "auth.oauth.provider"

    secret_key = fields.Char()

    # def oauth_token(
    #         self, type_grant, oauth_provider_rec, code=None,
    #         refresh_token=None, context=None):
    #     url = "https://www.google.com"
    #     timeout = 5
    #     try:
    #         # requesting URL
    #         request_int = requests.get(url, timeout=timeout)

    #     # catching exception
    #     except (requests.ConnectionError, requests.Timeout) as exception:
    #         raise UserError("Internet is off")
    #     data = dict(
    #         grant_type=type_grant,
    #         redirect_uri=self.env['ir.config_parameter'].sudo().get_param(
    #             'web.base.url') + '/auth_oauth/microsoft/signin',
    #         client_id=oauth_provider_rec.client_id,
    #         client_secret=oauth_provider_rec.secret_key,
    #     )
    #     if code:
    #         data.update({'code': code})
    #     elif refresh_token:
    #         data.update({'refresh_token': refresh_token})
    #     return json.loads(urllib.request.urlopen(
    #         urllib.request.Request(
    #             oauth_provider_rec.validation_endpoint,
    #             urllib.parse.urlencode(data).encode("utf-8"))).read())

    def oauth_token(
        self,
        type_grant,
        oauth_provider_rec,
        code=None,
        refresh_token=None,
        context=None,
    ):
        data = dict(
            grant_type=type_grant,
            redirect_uri=request.env["ir.config_parameter"]
            .sudo()
            .get_param("web.base.url")
            + "/auth_oauth/microsoft/signin",
            client_id=oauth_provider_rec.client_id,
            client_secret=oauth_provider_rec.secret_key,
        )
        if code:
            data.update({"code": code})
        elif refresh_token:
            data.update({"refresh_token": refresh_token})
        return json.loads(
            urllib.request.urlopen(
                urllib.request.Request(
                    oauth_provider_rec.validation_endpoint,
                    urllib.parse.urlencode(data).encode("utf-8"),
                )
            ).read()
        )
