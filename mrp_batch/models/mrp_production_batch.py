# Import Odoo libs
import html
import logging
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, format_datetime
from odoo.tools.misc import format_date

_logger = logging.getLogger(__name__)


# Constants for operation types
OPERATION_TYPE_BUILD = "build"
OPERATION_TYPE_TEST = "test"
OPERATION_TYPE_OTHER = "other"

# Constants for batch tag names
TAG_NAME_DELAYED = "Delayed"
TAG_NAME_PLANNED = "Planned"

# Constants for batch states
BATCH_STATE_DRAFT = "draft"
BATCH_STATE_CONFIRM = "confirm"
BATCH_STATE_PROGRESS = "progress"
BATCH_STATE_DONE = "done"
BATCH_STATE_CANCEL = "cancel"
BATCH_STATE_HOLD = "hold"

# Constants for MO states
MO_STATE_DRAFT = "draft"
MO_STATE_CONFIRMED = "confirmed"
MO_STATE_PROGRESS = "progress"
MO_STATE_TO_CLOSE = "to_close"
MO_STATE_DONE = "done"
MO_STATE_CANCEL = "cancel"

class MrpProductionBatch(models.Model):
    """New Object for Batching Manufacturing Orders."""

    _name = "mrp.production.batch"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "mrp_batch_schedule_id, date_start, workcenter_tag_id"
    _description = "Manufacturing Batch"

    # COLUMNS #########

    name = fields.Char(string="Name", index=True)
    sequence = fields.Integer()
    notes = fields.Text(string="Notes")
    partner_ids = fields.Many2many(
        "res.partner",
        string="Customer(s)",
        compute="_compute_partner_ids",
        readonly=True,
        index=True,
        store=True,
    )
    product_ids = fields.Many2many(
        "product.product",
        string="Product(s)",
        compute="_compute_product_ids",
        readonly=True,
        index=True,
        store=True,
    )
    product_tmpl_ids = fields.Many2many(
        "product.template",
        string="Product Template(s)",
        compute="_compute_product_tmpl_ids",
        readonly=True,
        index=True,
        store=True,
    )
    exception_ids = fields.Many2many(
        "exception.rule",
        compute="_compute_exceptions",
        string="Exceptions",
        store=True,
        copy=False,
    )
    exceptions_summary = fields.Html(
        compute="_compute_exceptions",
        store=True,
        copy=False,
    )
    tag_ids = fields.Many2many("mrp.production.batch.tag", string="Tags")
    sale_order_ids = fields.Many2many(
        "sale.order",
        string="Sale Order(s)",
        compute="_compute_sale_order_ids",
        readonly=True,
        index=True,
        store=True,
    )
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
    date_end = fields.Datetime(
        string="Date End",
        compute="_compute_date_end",
        store=True,
    )
    date_finished = fields.Datetime(
        string="Date Finished",
        compute="_compute_date_finished",
        store=True,
    )
    workcenter_tag_id = fields.Many2one(
        "mrp.workcenter.tag",
        string="Workcenter Tag",
    )
    is_outdated_bom = fields.Boolean(
        string="Outdated BoM",
        compute="_compute_outaged_bom",
        help="The BoM has been updated since creation of the MO",
    )
    mrp_batch_schedule_id = fields.Many2one(
        "mrp.production.batch.schedule",
        string="Day",
        help="The schedule is used to group batch's by day.",
    )

    # Booleans representing various states for UI controls
    is_confirmed = fields.Boolean(
        string="Confirmed",
        compute="_compute_mrp_production_confirm",
    )
    reserve_visible = fields.Boolean(
        string="Reserved",
        compute="_compute_reserve_and_unreserve_visible",
    )
    unreserve_visible = fields.Boolean(
        string="Unreserved",
        compute="_compute_reserve_and_unreserve_visible",
    )
    is_cancel = fields.Boolean(
        string="Cancel",
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
    is_planned = fields.Boolean(
        string="Planned",
        compute="_compute_is_planned",
        store=True,
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
        store=True,
    )
    date_deadline = fields.Datetime(
        string="Deadline",
        compute="_compute_date_deadline",
        store=True,
    )
    components_availability = fields.Char(
        string="Component Status",
        compute="_compute_components_availability",
        store=True,
        help="Latest component availability status for this MO. If green, then the MO's readiness status is ready, as per BOM configuration.",
    )
    components_availability_state = fields.Selection(
        [
            ("available", "Available"),
            ("expected", "Expected"),
            ("late", "Late"),
            ("unavailable", "Not Available"),
        ],
        compute="_compute_components_availability",
        store=True,
        search="_search_components_availability_state",
    )
    reservation_state = fields.Selection(
        [
            ("confirmed", "Waiting"),
            ("assigned", "Ready"),
            ("waiting", "Waiting Another Operation"),
        ],
        string="MO Readiness",
        compute="_compute_reservation_state",
        copy=False,
        index=True,
        readonly=True,
        store=True,
        tracking=True,
        help="Manufacturing readiness for this MO, as per bill of material configuration:\n\
            * Ready: The material is available to start the production.\n\
            * Waiting: The material is not available to start the production.\n",
    )
    components_availability_details = fields.Text(
        string="Components Availability Details",
        compute="_compute_components_availability_details",
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
        compute="_compute_build_test_other_durations_expected",
        store=True,
    )
    total_test_duration_expected = fields.Float(
        string="Expected Test Duration",
        compute="_compute_build_test_other_durations_expected",
        store=True,
    )
    total_other_duration_expected = fields.Float(
        string="Expected Other Duration",
        compute="_compute_build_test_other_durations_expected",
        store=True,
    )
    total_duration = fields.Float(
        string="Real Duration",
        compute="_compute_total_duration",
        store=True,
    )
    total_build_duration = fields.Float(
        string="Real Build Duration",
        compute="_compute_build_test_other_durations",
        store=True,
    )
    total_test_duration = fields.Float(
        string="Real Test Duration",
        compute="_compute_build_test_other_durations",
        store=True,
    )
    total_other_duration = fields.Float(
        string="Real Other Duration",
        compute="_compute_build_test_other_durations",
        store=True,
    )

    # Fields tracking the avg per unit durations for the batch
    avg_duration_expected = fields.Float(
        string="Expected Unit Duration",
        compute="_compute_avg_unit_duration_expected",
        store=True,
    )
    avg_build_duration_expected = fields.Float(
        string="Expected Unit Build Duration",
        compute="_compute_build_test_unit_other_durations_expected",
        store=True,
    )
    avg_test_duration_expected = fields.Float(
        string="Expected Unit Test Duration",
        compute="_compute_build_test_unit_other_durations_expected",
        store=True,
    )
    avg_other_duration_expected = fields.Float(
        string="Expected Unit Other Duration",
        compute="_compute_build_test_unit_other_durations_expected",
        store=True,
    )
    avg_duration = fields.Float(
        string="Unit Duration",
        compute="_compute_avg_unit_duration",
        store=True,
    )
    avg_build_duration = fields.Float(
        string="Unit Build Duration",
        compute="_compute_build_test_unit_other_durations",
        store=True,
    )
    avg_test_duration = fields.Float(
        string="Unit Test Duration",
        compute="_compute_build_test_unit_other_durations",
        store=True,
    )
    avg_other_duration = fields.Float(
        string="Unit Other Duration",
        compute="_compute_build_test_unit_other_durations",
        store=True,
    )

    # Fields tracking the remaining durations for the batch
    remaining_duration = fields.Float(
        string="Remaining Duration",
        compute="_compute_remaining_duration",
        store=True,
    )
    remaining_build_duration = fields.Float(
        string="Remaining Build Duration",
        compute="_compute_remaining_build_duration",
        store=True,
    )
    remaining_test_duration = fields.Float(
        string="Remaining Test Duration",
        compute="_compute_remaining_test_duration",
        store=True,
    )
    remaining_other_duration = fields.Float(
        string="Remaining Other Duration",
        compute="_compute_remaining_other_duration",
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
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
    )
    picking_batch_ids = fields.One2many(
        "stock.picking.batch",
        "mrp_batch_id",
        string="Batch Transfers",
    )
    # Count of associated sale orders
    sale_order_count = fields.Integer(
        "Total Sale Order Count",
        compute="_compute_sale_order_count",
    )
    # Count of associated internal Tranfer
    picking_count = fields.Integer(
        "Total Sale Order Count",
        compute="_compute_picking_count",
    )
    # Count of associated batch pickings
    picking_batch_count = fields.Integer(
        string="Batch Transfers Count",
        compute="_compute_picking_count",
        store=False,
    )

    # END #########
    # METHODS #####

    # Action and Button Methods
    def action_assign(self):
        # Assign raw materials to production orders that are not completed or canceled
        for rec in self:
            queued = False
            enable_delay = (
                self.env["ir.config_parameter"]
                .sudo()
                .get_param("mrp_batch.enable_delay_action_assign", "False")
            )
            for mo in rec.production_ids.filtered(
                lambda x: x.state not in ("draft", "done", "cancel")
            ):
                if enable_delay and enable_delay.lower() in ("true", "1", "yes"):
                    mo.with_delay().action_assign()
                    queued = True
                else:
                    mo.action_assign()
            if queued:
                rec.is_queuing = True

    def action_confirm(self):
        # Confirm the batch and associated manufacturing orders
        for rec in self:
            queued = False
            rec.state = "confirm"
            enable_delay = (
                self.env["ir.config_parameter"]
                .sudo()
                .get_param("mrp_batch.enable_delay_action_confirm", "False")
            )
            for mo in rec.production_ids.filtered(lambda x: x.state == "draft"):
                if enable_delay and enable_delay.lower() in ("true", "1", "yes"):
                    mo.with_delay().action_confirm()
                    queued = True
                else:
                    mo.action_confirm()
            if queued:
                rec.is_queuing = True

    def button_plan(self):
        for rec in self:
            queued = False
            productions = rec.production_ids.filtered(
                lambda x: x.state != "draft" and not x.is_planned
            )
            if productions:
                enable_delay = (
                    self.env["ir.config_parameter"]
                    .sudo()
                    .get_param("mrp_batch.enable_delay_button_plan", "False")
                )
                for mo in productions:
                    if enable_delay and enable_delay.lower() in ("true", "1", "yes"):
                        mo.with_delay().button_plan()
                        queued = True
                    else:
                        mo.button_plan()

                if rec.state == "draft" and not any(
                    productions.filtered(lambda p: p.state == "draft")
                ):
                    rec.state = "confirm"
            if queued:
                rec.is_queuing = True

    def button_unplan(self):
        for rec in self:
            queued = False
            enable_delay = (
                self.env["ir.config_parameter"]
                .sudo()
                .get_param("mrp_batch.enable_delay_button_unplan", "False")
            )

            eligible_productions = rec.production_ids.filtered(
                lambda mo: not any(
                    wo.state in ("done", "progress") for wo in mo.workorder_ids
                )
            )

            for mrp_production in eligible_productions:
                if enable_delay and enable_delay.lower() in ("true", "1", "yes"):
                    mrp_production.with_delay().button_unplan()
                    queued = True
                else:
                    mrp_production.button_unplan()
            if queued:
                rec.is_queuing = True

    def action_unreserve(self):
        for rec in self:
            queued = False
            enable_delay = (
                self.env["ir.config_parameter"]
                .sudo()
                .get_param("mrp_batch.enable_delay_action_unreserve", "False")
            )

            for mo in rec.production_ids.filtered(
                lambda x: x.state not in ("draft", "done", "cancel")
            ):
                if enable_delay and enable_delay.lower() in ("true", "1", "yes"):
                    mo.with_delay().do_unreserve()
                    queued = True
                else:
                    mo.do_unreserve()
            if queued:
                rec.is_queuing = True

    def action_done(self):
        for rec in self:
            queued = False

            enable_delay = (
                self.env["ir.config_parameter"]
                .sudo()
                .get_param("mrp_batch.enable_delay_action_done", "False")
            )

            for mo in rec.production_ids.filtered(
                lambda x: x.state not in ("done", "cancel")
            ):
                if enable_delay and enable_delay.lower() in ("true", "1", "yes"):
                    mo.with_delay().button_mark_done()
                    queued = True
                else:
                    mo.button_mark_done()
            if queued:
                rec.is_queuing = True
            rec.state = "done"

    def action_cancel(self):
        for rec in self:
            queued = False
            rec.state = "cancel"
            enable_delay = (
                self.env["ir.config_parameter"]
                .sudo()
                .get_param("mrp_batch.enable_delay_action_cancel", "False")
            )

            eligible_productions = rec.production_ids.filtered(
                lambda mo: not any(wo.state == "done" for wo in mo.workorder_ids)
            )
            for mrp_production in eligible_productions:
                if enable_delay and enable_delay.lower() in ("true", "1", "yes"):
                    mrp_production.with_delay().action_cancel()
                    queued = True
                else:
                    mrp_production.action_cancel()
            if queued:
                rec.is_queuing = True

    def action_lock_and_unlock(self):
        # Lock all Manufacturing Orders in the batch.
        for rec in self:
            for mo in rec.production_ids:
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

    def action_update_bom(self):
        # Button that shows if any MO had changes to the BoM and update them.
        for batch in self:
            for production in batch.production_ids:
                # If MO has outdated BoM and in state where it can change, then update
                if production.is_outdated_bom and production.state in [
                    "draft",
                    "confirmed",
                ]:
                    production.action_update_bom()

    def action_open_mrp_batch_schedule(self):
        """Opens the related schedule in form view."""
        self.ensure_one()
        if self.mrp_batch_schedule_id:
            return {
                "type": "ir.actions.act_window",
                "name": "Manufacturing Batch Schedule",
                "res_model": "mrp.production.batch.schedule",
                "view_mode": "form",
                "res_id": self.mrp_batch_schedule_id.id,
                "target": "current",  # Opens in the same window
                "context": "{'create': False}",
            }

    def action_open_batch_transfers(self):
        # Ensures the method is called on a single record.
        self.ensure_one()
        # Defines the base action for viewing the stock picking batch.
        action = {
            "res_model": "stock.picking.batch",
            "type": "ir.actions.act_window",
        }
        # Checks if there is only one batch ID in `picking_batch_ids`.
        if len([batch.id for batch in self.picking_batch_ids]) == 1:
            # If there is a single batch, open it in form view.
            action.update(
                {
                    "view_mode": "form",
                    "res_id": self.picking_batch_ids.id,
                }
            )
        else:
            # If there are multiple batches, open them in tree and form view with a
            # domain filter.
            action.update(
                {
                    "name": "Batch Transfer",
                    "domain": [("id", "in", self.picking_batch_ids.ids)],
                    "view_mode": "tree, form",
                }
            )
        return action

    # Compute Methods
    @api.depends(
        "production_ids",
        "production_ids.mrp_batch_id",
        "production_ids.state",
    )
    def _compute_batch_state(self):
        """Compute the state of the batch based on the states of associated MOs,
        ignoring 'cancel' states unless all are 'cancel'."""
        # Pre-compute all non-cancel states
        batch_states = {}
        for batch in self:
            if batch.state == "hold":
                continue  # Do not update if batch is on hold

            # Pre-filter and collect non-cancel states
            non_cancel_states = batch.production_ids.filtered(
                lambda mo: mo.state != "cancel"
            ).mapped("state")

            if not non_cancel_states and batch.production_ids:  # All are 'cancel'
                batch_states[batch.id] = "cancel"
            elif all(state == "draft" for state in non_cancel_states):
                batch_states[batch.id] = "draft"
            elif all(state == "confirmed" for state in non_cancel_states):
                batch_states[batch.id] = "confirm"
            elif any(state in ("progress", "to_close") for state in non_cancel_states):
                batch_states[batch.id] = "progress"
            elif all(state == "done" for state in non_cancel_states):
                batch_states[batch.id] = "done"
            else:
                # Default to draft if no clear state
                batch_states[batch.id] = "draft"

        # Apply computed states
        for batch in self:
            if batch.state != "hold":
                batch.state = batch_states.get(batch.id, batch.state)

    @api.depends(
        "production_ids.sale_order_id.tag_ids",
        "production_ids.state",
    )
    def _compute_sale_tags(self):
        for rec in self:
            # Exclude canceled MOs
            valid_productions = rec.production_ids.filtered(
                lambda mo: mo.state != "cancel"
            )

            # Collect sale tags
            all_tags = valid_productions.mapped("sale_order_id.tag_ids")
            rec.sale_tag_ids = [(6, 0, all_tags.ids)]

    @api.depends(
        "date_start",
        "date_deadline",
    )
    def _compute_is_delayed(self):
        # Check if the scheduled date falls after deadline
        self.is_delayed = False
        for rec in self:
            if rec.date_start and rec.date_deadline:
                scheduled_date = rec.date_start.date()
                deadline_date = rec.date_deadline.date()
                rec.is_delayed = scheduled_date >= deadline_date

            # Explicitly trigger _compute_tags after setting is_delayed
            # Removed manual compute call - handled by @api.depends decorator

    @api.depends("production_ids")
    def _compute_partner_ids(self):
        # Compute the customer(s) based on associated production records
        for rec in self:
            rec.partner_ids = False
            if rec.production_ids:
                # get partner IDs in one operation
                partners = (
                    rec.production_ids.procurement_group_id.mrp_production_ids.move_dest_ids.group_id.sale_id.partner_id
                )
                rec.partner_ids = partners.ids

    @api.depends("production_ids")
    def _compute_sale_order_ids(self):
        # Compute the Sale Order(s) based on associated production records
        for rec in self:
            rec.sale_order_ids = False
            if rec.production_ids:
                # get sale order IDs in one operation
                rec.sale_order_ids = rec.production_ids.sale_order_id.ids

    @api.depends("production_ids")
    def _compute_product_ids(self):
        # Compute the product(s) based on associated production records
        for rec in self:
            rec.product_ids = False
            if rec.production_ids:
                # get product IDs in one operation
                rec.product_ids = rec.production_ids.product_id.ids

    @api.depends("production_ids")
    def _compute_product_tmpl_ids(self):
        # Compute the product template(s) based on associated production records
        for rec in self:
            rec.product_tmpl_ids = False
            if rec.production_ids:
                # get product template IDs in one operation
                rec.product_tmpl_ids = rec.production_ids.product_tmpl_id.ids

    @api.depends(
        "exception_ids",
        "production_ids.state",
        "production_ids.exception_ids",
        "production_ids.main_exception_id",
        "production_ids.ignore_exception",
    )
    def _compute_exceptions(self):
        for rec in self:
            # Exclude canceled MOs
            valid_productions = rec.production_ids.filtered(
                lambda mo: mo.state != "cancel"
            )

            # Collect exceptions
            all_exceptions = valid_productions.mapped("exception_ids")
            rec.exception_ids = [(6, 0, all_exceptions.ids)]

            # Compute exceptions summary
            if all_exceptions:
                rec.exceptions_summary = "<ul>%s</ul>" % "".join(
                    [
                        f"<li>{html.escape(e.name)}: <i>{html.escape(e.description or '')}</i> <b>"
                        + _(
                            f"{'(Blocking exception)' if e.is_blocking else ''}</b></li>"
                        )
                        for e in all_exceptions
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
        for rec in self:
            rec.earliest_start = False
            if rec.production_ids:
                # Use min directly on the mapped values
                start_dates = rec.production_ids.mapped("date_start")
                if start_dates:
                    rec.earliest_start = min(start_dates)

    @api.depends(
        "date_start",
        "remaining_duration",
    )
    def _compute_date_end(self):
        for rec in self:
            if rec.date_start and rec.remaining_duration is not None:
                rec.date_end = rec.date_start + timedelta(
                    minutes=rec.remaining_duration
                )
            else:
                rec.date_end = False

    @api.depends(
        "production_ids",
        "production_ids.date_finished",
        "production_ids.state",
    )
    def _compute_date_finished(self):
        # Determine the finished date among all productions in the batch
        for rec in self:
            rec.date_finished = False
            if rec.production_ids:
                # Use min directly on the mapped values
                finished_dates = rec.production_ids.mapped("date_finished")
                if finished_dates:
                    rec.date_finished = min(finished_dates)

    @api.depends(
        "production_ids",
        "production_ids.date_deadline",
        "production_ids.state",
    )
    def _compute_date_deadline(self):
        # Determine the deadline date among all productions in the batch
        for rec in self:
            rec.date_deadline = False
            if rec.production_ids:
                # Filter out productions without a date_deadline
                deadlines = [
                    production.date_deadline
                    for production in rec.production_ids
                    if production.date_deadline
                ]
                # Compute the maximum deadline if there are any valid dates
                rec.date_deadline = max(deadlines) if deadlines else False

    @api.depends(
        "production_ids",
        "production_ids.is_outdated_bom",
    )
    def _compute_outaged_bom(self):
        for rec in self:
            # Exclude MOs in the "cancel" state
            productions = rec.production_ids.filtered(lambda p: p.state != "cancel")
            rec.is_outdated_bom = any(productions.filtered(lambda p: p.is_outdated_bom))

    # Computes for Expected & Real durations
    def _compute_durations_by_type(self, workorders, duration_field="duration_expected"):
        """
        Helper method to compute durations by operation type.
        Returns dict with keys: build, test, other
        """
        result = {
            OPERATION_TYPE_BUILD: 0.0,
            OPERATION_TYPE_TEST: 0.0,
            OPERATION_TYPE_OTHER: 0.0,
        }
        for wo in workorders:
            op_type = wo.operation_type
            if op_type in result:
                result[op_type] += getattr(wo, duration_field, 0.0)
        return result

    @api.depends(
        "production_ids.duration_expected",
        "production_ids.state",
    )
    def _compute_total_duration_expected(self):
        for rec in self:
            # Exclude MOs in the "cancel" state
            productions = rec.production_ids.filtered(lambda p: p.state != "cancel")
            rec.total_duration_expected = sum(productions.mapped("duration_expected"))

    @api.depends(
        "production_ids.duration",
    )
    def _compute_total_duration(self):
        for rec in self:
            # Exclude MOs in the "cancel" state
            productions = rec.production_ids.filtered(lambda p: p.state != "cancel")
            rec.total_duration = sum(productions.mapped("duration"))

    @api.depends(
        "production_ids.workorder_ids.operation_id.type",
        "production_ids.duration_expected",
        "production_ids.state",
    )
    def _compute_build_test_other_durations_expected(self):
        """Compute expected durations by operation type using helper method."""
        for rec in self:
            # Exclude MOs in the "cancel" state
            productions = rec.production_ids.filtered(lambda p: p.state != "cancel")
            workorders = productions.mapped("workorder_ids")
            
            durations = rec._compute_durations_by_type(workorders, "duration_expected")
            rec.total_build_duration_expected = durations[OPERATION_TYPE_BUILD]
            rec.total_test_duration_expected = durations[OPERATION_TYPE_TEST]
            rec.total_other_duration_expected = durations[OPERATION_TYPE_OTHER]

    @api.depends(
        "production_ids.workorder_ids.operation_id.type",
        "production_ids.duration",
    )
    def _compute_build_test_other_durations(self):
        """Compute real durations by operation type using helper method."""
        for rec in self:
            # Exclude MOs in the "cancel" state
            productions = rec.production_ids.filtered(lambda p: p.state != "cancel")
            workorders = productions.mapped("workorder_ids")
            
            durations = rec._compute_durations_by_type(workorders, "duration")
            rec.total_build_duration = durations[OPERATION_TYPE_BUILD]
            rec.total_test_duration = durations[OPERATION_TYPE_TEST]
            rec.total_other_duration = durations[OPERATION_TYPE_OTHER]

    @api.depends("is_delayed", "is_planned")
    def _compute_tags(self):
        for rec in self:
            # Keep track of existing tags by their IDs
            tag_ids = set(rec.tag_ids.ids)

            # Find or create the tags for Delayed and Planned
            delayed_tag = self.env["mrp.production.batch.tag"].search(
                [("name", "=", TAG_NAME_DELAYED)], limit=1
            )
            planned_tag = self.env["mrp.production.batch.tag"].search(
                [("name", "=", TAG_NAME_PLANNED)], limit=1
            )

            # Add or remove Delayed tag based on is_delayed
            if rec.is_delayed and delayed_tag:
                tag_ids.add(delayed_tag.id)  # Add tag if it's True
            else:
                tag_ids.discard(delayed_tag.id)  # Remove tag if it's False

            # Add or remove Planned tag based on is_planned
            if rec.is_planned and planned_tag:
                tag_ids.add(planned_tag.id)  # Add tag if it's True
            else:
                tag_ids.discard(planned_tag.id)  # Remove tag if it's False

            # Assign the tags to the rec (update the tag_ids field)
            rec.tag_ids = [(6, 0, list(tag_ids))]  # Set the updated list of tag IDs

    # Computes for Average Unit Expected & Real durations
    @api.depends(
        "production_ids.duration_expected",
        "production_ids.state",
    )
    def _compute_avg_unit_duration_expected(self):
        for rec in self:
            productions = rec.production_ids.filtered(lambda p: p.state != "cancel")
            durations = productions.mapped("duration_expected")
            rec.avg_duration_expected = (
                sum(durations) / len(durations) if durations else 0
            )

    @api.depends(
        "production_ids.duration",
    )
    def _compute_avg_unit_duration(self):
        for rec in self:
            productions = rec.production_ids.filtered(lambda p: p.state != "cancel")
            durations = productions.mapped("duration")
            rec.avg_duration = sum(durations) / len(durations) if durations else 0

    @api.depends(
        "production_ids.workorder_ids.operation_id.type",
        "production_ids.duration_expected",
        "production_ids.state",
    )
    def _compute_build_test_unit_other_durations_expected(self):
        """Compute average unit expected durations by operation type using helper method."""
        for rec in self:
            productions = rec.production_ids.filtered(lambda p: p.state != "cancel")
            workorders = productions.mapped("workorder_ids")
            
            durations = rec._compute_durations_by_type(workorders, "duration_expected")
            build_durations = [
                wo.duration_expected
                for wo in workorders
                if wo.operation_type == OPERATION_TYPE_BUILD
            ]
            test_durations = [
                wo.duration_expected for wo in workorders if wo.operation_type == OPERATION_TYPE_TEST
            ]
            other_durations = [
                wo.duration_expected
                for wo in workorders
                if wo.operation_type == OPERATION_TYPE_OTHER
            ]
            
            rec.avg_build_duration_expected = (
                sum(build_durations) / len(build_durations) if build_durations else 0
            )
            rec.avg_test_duration_expected = (
                sum(test_durations) / len(test_durations) if test_durations else 0
            )
            rec.avg_other_duration_expected = (
                sum(other_durations) / len(other_durations) if other_durations else 0
            )

    @api.depends(
        "production_ids.workorder_ids.operation_id.type",
        "production_ids.duration",
    )
    def _compute_build_test_unit_other_durations(self):
        """Compute average unit real durations by operation type using helper method."""
        for rec in self:
            productions = rec.production_ids.filtered(lambda p: p.state != "cancel")
            workorders = productions.mapped("workorder_ids")
            
            build_durations = [
                wo.duration for wo in workorders if wo.operation_type == OPERATION_TYPE_BUILD
            ]
            test_durations = [
                wo.duration for wo in workorders if wo.operation_type == OPERATION_TYPE_TEST
            ]
            other_durations = [
                wo.duration for wo in workorders if wo.operation_type == OPERATION_TYPE_OTHER
            ]
            
            rec.avg_build_duration = (
                sum(build_durations) / len(build_durations) if build_durations else 0
            )
            rec.avg_test_duration = (
                sum(test_durations) / len(test_durations) if test_durations else 0
            )
            rec.avg_other_duration = (
                sum(other_durations) / len(other_durations) if other_durations else 0
            )

    @api.depends(
        "total_duration",
        "total_duration_expected",
    )
    def _compute_remaining_duration(self):
        for rec in self:
            rec.remaining_duration = rec.total_duration_expected - rec.total_duration

    @api.depends(
        "total_build_duration_expected",
        "total_build_duration",
    )
    def _compute_remaining_build_duration(self):
        for rec in self:
            rec.remaining_build_duration = (
                rec.total_build_duration_expected - rec.total_build_duration
            )

    @api.depends(
        "total_test_duration_expected",
        "total_test_duration",
    )
    def _compute_remaining_test_duration(self):
        for rec in self:
            rec.remaining_test_duration = (
                rec.total_test_duration_expected - rec.total_test_duration
            )

    @api.depends(
        "total_other_duration_expected",
        "total_other_duration",
    )
    def _compute_remaining_other_duration(self):
        for rec in self:
            rec.remaining_other_duration = (
                rec.total_other_duration_expected - rec.total_other_duration
            )

    @api.depends(
        "production_ids",
        "production_ids.procurement_group_id.mrp_production_ids.move_dest_ids.sale_line_id.price_unit",
        "production_ids.product_qty",
        "production_ids.state",
    )
    def _compute_revenue(self):
        for rec in self:
            # Exclude canceled MOs
            valid_productions = rec.production_ids.filtered(
                lambda mo: mo.state != "cancel"
            )
            # Compute revenue
            total = sum(
                sale_line.price_unit * mo.product_qty
                for mo in valid_productions
                for sale_line in mo.procurement_group_id.mrp_production_ids.move_dest_ids.sale_line_id
            )
            rec.total_revenue = total

    @api.depends(
        "production_ids",
        "production_ids.state",
    )
    def _compute_mrp_production_cancel(self):
        # Determine if all productions are canceled or in done state
        for rec in self:
            rec.is_cancel = False
            if rec.production_ids:
                rec.is_cancel = all(
                    production.state in ("done", "cancel")
                    for production in rec.production_ids
                )

    @api.depends(
        "production_ids",
        "production_ids.state",
        "production_ids.is_planned",
    )
    def _compute_is_planned(self):
        for rec in self:
            rec.is_planned = False
            # Filter out production orders with states 'to_close', 'done', or 'cancel'
            filtered_productions = rec.production_ids.filtered(
                lambda p: p.state not in ("progress", "to_close", "done", "cancel")
                and p.workorder_ids
            )
            # Set is_planned if all MO's that have workorders are planned.
            if filtered_productions:
                rec.is_planned = all(
                    production.is_planned for production in filtered_productions
                )
            # Explicitly trigger _compute_tags after setting is_delayed
            # Removed manual compute call - handled by @api.depends decorator

    @api.depends(
        "production_ids",
        "production_ids.state",
    )
    def _compute_mrp_production_confirm(self):
        # Check if all production orders are confirmed or in progress
        for rec in self:
            rec.is_confirmed = True
            # Filter out production orders with states 'to_close', 'done', or 'cancel'
            filtered_productions = rec.production_ids.filtered(
                lambda p: p.state == "draft"
            )

            # Set is_confirmed if all MO's that have workorders are planned.
            if rec.production_ids and filtered_productions:
                rec.is_confirmed = not any(
                    production.state == "draft" for production in rec.production_ids
                )

    @api.depends(
        "production_ids",
        "production_ids.move_raw_ids",
        "production_ids.state",
        "production_ids.move_raw_ids.product_uom_qty",
        "production_ids.unreserve_visible",
        "production_ids.reserve_visible",
    )
    def _compute_reserve_and_unreserve_visible(self):
        # Determine the visibility of reserve/unreserve actions based on productions
        for rec in self:
            rec.reserve_visible = False
            rec.unreserve_visible = False
            # Filter out production orders with states 'to_close', 'done', or 'cancel'
            filtered_productions = rec.production_ids.filtered(
                lambda p: p.state not in ("progress", "to_close", "done", "cancel")
            )
            if rec.production_ids:
                rec.unreserve_visible = any(
                    production.unreserve_visible for production in filtered_productions
                )
                rec.reserve_visible = any(
                    production.reserve_visible for production in filtered_productions
                )

    @api.depends("production_ids.move_raw_ids")
    def _compute_mrp_production_done(self):
        # Check if all move lines are open or if all productions are completed
        for rec in self:
            rec.is_move_raw_ids = False
            rec.is_produce_all = False
            if rec.production_ids:
                rec.is_move_raw_ids = all(
                    move.state not in ("done", "cancel")
                    for production in rec.production_ids
                    for move in production.move_raw_ids
                )
                rec.is_produce_all = all(
                    production.qty_producing for production in rec.production_ids
                )

    @api.depends("production_ids.workorder_ids.state")
    def _compute_lock(self):
        # Determine if the lock button should be displayed based on work order states
        for rec in self:
            rec.show_lock = False
            rec.is_locked = False
            if rec.production_ids and rec.state != "cancel":
                rec.show_lock = all(
                    wo.state in ("done", "cancel")
                    for production in rec.production_ids
                    for wo in production.workorder_ids
                )
                rec.is_locked = any(
                    wo.state in ("done", "cancel")
                    for production in rec.production_ids
                    for wo in production.workorder_ids
                )

    @api.depends(
        "production_ids.state",
        "production_ids.qty_producing",
        "production_ids.qty_produced",
    )
    def _compute_qty(self):
        for rec in self:
            # Exclude canceled MOs
            valid_productions = rec.production_ids.filtered(
                lambda mo: mo.state != "cancel"
            )

            # Compute quantities
            qty_producing = sum(mo.product_qty for mo in valid_productions)
            qty_produced = sum(mo.qty_produced for mo in valid_productions)
            qty_remaining = qty_producing - qty_produced

            rec.qty_producing = qty_producing
            rec.qty_produced = qty_produced
            rec.qty_remaining = qty_remaining

            # Compute percentage complete
            if qty_producing > 0.0:
                rec.percent_complete = qty_produced / qty_producing
            else:
                rec.percent_complete = 0.0

    @api.depends(
        "production_ids",
        "production_ids.state",
        "production_ids.reservation_state",
    )
    def _compute_components_availability(self):
        """Computes batch-level component availability based on MO statuses."""
        for batch in self:
            batch.components_availability = False
            batch.components_availability_state = False

            valid_productions = batch.production_ids.filtered(
                lambda mo: mo.state not in ("draft", "cancel", "done", "to_close")
            )
            if not valid_productions:
                continue

            # Fetch all raw moves
            # Note: forecast_availability is computed automatically via @api.depends
            all_raw_moves = valid_productions.move_raw_ids

            latest_forecast_date = False
            is_unavailable = False

            # Optimize: Bulk read products and forecast data
            # Prefetch products to avoid N+1 queries
            products = all_raw_moves.mapped("product_id")
            
            for move in all_raw_moves:
                product = move.product_id

                required_qty = 0 if move.state == "draft" else move.product_qty
                if (
                    float_compare(
                        move.forecast_availability,
                        required_qty,
                        precision_rounding=product.uom_id.rounding,
                    )
                    == -1
                ):
                    is_unavailable = True

                if move.forecast_expected_date:
                    latest_forecast_date = (
                        max(latest_forecast_date, move.forecast_expected_date)
                        if latest_forecast_date
                        else move.forecast_expected_date
                    )

            # Set batch-level availability based on the worst-case scenario
            if is_unavailable:
                batch.components_availability = _("Not Available")
                batch.components_availability_state = "unavailable"
            elif latest_forecast_date:
                batch.components_availability = _(
                    "Exp %s", format_date(self.env, latest_forecast_date)
                )
                batch.components_availability_state = (
                    "late"
                    if batch.date_start and latest_forecast_date > batch.date_start
                    else "expected"
                )
            else:
                batch.components_availability = _("Available")
                batch.components_availability_state = "available"
            enable_component_details_delay = (
                self.env["ir.config_parameter"]
                .sudo()
                .get_param("mrp_batch.enable_delay_component_availability_details", "False")
            )
            if enable_component_details_delay and enable_component_details_delay.lower() in ("true", "1", "yes"):
                batch.with_delay()._compute_components_availability_details()
            else:
                batch._compute_components_availability_details()

    def _compute_components_availability_details(self):
        """Computes batch-level component availability based on MO statuses."""
        for batch in self:
            batch.components_availability_details = ""

            valid_productions = batch.production_ids.filtered(
                lambda mo: mo.state not in ("draft", "cancel", "done", "to_close")
            )
            if not valid_productions:
                continue

            # Fetch all raw moves
            # Note: forecast_availability is computed automatically via @api.depends
            all_raw_moves = valid_productions.move_raw_ids

            product_status_map = {}

            for move in all_raw_moves:
                product = move.product_id
                if product.id in product_status_map:
                    continue  # Skip duplicate product

                required_qty = 0 if move.state == "draft" else move.product_qty
                if (
                    float_compare(
                        move.forecast_availability,
                        required_qty,
                        precision_rounding=product.uom_id.rounding,
                    )
                    == -1
                ):
                    product_status_map[product.id] = (
                        f"{product.default_code}: Not Available"
                    )

                if move.forecast_expected_date:
                    product_status_map[product.id] = (
                        f"{product.default_code}: Exp. {format_date(self.env, move.forecast_expected_date)}"
                    )

            # Populate the details field
            batch.components_availability_details = "\n".join(
                product_status_map.values()
            )

    @api.depends(
        "production_ids",
        "production_ids.reservation_state",
        "production_ids.move_raw_ids.state",
    )
    def _compute_reservation_state(self):
        """Computes batch-level reservation state based on MO statuses."""
        for batch in self:
            valid_productions = batch.production_ids.filtered(
                lambda mo: mo.state != "cancel"
            )

            if not valid_productions:
                batch.reservation_state = False
                continue

            # Pre-calculate states
            states = valid_productions.mapped("reservation_state")
            if "assigned" in states:
                batch.reservation_state = "assigned"
            elif "confirmed" in states:
                batch.reservation_state = "confirmed"
            elif "waiting" in states:
                batch.reservation_state = "waiting"
            else:
                batch.reservation_state = False

    # Smart Button Methods
    @api.depends("production_ids.move_raw_ids")
    def _compute_sale_order_count(self):
        # Compute the total count of sales orders associated with productions
        for rec in self:
            rec.sale_order_count = len(
                rec.production_ids.mapped(
                    "procurement_group_id.mrp_production_ids.move_dest_ids.group_id.sale_id"
                )
            )

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

            # Set mrp_batch_schedule_id
            if "date_start" in vals and "workcenter_tag_id" in vals:
                vals["mrp_batch_schedule_id"] = self._get_or_create_schedule(
                    vals["date_start"], vals["workcenter_tag_id"]
                ).id
        batches = super().create(vals_list)
        workcenter_obj = self.env["mrp.workcenter"]
        for batch in batches:
            if batch.workcenter_tag_id:
                for mo in batch.production_ids:
                    for workorder in mo.workorder_ids.filtered(
                        lambda l: l.state not in ("done", "cancel", "progress")
                    ):
                        if (
                            workorder.workcenter_id.type != workorder.operation_type
                            or workorder.workcenter_id.tag_ids.ids
                            not in batch.workcenter_tag_id.ids
                        ):
                            correct_workcenter = workcenter_obj.search(
                                [
                                    ("type", "=", workorder.operation_type),
                                    ("tag_ids", "in", batch.workcenter_tag_id.ids),
                                ],
                                limit=1,
                            )
                            if correct_workcenter:
                                workorder.workcenter_id = correct_workcenter.id

        return batches

    def write(self, vals):
        # If scheduled date changes, then log chatter message on sale orders.
        if "date_start" in vals:
            for batch in self:
                old_date = batch.date_start
                new_date = vals.get("date_start")
                user_tz = self.env.context.get("tz") or self.env.user.tz or "UTC"

                old_date_str = (
                    old_date
                    and format_datetime(
                        self.env, old_date, tz=user_tz, dt_format="short"
                    )
                    or _("None")
                )
                new_date_str = (
                    new_date
                    and format_datetime(
                        self.env, new_date, tz=user_tz, dt_format="short"
                    )
                    or _("None")
                )
                if old_date != new_date:
                    for sale_order in batch.sale_order_ids:
                        message = _(
                            "Manufacturing Batch <b>%s</b> Scheduled Date Changed:<br/>"
                            "<b> %s</b> → <b>%s</b>"
                        ) % (batch.name, old_date_str, new_date_str)
                        sale_order.message_post(body=message, body_is_html=True)
        res = super().write(vals)

        for batch in self:
            if vals.get("date_start") and batch.state in ("draft", "confirm"):
                for mo in batch.production_ids:
                    # If the job is related to a manufacturing order, check its batch
                    if mo.state in ("draft", "confirmed"):
                        mo.date_start = batch.date_start

            # Set mrp_batch_schedule_id
            if "date_start" in vals or "workcenter_tag_id" in vals:
                date_start = (
                    vals.get("date_start", batch.date_start) or batch.date_start
                )
                workcenter_tag_id = (
                    vals.get("workcenter_tag_id", batch.workcenter_tag_id.id)
                    or batch.workcenter_tag_id
                )
                if date_start and workcenter_tag_id:
                    batch.mrp_batch_schedule_id = batch._get_or_create_schedule(
                        date_start, workcenter_tag_id
                    )
            if "workcenter_tag_id" in vals or "production_ids" in vals:
                workcenter_obj = self.env["mrp.workcenter"]
                if batch.workcenter_tag_id:
                    for mo in batch.production_ids:
                        for workorder in mo.workorder_ids.filtered(
                            lambda l: l.state not in ("done", "cancel", "progress")
                        ):
                            if (
                                workorder.workcenter_id.type != workorder.operation_type
                                or workorder.workcenter_id.tag_ids.ids
                                not in batch.workcenter_tag_id.ids
                            ):
                                correct_workcenter = workcenter_obj.search(
                                    [
                                        ("type", "=", workorder.operation_type),
                                        ("tag_ids", "in", batch.workcenter_tag_id.ids),
                                    ],
                                    limit=1,
                                )
                                if correct_workcenter:
                                    workorder.workcenter_id = correct_workcenter.id
        return res

    def _get_or_create_schedule(self, date_start, workcenter_tag_id):
        """Find or create a schedule based on date_start and workcenter_tag_id."""
        schedule_date = fields.Date.to_date(date_start)
        domain = [
            ("date", "=", schedule_date),
            ("workcenter_tag_id", "=", workcenter_tag_id),
        ]
        schedule = self.env["mrp.production.batch.schedule"].search(domain, limit=1)

        if not schedule:
            schedule = self.env["mrp.production.batch.schedule"].create(
                {
                    "date": schedule_date,
                    "workcenter_tag_id": workcenter_tag_id,
                }
            )
        return schedule

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

    def _compute_picking_count(self):
        # Compute the total count of internal tranfer associated with productions
        for rec in self:
            rec.picking_count = len(rec.production_ids.mapped("picking_ids"))
            rec.picking_batch_count = len(rec.picking_batch_ids)

    # Smart Button Methods
    def action_view_mo_delivery(self):
        """Returns an action that display picking related to manufacturing order.
        It can either be a list view or in a form view (if there is only one picking to show).
        """
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "stock.action_picking_tree_all"
        )
        picking_ids = self.production_ids.mapped("picking_ids")
        if len(picking_ids) > 1:
            action["domain"] = [("id", "in", picking_ids.ids)]
        elif picking_ids:
            action["res_id"] = picking_ids.id
            action["views"] = [(self.env.ref("stock.view_picking_form").id, "form")]
            if "views" in action:
                action["views"] += [
                    (state, view) for state, view in action["views"] if view != "form"
                ]
        action["context"] = dict(self._context)
        return action

    # END #########
