# Copyright 2019-2020 ForgeFlow S.L. (https://www.forgeflow.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


def uninstall_hook(env):
    sr = env["stock.request"].search([("state", "=", "submitted")])
    sr.write({"state": "draft"})
    sro = env["stock.request.order"].search([("state", "=", "submitted")])
    sro.write({"state": "draft"})
