# See LICENSE file for full copyright and licensing details.

import http.client as httplib
import json
import logging

import werkzeug.utils
from werkzeug.urls import url_encode

import odoo
from odoo import http
from odoo.http import request

from odoo.addons.auth_oauth.controllers.main import (
    OAuthLogin as Home,
    fragment_to_query_string,
)
from odoo.addons.web.controllers.utils import _get_login_redirect_url

_logger = logging.getLogger(__name__)


class OAuthLogin(Home):
    def list_providers(self):
        try:
            providers = (
                request.env["auth.oauth.provider"]
                .sudo()
                .search_read([("enabled", "=", True)])
            )
        except Exception:
            providers = []
        provider_microsoft = request.env.ref(
            "odoo_microsoft_account.provider_microsoft"
        )
        base_url = request.env["ir.config_parameter"].sudo().get_param("web.base.url")
        for provider in providers:
            if provider.get("id") == provider_microsoft.id:
                return_url = base_url + "/auth_oauth/microsoft/signin"
                params = dict(
                    client_id=provider["client_id"],
                    response_type="code",
                    redirect_uri=return_url,
                    prompt="select_account",
                    scope=provider["scope"],
                )
            else:
                return_url = base_url + "/auth_oauth/signin"
                state = self.get_state(provider)
                params = dict(
                    response_type="token",
                    client_id=provider["client_id"],
                    redirect_uri=return_url,
                    scope=provider["scope"],
                    state=json.dumps(state),
                )
            provider["auth_link"] = "%s?%s" % (
                provider["auth_endpoint"],
                url_encode(params),
            )
        return providers


class OAuthController(http.Controller):
    @http.route("/auth_oauth/microsoft/signin", type="http", auth="none", csrf=False)
    @fragment_to_query_string
    def microsoft_signin(self, **kw):
        pool = request.env
        root_url = (
            request.env["ir.config_parameter"].sudo().get_param("web.base.url") + "/"
        )
        oauth_provider_rec = (
            pool["ir.model.data"]
            .sudo()
            ._xmlid_to_res_id("odoo_microsoft_account.provider_microsoft")
        )
        provider = pool["auth.oauth.provider"].sudo().browse(oauth_provider_rec)
        authorization_data = (
            pool["auth.oauth.provider"]
            .sudo()
            .oauth_token(
                "authorization_code", provider, kw.get("code"), refresh_token=None
            )
        )
        access_token = authorization_data.get("access_token")
        refresh_token = authorization_data.get("refresh_token")
        try:
            conn = httplib.HTTPSConnection(provider.data_endpoint, timeout=200)
            conn.request(
                "GET",
                "/v1.0/me",
                "",
                {"Authorization": access_token, "Accept": "application/json"},
            )
            response = conn.getresponse()
            data = json.loads(response.read())
            displayName = data.get("displayName")
            mail = data.get("userPrincipalName")
            user_id = data.get("id")
            conn.close()
        except Exception as e:
            _logger.exception(e)
        try:
            credentials = (
                pool["res.users"]
                .sudo()
                .microsoft_auth_oauth(
                    provider.id,
                    {
                        "access_token": access_token,
                        "user_id": user_id,
                        "email": mail,
                        "name": displayName,
                        "microsoft_refresh_token": refresh_token,
                    },
                )
            )
            request.cr.commit()
            pre_uid = request.session.authenticate(*credentials)
            resp = request.redirect(
                _get_login_redirect_url(pre_uid, root_url + "web?"), 303
            )
            return resp
        except AttributeError:
            _logger.error(
                "auth_signup not installed on"
                " database %s: oauth sign up cancelled." % (request.cr.dbname)
            )
            url = "/web/login?oauth_error=1"
        except odoo.exceptions.AccessDenied:
            _logger.info(
                "OAuth2: access denied,"
                " redirect to main page in case a valid"
                " session exists, without setting cookies"
            )
            url = "/web/login?oauth_error=3"
            redirect = werkzeug.utils.redirect(url, 303)
            redirect.autocorrect_location_header = False
            return redirect
        except Exception as e:
            _logger.exception("OAuth2: %s" % str(e))
            url = "/web/login?oauth_error=2"

        redirect = request.redirect(root_url + url, 303)
        redirect.autocorrect_location_header = False
        return redirect
