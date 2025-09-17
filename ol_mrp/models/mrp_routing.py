# Import Odoo libs
from odoo import models, fields


class MrpRoutingWorkcenter(models.Model):
    _inherit = "mrp.routing.workcenter"

    # COLUMNS #####

    # Override the core field to make it company dependent and readonly
    time_cycle_manual = fields.Float(
        string="Manual Cycle Time",
        company_dependent=True,
        readonly=False,
        help="Time in minutes for the manual cycle, specific to each company.",
    )
    # Fields that should not trigger BOM update functionality
    _excluded_fields_for_bom_update = [
        "time_cycle_manual",
    ]

    # END #########
    # METHODS ##########

    def copy(self, default=None):
        """
        When create_get_bom() is called to determine if a new BOM should be created,
        and a new BOM should indeed be created, the new BOM's operations are created
        by copying the scaffold BOM's operations.

        We add in the time_cycle_manual value to be copied here, since that represents
        the "base line" time_cycle_manual values of the product.template record.
        """
        default = dict(default or {})
        res = super().copy(default)
        onlogic_companies = self.env["res.company"].get_all().sorted(key=lambda c: c.id)
        for company in onlogic_companies:
            if (
                ("time_cycle_manual" not in default)
                and self.bom_id
                and self.bom_id.scaffolding_bom
            ):
                # We need to use sudo here, in case the user that triggered
                # the action doesn't have access to both companies.
                company_time_cycle_manual = (
                    self.sudo().with_company(company).time_cycle_manual
                )
                res.sudo().with_company(company).write(
                    {"time_cycle_manual": company_time_cycle_manual}
                )
        return res

    def write(self, vals):
        """
        We override the _set_outdated_bom_in_productions method to require the has_relevant_updates flag,
        so we can filter out updates that we don't want to trigger BOM updates for.

        This is to prevent us from updating the BOM when certain fields are updated, which would potentially
        cause undesired updates to the BOM in production orders.
        """
        has_relevant_updates = any(
            key not in self._excluded_fields_for_bom_update for key in vals.keys()
        )
        if has_relevant_updates:
            self.bom_id._set_outdated_bom_in_productions(has_relevant_updates=True)
        return super().write(vals)

    # END #########
