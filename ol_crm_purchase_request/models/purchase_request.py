from odoo import fields, models


class PurchaseRequest(models.Model):
    _inherit = "purchase.request"

    opportunity_id = fields.Many2one("crm.lead", string="Opportunity")
