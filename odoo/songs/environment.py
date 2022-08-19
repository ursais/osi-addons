# Copyright (c) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
import os

import anthem
from anthem.lyrics.records import create_or_update


@anthem.log
def reset_queue_jobs(ctx):
    """Reset Queue Jobs"""
    jobs = ctx.env["queue.job"].search([("state", "in", ["started", "enqueued"])])
    jobs.write({"state": "pending"})


@anthem.log
def setup_admin_user(ctx):
    """Setup Admin User"""
    admin = ctx.env.ref("base.user_admin")
    admin.write(
        {
            "new_password": os.environ.get("ODOO_ADMIN_USER_PASSWORD"),
            "tz": os.environ.get("ODOO_ADMIN_USER_TIMEZONE"),
        }
    )
    admin._set_new_password()


@anthem.log
def set_mail_server(ctx):
    """Set Mail Server"""
    if os.getenv("RUNNING_ENV") != "production":
        mailhog = create_or_update(
            ctx,
            "ir.mail_server",
            "__setup__.ir_mail_server_mailhog",
            {
                "name": "MailHog",
                "smtp_host": os.environ.get("ODOO_SMTP_SERVER", "mail"),
                "smtp_port": os.environ.get("ODOO_SMTP_PORT", 25),
            },
        )
        try:
            mailhog.test_smtp_connection()
        except Exception as exception:
            ctx.log_line("Test SMTP connection to MailHog: %s" % str(exception))


@anthem.log
def set_ribbon(ctx):
    """Set Ribbon"""
    if os.getenv("RUNNING_ENV") != "production":
        background = ctx.env["ir.config_parameter"].search(
            [("key", "=", "ribbon.background.color")]
        )
        background.value = "rgba(0,128,0,.6)"
        color = ctx.env["ir.config_parameter"].search([("key", "=", "ribbon.color")])
        color.value = "#f0f0f0"
        name = ctx.env["ir.config_parameter"].search([("key", "=", "ribbon.name")])
        name.value = os.getenv("RUNNING_ENV").upper() + "<br/>({db_name})"


@anthem.log
def set_version(ctx):
    """Set in the database"""
    create_or_update(
        ctx,
        "ir.config_parameter",
        "__setup__.ir_database_version",
        {"key": "database.version", "value": os.getenv("VERSION", "setup")},
    )


@anthem.log
def main(ctx):
    """Environment"""
    setup_admin_user(ctx)
    set_mail_server(ctx)
    set_ribbon(ctx)
    #    reset_queue_jobs(ctx)
    set_version(ctx)
