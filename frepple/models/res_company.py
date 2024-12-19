# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 by frePPLe bv
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

import logging
import time

from odoo import api, models, fields, exceptions
from ..controllers.frepplexml import encode_jwt, decode_jwt

_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _name = "res.company"
    _inherit = "res.company"

    manufacturing_warehouse = fields.Many2one(
        "stock.warehouse", "Manufacturing warehouse", ondelete="set null"
    )
    calendar = fields.Many2one("resource.calendar", "Calendar", ondelete="set null")
    webtoken_key = fields.Char("Webtoken key", size=128)
    frepple_server = fields.Char("frePPLe web server", size=128)
    disclose_stack_trace = fields.Boolean(
        default=False,
        help="Send stack trace to your frepple server upon connector exceptions.",
    )
    respect_reservations = fields.Boolean(
        default=True,
        help="When checked frepple respects the reservations. When unchecked frepple can reallocate material.",
    )

    @api.model
    def getFreppleURL(self, navbar=True, _url="/"):
        """
        Create an authorization header trusted by frePPLe
        """
        user_company_webtoken = self.env.user.company_id.webtoken_key
        if not user_company_webtoken:
            raise exceptions.UserError("FrePPLe company web token not configured")
        encode_params = dict(
            exp=round(time.time()) + 600, user=self.env.user.login, navbar=navbar
        )
        webtoken = encode_jwt(encode_params, user_company_webtoken)
        if not isinstance(webtoken, str):
            webtoken = webtoken.decode("ascii")
        server = self.env.user.company_id.frepple_server
        if not server:
            raise exceptions.UserError("FrePPLe server URL not configured")
        url = "%s%s?webtoken=%s" % (server, _url, webtoken)
        return url
