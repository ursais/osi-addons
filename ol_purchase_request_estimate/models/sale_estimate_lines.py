# Import Odoo libs
from odoo import fields, models


class SaleEstimatelineJob(models.Model):
    _inherit = "sale.estimate.line.job"

    # COLUMNS ######

    specifications = fields.Text()

    # END ##########
