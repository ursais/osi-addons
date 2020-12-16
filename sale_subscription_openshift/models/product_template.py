# Copyright (C) 2020 Open Source Integrators
# Copyright (C) 2020 Serpent Consulting Services Pvt. Ltd.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    openshift_backend_id = fields.Many2one("backend.openshift", "OpenShift Backend")
    operator = fields.Char(
        "Operator",
        help="""OpenShift operator used to create an instance from
        when the product is sold""",
    )
