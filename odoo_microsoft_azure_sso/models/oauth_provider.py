# -*- coding: utf-8 -*-
# Powered by Kanak Infosystems LLP.
# © 2020 Kanak Infosystems LLP. (<https://www.kanakinfosystems.com>).

import logging
import requests

from odoo import fields, models

_logger = logging.getLogger(__name__)


class AuthOauthProvider(models.Model):
    _inherit = "auth.oauth.provider"

    microsoft_secret_key = fields.Char(string='Secret Key')
    microsoft_tenant_id = fields.Char(string='Tenant ID')
    microsoft_provider = fields.Boolean(compute="_compute_microsoft_provider")

    def _compute_microsoft_provider(self):
        for provider in self:
            provider.microsoft_provider = False
            if provider.data_endpoint:
                if "graph.microsoft.com" in provider.data_endpoint:
                    provider.microsoft_provider = True

    def get_microsoft_oauth_token(self, code=None, refresh_token=None, context=None):
        try:
            requests.get("https://graph.microsoft.com", timeout=5)
        except (requests.ConnectionError, requests.Timeout) as exception:
            _logger.error("Your internet connenction is very slow or off: %s" % str(exception))

        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        data = dict(
            grant_type="authorization_code",
            redirect_uri=base_url + "/auth_oauth/microsoft/signin",
            client_id=self.client_id,
            client_secret=self.microsoft_secret_key,
        )
        if code:
            data.update({
                "code": code
            })
        elif refresh_token:
            data.update({
                "refresh_token": refresh_token
            })

        headers = {
            "content-type": "application/x-www-form-urlencoded"
        }
        validation_endpoint = self.validation_endpoint
        if self.microsoft_tenant_id != 'common':
            validation_endpoint = self.validation_endpoint.replace('common', self.microsoft_tenant_id)
        response = requests.post(validation_endpoint, data=data, headers=headers)
        return response.json()
