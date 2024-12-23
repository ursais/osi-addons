from odoo import fields, models


class SaleEstimateJob(models.Model):
    _inherit = "sale.blanket.order"

    opportunity_id = fields.Many2one("crm.lead")
