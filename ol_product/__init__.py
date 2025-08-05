# Import Python libs
import logging

_logger = logging.getLogger(__name__)

# Import Odoo libs
from . import models
from odoo import api, SUPERUSER_ID


def _post_init_hook_compute_is_kits(env):
    """Post-install hook to compute is_kits for existing templates."""
    templates = env["product.template"].search([])
    templates._compute_is_kits()
    _logger.info(f"Calculating `is_kits` for existing product.templates.")