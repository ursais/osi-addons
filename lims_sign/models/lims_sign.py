import uuid

from odoo import Command, _, fields, models
from odoo.exceptions import UserError


class LimsOrder(models.Model):
    _inherit = "lims.order"

    sign_request_ids = fields.One2many(
        "sign.request", "lims_order_id", string="Signature Requests"
    )
    sign_request_count = fields.Integer(
        compute="_compute_sign_request_count", string="Sign Requests"
    )

    def _compute_sign_request_count(self):
        for rec in self:
            rec.sign_request_count = len(rec.sign_request_ids)

    def _generate_uuid(self):
        return str(uuid.uuid4())

    def action_send_for_signature(self):
        """Send unsigned LIMS documents for signature using Odoo Sign internals."""
        Documents = self.env["documents.document"]
        SignTemplate = self.env["sign.template"]

        for rec in self:
            docs_to_sign = Documents.search(
                [
                    ("res_model", "=", rec._name),
                    ("res_id", "=", rec.id),
                ]
            )
            if not docs_to_sign:
                raise UserError(_("No documents found for this LIMS order."))

            partner = rec.partner_id or rec.company_id.partner_id
            if not partner:
                raise UserError(_("No partner found for this LIMS order."))

            for doc in docs_to_sign:
                if not doc.attachment_id:
                    raise UserError(
                        _("Document %s has no attachment to sign.") % doc.name
                    )

                attachment_copy = doc.attachment_id.copy(
                    {"res_model": False, "res_id": False}
                )
                template = SignTemplate.create(
                    {
                        "name": f"LIMS Template - {doc.name}",
                        "attachment_id": attachment_copy.id,
                        "active": False,
                    }
                )

                roles = template.sign_item_ids.mapped("responsible_id")
                request_items = []
                if roles:
                    for default_order, role in enumerate(roles):
                        request_items.append(
                            Command.create(
                                {
                                    "partner_id": partner.id,
                                    "role_id": role.id
                                    or self.env.ref("sign.sign_item_role_default").id,
                                    "mail_sent_order": default_order + 1,
                                }
                            )
                        )
                else:
                    default_role = self.env.ref("sign.sign_item_role_default")
                    request_items.append(
                        Command.create(
                            {
                                "partner_id": partner.id,
                                "role_id": default_role.id,
                                "mail_sent_order": 1,
                            }
                        )
                    )

                SignRequest = self.env["sign.request"]
                sign_request = SignRequest.create(
                    {
                        "template_id": template.id,
                        "request_item_ids": request_items,
                        "reference": doc.name,
                        "subject": f"Signature request - {doc.name}",
                        "attachment_ids": [Command.set([attachment_copy.id])],
                        "message": False,
                    }
                )

                sign_request.sudo().write(
                    {
                        "lims_order_id": rec.id,
                        "access_token": self._generate_uuid(),
                        "reference": doc.name,
                    }
                )

            rec.message_post(body=_("Documents sent for signature."))

    def action_view_sign_requests(self):
        self.ensure_one()
        action = self.env.ref("sign.sign_request_action", False)
        result = action.read()[0]
        result["domain"] = [("lims_order_id", "=", self.id)]
        result["context"] = {"default_lims_order_id": self.id}
        return result
