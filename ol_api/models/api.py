# Import Python libs
import json
import hmac
import hashlib

# Import Odoo libs
from odoo import models


class API(models.Model):
    _name = "api"
    _description = "API"

    def generate_hmac_signature(self, key, msg):
        """
        Generate a HMAC hash based on the webhook data and secret
        """
        return hmac.new(
            key=key.encode("utf-8"),
            msg=json.dumps(msg).encode("utf-8"),
            digestmod=hashlib.sha256,
        ).hexdigest()
