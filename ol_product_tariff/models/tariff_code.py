# Import Python Libs

# Import Odoo Libs
from odoo import models, fields


class TariffCode(models.Model):
    _name = "tariff.code"
    _description = "Tariff Code"

    def _get_default_type_id(self):
        if self.env.company.short_name == "eu":
            return self.env.ref("ol_product_tariff.taric_code")

        if self.env.company.short_name == "us":
            return self.env.ref("ol_product_tariff.hts_code")

        return None

    # COLUMNS ###
    name = fields.Char(string="Name", size=64, required=True)
    company_id = fields.Many2one(
        string="Internal Company",
        comodel_name="res.company",
        default=lambda self: self.env.company,
        readonly=True,
    )
    short_description = fields.Char(string="Short Description")
    description = fields.Text(string="Description")
    schedule_b = fields.Char(string="Schedule B")
    type_id = fields.Many2one(
        comodel_name="tariff.code.type",
        string="Type",
        required=True,
        default=_get_default_type_id,
    )
    code = fields.Char(string="Code", required=True)
    # END #######
