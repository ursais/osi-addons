from odoo import api, fields, models


class MrpProduction(models.Model):
    """
    Add functions for printing MO based reports
    """

    _inherit = 'mrp.production'

    def get_bin_label_data(self):
        """
        Get a dict of information for this MO to be used on the bin label
        """
        self.ensure_one()

        res = {
            'name': self.name,
            'product': f'{self.product_qty}x {self.product_id.default_code}',
            'sale_order': '',
            'rush_order': False,
            'customer': '',
            'salesperson': '',
            'carrier': '',
            'ship_by': '',
        }

        if self.sale_order_id:
            res.update(
                {
                    'sale_order': self.sale_order_id.name,
                    'rush_order': self.sale_order_id.rush_order,
                    # TODO: "self.sale_order_id.partner_id.get_company_name()" method not found
                    # 'customer': self.sale_order_id.partner_id.get_company_name(),
                    'customer': self.sale_order_id.partner_id.company_name,
                    'salesperson': self.sale_order_id.user_id.name,
                    'carrier': self.sale_order_id.carrier_id.name,
                    'ship_by': self.sale_order_id.original_commitment_date,
                }
            )
        return res
