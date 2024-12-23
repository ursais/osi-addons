from odoo import fields, models


class MrpEco(models.Model):
    _inherit = "mrp.eco"

    opportunity_id = fields.Many2one("crm.lead", string="Opportunity")
