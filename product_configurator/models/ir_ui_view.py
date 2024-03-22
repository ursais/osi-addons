from odoo import models


class View(models.Model):
    _inherit = "ir.ui.view"

    def _validate_tag_button(self, node, name_manager, node_info):
        special = node.get("special")
        if special and special == "no_save":
            return
        return super()._validate_tag_button(node, name_manager, node_info)
