from odoo import api, fields, models


class MrpProductionBatch(models.Model):
    _name = "mrp.production.batch"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = " Manufacturing Batch"

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
            ("confirm", "Confirm"),
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
        strng="Unreserved",
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
        compute="compute_mrp_production_done",
    )
    is_produce_all = fields.Boolean(
        string="Is All Produced",
        compute="compute_mrp_production_done",
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
        compute="compute_show_lock",
    )
    is_locked = fields.Boolean(
        string="Is Locked",
        compute="compute_show_lock",
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
    total_duration = fields.Float(
        "Real Duration",
        compute="_compute_total_duration",
    )
    total_duration_expected = fields.Float(
        "Expected Duration",
        compute="_compute_total_duration_expected",
    )
    sale_order_count = fields.Integer(
        "Total Sale Order Count",
        compute="_compute_sale_order_count",
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals["name"] = self.env["ir.sequence"].next_by_code(
                "mrp.production.batch"
            ) or ("New")
            return super().create(vals_list)

    def _compute_check_date(self):
        self.is_date = False
        for rec in self:
            if rec.date_scheduled and rec.earliest_start:
                Scheduled_date = rec.date_scheduled.date()
                earliest_start = rec.earliest_start.date()
                rec.is_date = Scheduled_date != earliest_start

    def _compute_partner_id(self):
        for record in self:
            record.partner_ids = (
                record.production_ids.procurement_group_id.mrp_production_ids.move_dest_ids.group_id.sale_id.partner_id.ids
            )

    def _compute_earliest_start(self):
        for record in self:
            record.earliest_start = False
            if record.production_ids:
                start_date = min(
                    production.date_start for production in record.production_ids
                )
                record.earliest_start = start_date

    def action_cancel(self):
        for record in self:
            record.is_queuing = True
            record.state = "cancel"
            for mrp_production in record.production_ids:
                mrp_production.with_delay().action_cancel()

    @api.depends("production_ids.state")
    def _compute_mrp_production_cancel(self):
        for record in self:
            record.is_cancel = False
            record.is_cancel_id = False
            record.is_cancel_id = all(
                production.id for production in record.production_ids
            )
            record.is_cancel = all(
                production.state in ("done", "cancel")
                for production in record.production_ids
            )

    def button_plan(self):
        for record in self:
            record.is_queuing = True
            if record.state == "draft":
                record.state = "confirm"
            for mrp_production in record.production_ids:
                mrp_production.with_delay().button_plan()

    def button_unplan(self):
        for record in self:
            record.is_queuing = True
            for mrp_production in record.production_ids:
                mrp_production.with_delay().button_unplan()

    def _compute_is_planned(self):
        for record in self:
            record.is_planned = False
            record.is_plan = False
            record.is_workorder_ids = False
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

    def action_confirm(self):
        for record in self:
            record.is_queuing = True
            record.state = "confirm"
            for mo in record.production_ids.filtered(lambda x: x.state == "draft"):
                mo.with_delay().action_confirm()

    @api.depends("production_ids.state")
    def _compute_mrp_production_confirm(self):
        for record in self:
            record.is_confirm_check = False
            record.is_confirm_check = all(
                production.state != "draft" for production in record.production_ids
            )

    def action_assign(self):
        for record in self:
            record.is_queuing = True
            for mo in record.production_ids.filtered(
                lambda x: x.state not in ("draft", "done", "cancel")
            ):
                mo.with_delay().action_assign()

    def action_unreserve(self):
        for record in self:
            record.is_queuing = True
            for mo in record.production_ids.filtered(
                lambda x: x.state not in ("draft", "done", "cancel")
            ):
                mo.with_delay().do_unreserve()

    @api.depends("production_ids.state")
    def _compute_mrp_production_reserve_batch(self):
        for record in self:
            record.is_reserved_batch = False
            record.is_reserved_batch = all(
                production.state in ("draft", "done", "cancel")
                for production in record.production_ids
            )

    def _compute_reserve_and_unreserve_visible(self):
        for record in self:
            record.is_reserved = False
            record.is_unreserved = False
            record.is_unreserved = all(
                production.unreserve_visible for production in record.production_ids
            )
            record.is_reserved = all(
                production.reserve_visible for production in record.production_ids
            )

    def action_lock_and_unlock(self):
        for record in self:
            for mo in record.production_ids:
                mo.action_toggle_is_locked()

    def compute_show_lock(self):
        for record in self:
            record.show_lock = False
            record.is_locked = False
            record.is_locked = all(
                production.is_locked for production in record.production_ids
            )
            record.show_lock = all(
                production.show_lock for production in record.production_ids
            )

    def action_done(self):
        for record in self:
            record.is_queuing = True
            for mo in record.production_ids.filtered(
                lambda x: x.state not in ("draft", "done", "cancel")
            ):
                mo.with_delay().button_mark_done()
            record.state = "done"

    def compute_mrp_production_done(self):
        for record in self:
            record.is_produce_all = False
            record.is_move_raw_ids = False
            record.is_move_raw_ids = all(
                production.move_raw_ids for production in record.production_ids
            )
            record.is_produce_all = all(
                production.show_produce_all for production in record.production_ids
            )

    def _compute_total_duration(self):
        for rec in self:
            rec.total_duration = sum(
                rec.production_ids.mapped("workorder_ids").mapped("duration")
            )

    def _compute_total_duration_expected(self):
        for rec in self:
            rec.total_duration_expected = sum(
                rec.production_ids.mapped("workorder_ids").mapped("duration_expected")
            )

    def _compute_sale_order_count(self):
        for rec in self:
            rec.sale_order_count = len(
                rec.production_ids.mapped("procurement_group_id")
                .mapped("mrp_production_ids")
                .mapped("move_dest_ids")
                .mapped("group_id")
                .mapped("sale_id")
            )

    def action_view_sale(self):
        self.ensure_one()
        sale_ids = (
            self.production_ids.mapped("procurement_group_id")
            .mapped("mrp_production_ids")
            .mapped("move_dest_ids")
            .mapped("group_id")
            .mapped("sale_id")
            .ids
        )
        action = {
            "name": "Sale Orders",
            "res_model": "sale.order",
            "type": "ir.actions.act_window",
        }
        if len(sale_ids) == 1:
            action.update(
                {
                    "view_mode": "form",
                    "res_id": sale_ids[0],
                }
            )
        else:
            action.update(
                {
                    "domain": [("id", "in", sale_ids)],
                    "view_mode": "tree,form",
                }
            )
        return action

    def action_open_add_to_batch_wizard(self):
        return {
            "name": "Add to Batch",
            "type": "ir.actions.act_window",
            "res_model": "add.manufacturing.order.wizard",
            "view_mode": "form",
            "target": "new",
        }

    def _check_and_update_queuing(self):
        for batch in self:
            # Search for all jobs related to this batch by using `filtered` if
            # `records` is a JSON/text field or One2many
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

            # Check if all jobs are either done or failed
            if all(job.state in ["done", "failed", "cancelled"] for job in jobs):
                batch.is_queuing = False
