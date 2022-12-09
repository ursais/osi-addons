from datetime import timedelta
from odoo import fields, models
from odoo.tools.misc import format_date


class StockInventory(models.Model):
    _name = 'stock.inventory'
    _inherit = ['stock.inventory', 'mail.thread']

    def convert_date(self, date):
        converted_date = format_date(self.env, date, lang_code=self.env.user.lang)
        return converted_date

    def notify_for_inventory_adjustments(self):
        InvAdjObj = self.env['stock.inventory']
        all_inv_adjustments = InvAdjObj.search([
            ('cycle_count_id', '!=', False),
            ('state', '!=', 'done')
        ])

        for inv_adjustment in all_inv_adjustments:
            sch_date = inv_adjustment.date.date()
            notify_date = sch_date - timedelta(days=inv_adjustment.cycle_count_id.cycle_count_rule_id.notify_before)
            if fields.date.today() == notify_date:
                inv_adjustment.notify_linked_followers()

    def notify_linked_followers(self):
        mail_template = self.env.ref('osi_stock_cycle_count.stock_adjustment_notify_template')
        # Send email to followers.
        all_followers = self.message_follower_ids.mapped('partner_id')
        for follower in all_followers:
            mail_template.write({"email_to": follower.email})
            mail_template.with_context(
                name=follower.name, lang=follower.lang,
                sch_date=self.convert_date(self.date),
                inv_name=self.name).sudo().send_mail(0, force_send=True)
