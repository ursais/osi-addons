# Import Odoo libs
from odoo import api, fields, models


class MrpProductionBatch(models.Model):
    """New Object for Batching Manufacturing Orders."""

    _name = "mrp.production.batch"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Manufacturing Batch"

    # COLUMNS #########

    name = fields.Char(string="Name", index=True)
    desc = fields.Text(string="Description")
    partner_ids = fields.Many2many(
        "res.partner",
        string="Customer",
        compute="_compute_partner_id",
        readonly=True,
        index=True,
    )
    tag_ids = fields.Many2many("mrp.production.batch.tag", string="Tags")
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
    date_scheduled = fields.Datetime(string="Scheduled Date")

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
        compute="_compute_show_lock",
    )
    is_locked = fields.Boolean(
        string="Is Locked",
        compute="_compute_show_lock",
    )
    is_queuing = fields.Boolean(
        string="Is Queuing",
        default=False,
    )
    earliest_start = fields.Datetime(
        string="Earliest start",
        compute="_compute_earliest_start",
    )
    is_date = fields.Boolean(
        string="Is Date",
        compute="_compute_check_date",
    )

    # Fields tracking the total and expected durations for the batch
    total_duration = fields.Float(
        "Real Duration",
        compute="_compute_total_duration",
    )
    total_duration_expected = fields.Float(
        "Expected Duration",
        compute="_compute_total_duration_expected",
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
    def _compute_check_date(self):
        # Check if the scheduled date differs from the earliest start date
        self.is_date = False
        for rec in self:
            if rec.date_scheduled and rec.earliest_start:
                scheduled_date = rec.date_scheduled.date()
                earliest_start = rec.earliest_start.date()
                rec.is_date = scheduled_date != earliest_start

    @api.depends("production_ids")
    def _compute_partner_id(self):
        # Compute the customer based on associated production records
        for record in self:
            record.partner_ids = False
            if record.production_ids:
                record.partner_ids = (
                    record.production_ids.procurement_group_id.mrp_production_ids.move_dest_ids.group_id.sale_id.partner_id.ids
                )

    @api.depends(
        "production_ids",
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
    def _compute_show_lock(self):
        # Determine if the lock button should be displayed based on work order states
        for record in self:
            record.show_lock = False
            record.is_locked = False
            if record.production_ids:
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

    @api.depends("production_ids")
    def _compute_total_duration(self):
        # Sum the total duration of all productions in the batch
        for record in self:
            record.total_duration = sum(
                production.duration for production in record.production_ids
            )

    @api.depends("production_ids")
    def _compute_total_duration_expected(self):
        # Sum the expected durations of all productions in the batch
        for record in self:
            record.total_duration_expected = sum(
                production.duration_expected for production in record.production_ids
            )

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
            return super().create(vals_list)

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

    # END #########
