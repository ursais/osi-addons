from odoo import api, fields, models
# from odoo.addons.ol_base.tools import date_util


class HelpdeskRma(models.Model):
    """
    Add reporting functions to RMAs
    """

    _inherit = 'helpdesk.rma'

    # COLUMNS #####

    # END #########

    def get_bin_label_data(self):
        """
        Get a dict of information for this RMA to be used on the bin label
        """
        self.ensure_one()

        res = {
            'name': self.name,
            'rush_order': self.rush,
            'sale_order': self.sale_order_id.name,
            'account_manager': self.account_manager.name,
            'customer': self.partner_id.commercial_partner_id.display_name,
            'received': self.get_move_date(),
            'products': [f'{line.product_qty}x {line.name}' for line in self.used_rma_line_ids],
        }

        return res

    def get_move_date(self):
        """
        Gets date from stock move
        """
        self.ensure_one()
        if not self.received_date or not self.used_rma_line_ids.filtered(lambda l: l.received):
            return False

        return date_util.get_local_date_from_utc(
            datetime=self.received_date, tz=self.env.context.get('tz') or self.env.user.tz, string=True
        )
