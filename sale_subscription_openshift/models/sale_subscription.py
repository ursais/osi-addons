# Copyright (C) 2020 Open Source Integrators
# Copyright (C) 2020 Serpent Consulting Services Pvt. Ltd.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
import os

from odoo import api, fields, models


class SaleSubscriptionLine(models.Model):
    _inherit = "sale.subscription.line"

    instance_name = fields.Char("Instance Name")
    instance_url = fields.Char("Instance URL")

    def openshift_login(self, product):
        token = product.product_tmpl_id.openshift_backend_id.token
        api_url = product.product_tmpl_id.openshift_backend_id.api_url
        login_command = "oc login --token=" + str(token) + " --server=" + str(api_url)
        os.system(login_command)

    @api.model
    def create(self, vals):
        if vals.get("product_id"):
            product_rec = self.env["product.product"].browse([vals.get("product_id")])
            if product_rec.product_tmpl_id.operator:
                self.openshift_login(product_rec)
                project_code = (
                    product_rec.product_tmpl_id.openshift_backend_id.create_project
                )
                if project_code:
                    os.system(str(project_code))
                    self.instance_url = (
                        "https://"
                        + vals.get("instance_name")
                        + "."
                        + product_rec.product_tmpl_id.openshift_backend_id.apps_domain
                    )
                    template = self.env.ref(
                        "sale_subscription_openshift.email_kudu_instance_available",
                        raise_if_not_found=False,
                    )
                    template.send_mail(self.id, force_send=True)
        return super(SaleSubscriptionLine, self).create(vals)

    def action_suspend(self):
        res = super().action_suspend()
        if self.product_id.product_tmpl_id.openshift_backend_id:
            self.openshift_login(self.product_id)
            project_code = (
                self.product_id.product_tmpl_id.openshift_backend_id.suspend_project
            )
            if project_code:
                os.system(str(project_code))
                self.instance_url = (
                    "https://"
                    + self.instance_name
                    + "."
                    + self.product_id.product_tmpl_id.openshift_backend_id.apps_domain
                )
                template = self.env.ref(
                    "sale_subscription_openshift.email_kudu_instance_has_been_suspended",
                    raise_if_not_found=False,
                )
                template.send_mail(self.id, force_send=True)
        return res

    def action_re_activate(self):
        res = super().action_re_activate()
        if self.product_id.product_tmpl_id.openshift_backend_id:
            self.openshift_login(self.product_id)
            project_code = (
                self.product_id.product_tmpl_id.openshift_backend_id.resume_project
            )
            if project_code:
                os.system(str(project_code))
                self.instance_url = (
                    "https://"
                    + self.instance_name
                    + "."
                    + self.product_id.product_tmpl_id.openshift_backend_id.apps_domain
                )
                template = self.env.ref(
                    "sale_subscription_openshift.email_kudu_instance_has_been_resumed",
                    raise_if_not_found=False,
                )
                template.send_mail(self.id, force_send=True)
        return res

    def set_close(self):
        res = super().set_close()
        if self.product_id.product_tmpl_id.openshift_backend_id:
            self.openshift_login(self.product_id)
            project_code = (
                self.product_id.product_tmpl_id.openshift_backend_id.close_project
            )
            if project_code:
                os.system(str(project_code))
                self.instance_url = (
                    "https://"
                    + self.instance_name
                    + "."
                    + self.product_id.product_tmpl_id.openshift_backend_id.apps_domain
                )
                template = self.env.ref(
                    "sale_subscription_openshift.email_kudu_instance_has_been_closed",
                    raise_if_not_found=False,
                )
                template.send_mail(self.id, force_send=True)
        return res
