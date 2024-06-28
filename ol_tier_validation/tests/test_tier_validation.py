# Import Odoo libs
from odoo.tests import common, tagged
from odoo.exceptions import ValidationError


@tagged("-at_install", "post_install")
class TestProductTierValidation(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_user_1 = cls.env.ref("ol_tier_validation.res_user_john_doe")
        cls.tier_def_obj = cls.env["tier.definition"]

    def test_create_tier_definition_without_permissions(self):
        """
        Ensure users with permission can't create certain tier_definition fields
        User Error should be returned
        """
        # Create tier definition with python_code
        # Should return user error
        with self.assertRaises(ValidationError):
            self.tier_def_obj.with_user(self.test_user_1).create({
                'name': 'Tier Definition 1',
                'python_code': "#Testing Create python_code"
            })

        # Create tier definition with reviewer_expression
        # Should return user error
        with self.assertRaises(ValidationError):
            self.tier_def_obj.with_user(self.test_user_1).create({
                'name': 'Tier Definition 2',
                'reviewer_expression': "#Testing Create reviewer_expression"
            })

        # Create tier definition with neither
        # Should not return user error
        try:
            self.tier_def_obj.with_user(self.test_user_1).create({
                'name': 'Tier Definition 3',
            })
        except ValidationError:
            self.fail("create() raised ValidationError unexpectedly!")

    def test_write_tier_definition_without_permissions(self):
        """
        Ensure users with permission can't edit certain tier_definition fields
        """
        # Write tier definition with python_code
        # Should return user error
        with self.assertRaises(ValidationError):
            self.tier_def_obj.with_user(self.test_user_1).write({
                'python_code': '#Test Write python_code',
            })
        
        # Write tier definition with reviewer_expression
        # Should return user error
        with self.assertRaises(ValidationError):
            self.tier_def_obj.with_user(self.test_user_1).write({
                'reviewer_expression': '#Test Write reviewer_expression',
            })
        
        # write tier definition with neither
        # Should not return user error
        try:
            self.tier_def_obj.with_user(self.test_user_1).write({
                'name': 'Tier Definition 3 - Edit name',
            })
        except ValidationError:
            self.fail("write() raised ValidationError unexpectedly!")

    def test_create_tier_definition_with_permissions(self):
        """
        Ensure users with permission can create certain tier_definition fields
        """
        self.test_user_1.write({"groups_id": [(4, self.env.ref("ol_tier_validation.group_tier_validation_python").id)]})
        
        # Create tier definition with python_code
        # Should not return user error
        try:
            self.tier_def_obj.with_user(self.test_user_1).create({
                'name': 'Tier Definition 1',
                'python_code': "#Testing 1"
            })
        except ValidationError:
            self.fail("create() raised ValidationError unexpectedly on python_code!")

        # Create tier definition with reviewer_expression
        # Should not return user error
        try:
            self.tier_def_obj.with_user(self.test_user_1).create({
                'name': 'Tier Definition 2',
                'reviewer_expression': "#Testing 2"
            })
        except ValidationError:
            self.fail("create() raised ValidationError unexpectedly on reviewer_expression!")

        # Create tier definition with neither
        # Should not return user error
        try:
            self.tier_def_obj.with_user(self.test_user_1).create({
                'name': 'Tier Definition 3',
            })
        except ValidationError:
            self.fail("create() raised ValidationError unexpectedly on name!")

    def test_write_tier_definition_with_permissions(self):
        """
        Ensure users with permission can edit certain tier_definition fields
        """
        self.test_user_1.write({"groups_id": [(4, self.env.ref("ol_tier_validation.group_tier_validation_python").id)]})

        # Write tier definition with python_code
        # Should not return user error
        try:
            self.tier_def_obj.with_user(self.test_user_1).write({
                'field_name': 'field_value',
            })
        except ValidationError:
            self.fail("write() raised ValidationError unexpectedly on python_code!")
        
        # Write tier definition with reviewer_expression
        # Should not return user error
        try:
            self.tier_def_obj.with_user(self.test_user_1).write({
                'field_name': 'field_value',
            })
        except ValidationError:
            self.fail("write() raised ValidationError unexpectedly on reviewer_expression!")
        
        # Write tier definition with name
        # Should not return user error
        try:
            self.tier_def_obj.with_user(self.test_user_1).write({
                'name': 'Tier Definition 3 - Edit',
            })
        except ValidationError:
            self.fail("create() raised ValidationError unexpectedly on name!")
