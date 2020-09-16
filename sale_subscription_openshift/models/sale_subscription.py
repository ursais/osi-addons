# Copyright (C) 2020 Open Source Integrators
# Copyright (C) 2020 Serpent Consulting Services Pvt. Ltd.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
import os
from datetime import timedelta

from odoo import api, fields, models


class SaleSubscription(models.Model):
    _inherit = "sale.subscription"

    @api.model
    def _cron_recurring_create_invoice(self):
        today_date = fields.Date.context_today(self)
        date = fields.Date.context_today(self) + timedelta(days=10)
        recurring_sub = self.search(
            [("recurring_next_date", "=", date), ("payment_token_id", "=", False)]
        )
        suspend_sub = self.search(
            [("recurring_next_date", "=", today_date), ("payment_token_id", "=", False)]
        )
        recurring_sub.action_10_day_reminder()
        suspend_sub.action_suspend()
        return super(SaleSubscription, self)._cron_recurring_create_invoice()

    def action_suspend(self):
        res = super().action_suspend()
        for rec in self:
            for line_rec in rec.recurring_invoice_line_ids:
                if line_rec.product_id.product_tmpl_id.openshift_backend_id:
                    line_rec.openshift_login(line_rec.product_id)
                    suspend_code = (
                        line_rec.product_id.product_tmpl_id.openshift_backend_id.suspend_project
                    )
                    apps_domain = (
                        line_rec.product_id.product_tmpl_id.openshift_backend_id.apps_domain
                    )
                    if suspend_code:
                        os.system(str(suspend_code))
                        line_rec.instance_url = (
                            "https://" + line_rec.instance_name + "." + apps_domain
                        )
                        template = line_rec.env.ref(
                            "sale_subscription_openshift.\
                                email_kudu_instance_has_been_suspended",
                            raise_if_not_found=False,
                        )
                        template.send_mail(line_rec.id, force_send=True)
        return res

    def action_re_activate(self):
        res = super().action_re_activate()
        for rec in self:
            for line_rec in rec.recurring_invoice_line_ids:
                if line_rec.product_id.product_tmpl_id.openshift_backend_id:

                    line_rec.openshift_login(line_rec.product_id)
                    resume_code = (
                        line_rec.product_id.product_tmpl_id.openshift_backend_id.resume_project
                    )
                    apps_domain = (
                        line_rec.product_id.product_tmpl_id.openshift_backend_id.apps_domain
                    )
                    if resume_code:
                        os.system(str(resume_code))
                        line_rec.instance_url = (
                            "https://" + line_rec.instance_name + "." + apps_domain
                        )
                        template = line_rec.env.ref(
                            "sale_subscription_openshift.email_kudu_instance_has_been_resumed",
                            raise_if_not_found=False,
                        )
                        template.send_mail(line_rec.id, force_send=True)
        return res

    def set_close(self):
        res = super().set_close()
        for rec in self:
            for line_rec in rec.recurring_invoice_line_ids:
                if line_rec.product_id.product_tmpl_id.openshift_backend_id:
                    line_rec.openshift_login(line_rec.product_id)
                    close_code = (
                        line_rec.product_id.product_tmpl_id.openshift_backend_id.close_project
                    )
                    apps_domain = (
                        line_rec.product_id.product_tmpl_id.openshift_backend_id.apps_domain
                    )
                    if close_code:
                        os.system(str(close_code))
                        line_rec.instance_url = (
                            "https://" + line_rec.instance_name + "." + apps_domain
                        )
                        template = line_rec.env.ref(
                            "sale_subscription_openshift.\
                                email_kudu_instance_has_been_closed",
                            raise_if_not_found=False,
                        )
                        template.send_mail(line_rec.id, force_send=True)
        return res

    def action_10_day_reminder(self):
        for rec in self:
            for rec_id in rec.recurring_invoice_line_ids:
                template = self.env.ref(
                    "sale_subscription_openshift.email_kudu_instance_will_be_closed",
                    raise_if_not_found=False,
                )
                template.send_mail(rec_id.id, force_send=True)
