# Copyright (c) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
import os
from base64 import b64encode

import anthem
from pkg_resources import resource_string

from ..common import req


@anthem.log
def setup_admin_user(ctx):
    """Setup admin user"""
    admin = ctx.env.ref("base.user_admin")
    admin.write(
        {
            "new_password": os.environ.get("ODOO_ADMIN_USER_PASSWORD"),
            "tz": os.environ.get("ODOO_ADMIN_USER_TIMEZONE"),
        }
    )
    admin._set_new_password()


@anthem.log
def setup_company(ctx):
    """Setup company"""
    # load logo on company
    logo_content = resource_string(req, "songs/data/images/logo.png")
    b64_logo = b64encode(logo_content)

    values = {
        "name": "Open Source Integrators",
        "street": "PO Box 940",
        "zip": "85236",
        "state_id": ctx.env.ref("base.state_us_3").id,
        "city": "Higley",
        "country_id": ctx.env.ref("base.us").id,
        "phone": "+1 (855) 811-2377",
        "email": "contact@opensourceintegrators.com",
        "website": "https://www.opensourceintegrators.com",
        "vat": "",
        "logo": b64_logo,
        "currency_id": ctx.env.ref("base.USD").id,
    }
    ctx.env.ref("base.main_company").write(values)


@anthem.log
def main(ctx):
    setup_company(ctx)
    setup_admin_user(ctx)
