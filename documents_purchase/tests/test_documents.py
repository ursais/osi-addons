# Copyright (C) 2021 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
import base64

from odoo.tests.common import TransactionCase, tagged

TEXT = base64.b64encode(bytes("workflow bridge purchase", "utf-8"))


@tagged("post_install", "-at_install")
class TestCaseDocumentsBridgePurchase(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.folder_test = cls.env["documents.document"].create(
            {"name": "folder_test", "type": "folder"}
        )
        cls.company_test = cls.env["res.company"].create(
            {
                "name": "test bridge purchase",
                "purchase_folder_id": cls.folder_test.id,
                "documents_purchase_settings": False,
            }
        )
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Vendor Doc Test",
                "company_id": cls.company_test.id,
            }
        )
        cls.purchase = cls.env["purchase.order"].create(
            {
                "partner_id": cls.partner.id,
                "company_id": cls.company_test.id,
            }
        )
        cls.attachment_txt = cls.env["ir.attachment"].create(
            {
                "datas": TEXT,
                "name": "fileTextTwo.txt",
                "mimetype": "text/plain",
            }
        )

    def test_bridge_folder_purchase_settings_on_write(self):
        self.company_test.write({"documents_purchase_settings": True})
        self.attachment_txt.write(
            {
                "res_model": "purchase.order",
                "res_id": self.purchase.id,
            }
        )
        document = self.env["documents.document"].search(
            [("attachment_id", "=", self.attachment_txt.id)]
        )
        self.assertEqual(
            document.folder_id,
            self.folder_test,
            "the purchase document should have a folder",
        )

    def test_bridge_folder_purchase_settings_disabled(self):
        self.attachment_txt.write(
            {
                "res_model": "purchase.order",
                "res_id": self.purchase.id,
            }
        )
        document = self.env["documents.document"].search(
            [("attachment_id", "=", self.attachment_txt.id)]
        )
        self.assertFalse(
            document,
            "no documents.document should be created while the purchase bridge is off",
        )

    def test_default_res_id_model(self):
        self.company_test.write({"documents_purchase_settings": True})
        attachment = (
            self.env["ir.attachment"]
            .with_context(
                default_res_id=self.purchase.id,
                default_res_model=self.purchase._name,
            )
            .create(
                {
                    "datas": TEXT,
                    "name": "fileFromContext.txt",
                    "mimetype": "text/plain",
                }
            )
        )
        document = self.env["documents.document"].search(
            [("attachment_id", "=", attachment.id)]
        )
        self.assertTrue(
            document, "It should have created a document from default values"
        )
        self.assertEqual(document.folder_id, self.folder_test)
