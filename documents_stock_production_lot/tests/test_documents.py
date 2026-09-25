# Copyright (C) 2021 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
import base64

from odoo.tests.common import TransactionCase, tagged

TEXT = base64.b64encode(bytes("workflow bridge lot", "utf-8"))


@tagged("post_install", "-at_install")
class TestCaseDocumentsBridgeLot(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.folder_test = cls.env["documents.document"].create(
            {"name": "folder_test", "type": "folder"}
        )
        cls.company_test = cls.env["res.company"].create(
            {
                "name": "test bridge lot",
                "lot_folder_id": cls.folder_test.id,
                "documents_lot_settings": False,
            }
        )
        cls.product = cls.env["product.product"].create(
            {
                "name": "Lot Doc Product",
                "is_storable": True,
                "tracking": "lot",
                "company_id": cls.company_test.id,
            }
        )
        cls.lot = cls.env["stock.lot"].create(
            {
                "name": "LOT-DOC-001",
                "product_id": cls.product.id,
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

    def test_bridge_folder_lot_settings_on_write(self):
        self.company_test.write({"documents_lot_settings": True})
        self.attachment_txt.write(
            {
                "res_model": "stock.lot",
                "res_id": self.lot.id,
            }
        )
        document = self.env["documents.document"].search(
            [("attachment_id", "=", self.attachment_txt.id)]
        )
        self.assertEqual(
            document.folder_id,
            self.folder_test,
            "the lot document should have a folder",
        )

    def test_bridge_folder_lot_settings_disabled(self):
        self.attachment_txt.write(
            {
                "res_model": "stock.lot",
                "res_id": self.lot.id,
            }
        )
        document = self.env["documents.document"].search(
            [("attachment_id", "=", self.attachment_txt.id)]
        )
        self.assertFalse(
            document,
            "no documents.document should be created while the lot bridge is off",
        )

    def test_default_res_id_model(self):
        self.company_test.write({"documents_lot_settings": True})
        attachment = (
            self.env["ir.attachment"]
            .with_context(
                default_res_id=self.lot.id,
                default_res_model=self.lot._name,
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

    def test_action_link_to_lot(self):
        self.company_test.write({"documents_lot_settings": True})
        document = self.env["documents.document"].create(
            {
                "datas": TEXT,
                "name": "fileToLink.txt",
                "mimetype": "text/plain",
                "folder_id": self.folder_test.id,
            }
        )
        action = document.action_link_to_record("stock.lot")
        self.assertEqual(action["res_model"], "documents.link_to_record_wizard")
        self.assertEqual(action["target"], "new")
