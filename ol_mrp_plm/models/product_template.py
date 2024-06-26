# Import Odoo libs
from odoo import api, models, _
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    """
    Inherit Product Template for Method Overriding.
    """

    _inherit = "product.template"

    # METHODS ##########

    def write(self, vals):
        ecoStage = self.env['mrp.eco.stage'].search([
            ('product_state_id','=',self.product_state_id.id),('allow_bom_edits','=',True)], limit=1)
        if (any(field in vals for field in 
            ['detailed_type','invoice_policy','uom_id','uom_po_id','categ_id','attribute_line_ids']) and
            not self.env["res.users"].has_group('ol_mrp_plm.group_bypass_bom_restiction') and
            not ecoStage):
            raise ValidationError(_('''Raise ValidationError Cannot update %s
             BOM because either there are no active ECO’s in a stage that allows editing this BOM.
             Please make sure a PLM ECO is in a stage that permits editing.''', self.name
            ))
        return super().write(vals)

    # END #########
