import os

from odoo import api, models, fields
from odoo.tools import config


class IrAttachment(models.Model):

    _inherit = "ir.attachment"

    public_asset = fields.Boolean(default=False)

    def toggle_public(self):
        """
        Toggles attachments between public and private. Private attachments are stored in the default `/odoo/data`
        directory. Public attachments are stored in the `public_asset_dir` defined in the odoo configuration.
        This method handles the logic to move the assets between these volumes.

        TODO: When odoo groups have been setup, we should limit this functionality to check if the user is in
        product management or marketing
        """
        # Read in the data from the existing file and remove it from the filestore
        datas = self._file_read(self.store_fname)
        os.unlink(self._full_path(self.store_fname))
        # Toggle the file's public status and write the file to the other filestore
        self.public_asset = not self.public_asset
        self._file_write(datas, self.checksum)

    @api.model
    def _filestore(self):
        """
        For public facing attachments we want to save them to a different volume from the standard data dir.
        This method tells odoo which directory to look for/save attachments in.
        """
        if self.exists() and self.public_asset:
            return os.path.join(
                config["public_asset_dir"], "filestore", self._cr.dbname
            )
        return config.filestore(self._cr.dbname)


class IrBinary(models.AbstractModel):

    _inherit = "ir.binary"

    def _record_to_stream(self, record, field_name):
        """
        This method is used when we are retrieving files for things like previews.
        It is necessary to inherit this because we need to be able to point odoo to files in the public filestore.

        This method will return a Stream object which has a `path` attribute pointing to the file location. For
        files that are public, we need to override this to point to the public filestore.
        """
        res = super()._record_to_stream(record, field_name)
        if (
            record._name == "ir.attachment"
            and field_name in ("raw", "datas", "db_datas")
            and record.public_asset
        ):
            res.path = record._full_path(record.store_fname)
        return res
