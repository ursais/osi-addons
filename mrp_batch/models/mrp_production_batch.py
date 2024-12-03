# Import Odoo libs
import html

from odoo import api, fields, models


class MrpProductionBatch(models.Model):
    """New Object for Batching Manufacturing Orders."""

    _name = "mrp.production.batch"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Manufacturing Batch"

    # COLUMNS #########

    name = fields.Char(string="Name", index=True)
    sequence = fields.Integer()
    daily_sequence = fields.Integer(
        string="Daily Sequence",
        compute="_compute_daily_sequence",
        store=True,
    )
    notes = fields.Text(string="Notes")
    partner_ids = fields.Many2many(
        "res.partner",
        string="Customer(s)",
        compute="_compute_partner_ids",
        readonly=True,
        index=True,
    )
    product_ids = fields.Many2many(
        "product.product",
        string="Product(s)",
        compute="_compute_product_ids",
        readonly=True,
        index=True,
    )
    product_tmpl_ids = fields.Many2many(
        "product.template",
        string="Product Template(s)",
        compute="_compute_product_tmpl_ids",
        readonly=True,
        index=True,
    )
    exception_ids = fields.Many2many(
        "exception.rule",
        compute="_compute_exception_ids",
        string="Exceptions",
        store=True,
        copy=False,
    )
    exceptions_summary = fields.Html(
        compute="_compute_exceptions_summary",
        store=True,
    )
    tag_ids = fields.Many2many("mrp.production.batch.tag", string="Tags")
    sale_tag_ids = fields.Many2many("crm.tag", compute="_compute_sale_tags")
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("progress", "In Progress"),
            ("confirm", "Confirmed"),
            ("done", "Done"),
            ("cancel", "Cancel"),
            ("hold", "Hold"),
        ],
        default="draft",
        string="Status",
    )
    production_ids = fields.One2many(
        "mrp.production",
        "mrp_batch_id",
        string="Manufacturing productions",
    )
    responsible_id = fields.Many2one(
        "res.users",
        string="Owner",
        required=True,
    )
    date_start = fields.Datetime(string="Scheduled Date")
    date_finished = fields.Datetime(
        string="Date Finished",
        compute="_compute_date_finished",
        store=True,
    )
    workcenter_tag_id = fields.Many2one(
        "mrp.workcenter.tag",
        string="Workcenter Tag",
    )

    # Booleans representing various states for UI controls
    is_confirm_check = fields.Boolean(
        string="show_state",
        compute="_compute_mrp_production_confirm",
    )
    is_reserved = fields.Boolean(
        string="Reserved",
        compute="_compute_reserve_and_unreserve_visible",
    )
    is_reserved_batch = fields.Boolean(
        string="Reserved Batch",
        compute="_compute_mrp_production_reserve_batch",
    )
    is_unreserved = fields.Boolean(
        string="Unreserved",
        compute="_compute_reserve_and_unreserve_visible",
    )
    is_cancel = fields.Boolean(
        string="Cancel",
        compute="_compute_mrp_production_cancel",
    )
    is_cancel_id = fields.Boolean(
        string="Is All Canceled",
        compute="_compute_mrp_production_cancel",
    )
    is_move_raw_ids = fields.Boolean(
        string="Is Open Moves",
        compute="_compute_mrp_production_done",
    )
    is_produce_all = fields.Boolean(
        string="Is All Produced",
        compute="_compute_mrp_production_done",
    )
    is_workorder_ids = fields.Boolean(
        string="Has Work Orders",
        compute="_compute_is_planned",
    )
    is_planned = fields.Boolean(
        string="Planned",
        compute="_compute_is_planned",
    )
    is_plan = fields.Boolean(
        string="Is Plan",
        compute="_compute_is_planned",
    )
    show_lock = fields.Boolean(
        string="Show Lock Button",
        compute="_compute_lock",
    )
    is_locked = fields.Boolean(
        string="Is Locked",
        compute="_compute_lock",
    )
    is_queuing = fields.Boolean(
        string="Is Queuing",
        default=False,
    )
    earliest_start = fields.Datetime(
        string="Earliest start",
        compute="_compute_earliest_start",
        store=True,
    )
    is_delayed = fields.Boolean(
        string="Is Delayed",
        compute="_compute_is_delayed",
    )
    date_deadline = fields.Datetime(
        string="Deadline",
        compute="_compute_date_deadline",
        store=True,
    )

    # Fields tracking the total and expected durations for the batch
    total_duration_expected = fields.Float(
        string="Expected Duration",
        compute="_compute_total_duration_expected",
        store=True,
    )
    total_build_duration_expected = fields.Float(
        string="Expected Build Duration",
        compute="_compute_build_test_durations_expected",
        store=True,
    )
    total_test_duration_expected = fields.Float(
        string="Expected Test Duration",
        compute="_compute_build_test_durations_expected",
        store=True,
    )
    total_duration = fields.Float(
        string="Real Duration",
        compute="_compute_total_duration",
        store=True,
    )
    total_build_duration = fields.Float(
        string="Real Build Duration",
        compute="_compute_build_test_durations",
        store=True,
    )
    total_test_duration = fields.Float(
        string="Real Test Duration",
        compute="_compute_build_test_durations",
        store=True,
    )

    # Misc compute fields
    qty_produced = fields.Float(
        string="Qty Produced",
        compute="_compute_qty",
        store=True,
    )
    qty_producing = fields.Float(
        string="Qty to Produce",
        compute="_compute_qty",
        store=True,
    )
    qty_remaining = fields.Float(
        string="Qty Remaining",
        compute="_compute_qty",
        store=True,
    )
    percent_complete = fields.Float(
        string="% Complete",
        compute="_compute_qty",
        store=True,
    )
    total_revenue = fields.Monetary(
        string="Total Revenue",
        compute="_compute_revenue",
        store=True,
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        required=True,
        default=lambda self: self.env.company.currency_id,
    )

    # Count of associated sale orders
    sale_order_count = fields.Integer(
        "Total Sale Order Count",
        compute="_compute_sale_order_count",
    )

    # END #########
    # METHODS #####

    # Action and Button Methods
    def action_assign(self):
        # Assign raw materials to production orders that are not completed or canceled
        for record in self:
            record.is_queuing = True
            for mo in record.production_ids.filtered(
                lambda x: x.state not in ("draft", "done", "cancel")
            ):
                mo.with_delay().action_assign()

    def action_confirm(self):
        # Confirm the batch and associated manufacturing orders
        for record in self:
            record.is_queuing = True
            record.state = "confirm"
            for mo in record.production_ids.filtered(lambda x: x.state == "draft"):
                mo.with_delay().action_confirm()

    def button_plan(self):
        # Plan the batch and its production orders
        for record in self:
            record.is_queuing = True
            if record.state == "draft":
                record.state = "confirm"
            for mrp_production in record.production_ids:
                mrp_production.with_delay().button_plan()

    def button_unplan(self):
        # Unplan all manufacturing orders in the batch
        for record in self:
            record.is_queuing = True
            for mrp_production in record.production_ids:
                mrp_production.with_delay().button_unplan()

    def action_unreserve(self):
        # Unreserve raw materials for production orders
        for record in self:
            record.is_queuing = True
            for mo in record.production_ids.filtered(
                lambda x: x.state not in ("draft", "done", "cancel")
            ):
                mo.with_delay().do_unreserve()

    def action_done(self):
        # Complete the batch and mark productions as done
        for record in self:
            record.is_queuing = True
            record.state = "done"
            for mo in record.production_ids.filtered(
                lambda x: x.state not in ("done", "cancel")
            ):
                mo.with_delay().button_mark_done()

    def action_cancel(self):
        # Cancel the batch and related manufacturing orders
        for record in self:
            record.is_queuing = True
            record.state = "cancel"
            for mrp_production in record.production_ids:
                mrp_production.with_delay().action_cancel()

    def action_lock_and_unlock(self):
        # Lock all Manufacturing Orders in the batch.
        for record in self:
            for mo in record.production_ids:
                mo.action_toggle_is_locked()

    def action_open_add_to_batch_wizard(self):
        # Return an action that opens the "Add to Batch" wizard in a modal form
        return {
            "name": "Add to Batch",
            "type": "ir.actions.act_window",
            "res_model": "add.manufacturing.order.wizard",
            "view_mode": "form",
            "target": "new",  # Opens as a modal window
        }

    # Compute Methods
    @api.depends(
        "production_ids",
        "production_ids.mrp_batch_id",
    )
    def _compute_batch_state(self):
        """Compute the state of the batch based on the states of associated MOs,
        ignoring 'cancel' states unless all are 'cancel'."""
        for batch in self:
            if batch.state == "hold":
                continue  # Do not update if batch is on hold

            # Exclude 'cancel' states from the evaluation
            non_cancel_states = batch.production_ids.filtered(
                lambda mo: mo.state != "cancel"
            ).mapped("state")

            if not non_cancel_states and batch.production_ids:  # All are 'cancel'
                batch.state = "cancel"
            elif all(state == "draft" for state in non_cancel_states):
                batch.state = "draft"
            elif all(state == "confirmed" for state in non_cancel_states):
                batch.state = "confirm"
            elif any(state in ("progress", "to_close") for state in non_cancel_states):
                batch.state = "progress"
            elif all(state == "done" for state in non_cancel_states):
                batch.state = "done"

    @api.depends("production_ids.sale_order_id.tag_ids")
    def _compute_sale_tags(self):
        for rec in self:
            # Collect all sale_tag_ids from the lines
            all_tags = rec.production_ids.sale_order_id.mapped("tag_ids")

            # Update the main object's sale_tag_ids
            rec.sale_tag_ids = [(6, 0, all_tags.ids)]

    def _compute_is_delayed(self):
        # Check if the scheduled date falls after deadline
        self.is_delayed = False
        for rec in self:
            if rec.date_start and rec.date_deadline:
                scheduled_date = rec.date_start.date()
                deadline_date = rec.date_deadline.date()
                rec.is_delayed = scheduled_date >= deadline_date

    @api.depends("production_ids")
    def _compute_partner_ids(self):
        # Compute the customer(s) based on associated production records
        for record in self:
            record.partner_ids = False
            if record.production_ids:
                record.partner_ids = (
                    record.production_ids.procurement_group_id.mrp_production_ids.move_dest_ids.group_id.sale_id.partner_id.ids
                )

    @api.depends("production_ids")
    def _compute_product_ids(self):
        # Compute the product(s) based on associated production records
        for record in self:
            record.product_ids = False
            if record.production_ids:
                record.product_ids = record.production_ids.product_id.ids

    @api.depends("production_ids")
    def _compute_product_tmpl_ids(self):
        # Compute the product template(s) based on associated production records
        for record in self:
            record.product_tmpl_ids = False
            if record.production_ids:
                record.product_tmpl_ids = record.production_ids.product_tmpl_id.ids

    @api.depends(
        "production_ids",
        "production_ids.exception_ids",
        "production_ids.ignore_exception",
    )
    def _compute_exception_ids(self):
        for record in self:
            # Filter out production records where ignore_exception is True
            valid_productions = record.production_ids.filtered(
                lambda p: not p.ignore_exception
            )

            # Collect exception_ids from the remaining productions
            record.exception_ids = (
                valid_productions.mapped("exception_ids").ids
                if valid_productions
                else False
            )

    @api.depends("exception_ids")
    def _compute_exceptions_summary(self):
        for rec in self:
            if rec.exception_ids and not rec.ignore_exception:
                rec.exceptions_summary = "<ul>%s</ul>" % "".join(
                    [
                        f"<li>{html.escape(e.name)}: <i>{html.escape(e.description or '')}</i> <b>"
                        + _(
                            f"{'(Blocking exception)' if e.is_blocking else ''}</b></li>"
                        )
                        for e in rec.exception_ids
                    ]
                )
            else:
                rec.exceptions_summary = False

    @api.depends(
        "production_ids",
        "production_ids.date_start",
        "production_ids.state",
    )
    def _compute_earliest_start(self):
        # Determine the earliest start date among all productions in the batch
        for record in self:
            record.earliest_start = False
            if record.production_ids:
                start_date = min(
                    production.date_start for production in record.production_ids
                )
                record.earliest_start = start_date

    @api.depends(
        "production_ids",
        "production_ids.date_finished",
        "production_ids.state",
    )
    def _compute_date_finished(self):
        # Determine the finished date among all productions in the batch
        for record in self:
            record.date_finished = False
            if record.production_ids:
                start_date = min(
                    production.date_finished for production in record.production_ids
                )
                record.date_finished = start_date

    @api.depends(
        "production_ids",
        "production_ids.date_deadline",
        "production_ids.state",
    )
    def _compute_deadline_date(self):
        # Determine the deadline date among all productions in the batch
        for record in self:
            record.date_deadline = False
            if record.production_ids:
                # Filter out productions without a date_deadline
                deadlines = [
                    production.date_deadline
                    for production in record.production_ids
                    if production.date_deadline
                ]
                # Compute the maximum deadline if there are any valid dates
                record.date_deadline = max(deadlines) if deadlines else False

    @api.depends(
        "production_ids.workorder_ids.operation_id.type",
        "production_ids.duration_expected",
    )
    def _compute_build_test_durations_expected(self):
        # Determine the build/test expected durations all productions in the batch
        for record in self:
            total_build = 0.0
            total_test = 0.0

            # Iterate through all related work orders
            for production in record.production_ids:
                for workorder in production.workorder_ids:
                    if workorder.operation_type == "build":
                        total_build += workorder.duration_expected
                    elif workorder.operation_type == "test":
                        total_test += workorder.duration_expected

            record.total_build_duration_expected = total_build
            record.total_test_duration_expected = total_test

    @api.depends(
        "production_ids.workorder_ids.operation_id.type",
        "production_ids.duration",
    )
    def _compute_build_test_durations(self):
        # Determine the build/test real durations all productions in the batch
        for record in self:
            total_build = 0.0
            total_test = 0.0

            # Iterate through all related work orders
            for production in record.production_ids:
                for workorder in production.workorder_ids:
                    if workorder.operation_type == "build":
                        total_build += workorder.duration
                    elif workorder.operation_type == "test":
                        total_test += workorder.duration

            record.total_build_duration = total_build
            record.total_test_duration = total_test

    @api.depends(
        "production_ids.procurement_group_id.mrp_production_ids.move_dest_ids.sale_line_id.price_unit",
        "production_ids.product_qty",
    )
    def _compute_revenue(self):
        for record in self:
            total = 0.0
            for mo in record.production_ids:
                sale_line = (
                    mo.procurement_group_id.mrp_production_ids.move_dest_ids.sale_line_id
                )
                if sale_line:
                    total += sale_line.price_unit * mo.product_qty
            record.total_revenue = total

    @api.depends("production_ids.state")
    def _compute_mrp_production_cancel(self):
        # Determine if all productions are canceled or in done state
        for record in self:
            record.is_cancel = False
            record.is_cancel_id = False
            if record.production_ids:
                record.is_cancel_id = all(
                    production.id for production in record.production_ids
                )
                record.is_cancel = all(
                    production.state in ("done", "cancel")
                    for production in record.production_ids
                )

    @api.depends(
        "production_ids.state",
        "production_ids.is_planned",
        "production_ids.workorder_ids",
    )
    def _compute_is_planned(self):
        # Compute planned status and check for associated work orders
        for record in self:
            record.is_planned = False
            record.is_plan = False
            record.is_workorder_ids = False
            if record.production_ids:
                record.is_workorder_ids = all(
                    production.workorder_ids for production in record.production_ids
                )
                record.is_plan = all(
                    production.state not in ("confirmed", "progress", "to_close")
                    for production in record.production_ids
                )
                record.is_planned = all(
                    production.is_planned for production in record.production_ids
                )

    @api.depends("production_ids.state")
    def _compute_mrp_production_confirm(self):
        # Check if all production orders are confirmed or in progress
        for record in self:
            record.is_confirm_check = False
            record.is_confirm_check = all(
                production.state != "draft" for production in record.production_ids
            )

    @api.depends("production_ids.state")
    def _compute_mrp_production_reserve_batch(self):
        # Check if all productions are in a state where they can be reserved
        for record in self:
            record.is_reserved_batch = False
            if record.production_ids:
                record.is_reserved_batch = all(
                    production.state in ("draft", "done", "cancel")
                    for production in record.production_ids
                )

    @api.depends(
        "production_ids.move_raw_ids",
        "production_ids.state",
        "production_ids.move_raw_ids.product_uom_qty",
    )
    def _compute_reserve_and_unreserve_visible(self):
        # Determine the visibility of reserve/unreserve actions based on productions
        for record in self:
            record.is_reserved = False
            record.is_unreserved = False
            if record.production_ids:
                record.is_unreserved = all(
                    production.unreserve_visible for production in record.production_ids
                )
                record.is_reserved = all(
                    production.reserve_visible for production in record.production_ids
                )

    @api.depends("production_ids.move_raw_ids")
    def _compute_mrp_production_done(self):
        # Check if all move lines are open or if all productions are completed
        for record in self:
            record.is_move_raw_ids = False
            record.is_produce_all = False
            if record.production_ids:
                record.is_move_raw_ids = all(
                    move.state not in ("done", "cancel")
                    for production in record.production_ids
                    for move in production.move_raw_ids
                )
                record.is_produce_all = all(
                    production.qty_producing for production in record.production_ids
                )

    @api.depends("production_ids.workorder_ids.state")
    def _compute_lock(self):
        # Determine if the lock button should be displayed based on work order states
        for record in self:
            record.show_lock = False
            record.is_locked = False
            if record.production_ids and record.state != "cancel":
                record.show_lock = all(
                    wo.state in ("done", "cancel")
                    for production in record.production_ids
                    for wo in production.workorder_ids
                )
                record.is_locked = any(
                    wo.state in ("done", "cancel")
                    for production in record.production_ids
                    for wo in production.workorder_ids
                )

    @api.depends("production_ids.duration")
    def _compute_total_duration(self):
        # Sum the total duration of all productions in the batch
        for record in self:
            record.total_duration = sum(
                production.duration for production in record.production_ids
            )

    @api.depends("production_ids.duration_expected")
    def _compute_total_duration_expected(self):
        # Sum the expected durations of all productions in the batch
        for record in self:
            record.total_duration_expected = sum(
                production.duration_expected for production in record.production_ids
            )

    @api.depends(
        "production_ids.state",
        "production_ids.qty_producing",
        "production_ids.qty_produced",
    )
    def _compute_qty(self):
        # Compute the total count of sales orders associated with productions
        for record in self:
            # Sum product_qty for all lines where state is not 'cancelled'
            record.qty_producing = sum(mo.product_qty for mo in record.production_ids)
            record.qty_produced = sum(mo.qty_produced for mo in record.production_ids)
            record.qty_remaining = record.qty_producing - record.qty_produced
            if record.qty_producing > 0.0:
                record.percent_complete = record.qty_produced / record.qty_producing
            else:
                record.percent_complete = 0.0

    # Smart Button Methods
    @api.depends("production_ids.move_raw_ids")
    def _compute_sale_order_count(self):
        # Compute the total count of sales orders associated with productions
        for record in self:
            record.sale_order_count

    def action_view_sale(self):
        # Ensure the method is called on a single record
        self.ensure_one()

        # Gather sale order IDs related to the productions in this batch
        # Traverse through procurement groups, MRP productions, destination moves,
        # and sale orders to find linked sales
        sale_ids = (
            self.production_ids.mapped("procurement_group_id")
            .mapped("mrp_production_ids")
            .mapped("move_dest_ids")
            .mapped("group_id")
            .mapped("sale_id")
            .ids
        )

        # Define the action to open sale orders in the appropriate view
        action = {
            "name": "Sale Orders",
            "res_model": "sale.order",
            "type": "ir.actions.act_window",
        }

        # If there is a single sale order, open it in form view
        if len(sale_ids) == 1:
            action.update(
                {
                    "view_mode": "form",
                    "res_id": sale_ids[0],
                }
            )
        else:
            # If there are multiple sale orders, open them in a list (tree) view
            action.update(
                {
                    "domain": [("id", "in", sale_ids)],
                    "view_mode": "tree,form",
                }
            )

        return action

    # Other Internal Methods
    @api.model_create_multi
    def create(self, vals_list):
        # Override create to assign a sequence number to the new batch record
        for vals in vals_list:
            vals["name"] = (
                self.env["ir.sequence"].next_by_code("mrp.production.batch") or "New"
            )
        res = super().create(vals_list)
        res._compute_daily_sequence()
        return res

    def write(self, vals):
        res = super().write(vals)

        for batch in self:
            if "date_start" in vals and batch.state in ("draft", "confirm"):
                for mo in batch.production_ids:
                    # If the job is related to a manufacturing order, check its batch
                    if mo.state in ("draft", "confirmed"):
                        mo.date_start = batch.date_start
                batch._compute_daily_sequence()

        return res

    def _check_and_update_queuing(self):
        # For each batch, check the status of any related queue jobs
        for batch in self:
            # Find all queue jobs related to the MRP productions in this batch
            # The search filters jobs to only include those with
            # model name 'mrp.production' and further filters to ensure jobs reference
            # productions in this batch
            jobs = (
                self.env["queue.job"]
                .search(
                    [
                        ("model_name", "=", "mrp.production"),
                    ]
                )
                .filtered(
                    lambda job: set(batch.production_ids.ids) & set(job.records.ids)
                )
            )

            # If all jobs related to the batch are in 'done', 'failed',
            # or 'cancelled' states, mark the batch as no longer in a queuing state
            if all(job.state in ["done", "failed", "cancelled"] for job in jobs):
                batch.is_queuing = False

    @api.depends("date_start")
    def _compute_daily_sequence(self):
        for record in self:
            if record.date_start:
                # Get the start and end of the day
                start_of_day = fields.Datetime.context_timestamp(
                    record, record.date_start
                ).replace(hour=0, minute=0, second=0, microsecond=0)
                end_of_day = start_of_day.replace(hour=23, minute=59, second=59)

                # Fetch all records for the same day
                same_day_records = self.search(
                    [
                        (
                            "date_start",
                            ">=",
                            fields.Datetime.to_string(start_of_day),
                        ),
                        ("date_start", "<=", fields.Datetime.to_string(end_of_day)),
                    ],
                    order="date_start asc, id asc",
                )  # Sort by date_start (and id for stability)

                # Assign daily_sequence
                for idx, rec in enumerate(same_day_records, start=1):
                    rec.daily_sequence = idx

    # END #########
