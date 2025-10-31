from odoo import _, fields, models
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval


class LimsOrder(models.Model):
    _inherit = "lims.order"

    def action_open_create_document_wizard(self):
        self.ensure_one()
        action = self.env.ref("lims_documents.action_lims_order_document_wizard", False)
        if not action:
            return {
                "type": "ir.actions.act_window",
                "name": "Create Document",
                "res_model": "lims.order.document.wizard",
                "view_mode": "form",
                "target": "new",
                "context": {"default_order_id": self.id},
            }

        action = action.read()[0]

        raw_context = action.get("context")
        if isinstance(raw_context, str):
            try:
                ctx = safe_eval(raw_context)
            except Exception:
                ctx = {}
        elif isinstance(raw_context, dict):
            ctx = raw_context.copy()
        else:
            ctx = {}

        ctx.update({"default_order_id": self.id})
        action["context"] = ctx
        return action

    def _compute_document_count(self):
        Document = self.env["documents.document"]
        for rec in self:
            model = rec._name
            docs = Document.search([("res_model", "=", model), ("res_id", "=", rec.id)])
            rec.document_count = len(docs)

    document_count = fields.Integer(
        string="Documents", compute="_compute_document_count", store=False
    )

    def action_view_documents(self):
        """Open Documents linked to this LIMS order."""
        self.ensure_one()

        action = self.env.ref("documents.document_action", False)
        if not action:
            return {
                "type": "ir.actions.act_window",
                "name": _("Documents"),
                "res_model": "documents.document",
                "view_mode": "list,form",
                "domain": [("res_model", "=", self._name), ("res_id", "=", self.id)],
            }

        action = action.read()[0]
        action.update(
            {
                "domain": [("res_model", "=", self._name), ("res_id", "=", self.id)],
                "context": {"default_res_model": self._name, "default_res_id": self.id},
                "res_model": "documents.document",
            }
        )
        return action


class LimsOrderDocumentWizard(models.TransientModel):
    _name = "lims.order.document.wizard"
    _description = "Create Document from LIMS Order"

    name = fields.Char(string="Document Name", required=True)
    description = fields.Text()
    order_id = fields.Many2one("lims.order", required=True, ondelete="cascade")
    upload = fields.Binary(string="Upload File", attachment=True, required=True)
    filename = fields.Char(string="File Name")

    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if not res.get("order_id") and self.env.context.get("default_order_id"):
            res["order_id"] = self.env.context.get("default_order_id")
        return res

    def action_create_document(self):
        Document = self.env.get("documents.document")
        Attachment = self.env["ir.attachment"]

        for wiz in self:
            lims_order = wiz.order_id
            if not wiz.upload:
                raise UserError(_("Please upload a file before creating a document."))

            attachment = Attachment.create(
                {
                    "name": wiz.filename or wiz.name,
                    "datas": wiz.upload,
                    "res_model": "lims.order",
                    "res_id": lims_order.id,
                    "type": "binary",
                    "mimetype": False,
                }
            )

            Document.create(
                {
                    "name": wiz.name,
                    "folder_id": False,
                    "owner_id": wiz.env.user.partner_id.id,
                    "res_model": "lims.order",
                    "res_id": lims_order.id,
                    "attachment_id": attachment.id,
                    "description": wiz.description,
                }
            )

        return {"type": "ir.actions.act_window_close"}
