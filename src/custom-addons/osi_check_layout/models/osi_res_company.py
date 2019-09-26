# Copyright (C) 2019 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class res_company(models.Model):
    _inherit = "res.company"

    us_check_layout = fields.Selection(string="Check Layout", required=True,
        help="Select the format corresponding to the check paper you will be "
             "printing your checks on.\nIn order to disable the printing "
             "feature, select 'None'.",
        selection=[
            ('disabled', 'None'),
            ('osi_check_layout.action_print_check_top', 'Check on top'),
            ('osi_check_layout.action_print_check_middle', 'Check in middle'),
            ('osi_check_layout.action_print_check_bottom', 'Check on bottom')
        ],
        default="osi_check_layout.action_print_check_bottom")

    us_check_multi_stub = fields.Boolean('Multi-Pages Check Stub',
        help="This option allows you to print check details (stub) on "
             "multiple pages if they don't fit on a single page.",
        default="False")

    us_check_margin_top = fields.Float('Top Margin', default=0.25,
        help="Adjust the margins of generated checks to make it fit your "
             "printer's settings.")

    us_check_margin_left = fields.Float('Left Margin', default=0.25,
        help="Adjust the margins of generated checks to make it fit your "
             "printer's settings.")
