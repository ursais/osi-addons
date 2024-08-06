# Copyright 2017-22 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import api, fields, models


class RmaOperation(models.Model):
    _inherit = "rma.operation"

    refund_policy = fields.Selection(
        [
            ("no", "No refund"),
            ("ordered", "Based on Ordered Quantities"),
            ("delivered", "Based on Delivered Quantities"),
            ("received", "Based on Received Quantities"),
        ],
        default="no",
    )

    refund_journal_id = fields.Many2one(
        comodel_name="account.journal",
        string="Refund Account Journal",
        domain="[('id', 'in', valid_refund_journal_ids)]",
    )

    valid_refund_journal_ids = fields.Many2many(
        comodel_name="account.journal",
        compute="_compute_domain_valid_journal",
    )
    automated_refund = fields.Boolean(
        help="In the scenario where a company uses anglo-saxon accounting, if "
        "you receive products from a customer and don't expect to refund the customer "
        "but send a replacement unit, mark this flag to be accounting consistent"
    )
    refund_free_of_charge = fields.Boolean(
        help="In case of automated refund you should mark this option as long automated"
        "refunds mean to compensate Stock Interim accounts only without hitting"
        "Accounts receivable"
    )

    @api.onchange("type")
    def _compute_domain_valid_journal(self):
        for rec in self:
            if rec.type == "customer":
                rec.valid_refund_journal_ids = self.env["account.journal"].search(
                    [("type", "=", "sale")]
                )
            else:
                rec.valid_refund_journal_ids = self.env["account.journal"].search(
                    [("type", "=", "purchase")]
                )

    @api.onchange("automated_refund")
    def _onchange_automated_refund(self):
        for rec in self:
            rec.refund_free_of_charge = rec.automated_refund
