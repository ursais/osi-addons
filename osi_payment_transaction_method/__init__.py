# Copyright (C) 2024 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from . import models

def post_init_hook(cr, registry):
    """Post-init hook entry point."""
    from .models.payment_transaction_post_init_hook import post_init_hook as _post_init_hook
    _post_init_hook(cr, registry)
