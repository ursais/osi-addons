# Import Odoo libs
from odoo import fields, models


class ProductConfigSession(models.Model):
    """
    Inherit product config session to add company field.
    """

    _inherit = "product.config.session"

    # COLUMNS ##########

    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        default=lambda self: self.env.company,
    )

    # END ##########
    # METHODS #####

    def _compute_currency_id(self):
        super()._compute_currency_id()
        """Super call the method to set the currency base on current company Currency."""
        main_company = self.env["res.company"]._get_main_company()
        for session in self:
            if session.product_tmpl_id.currency_id:
                session.currency_id = session.product_tmpl_id.currency_id.id

    # END #########
