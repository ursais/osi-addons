# Copyright (C) 2020 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.mrp.tests.common import TestMrpCommon


class TestMrpReportBomStructure(TestMrpCommon):
    def test_get_bom_lines(self):
        report_1 = self.env["report.mrp.report_bom_structure"]
        line_ids = self.bom_1.bom_line_ids
        for line in line_ids:
            line.designator = "designator" + str(line.id)
        components, total = report_1._get_bom_lines(
            self.bom_1, 1, self.product_4, self.bom_1.bom_line_ids, 1
        )
        for dictionary in components:
            line_id = line_ids.search([("id", "=", dictionary["line_id"])])
            self.assertEquals(line_id.designator, dictionary["designator"])

    def test_get_pdf_line(self):
        report_1 = self.env["report.mrp.report_bom_structure"]
        line_ids = self.bom_1.bom_line_ids
        for line in line_ids:
            line.designator = "designator" + str(line.id)
        data = report_1._get_pdf_line(self.bom_1.id, self.product_4, 1)
        # loop through every line but the last("operations")
        for index in range(len(data["lines"]) - 1):
            self.assertTrue("designator" in data["lines"][index])
