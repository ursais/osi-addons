# Import Odoo libs
from odoo import models, fields, api, _


class ProductTemplate(models.Model):
    """
    Add fields and methods related to phantom kits
    """

    _inherit = 'product.template'

    # COLUMNS #####

    is_phantom_kit = fields.Boolean(
        string="Is Phantom Kit",
        help=(
            "Helper field to know if a product is a Phantom Kit. "
            "We only consider a product a Phantom Kit if it has a valid Phantom Kit BOM set"
        ),
        compute="_compute_is_phantom_kit",
        search="_search_is_phantom_kit",
        readonly=True,
    )
    phantom_bom_id = fields.Many2one(
        comodel_name='mrp.bom',
        string='Phantom Kit BoM',
        company_dependent=True,
    )

    # END #########
    # METHODS ##########

    @api.depends('phantom_bom_id')
    @api.depends_context('company')
    def _compute_is_phantom_kit(self):
        """
        Helper function
        """
        for product in self:
            product.is_phantom_kit = bool(product.phantom_bom_id.exists())

    def _search_is_phantom_kit(self, operator, value):
        """
        Convenience function for searching for phantom kits
        """
        if operator not in ('=', '!='):
            raise NotImplementedError(
                'Invalid operator for field [stock.picking.has_delivery_holds]: {}'.format(operator)
            )
        # we use double negatives here because [('phantom_bom_id', '=', True)] does not work
        no_kit = (operator == '=' and not value) or (operator == '!=' and value)
        return [('phantom_bom_id', '!=', no_kit)]

    # END #########
