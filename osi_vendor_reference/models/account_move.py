# Copyright (C) 2019 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, models


class AccountMove(models.Model):
    _inherit = "account.move"

    # Load all unsold PO lines
    @api.onchange("purchase_vendor_bill_id", "purchase_id")
    def _onchange_purchase_auto_complete(self):
        res = super(AccountMove, self)._onchange_purchase_auto_complete()

        # Get Partner Ref from PO
        # Check If reference in PO, if already there append new reference
        if self.purchase_id and self.purchase_id.partner_ref:
            if (
                self.payment_reference
                and self.payment_reference != self.purchase_id.partner_ref
            ):
                self.payment_reference = (
                    self.payment_reference + "; " + self.purchase_id.partner_ref
                )
            else:
                self.payment_reference = self.purchase_id.partner_ref
        return res

    @api.model
    def default_get(self, default_fields):
        res = super(AccountMove, self).default_get(default_fields)
        if res and "purchase_id" in res:
            po_rec = self.env["purchase.order"].browse(res.get("purchase_id"))

            # Check If reference in PO, if already there append new reference
            if "reference" in res and po_rec and po_rec.partner_ref:
                if (
                    res["payment_reference"]
                    and res["payment_reference"] != po_rec.partner_ref
                ):
                    res["payment_reference"] = (
                        res["payment_reference"] + "; " + po_rec.partner_ref
                    )
                else:
                    res["payment_reference"] = po_rec.partner_ref
        return res
