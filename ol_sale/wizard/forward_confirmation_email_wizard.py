# Import Python libs
import re

# Import Odoo libs
from odoo import api, fields, models


class ForwardConfirmationEmailWizard(models.TransientModel):
    _name = "forward.confirmation.email.wizard"
    _description = "Forward Confirmation Email Wizard"

    # COLUMNS ###
    recipients = fields.Text(string="Recipients", help="Comma separated list of emails")
    text_intro = fields.Text(
        string="Introduction text",
        help="This will get inserted to the start of the email",
    )
    text_body = fields.Text(
        string="Body text", help="This will get inserted before the product list"
    )
    text_closing = fields.Text(
        string="Closing text", help="This will get inserted to end of the email"
    )
    order_id = fields.Many2one(comodel_name="sale.order", string="Sale Order")

    # END #######
    # METHODS ###

    @api.model
    def default_get(self, fields):
        """Pre-load fields in the wizard with existing data"""
        res = super(ForwardConfirmationEmailWizard, self).default_get(fields)

        # set sale order from context
        if (
            self._context
            and self._context.get("active_id")
            and self._context.get("active_model")
        ):
            active_model = self._context["active_model"]
            model = self.env[active_model].browse(self._context["active_id"])
            if active_model == "sale.order":
                # Set existing data as defaults on all fields
                res["order_id"] = model.id

        return res

    def forward_confirmation_email(self):
        """
        Send Order confirmation email to they given email addresses
        """

        # Set the sender of the email
        sender = self.env.user.email or self.order_id.company_id.email_formatted

        # Get the formatted recipient email list
        recipients = ",".join(self.get_email_addresses())

        # Get the order confirmation email template
        template = self.env.ref("ol_sale.forward_order_confirmation_email_template")

        # Create and send the email based on the confirmation template immediately
        template.with_context(
            email_from=sender, email_to=recipients, text_intro=self.text_intro
        ).send_email_with_terms_and_conditions(
            self.order_id.company_id, self.order_id.id
        )

        return True

    def get_email_addresses(self):
        """Extract email addresses from the user input"""

        emails = re.findall(r"[\w\.-]+@[\w\.-]+", self.recipients)
        return emails

    # END #######
