# Import module files
from . import models
from . import wizard

# Import Python libs
import logging
from datetime import datetime

# Import Odoo libs
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def _run_install_scripts(env):
    _set_system_stock_state(env)


def _set_system_stock_state(env):
    """
    We want to set the initial values for Portfolio Systems when we install this module
    """
    # NOTE: be careful when using the SUPERUSER_ID! Use the appropriate user when doing this
    env = api.Environment(env.cr, SUPERUSER_ID, {})

    onlogic_companies = env["res.company"].get_all().sorted(key=lambda c: c.id)

    for company in onlogic_companies:
        start_time = datetime.now()
        env = api.Environment(env.cr, company.company_user_id.id, {})

        # Get Portfolio Systems
        portfolio_systems = (
            env["product.template"]
            .search(
                [
                    ("has_configurable_attributes", "=", True),
                    ("system_tier", "=", "normal"),
                ]
            )
            .filtered(lambda s: not s.system_stock_state)
        )

        _logger.info(
            f"[{company.short_name.upper()}] START Set initial `System Stock State` value for"
            f" {len(portfolio_systems)} Portfolio systems"
        )

        # Update the records `system_stock_state` field if necessary
        updated_portfolios, data = portfolio_systems.with_context(
            skip_webhooks=True
        ).update_system_stock_state()

        _logger.info(
            f"[{company.short_name.upper()}] Done Set initial `System Stock State` value for"
            f" {len(portfolio_systems)} Portfolio systems. {len(updated_portfolios)} records updated in:"
            f" {datetime.now() - start_time}s"
        )
