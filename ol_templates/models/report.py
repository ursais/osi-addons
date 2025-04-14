# Import Odoo libs
from odoo import api, models, fields


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    # COLUMNS #####

    paperformat_xmlid_base = fields.Char(string="Base name of paper format XML ID")

    # END #########

    @api.model
    def get_paperformat(self):
        """
        Choose the paper format to print the report based on the user's company
        """
        if not self or not self.paperformat_xmlid_base:
            # Super method is @api.model, so support the case where self is empty
            # or if there's no company-specific format to be used
            return super().get_paperformat()

        format_base = self.paperformat_xmlid_base

        # Get the company of the user
        user_company = self.env.company

        # Get the company specific paper format we defined in
        # `ol_templates/report/report_definitions.xml`
        paper_format_obj = None
        if user_company.short_name.lower() == "eu":
            paper_format_obj = self.env.ref(format_base + "_eu", False)
        elif user_company.short_name.lower() == "us":
            paper_format_obj = self.env.ref(format_base + "_us", False)

        if not paper_format_obj:
            # Could not find the xml id given, so default to the super method
            return super().get_paperformat()

        return paper_format_obj
