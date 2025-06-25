# Import Python libs
import json
import hmac
import hashlib

# Import Odoo libs
from odoo import models


class API(models.Model):
    _name = "api"
    _description = "API"

    def generate_hmac_signature(self, key, data):
        """
        Generate a HMAC hash based on the webhook data and secret
        """
        data_string = json.dumps(data, indent=None, separators=(",", ":"))
        hmac_obj = hmac.new(key.encode("utf-8"), data_string.encode("utf-8"), hashlib.sha256)
        return hmac_obj.hexdigest()
