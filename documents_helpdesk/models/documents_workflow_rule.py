# Copyright (C) 2021 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import fields, models


class DocumentsWorkflowRule(models.Model):
    _inherit = ["documents.workflow.rule"]

    def _compute_business(self):
        return self._get_business()

    has_business_option = fields.Boolean(default=True, compute="_compute_business")
    create_model = fields.Selection(
        selection_add=[("helpdesk.ticket", "Helpdesk Ticket")]
    )

    def create_record(self, documents=None):
        res = super(DocumentsWorkflowRule, self).create_record(documents=documents)
        if self.create_model == "helpdesk.ticket":
            ticket = self.env[self.create_model].create(
                {
                    "name": "Ticket created from Documents",
                    "team_id": self.env.ref("helpdesk.helpdesk_team1").id,
                }
            )

            for document in documents:
                # this_document is the document in use for the workflow
                this_document = document
                if (
                    document.res_model or document.res_id
                ) and document.res_model != "documents.document":
                    attachment_copy = document.attachment_id.with_context(
                        no_document=True
                    ).copy()
                    this_document = document.copy({"attachment_id": attachment_copy.id})
                this_document.write(
                    {
                        "res_model": ticket._name,
                        "res_id": ticket.id,
                    }
                )

            view_id = self.env.ref("helpdesk.helpdesk_ticket_view_form").id
            return {
                "type": "ir.actions.act_window",
                "res_model": "helpdesk.ticket",
                "name": "New helpdesk ticket",
                "context": self._context,
                "view_mode": "form",
                "views": [(view_id, "form")],
                "res_id": ticket.id if ticket else False,
                "view_id": view_id,
            }
        return res
