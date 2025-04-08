from odoo import models


class MailTemplate(models.Model):
    _inherit = "mail.template"

    def send_email_with_terms_and_conditions(
        self,
        company,
        res_id,
        force_send=False,
        raise_exception=False,
        email_values=None,
        notif_layout=False,
    ):
        """
        Find and set the T&C attachments for the template
        Replicates the core `send_email()` function signature and calls it
        with updated attachments
        """
        if not company:
            # If by some error the SO did not have a company set on it we
            # want to set a default value.
            # For this we assume that the currently logged in user
            # can only manage Sale Orders that have the same company as him
            company = self.env.company

        # These are the normal attachments for this email
        non_tc_attachment_ids = self.attachment_ids.sudo().filtered(
            lambda att: att.description != "company_terms_and_conditions_document"
        )

        # Find the current T&C document attached to the SO company
        # we handle that on the attachment import `import_tc_pdf_wizard.py`
        tc_attachment = self.env["ir.attachment"].search(
            [
                ("res_model", "=", "res.company"),
                ("res_id", "=", company.id),
                ("company_id", "=", company.id),
                ("description", "=", "company_terms_and_conditions_document"),
            ],
            limit=1,
        )

        # Override the attachements by adding the Ts & Cs attachment to the
        # existing ones
        if not email_values:
            email_values = {}

        email_values["attachment_ids"] = [
            (4, attach_id) for attach_id in (non_tc_attachment_ids | tc_attachment).ids
        ]

        return self.send_mail(
            res_id,
            force_send=force_send,
            raise_exception=raise_exception,
            email_values=email_values,
            email_layout_xmlid=notif_layout,
        )
