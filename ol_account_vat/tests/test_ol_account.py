from odoo.tests import common, tagged


@tagged("-at_install", "post_install")
class TestAccountFiscalPosition(common.TransactionCase):
    @classmethod
    def setUpClass(self):
        super().setUpClass()

        self.company = self.env.company
        self.country = self.company.country_id
        self.netherlands = self.env.ref("base.nl")

        # Partner with same country as the company (domestic)
        self.partner = self.env["res.partner"].create(
            {
                "name": "Test Domestic Partner",
                "country_id": self.country.id,
            }
        )
        self.partner2 = self.env["res.partner"].create(
            {
                "name": "Test Non - Domestic Partner",
                "country_id": self.netherlands.id,
            }
        )

        self.fiscal_ids = self.env["account.fiscal.position"].search(
            [("country_id", "=", self.country.id)]
        )
        self.fiscal_ids.active = False
        # Create fiscal positions, one that should be excluded
        self.fp_included = self.env["account.fiscal.position"].create(
            {
                "name": "Domestic - Include",
                "company_id": self.company.id,
                "country_id": self.country.id,
                "auto_apply": True,
                "ignore_for_domestic_deliveries": False,
            }
        )

        self.fp_ignored = self.env["account.fiscal.position"].create(
            {
                "name": "Domestic - Ignore",
                "company_id": self.company.id,
                "country_id": self.country.id,
                "auto_apply": True,
                "ignore_for_domestic_deliveries": True,
            }
        )

        self.fp_non_domestic = self.env["account.fiscal.position"].create(
            {
                "name": "Foreign - Include",
                "company_id": self.company.id,
                "country_id": self.netherlands.id,
                "auto_apply": True,
                "ignore_for_domestic_deliveries": True,
            }
        )

    def test_get_fiscal_position_domestic_without_ignore(self):
        """
        Should return only the fiscal position with ignore_for_domestic_deliveries=False
        when the partner is domestic.
        """
        fiscal_position = self.env["account.fiscal.position"]._get_fiscal_position(
            self.partner
        )

        self.assertTrue(fiscal_position, "Fiscal position should be returned")
        self.assertNotEqual(
            fiscal_position, self.fp_ignored, "Ignored FP should not be returned"
        )
        self.assertEqual(
            fiscal_position, self.fp_included, "Included FP should be returned"
        )

        fiscal_position = self.env["account.fiscal.position"]._get_fiscal_position(
            self.partner2
        )

        self.assertTrue(fiscal_position, "Fiscal position should be returned")
        self.assertEqual(
            fiscal_position,
            self.fp_non_domestic,
            "Non-domestic FP should be returned regardless of ignore_for_domestic_deliveries",
        )
