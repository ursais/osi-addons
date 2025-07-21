from odoo import models, fields, api


class Document(models.Model):

    _inherit = "documents.document"

    public_asset = fields.Boolean(default=False)
    public_eligible = fields.Boolean(compute="_compute_public_eligible", store=True)

    @api.depends("folder_id")
    def _compute_public_eligible(self):
        """
        Attachments are only eligible to be marked as public if they are living within specific document folders.
        This field is used to determine whether the attachment is eligible.
        """
        product_asset_folder = self.env["documents.folder"].search(
            [("name", "=", "Products"), ("parent_folder_id", "=", False)], limit=1
        )
        for rec in self:
            if rec.folder_id.parent_path.startswith(str(product_asset_folder.id)):
                rec.public_eligible = True
            else:
                rec.public_eligible = False

    def toggle_public(self):
        """
        Toggles a document and it's associated attachment's public status. This is limited to documents uploaded
        to specified folders.

        When a document is marked as public, it will be saved into a different volume within the odoo image
        which will then be mirrored to a GCP bucket.
        """
        self.public_asset = not self.public_asset
        self.attachment_id.toggle_public()

    def write(self, vals):
        """
        If a document is moved between folders, we need to check to make sure that it is still in a folder that
        is public eligible. The `public_eligible` field will automatically recompute if a document moves folders,
        so we can just call toggle_public to set the public status correctly.
        """
        res = super().write(vals)
        if not self.public_eligible and self.public_asset:
            self.toggle_public()
        return res

    def action_archive(self):
        # When deleting a document, mark the associated attachment as private. This will make garbage collection easier
        for document in self:
            if document.public_asset:
                document.toggle_public()
        return super().action_archive()
