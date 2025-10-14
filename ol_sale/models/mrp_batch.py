# Import Odoo libs
from odoo import _,api,fields, models
from datetime import timedelta,datetime



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
    date_start = fields.Datetime(string="Scheduled Date", compute="_compute_date_start",store=True,readonly=True,)
    date_change_exception = fields.Boolean(string="Customer Request Date Change Proposed", default=False)
    customer_request_date_proposed = fields.Date(string="Proposed Customer Request Date")


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
            # 
            rush_lead_time = (
                self.env["ir.config_parameter"]
                .sudo()
                .get_param("ol_sale.rush_lead_time")
            )
            valid_productions = record.production_ids.filtered(
                lambda mo: mo.state not in ("draft", "cancel", "done", "to_close")
            )
            if not valid_productions:
                continue
            sale_order = record.production_ids.mapped("sale_order_id")
            # Fetch all raw moves and ensure calculations are up to date
            all_raw_moves = valid_productions.move_raw_ids
            all_raw_moves._fields["forecast_availability"].compute_value(all_raw_moves)
            if not all_raw_moves:
                continue
            forecast_expected_date = all_raw_moves.filtered("forecast_expected_date").mapped("forecast_expected_date")
            if not forecast_expected_date:
                continue
            forecast_expected_date = max(forecast_expected_date)
            total_lead_time = int(record.company_id.manufacturing_lead) + int(default_produce_delay)
            if not record.rush_order:
                if forecast_expected_date:
                    estimated_ship_date = forecast_expected_date + timedelta(days=total_lead_time)
                    weekday = estimated_ship_date.weekday()
                    # If Saturday (5), add 2 days → Monday
                    # If Sunday (6), add 1 day → Monday
                    if weekday == 5:
                        estimated_ship_date += timedelta(days=2)
                    elif weekday == 6:
                        estimated_ship_date += timedelta(days=1)
                    record.estimated_ship_date = estimated_ship_date
                if record.components_availability_state == "available" and record.ops_build_date:
                    estimated_ship_date = record.ops_build_date + timedelta(days=total_lead_time)
                    weekday = estimated_ship_date.weekday()
                    # If Saturday (5), add 2 days → Monday
                    # If Sunday (6), add 1 day → Monday
                    if weekday == 5:
                        estimated_ship_date += timedelta(days=2)
                    elif weekday == 6:
                        estimated_ship_date += timedelta(days=1)
                    record.estimated_ship_date = estimated_ship_date
            if forecast_expected_date and record.rush_order:
                estimated_ship_date = forecast_expected_date + timedelta(days=int(rush_lead_time))
                weekday = estimated_ship_date.weekday()
                # If Saturday (5), add 2 days → Monday
                # If Sunday (6), add 1 day → Monday
                if weekday == 5:
                    estimated_ship_date += timedelta(days=2)
                elif weekday == 6:
                    estimated_ship_date += timedelta(days=1)
                record.estimated_ship_date = estimated_ship_date


    @api.depends("sale_order_ids","production_ids")
    def _compute_date_start(self):
        for record  in self:
            for production in record.production_ids.filtered("sale_order_id"):
                record.date_start = production.sale_order_id.mapped("commitment_date")[0]


    @api.depends("date_start","production_ids")
    def _compute_allocation_date(self):
        for batch in self:
            for production in batch.production_ids:
                allocation_date = False
                if batch.date_start and production.picking_type_id.reservation_method == 'by_date':
                    allocation_date =  batch.date_start - timedelta(days=production.picking_type_id.reservation_days_before)
                batch.allocation_date = allocation_date

    # END #########

    # Object Button Methods ##############

    def action_approve_date_change(self):
        if self.customer_request_date_proposed:
            self.message_post(body=_("Customer Request Date Change Approved Updated to %s.") % (self.customer_request_date_proposed))
            self.date_start = self.customer_request_date_proposed
            self.customer_request_date_proposed = False
            self.date_change_exception = False

    def button_reject(self):
        for batch in self:
            if not batch.customer_request_date_proposed:
                continue

            for production in batch.production_ids:
                sale_order = production.sale_order_id
                if not sale_order:
                    continue

                partner = sale_order.user_id.partner_id
                # Revert Sale Order commitment_date to original batch start
                old_date = batch.customer_request_date_proposed
                new_date = batch.date_start.date()
                sale_order.commitment_date = new_date

                partner_url = _("Dear ") + partner._get_html_link()
                body = _(f"\nCustomer Request Date Change was Rejected The date was changed back from {old_date} to the original date {new_date}. ")

                # Post message to Sale Order chatter
                sale_order.message_post(
                    author_id=batch.env.user.partner_id.id,
                    body=partner_url+body,
                    subtype_xmlid='mail.mt_comment',
                )

            # Reset batch fields
            batch.customer_request_date_proposed = False
            batch.date_change_exception = False
            batch.message_post(body=_("Customer Request Date Change Rejected."))

        # END #########





