# Import Odoo libs
from odoo import api,fields, models
from datetime import timedelta


class MrpProductionBatch(models.Model):
    """Inherit Object for Batching Manufacturing Orders."""

    _inherit = "mrp.production.batch"

    # COLUMNS #####
    ops_build_date = fields.Date(
        string="Build Date",
        copy=False,
    )

    ops_sequence = fields.Integer(string="Ops Sequence",copy=False)
    allocation_date = fields.Date(
        string="Allocation Date",
        compute="_compute_allocation_date",
        store=True,
        copy=False,
    )
    estimated_ship_date = fields.Date(
        string="Estimated Ship Date",
        compute="_compute_estimated_ship_date",
        store=True,
        copy=False,
    )
    sales_person_id = fields.Many2one("res.users",string="Sale Person",copy=False,compute="_compute_sales_person_account_manager",store=True)
    account_manager_id = fields.Many2one("res.users",string="Account Manager",copy=False,compute="_compute_sales_person_account_manager",store=True)

    date_confirm = fields.Datetime(
        string="Confirmation Date",
        readonly=True,
        copy=False,
        compute="_compute_date_confirm",
        store=True
    )
    date_start = fields.Datetime(string="Scheduled Date", compute="_compute_date_start",store=True)

    # END #########

    # Other Internal Methods

    @api.depends("production_ids")
    def _compute_sales_person_account_manager(self):
        # Compute the Sale Order(s) based on associated production records
        for rec in self:
            rec.sales_person_id = False
            rec.account_manager_id = False
            if rec.production_ids and rec.production_ids.sale_order_id:
                rec.sales_person_id = rec.production_ids.sale_order_id.user_id.id
                rec.account_manager_id = rec.production_ids.sale_order_id.account_manager_id.id

    @api.depends("state")
    def _compute_date_confirm(self):
        for rec in self:
            date_confirm = rec.date_confirm or False
            if rec.state == 'confirm' and not rec.date_confirm:
                date_confirm = fields.Datetime.now()
            rec.date_confirm = date_confirm

    @api.depends("components_availability","components_availability_state")
    def _compute_estimated_ship_date(self):
        for record in self:
            record.estimated_ship_date = False
            default_produce_delay = (
                self.env["ir.config_parameter"]
                .sudo()
                .get_param("mrp_batch.default_produce_delay")
            ) 
            use_manufacturing_lead = (
                self.env["ir.config_parameter"]
                .sudo()
                .get_param("mrp.use_manufacturing_lead")
            )
            valid_productions = record.production_ids.filtered(
                lambda mo: mo.state not in ("draft", "cancel", "done", "to_close")
            )
            if not valid_productions:
                continue

            # Fetch all raw moves and ensure calculations are up to date
            all_raw_moves = valid_productions.move_raw_ids
            all_raw_moves._fields["forecast_availability"].compute_value(all_raw_moves)
            forecast_expected_date = all_raw_moves.filtered("forecast_expected_date").mapped("forecast_expected_date")
            total_lead_time = int(self.company_id.manufacturing_lead) + int(default_produce_delay)
            if forecast_expected_date:
                record.estimated_ship_date = max(forecast_expected_date) + timedelta(days=total_lead_time)
            if record.components_availability_state == "available" and record.ops_build_date:
                record.estimated_ship_date = record.ops_build_date + timedelta(days=total_lead_time)

    @api.depends("sale_order_ids","production_ids")
    def _compute_date_start(self):
        for record  in self:
            for production in record.production_ids:
                

    @api.depends("production_ids")
    def _compute_allocation_date(self):
        for batch in self:
            for production in batch.production_ids:
                allocation_date = False
                print("##########>>",production, production.picking_type_id.reservation_days_before)
                if batch.date_start and production.picking_type_id.reservation_method == 'by_date':
                    pass
                    
                    # allocation_date = production.scheduled_date - 

                batch.allocation_date = allocation_date



