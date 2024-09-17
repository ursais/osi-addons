# Import Odoo libs
from odoo.exceptions import ValidationError
from odoo.addons.product_configurator.tests.test_product_configurator_test_cases import (
    ProductConfiguratorTestCases,
)


class TestMRPBOMRebuild(ProductConfiguratorTestCases):

    # Set up the test environment, configuring necessary models and data
    def setUp(self):
        # Call the parent class's setUp method
        super().setUp()
        # Initialize MRP BoM and BoM Line models for later use
        self.mrpBom = self.env["mrp.bom"]
        self.mrpBomLine = self.env["mrp.bom.line"]
        # Configure a product used in the test (through inherited method)
        self._configure_product_nxt_step()
        # Assign the configured product template to product_tmpl_id
        self.product_tmpl_id = self.config_product

    # Test the resetting of variant BoM when 'scaffolding_bom' is set to False
    def test01_reset_variant_bom_with_scaffold_bom(self):
        # Create a BoM record with scaffolding_bom set to False
        self.bom_id = self.mrpBom.create(
            {
                "product_tmpl_id": self.product_tmpl_id.id,
                "scaffolding_bom": False,
                "product_qty": 1.00,
                "type": "normal",
                "ready_to_produce": "all_available",
            }
        )
        # Call the method to reset all variant BoMs using the scaffold BoM
        self.bom_id.product_tmpl_id._reset_all_variants_bom_with_scaffold_bom()

    # Test the behavior of copying a BoM with 'scaffolding_bom' set to True
    def test02_reset_variant_bom_with_scaffold_bom(self):
        # Create a BoM record with scaffolding_bom set to True
        self.bom_id = self.mrpBom.create(
            {
                "product_tmpl_id": self.product_tmpl_id.id,
                "scaffolding_bom": True,
                "product_qty": 1.00,
                "type": "normal",
                "ready_to_produce": "all_available",
            }
        )
        # Assert that attempting to copy the BoM raises a ValidationError
        with self.assertRaises(ValidationError):
            self.bom_id.copy()

    # Test the onchange method for the 'scaffolding_bom' field and product_id
    def test03_onchange_scaffolding_bom_product_id(self):
        # Create a BoM record with default 'scaffolding_bom' value (False)
        self.bom_id = self.mrpBom.create(
            {
                "product_tmpl_id": self.product_tmpl_id.id,
                "product_qty": 1.00,
                "type": "normal",
                "ready_to_produce": "all_available",
            }
        )
        # Assert that the default value for scaffolding_bom is False
        self.assertFalse(self.bom_id.scaffolding_bom)
        # Trigger the onchange method for the 'scaffolding_bom' field
        self.bom_id.onchange_scaffolding_bom_product_id()
        # Assert that the value for scaffolding_bom is now True after the onchange
        self.assertTrue(self.bom_id.scaffolding_bom)
