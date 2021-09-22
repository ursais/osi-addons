# Copyright (C) 2021 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import api, fields, models

from odoo.addons.osi_edi_infrastructure.models.ftp import Ftp

_logger = logging.getLogger(__name__)


class EdiProvider(models.Model):
    _name = "edi.provider"
    _description = "EDI Provider"

    name = fields.Char(string="Name")
    com_method = fields.Selection(
        [
            ("none", "None"),
            ("ftp", "FTP"),
        ],
        string="Communication Method",
        default="none",
        copy=False,
    )
    host = fields.Char(string="FTP Host")
    user = fields.Char(string="FTP User")
    password = fields.Char(string="FTP Password")
    new_inbound_messages = fields.Char(string="New Inbound Messages")
    archived_inbound_messages = fields.Char(string="Archived Inbound Messages")
    new_outbound_messages = fields.Char(string="New Outbound Messages")
    archived_outbound_messages = fields.Char(string="Archived Outbound Messages")
    remote_export = fields.Char(string="Remote Export")
    remote_archive = fields.Char(string="Remote Archive")
    remote_import = fields.Char(string="Remote Import")
    archive_remote = fields.Boolean(string="Archive Remote")
    archive_local = fields.Boolean(string="Archive Local")
    mode = fields.Boolean("Test")
    active = fields.Boolean(default=True, help="Set active to false.")

    def toggle_mode(self):
        for c in self:
            c.mode = not c.mode

    def import_data(self):
        for rec in self:
            try:
                # Get default values
                MODE = rec.mode
                ARCHIVE_REMOTE = rec.archive_remote
                ARCHIVE_LOCAL = rec.archive_local
                HOST = rec.host
                USER = rec.user
                PASSWORD = rec.password

                REMOTE_EXPORT = rec.remote_export
                REMOTE_ARCHIVE = rec.remote_archive
                INBOUND_DIR = rec.new_inbound_messages

                # connect to server
                ftp = Ftp(
                    HOST,
                    USER,
                    PASSWORD,
                    mode=MODE,
                    archive_remote=ARCHIVE_REMOTE,
                    archive_local=ARCHIVE_LOCAL,
                )
                # download_files
                if not ftp.download_files(srcpath=REMOTE_EXPORT, dstpath=INBOUND_DIR):
                    print("Error downloading files")

                # clear remote folder for downloaded files
                if MODE and ftp.archive_remote:
                    ftp.move_remote_files(
                        srcpath=INBOUND_DIR,
                        delpath=REMOTE_EXPORT,
                        arcpath=REMOTE_ARCHIVE,
                    )

                ftp.disconnect()

            except Exception as e:
                _logger.error(
                    "Exception while importing data: %s.\n Original Traceback:\n%s",
                    e,
                    Exception,
                )

    @api.model
    def cron_import_data(self):

        providers = self.search([("active", "=", True)])
        for provider in providers:
            try:
                provider.import_data()
            except Exception as e:
                _logger.error(
                    "Exception running EDI FTP Cron: %s.\n Original Traceback:\n%s",
                    e,
                    Exception,
                )

    def export_data(self):
        for rec in self:
            try:
                # Get default values
                MODE = rec.mode
                ARCHIVE_REMOTE = rec.archive_remote
                ARCHIVE_LOCAL = rec.archive_local
                HOST = rec.host
                USER = rec.user
                PASSWORD = rec.password

                REMOTE_IMPORT = rec.remote_import
                OUTBOUND_DIR = rec.new_outbound_messages
                OUTBOUND_ARC = rec.archived_outbound_messages

                # connect to server
                ftp = Ftp(
                    HOST,
                    USER,
                    PASSWORD,
                    mode=MODE,
                    archive_remote=ARCHIVE_REMOTE,
                    archive_local=ARCHIVE_LOCAL,
                )

                # clear remote folder for downloaded files
                if MODE:
                    ftp.move_local_files(
                        dstpath=REMOTE_IMPORT,
                        delpath=OUTBOUND_DIR,
                        arcpath=OUTBOUND_ARC,
                    )

                ftp.disconnect()

            except Exception as e:
                _logger.error(
                    "Exception while exporting data: %s.\n Original Traceback:\n%s",
                    e,
                    Exception,
                )

    @api.model
    def cron_export_data(self):

        providers = self.search([("active", "=", True)])
        for provider in providers:
            try:
                provider.export_data()
            except Exception as e:
                _logger.error(
                    "Exception running EDI FTP Cron: %s.\n Original Traceback:\n%s",
                    e,
                    Exception,
                )
