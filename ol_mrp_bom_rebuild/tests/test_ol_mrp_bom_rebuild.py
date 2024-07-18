# Import Odoo libs
from odoo.exceptions import ValidationError
from odoo.addons.product_configurator.tests.test_product_configurator_test_cases import (
    ProductConfiguratorTestCases,
)

class TestMRPBOMRebuild(ProductConfiguratorTestCases):

    def setUp(self):
        super().setUp()
        self.mrpBom = self.env["mrp.bom"]
        self.mrpBomLine = self.env["mrp.bom.line"]
        self._configure_product_nxt_step()
        self.product_tmpl_id = self.config_product

    def test01_reset_variant_bom_with_master_bom(self):
        self.bom_id = self.mrpBom.create(
            {
                "product_tmpl_id": self.product_tmpl_id.id,
                "scaffolding_bom": False,
                "product_qty": 1.00,
                "type": "normal",
                "ready_to_produce": "all_available",
            }
        )
        self.bom_id.product_tmpl_id._reset_all_variants_bom_with_master_bom()

    def test02_reset_variant_bom_with_master_bom(self):
        self.bom_id = self.mrpBom.create(
            {
                "product_tmpl_id": self.product_tmpl_id.id,
                "scaffolding_bom": True,
                "product_qty": 1.00,
                "type": "normal",
                "ready_to_produce": "all_available",
            }
        )
        with self.assertRaises(ValidationError):
            self.bom_id.copy()

    def test03_onchange_scaffolding_bom_product_id(self):
        self.bom_id = self.mrpBom.create(
            {
                "product_tmpl_id": self.product_tmpl_id.id,
                "product_qty": 1.00,
                "type": "normal",
                "ready_to_produce": "all_available",
            }
        )
        self.assertFalse(self.bom_id.scaffolding_bom)
        self.bom_id.onchange_scaffolding_bom_product_id()
        self.assertTrue(self.bom_id.scaffolding_bom)
