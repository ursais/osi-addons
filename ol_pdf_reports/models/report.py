# Import Python libs
from odoo.tools.pdf import PdfFileWriter, PdfFileReader
import base64
from io import BytesIO
import logging

# Import Odoo libs
from odoo import models, fields

_logger = logging.getLogger(__name__)


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    # COLUMNS #####

    extra_content_ids = fields.Many2many(
        comodel_name="report.extra.content",
        relation="report_report_extra_content_rel",
        column1="report_id",
        column2="extra_content_id",
        string="Extra Contents",
        help="Extra contents (Pre Rendered PDFs) that will be added to the end of these reports",
    )

    # END #########

    def _render_qweb_pdf(self, report_ref, res_ids=None, data=None):
        """
        Add the Report Objects to the context so it's accessible later on
        """
        model = (
            self._get_report(report_ref).model or self.model
            or (data and data.get("context").get("active_model"))
        )
        report_objects = self.env[model].browse(res_ids)
        return super(
            IrActionsReport, self.with_context(report_objects=report_objects)
        )._render_qweb_pdf(report_ref, res_ids=res_ids, data=data)

    def _run_wkhtmltopdf(
        self,
        bodies,
        report_ref=False,
        header=None,
        footer=None,
        landscape=False,
        specific_paperformat_args=None,
        set_viewport_size=False,
    ):
        """
        Allow to add extra content to the end of any report
        """

        # Run teh super code to get the original PDF
        original_pdf_content = super()._run_wkhtmltopdf(
            bodies=bodies,
            report_ref=report_ref,
            header=header,
            footer=footer,
            landscape=landscape,
            specific_paperformat_args=specific_paperformat_args,
            set_viewport_size=set_viewport_size,
        )

        report_objects = self.env.context.get("report_objects", False)

        if not report_objects:
            return original_pdf_content

        def get_parsable_object(data):
            # Create a BytesIO object and write the pdf_content into it
            pdf_bytes = BytesIO()
            pdf_bytes.write(data)

            # Rewind the BytesIO object to the beginning
            pdf_bytes.seek(0)

            # Create a PdfFileReader object from the BytesIO object
            return PdfFileReader(pdf_bytes)

        extra_content_ids = self.get_allowed_extra_content_ids(report_objects)

        if extra_content_ids:

            # There are extra contents we need to add

            merger = PdfFileWriter()
            original_pdf_data = get_parsable_object(original_pdf_content)
            # Add the entire original PDF
            merger.append(original_pdf_data)

            for extra_content in extra_content_ids:
                # Append an extra pre-generated PDF to the existing PDF
                try:
                    if extra_content.pdf:
                        extra_pdf_content_data = get_parsable_object(
                            base64.b64decode(extra_content.pdf)
                        )
                        merger.append(extra_pdf_content_data)
                except Exception as error:
                    # We don't want to raise exceptions if the Extra Content has any problems,
                    # instead we just skip it
                    _logger.error(
                        "Could not append Extra Content"
                        f" ({extra_content.name} [{extra_content.pdf_filename}]) to Report {self.name} |"
                        f" Error: {error}"
                    )
                    continue

            # Write to an output PDF document
            output = BytesIO()
            merger.write(output)

            # Get the merged PDF content as bytes
            merged_pdf = output.getvalue()

            # Close the PdfFileWriter
            merger.close()
            return merged_pdf

        return original_pdf_content

    def get_allowed_extra_content_ids(self, report_objects):
        """
        Make sure we only return extra context for the correct companies
        in all places (Odoo UI, Click To Buy etc.).
        """
        report_model_companies = []
        if hasattr(self.env[report_objects._name], "company_id"):
            report_model_companies = report_objects.mapped("company_id.id")

        force_companies = (
            [self.env.context.get("force_company")]
            if "force_company" in self.env.context
            else []
        )
        context_allowed_companies = self.env.context.get("allowed_company_ids", [])
        non_empty_lists = [
            lst
            for lst in [
                report_model_companies,
                force_companies,
                context_allowed_companies,
            ]
            if lst
        ]
        # Convert non-empty lists to sets
        sets = map(set, non_empty_lists)

        # Find the intersection of all non-empty sets
        common_companies = set.intersection(*sets)
        return self.extra_content_ids.filtered(
            lambda ex: ex.company_id.id in common_companies
        )
