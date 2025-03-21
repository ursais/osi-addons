from odoo.tests import common, tagged

from odoo.addons.base.tests.common import DISABLED_MAIL_CONTEXT


@tagged("-at_install", "post_install")
class TestProductStateOlValidation(common.TransactionCase):
    """
    Test case to validate the display name of a product reporting system in Odoo.

    This test checks that the `display_name` of a `product.reporting.system` record is
    correctly constructed from its related `product.reporting.category`,
    `product.reporting.line`, and `product.reporting.series` records in the correct format:
    "Category A/Line A/Series A/System A".

    The test setup creates necessary records:
        - A `product.reporting.category` named "Category A".
        - A `product.reporting.line` named "Line A", associated with the category.
        - A `product.reporting.series` named "Series A", associated with the line.
        - A `product.reporting.system` named "System A", associated with the series.

    The test validates that the `display_name` of the `product.reporting.system` record
    is as expected, ensuring the correct concatenation of these names.

    This test case runs after the installation of the module, as indicated by the
    `@tagged("-at_install", "post_install")` decorator.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.category = cls.env["product.reporting.category"].create(
            {"name": "Category A"}
        )
        cls.line = cls.env["product.reporting.line"].create(
            {"name": "Line A", "category_id": cls.category.id}
        )
        cls.series = cls.env["product.reporting.series"].create(
            {"name": "Series A", "line_id": cls.line.id}
        )
        cls.system = cls.env["product.reporting.system"].create(
            {"name": "System A", "series_id": cls.series.id}
        )

    def test_display_name(self):
        self.assertEqual(
            self.system.display_name, "Category A/Line A/Series A/System A"
        )
