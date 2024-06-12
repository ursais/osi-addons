# Copyright (C) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class ProductConfigSession(models.Model):
    _inherit = "product.config.session"

    @api.model
    def values_available(
        self, check_val_ids=None, value_ids=None, custom_vals=None, product_tmpl_id=None
    ):
        """Overrides product configurator values_available to include
        the restriction policy option while generating available values"""
        check_val_ids = (
            self.value_ids.ids if check_val_ids is None else check_val_ids.copy()
        )
        product_tmpl = (
            self.env["product.template"].browse(product_tmpl_id)
            if not self.product_tmpl_id
            else self.product_tmpl_id
        )
        product_tmpl.ensure_one()
        value_ids = self.value_ids.ids if value_ids is None else value_ids.copy()
        if custom_vals is None:
            custom_vals = self._get_custom_vals_dict()

        avail_val_ids = []
        for attr_val_id in check_val_ids:
            config_lines = product_tmpl.config_line_ids.filtered(
                lambda line, attr_val_id: attr_val_id in line.value_ids.ids
            )
            domains = config_lines.mapped("domain_id").compute_domain()
            if product_tmpl.restriction_policy == "sequential":
                if len(config_lines) > 1:
                    for config in config_lines:
                        domain = config.domain_id.compute_domain()
                        avalable = self.validate_domains_against_sels(
                            domain, value_ids, custom_vals
                        )
                        if avalable:
                            avail_val_ids.append(attr_val_id)
                        elif attr_val_id in value_ids:
                            value_ids.remove(attr_val_id)
                else:
                    avail = self.validate_domains_against_sels(
                        domains, value_ids, custom_vals
                    )
                    if avail:
                        avail_val_ids.append(attr_val_id)
                    elif attr_val_id in value_ids:
                        value_ids.remove(attr_val_id)
            else:
                avail = self.validate_domains_against_sels(
                    domains, value_ids, custom_vals
                )
                if avail:
                    avail_val_ids.append(attr_val_id)
                elif attr_val_id in value_ids:
                    value_ids.remove(attr_val_id)
        return avail_val_ids
