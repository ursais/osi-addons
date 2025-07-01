class ONLTemplate:
    def product_templates(self):
        return self.env['product.template'].search([("has_configurable_attributes", "=", True)])