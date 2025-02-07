# Import Odoo libs
from odoo.addons.ls_product_configurator.tests.common import OnLogicProductConfiguratorSavepointCase


class TestTravelerLogic(OnLogicProductConfiguratorSavepointCase):
    """
    Test the logic behind gathering the information for the traveler
    """

    def setUp(self):
        """ Setup the test cases """
        super(TestTravelerLogic, self).setUp()

        self.k300_variant = self.k300_template._create_product_variant_qty(self.good_combination)
        self.assertTrue(self.k300_variant.exists(), 'No variant was created')

        self.k300_bom = self.env['mrp.bom']._bom_find(product=self.k300_variant)
        self.assertTrue(self.k300_bom.exists(), 'No variant BoM was created')

        # Remove all demo checks so we can set up better tests
        self.env['mrp.assembly.check'].search([]).unlink()
        self.assertFalse(self.env['mrp.assembly.check'].search([]), 'No checks should be present')

        any_old_product = self.env.ref('ls_base.mc500g')
        self.test_bom = self.env['mrp.bom'].create(
            {'product_tmpl_id': any_old_product.product_tmpl_id.id, 'product_id': any_old_product.id}
        )

        self.test_stage = self.env['mrp.assembly.stage'].create({'name': 'UNIT TEST STAGE'})
        self.test_classification = self.env['product.attribute.classification'].create(
            {'name': 'TEST CLASSIFICATION', 'stage_id': self.test_stage.id}
        )

    def test_get_traveler_info(self):
        """
        Test the data aggregation for the traveler
        """
        # Make sure all the right stages are there if there are no bom lines
        # stages marked as present even if empty, or some specific stages which are always added
        always_stages = self.env['mrp.assembly.stage'].search(
            [
                '|',
                '|',
                '|',
                ('show_when_empty', '=', True),
                ('name', '=', 'Operating System'),
                ('name', '=', 'BIOS'),
                ('id', '=', self.env.ref('ls_mrp_traveler.standard_work_stage').id),
            ]
        )
        traveler_dict = dict(self.test_bom.get_traveler_info())
        traveler_stages = self.env['mrp.assembly.stage']
        for key in traveler_dict.keys():
            traveler_stages |= key
        self.assertEqual(
            always_stages,
            traveler_stages,
            'Only "show_when_empty" stages and OS/BIOS/Std Work stages should be showing for empty BoM',
        )
        for key, info in traveler_dict.items():
            self.assertFalse(info.get('input_checks'), 'No input checks should be present yet')
            self.assertFalse(info.get('output_checks'), 'No output checks should be present yet')
            self.assertFalse(info.get('notes'), 'No notes should be present yet')
            self.assertFalse(info.get('lines'), 'No bom lines should be present yet')

        # Add a bom line and make sure it shows up in the right spot
        self.test_bom.write(
            {
                'bom_line_ids': [
                    (
                        0,
                        0,
                        {
                            'product_id': self.env.ref('ls_base.e3930_p').id,
                            'classification_id': self.test_classification.id,
                        },
                    )
                ]
            }
        )
        first_bom_line = self.test_bom.bom_line_ids
        traveler_dict = dict(self.test_bom.get_traveler_info())
        traveler_stages = self.env['mrp.assembly.stage']
        for key in traveler_dict.keys():
            traveler_stages |= key
        expected_stages = always_stages | self.test_stage
        self.assertEqual(
            expected_stages,
            traveler_stages,
            'New stage should be included',
        )
        # make sure all the other stages are still empty
        for key, info in traveler_dict.items():
            if key == self.test_stage:
                self.assertEqual(info.get('lines'), first_bom_line, 'BoM line was not added to traveler dict')
            else:
                self.assertFalse(info.get('lines'), 'No bom lines should be present yet')

            self.assertFalse(info.get('input_checks'), 'No input checks should be present yet')
            self.assertFalse(info.get('output_checks'), 'No output checks should be present yet')
            self.assertFalse(info.get('notes'), 'No notes should be present yet')

        # Add another bom line in the same place and make sure it shows up in the right spot
        self.test_bom.write(
            {
                'bom_line_ids': [
                    (
                        0,
                        0,
                        {
                            'product_id': self.env.ref('ls_base.ml210g_case').id,
                            'classification_id': self.test_classification.id,
                        },
                    )
                ]
            }
        )
        second_bom_line = self.test_bom.bom_line_ids - first_bom_line
        traveler_dict = dict(self.test_bom.get_traveler_info())
        traveler_stages = self.env['mrp.assembly.stage']
        for key in traveler_dict.keys():
            traveler_stages |= key
        self.assertEqual(
            expected_stages,
            traveler_stages,
            'New stage should still be included',
        )
        # make sure all the other stages are still empty
        for key, info in traveler_dict.items():
            if key == self.test_stage:
                self.assertEqual(
                    info.get('lines'),
                    first_bom_line | second_bom_line,
                    'BoM lines were not added to traveler dict',
                )
            else:
                self.assertFalse(info.get('lines'), 'No bom lines should be present yet')

            self.assertFalse(info.get('input_checks'), 'No input checks should be present yet')
            self.assertFalse(info.get('output_checks'), 'No output checks should be present yet')
            self.assertFalse(info.get('notes'), 'No notes should be present yet')

        # Add custom work sku and make sure that shows up in the right spot
        self.test_bom.write(
            {
                'bom_line_ids': [
                    (
                        0,
                        0,
                        {
                            'product_id': self.env.ref('ls_base.custom_work_instructions_service').id,
                            'classification_id': self.env.ref(
                                'ls_product_classification.hidden_classification'
                            ).id,
                        },
                    )
                ]
            }
        )
        self.test_bom.product_id.work_documentation_url = 'http://www.justdo.it/'
        custom_work_bom_line = self.test_bom.bom_line_ids - (first_bom_line | second_bom_line)
        traveler_dict = dict(self.test_bom.get_traveler_info())
        traveler_stages = self.env['mrp.assembly.stage']
        for key in traveler_dict.keys():
            traveler_stages |= key
        custom_work_stage = self.env.ref('ls_mrp_traveler.custom_work_stage')
        expected_stages -= self.env.ref('ls_mrp_traveler.standard_work_stage')
        expected_stages += custom_work_stage
        self.assertEqual(
            expected_stages,
            traveler_stages,
            'New stage should be included',
        )
        # make sure all the other stages are still empty, but custom work should be present
        for key, info in traveler_dict.items():
            if key == self.test_stage:
                self.assertEqual(
                    info.get('lines'),
                    first_bom_line | second_bom_line,
                    'BoM line was not added to traveler dict',
                )
            elif key == custom_work_stage:
                self.assertEqual(
                    info.get('documentation'),
                    self.test_bom.product_id.work_documentation_url,
                    'Documentation URL was not set',
                )
            else:
                self.assertFalse(info.get('lines'), 'No bom lines should be present yet')

            self.assertFalse(info.get('input_checks'), 'No input checks should be present yet')
            self.assertFalse(info.get('output_checks'), 'No output checks should be present yet')
            self.assertFalse(info.get('notes'), 'No notes should be present yet')

        # Add custom BIOS sku and make sure that shows up in the right spot
        self.test_bom.write(
            {
                'bom_line_ids': [
                    (
                        0,
                        0,
                        {
                            'product_id': self.env.ref('ls_base.custom_bios_service').id,
                            'classification_id': self.env.ref(
                                'ls_product_classification.hidden_classification'
                            ).id,
                        },
                    )
                ]
            }
        )
        self.test_bom.product_id.bios_name = 'super_special_custom_bios.txt'
        custom_bios_line = self.test_bom.bom_line_ids - (
            first_bom_line | second_bom_line | custom_work_bom_line
        )

        traveler_dict = dict(self.test_bom.get_traveler_info())
        traveler_stages = self.env['mrp.assembly.stage']
        for key in traveler_dict.keys():
            traveler_stages |= key

        self.assertEqual(
            expected_stages,
            traveler_stages,
            'New stage should be included',
        )
        bios_stage = self.env.ref('ls_product_classification.bios_classification').stage_id
        # make sure all the other stages are still empty, but custom work should be present
        for key, info in traveler_dict.items():
            if key == self.test_stage:
                self.assertEqual(
                    info.get('lines'),
                    first_bom_line | second_bom_line,
                    'BoM line was not added to traveler dict',
                )
            elif key == custom_work_stage:
                self.assertEqual(
                    info.get('documentation'),
                    self.test_bom.product_id.work_documentation_url,
                    'Documentation URL was not set',
                )
            elif key == bios_stage:
                self.assertEqual(
                    info.get('bios_name'), self.test_bom.product_id.bios_name, 'BIOS name was not set'
                )
            else:
                self.assertFalse(info.get('lines'), 'No bom lines should be present yet')

            self.assertFalse(info.get('input_checks'), 'No input checks should be present yet')
            self.assertFalse(info.get('output_checks'), 'No output checks should be present yet')
            self.assertFalse(info.get('notes'), 'No notes should be present yet')

    def test_check_aggregation(self):
        """
        Test gathering checks for a given stage and products
        """

        check_obj = self.env['mrp.assembly.check']

        stage = self.env.ref('ls_mrp_traveler.seat_2_stage')
        classification = self.env.ref('ls_product_classification.case_classification')
        line_products = self.env.ref('ls_base.e3930_p')
        all_products = line_products | self.env.ref('ls_base.ts32gmts800')

        self.assertNotEqual(
            stage, classification.stage_id, 'Test stage and test classification should not be the same'
        )

        all_checks = check_obj.get_all_checks(stage, classification, line_products, all_products)
        self.assertFalse(all_checks, 'No checks should match')

        # Add a check that's only for this stage
        stage_check = check_obj.create(
            {
                'name': 'STAGE ONLY CHECK',
                'stage_id': stage.id,
                'type': 'note',
                'priority': 1,
                'text': 'NOTE TEXT',
            }
        )
        # and one for a different stage only
        stage_check.copy({'stage_id': classification.stage_id.id})

        all_checks = check_obj.get_all_checks(stage, classification, line_products, all_products)
        expected = stage_check
        self.assertEqual(expected, all_checks, 'Only matching stage checks should match')

        # Add a check that is for this stage and for a product in it
        product_stage_check = check_obj.create(
            {
                'name': 'PRODUCT+STAGE CHECK',
                'stage_id': stage.id,
                'type': 'input',
                'priority': 1,
                'text': 'product and stage together',
            }
        )
        # Same product, different stage
        product_stage_check.copy({'stage_id': classification.stage_id.id})
        all_checks = check_obj.get_all_checks(stage, classification, line_products, all_products)
        expected |= product_stage_check
        self.assertEqual(expected, all_checks, 'Product+stage check should now be included')

        # Add a check that is for this stage and for one of the given classifications
        classification_stage_check = check_obj.create(
            {
                'name': 'CLASSIFICATION+STAGE CHECK',
                'stage_id': stage.id,
                'type': 'output',
                'priority': 1,
                'text': 'classification and stage together',
            }
        )
        # Same classification, different stage
        classification_stage_check.copy({'stage_id': classification.stage_id.id})
        all_checks = check_obj.get_all_checks(stage, classification, line_products, all_products)
        expected |= classification_stage_check
        self.assertEqual(expected, all_checks, 'Classification+stage check should now be included')

        # Add checks that are for this line's products, but do not have a stage
        product_only_check = check_obj.create(
            {
                'name': 'PRODUCT ONLY CHECK',
                'stage_id': False,
                'type': 'both',
                'priority': 1,
                'text': 'only product, no stage',
                'product_ids': [(4, line_products.id)],
            }
        )
        template_only_check = product_only_check.copy(
            {'product_ids': [], 'template_ids': [(4, line_products.product_tmpl_id.id)]}
        )
        # make copies for other products in this 'bom' and ones outside it
        product_only_check.copy({'product_ids': [(4, p.id) for p in all_products - line_products]})
        product_only_check.copy({'product_ids': [(4, self.env.ref('ls_base.mc500g').id)]})
        template_only_check.copy({'template_ids': [(4, p.id) for p in all_products - line_products]})
        template_only_check.copy({'template_ids': [(4, self.env.ref('ls_base.mc500g').id)]})

        all_checks = check_obj.get_all_checks(stage, classification, line_products, all_products)
        expected |= product_only_check | template_only_check
        self.assertEqual(expected, all_checks, 'Product and template only checks should now be included')

        # Add check that is for a classification in the BoM, but not a stage
        classification_only_check = check_obj.create(
            {
                'name': 'CLASSIFICATION ONLY CHECK',
                'stage_id': False,
                'type': 'both',
                'priority': 1,
                'text': 'only classification, no stage',
                'classification_id': classification.id,
            }
        )

        # make a copy for a classification not in the list
        classification_only_check.copy(
            {'classification_id': self.env.ref('ls_product_classification.ac_adapter_classification').id}
        )
        all_checks = check_obj.get_all_checks(stage, classification, line_products, all_products)
        expected |= classification_only_check
        self.assertEqual(expected, all_checks, 'Product and template only checks should now be included')
