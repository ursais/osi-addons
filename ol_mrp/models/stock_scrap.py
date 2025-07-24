# Import libs
from datetime import date

# Import Odoo libs
from odoo import models, _


class StockScrap(models.Model):
    """Inherit scrap to add chatter message on MO."""

    _inherit = "stock.scrap"

    # METHODS ###

    def do_scrap(self):
        """
        When scrapping from a MO, add note to MO & Batch chatter with scrap information
        """
        rec = super().do_scrap()
        for scrap in self:
            if scrap.production_id:
                user = self.env.user
                mo = scrap.production_id
                today_str = date.today().strftime("%Y-%m-%d")

                # Compose MO note
                mo_note = _(
                    f"<b>{user.name}</b> scrapped a component:<br/><ul>"
                    f"<li><b>Date:</b> {today_str}</li>"
                    f"<li><b>Product:</b> {scrap.product_id.name}</li>"
                    f"<li><b>Qty:</b> {scrap.scrap_qty} {scrap.product_uom_id.name}</li>"
                    f"<li><b>Source Location:</b> {scrap.location_id.name}</li>"
                    f"<li><b>Scrap Location:</b> {scrap.scrap_location_id.name}</li>"
                    f"<li><b>Reason:</b> {scrap.reason_code_id.name if scrap.reason_code_id else 'N/A'}</li>"
                    f"</ul>"
                )
                mo.message_post(body=mo_note, body_is_html=True)

                # If batch present, post to batch too
                if mo.mrp_batch_id:
                    batch_note = _(
                        f"<b>{user.name}</b> scrapped a component on MO <b>{mo.name}</b>:<br/><ul>"
                        f"<li><b>Date:</b> {today_str}</li>"
                        f"<li><b>Product:</b> {scrap.product_id.name}</li>"
                        f"<li><b>Qty:</b> {scrap.scrap_qty} {scrap.product_uom_id.name}</li>"
                        f"<li><b>Source Location:</b> {scrap.location_id.name}</li>"
                        f"<li><b>Scrap Location:</b> {scrap.scrap_location_id.name}</li>"
                        f"<li><b>Reason:</b> {scrap.reason_code_id.name if scrap.reason_code_id else 'N/A'}</li>"
                        f"</ul>"
                    )
                    mo.mrp_batch_id.message_post(body=batch_note, body_is_html=True)
        return rec

    # END ###
