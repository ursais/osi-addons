from odoo import _, api, models, exceptions


class ProductTemplate(models.Model):
    """
    Inherit Product Template for Method Overriding.
    """

    _inherit = "product.template"

    # METHODS ##########

    def write(self, vals):
        mrp_eco_stages = self.env['mrp.eco.stage'].search([
            ('product_state_id','=', self.product_state_id.id),
            ('allow_bom_edits','=', True)], limit=1)
        restricted_fields = ['detailed_type','invoice_policy','uom_id','uom_po_id','categ_id','attribute_line_ids']
        if (any(field in list(vals.keys()) for field in restricted_fields) 
            and not self.user_has_groups('ol_mrp_plm.group_bypass_bom_restiction')
            and not mrp_eco_stages
            ):
            raise exceptions.ValidationError(_(
                "Cannot update '%s' Product because either there are no active ECO’s in a stage that allows editing this Product."
                "\nPlease make sure a PLM ECO is in a stage that permits editing.", self.name))
        return super().write(vals)

    # END #########
