# Import Python libs
import logging
from werkzeug.utils import secure_filename

_logger = logging.getLogger(__name__)

# Import Odoo libs
from odoo import fields, models, api
from odoo.exceptions import ValidationError


class ReportExtraContent(models.Model):
    _name = 'report.extra.content'
    _description = 'Report Extra Content'
    _order = "priority"

    # COLUMNS #####
    pdf = fields.Binary(string='PDF', required=True, help="The PDF file to be appended to the reports")
    pdf_filename = fields.Char(string='PDF filename', help="Name of the uploaded PDF file")
    priority = fields.Integer(
        string='Priority',
        help=(
            "This defines in which order these Extra PDF Contents will be appended to the Reports. Lower"
            " number is higher priority."
        ),
    )
    name = fields.Char(string='Name')
    report_ids = fields.Many2many(
        comodel_name='ir.actions.report',
        relation='report_report_extra_content_rel',
        column1='extra_content_id',
        column2='report_id',
        string='Reports',
        help='The Reports that this content will be added to.',
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        change_default=True,
        string='Company',
        readonly=True,
        required=True,
        default=lambda self: self.env['res.company']._company_default_get('stock.quant'),
        help='The company to which this record belongs to',
    )
    # END #########
