from odoo import models


class MrpUnbuild(models.Model):
    _inherit = "mrp.unbuild"

    def action_unbuild(self):
        res = super(MrpUnbuild, self).action_unbuild()
        self.mo_id.with_context(
            from_unbuild=1, unbuild_name=self.name, unbuild_qty=self.product_qty
        ).run_consu_aml()
        return res
