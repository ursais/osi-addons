# Copyright 2020 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import models


class ResPartner(models.Model):
    _inherit = ["res.partner", "attribute.set.owner.mixin"]
    _name = "res.partner"


class ResCountry(models.Model):
    _inherit = ["res.country", "attribute.set.owner.mixin"]
    _name = "res.country"
