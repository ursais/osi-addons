from odoo import models,api
import logging
from itertools import islice

_logger = logging.getLogger(__name__)

class IrActionsServer(models.Model):
    _inherit = "ir.actions.server"
    
    @api.model
    def _process_by_domain(self, model_name, domain, method_name, priority=100, channel='root', batch_size=1000):
        self = self.sudo()
        Model = self.env[model_name].sudo()
        last_id = 0

        _logger.info(
            "Starting %s on %s with domain %s",
            method_name, model_name, domain
        )
        for company in self.env['res.company'].search([]):
            if model_name in ('account.move', 'account.move.line'):
                fiscalyear_lock_date = company.fiscalyear_lock_date
                domain += [('date', '>', fiscalyear_lock_date), ('company_id', '=', company.id)]

            while True:
                records = Model.search(
                    domain + [('id', '>', last_id)],
                    limit=batch_size,
                    order='id',
                )
                if not records:
                    break

                getattr(records.with_delay(description=method_name, priority=priority,channel=channel), method_name)()

                last_id = records[-1].id
                self._cr.commit()

        _logger.info(
            "Finished %s on %s",
            method_name, model_name
        )

    @api.model
    def run_all(self):
        self = self.sudo()
        # --------------------
        # RES.PARTNER
        # --------------------

        self._process_by_domain(
            'res.partner',
            ['|', '|',
                ('credit_limit', '>', 0),
                ('partner_rollup_id', '!=', False),
                ('invoice_ids.state', '=', 'posted')],
            '_compute_customer_deposit_balance',
            20,
            "root.account_queue"
        )

        self._process_by_domain(
            'res.partner',
            ['|', '|', '|',
                ('credit_limit', '>', 0),
                ('partner_rollup_id', '!=', False),
                ('child_ids', '!=', False),
                ('sale_order_ids', '!=', False)],
            '_compute_open_so_balance',
            20,
            "root.account_queue"
        )

        self._process_by_domain(
            'res.partner',
            ['|',('rollup_partner_ids', '!=', False),('total_due', '>', 0)],
            '_compute_outstanding_receivable',
            20,
            "root.account_queue"
        )

        self._process_by_domain(
            'res.partner',
            [('commercial_partner_id', '!=', False), 
            ('commercial_partner_id.property_payment_term_id', '!=', False)],
            '_compute_net_terms_allowed',
            35,
            "root.account_queue"
        )

        # --------------------
        # SALE.ORDER.LINE
        # --------------------

        self._process_by_domain(
            'sale.order.line',
            ['|', ('product_uom_qty', '>', 0), ('qty_delivered', '>', 0)],
            '_compute_bo_qty',
            40,
            "root.sale_queue"
        )

        self._process_by_domain(
            'sale.order.line',
            [('product_id', '!=', False)],
            '_compute_purchase_price',
            50,
            "root.sale_queue"
        )

        self._process_by_domain(
            'sale.order.line',
            ['|', ('qty_delivered', '>', 0), ('qty_invoiced', '>', 0)],
            '_compute_uigd_qty',
            75,
            "root.sale_queue"
        )

        self._process_by_domain(
            'sale.order.line',
            ['|', ('bo_qty', '>', 0), ('price_unit', '>', 0)],
            '_compute_bo_value',
            75,
            "root.sale_queue"
        )

        self._process_by_domain(
            'sale.order.line',
            [
                '|', '|',('move_ids.state', '!=', 'done'),
                ('move_ids.location_dest_id.usage', '!=', 'customer'),
                ('move_ids.to_refund', '=', False),
            ],
            '_compute_last_date_delivered',
            75,
            "root.sale_queue"
        )
        self._process_by_domain(
            'sale.order.line',
            [
                ('invoice_lines', '!=', False),
            ],
            '_compute_last_bill_date',
            100,
            "root.sale_queue"
        )

        self._process_by_domain(
            'sale.order.line',
            [
                ('invoice_status', '=', 'invoiced')
            ],
            '_compute_invoice_status',
            200,
            "root.sale_queue",
            500
        )

        # --------------------
        # SALE.ORDER
        # --------------------

        self._process_by_domain(
            'sale.order',
            ['|',('substate_id.name', '!=', 'Complete'),('substate_id', '!=', False)],
            '_compute_current_estimate_ship_date',
            40,
            "root.sale_queue"
        )

        self._process_by_domain(
            'sale.order',
            [('order_line.uigd_value', '!=', 0)],
            '_compute_uigd_value',
            75,
            "root.sale_queue"
        )

        self._process_by_domain(
            'sale.order',
            [('order_line.bo_value', '!=', 0)],
            '_compute_bo_value',
            75,
            "root.sale_queue"
        )

        self._process_by_domain(
            'sale.order',
            [('order_line.last_date_delivered', '!=', False)],
            '_compute_last_date_delivered',
            75,
            "root.sale_queue"
        )

        self._process_by_domain(
            'sale.order',
            [('order_line.last_bill_date', '!=', False)],
            '_compute_last_bill_date',
            75,
            "root.sale_queue"
        )

        self._process_by_domain(
            'sale.order',
            [('substate_id.name', '!=', 'Complete'),
             ('invoice_ids', '!=', False),
                '|', ('state', '=', 'sale'),
                ('sale_payment_method_id.include_in_credit_limit', '=', True)],
            '_compute_uninvoiced_balance',
            20,
            "root.sale_queue",
            250
        )

        
        # stock.picking
        self._process_by_domain(
            'stock.picking',
            [('picking_type_id.code', '=', 'outgoing'),
            ('state', 'not in', ['cancel', 'done'])],
            '_compute_total_sales_price',
            30,
            "root.stock_queue"
        )
        self._process_by_domain(
            'stock.picking',
            [('picking_type_id.code', '=', 'outgoing'),
            ('state', 'not in', ['cancel', 'done'])],
            '_compute_main_error',
            15,
            "root.stock_queue"
        )
        self._process_by_domain(
            'stock.picking',
            [
                ('sale_id', '!=', False),
                ('picking_type_id.code', '=', 'outgoing'),
                ('state', 'not in', ['cancel', 'done'])
            ],
            '_compute_credit_hold',
            20,
            "root.stock_queue"
        )
        #mrp.production
        self._process_by_domain(
            'mrp.production',
            [
                ('sale_order_id', '!=', False),
                ('state', 'not in', ['cancel', 'done'])
            ],
            '_compute_credit_hold',
            20,
            "root.mrp_queue"
        )
        #account.move
        self._process_by_domain(
            'account.move',
            [
                '|',
                ('partner_id.country_id.intrastat', '=', True),
                ('move_type', 'in', ('out_invoice', 'out_refund')),
            ],
            '_compute_intrastat_country_id',
            100,
            "root.account_queue"
        )
        self._process_by_domain(
            'account.move',
            [],
            '_compute_sale_type_id',
            20,
            "root.account_queue"
        )
        self._process_by_domain(
            'account.move',
            [
                ('move_type', '=', 'in_invoice'),
                ('payment_state', '!=', 'paid'),
            ],
            '_compute_po_line_price_difference',
            25,
            "root.account_queue"
        )
        
        #✅ ACCOUNT.MOVE.LINE
        self._process_by_domain(
            'account.move.line',
            [
                ('purchase_line_id', '!=', False),
                ('product_id.detailed_type', 'in', ('product', 'consu')),
                ('move_id.payment_state', '!=', 'paid'),
            ],
            '_compute_po_line_price_difference',
            25,
            "root.account_queue"
        )




        