# Import Odoo libs
from odoo import models


class IrConfigParameter(models.Model):
    _inherit = "ir.config_parameter"

    def get_as_boolean(self, key, default=False):
        """
        Evaluate the saved value as a boolean
        """
        result = self.get_param(key, default)
        if isinstance(result, bool):
            # If the result is already a boolean just return it
            return result
        # Evaluate result if it's a string
        return result.lower() == "true"
