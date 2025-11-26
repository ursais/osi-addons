# Import Odoo libs
# Constants for config parameter keys
CONFIG_ENABLE_DELAY_SO_ACTION_CONFIRM = CONFIG_ENABLE_DELAY_SO_ACTION_CONFIRM
CONFIG_AUTO_CONFIRM_MO = "auto_confirm_mo"


from odoo import models, api


class StockRule(models.Model):
    """
    Override stock rules to set sale_order_id gets set on MO.
    """

    _inherit = "stock.rule"

    # Methods #####

    def _prepare_mo_vals(
        self,
        product_id,
        product_qty,
        product_uom,
        location_dest_id,
        name,
        origin,
        company_id,
        values,
        bom,
    ):
        """
        Override the _prepare_mo_vals method to set the sale_order_id.
        """
        res = super()._prepare_mo_vals(
            product_id,
            product_qty,
            product_uom,
            location_dest_id,
            name,
            origin,
            company_id,
            values,
            bom,
        )

        # If sale_line_id exists in values, link the MO to the sale order
        sale_line_id = values.get("sale_line_id")
        if sale_line_id:
            sale_order = self.env["sale.order.line"].browse(sale_line_id).order_id
            sale_line = self.env["sale.order.line"].browse(sale_line_id)
            # Attach sale_order_id to the manufacturing order
            res.update(
                {
                    "sale_order_id": sale_order.id,
                    "sale_order_line_id": sale_line.id,
                    "ignore_exception": True,
                }
            )
        return res

    def _create_manufacturing_orders(self, procurements):
        """
        Override the _create_manufacturing_orders method to pass sale_order_id
        from the sale_line_id to the manufacturing order, even in complex routes.
        """
        for procurement, rule in procurements:
            sale_line = procurement.values.get("sale_line_id")
            if sale_line:
                procurement.values["sale_order_line_id"] = sale_line
        return super(StockRule, self)._create_manufacturing_orders(procurements)

    @api.model
    def _run_pull(self, procurements):
        res = super()._run_pull(procurements)
        enable_split = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param(CONFIG_ENABLE_DELAY_SO_ACTION_CONFIRM)
        )

        for procurement, rule in procurements:
            sale_line_id = procurement.values.get("sale_line_id")
            if sale_line_id:
                sale_order = self.env["sale.order.line"].browse(sale_line_id).order_id
                if enable_split and enable_split.lower() in ("true", "1", "yes"):
                    sale_order.with_delay().split_mo()
                else:
                    sale_order.split_mo()
        return res

    def _should_auto_confirm_procurement_mo(self, p):
        # We need to stop auto confirming MO to stop triggering single tranfer for all split MO,
        # Instead we will manually confirming MOs
        auto_confirm_mo = (
            self.env["ir.config_parameter"].sudo().get_param(CONFIG_AUTO_CONFIRM_MO, "")
        )
        if auto_confirm_mo and auto_confirm_mo.lower() in ("true", "1", "yes"):
            return super()._should_auto_confirm_procurement_mo(p)
        else:
            return False

    # # END #########
