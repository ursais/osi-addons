from odoo import api, models


class MrpBom(models.Model):
    _inherit = "mrp.bom"

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        default_produce_delay = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("mrp_batch.default_produce_delay")
        )
        default_days_to_prepare_mo = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("mrp_batch.default_days_to_prepare_mo")
        )
        if default_produce_delay:
            defaults.update({'produce_delay': default_produce_delay}) 
        if default_days_to_prepare_mo:
            defaults.update({'days_to_prepare_mo': default_days_to_prepare_mo}) 
        
        return defaults
