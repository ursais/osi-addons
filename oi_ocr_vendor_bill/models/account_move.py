# Copyright (C) 2024 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import io
import logging
import re
from datetime import datetime

from odoo import fields, models, _
from odoo.exceptions import UserError

try:
    import pytesseract
    from PIL import Image
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    pytesseract = None
    Image = None

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    ocr_text = fields.Text(
        string="OCR Extracted Text",
        readonly=True,
        help="Raw text extracted from vendor bill image using OCR",
    )
    ocr_processed = fields.Boolean(
        string="OCR Processed",
        default=False,
        readonly=True,
        help="Indicates if OCR has been processed for this invoice",
    )
    ocr_error = fields.Text(
        string="OCR Error",
        readonly=True,
        help="Error message if OCR processing failed",
    )

    def _get_image_attachments(self):
        """
        Get image attachments from the invoice.
        Returns list of ir.attachment records with image mimetypes.
        """
        self.ensure_one()
        image_mimetypes = [
            "image/jpeg",
            "image/jpg",
            "image/png",
            "image/gif",
            "image/bmp",
            "image/tiff",
            "image/webp",
        ]
        return self.env["ir.attachment"].search(
            [
                ("res_model", "=", self._name),
                ("res_id", "=", self.id),
                ("mimetype", "in", image_mimetypes),
            ],
            order="id desc",
            limit=10,
        )

    def _extract_text_from_image(self, image_data):
        """
        Extract text from image data using Tesseract OCR.

        :param image_data: Base64 encoded image data or binary image data
        :return: Extracted text string
        """
        if not TESSERACT_AVAILABLE:
            raise UserError(
                _(
                    "Tesseract OCR is not available. "
                    "Please install pytesseract and Pillow packages, "
                    "and ensure Tesseract OCR engine is installed on the system."
                )
            )

        try:
            # Decode base64 if needed
            if isinstance(image_data, str):
                image_bytes = base64.b64decode(image_data)
            else:
                image_bytes = image_data

            # Open image with PIL
            image = Image.open(io.BytesIO(image_bytes))

            # Convert to RGB if necessary (Tesseract requires RGB)
            if image.mode != "RGB":
                image = image.convert("RGB")

            # Perform OCR
            text = pytesseract.image_to_string(image, lang="eng")

            return text.strip()

        except Exception as e:
            _logger.error("OCR extraction failed: %s", str(e), exc_info=True)
            raise UserError(
                _("Failed to extract text from image: %s") % str(e)
            ) from e

    def _parse_date_string(self, date_str):
        """
        Parse date string from various formats.

        :param date_str: Date string in various formats
        :return: Date object or None
        """
        if not date_str:
            return None

        # Common date formats
        date_formats = [
            "%m/%d/%Y",
            "%m-%d-%Y",
            "%d/%m/%Y",
            "%d-%m-%Y",
            "%Y/%m/%d",
            "%Y-%m-%d",
            "%m/%d/%y",
            "%m-%d-%y",
            "%d/%m/%y",
            "%d-%m-%y",
        ]

        for fmt in date_formats:
            try:
                return datetime.strptime(date_str.strip(), fmt).date()
            except ValueError:
                continue

        return None

    def _parse_ocr_text(self, ocr_text):
        """
        Parse OCR text to extract invoice information.
        This is a basic implementation that can be extended.

        :param ocr_text: Raw OCR text
        :return: Dictionary with parsed fields
        """
        parsed_data = {}

        if not ocr_text:
            return parsed_data

        # Extract invoice number (common patterns)
        invoice_number_patterns = [
            r"(?:invoice|inv)[\s#:]*([A-Z0-9\-]+)",
            r"#[\s]*([A-Z0-9\-]+)",
            r"invoice[\s]*number[\s:]*([A-Z0-9\-]+)",
        ]
        for pattern in invoice_number_patterns:
            match = re.search(pattern, ocr_text, re.IGNORECASE)
            if match:
                parsed_data["ref"] = match.group(1).strip()
                break

        # Extract date (common patterns)
        date_patterns = [
            r"(?:date|dated)[\s:]*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})",
            r"(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})",
        ]
        for pattern in date_patterns:
            match = re.search(pattern, ocr_text, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                parsed_date = self._parse_date_string(date_str)
                if parsed_date:
                    parsed_data["invoice_date"] = parsed_date
                break

        # Extract total amount (common patterns)
        total_patterns = [
            r"(?:total|amount|sum)[\s:]*\$?[\s]*([\d,]+\.?\d*)",
            r"\$[\s]*([\d,]+\.?\d*)",
            r"([\d,]+\.?\d*)[\s]*total",
        ]
        for pattern in total_patterns:
            match = re.search(pattern, ocr_text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(",", "")
                try:
                    parsed_data["amount_total"] = float(amount_str)
                except ValueError:
                    pass
                break

        # Extract vendor name (first line or after "bill to" / "from")
        vendor_patterns = [
            r"(?:from|vendor|supplier)[\s:]*([A-Z][^\n]+)",
            r"^([A-Z][A-Za-z\s&]+(?:Inc|LLC|Ltd|Corp|Company)?)",
        ]
        for pattern in vendor_patterns:
            match = re.search(pattern, ocr_text, re.IGNORECASE | re.MULTILINE)
            if match:
                vendor_name = match.group(1).strip()
                # Clean up vendor name
                vendor_name = re.sub(r"\s+", " ", vendor_name)
                parsed_data["partner_name"] = vendor_name[:100]  # Limit length
                break

        return parsed_data

    def _apply_parsed_data(self, parsed_data):
        """
        Apply parsed OCR data to invoice fields.

        :param parsed_data: Dictionary with parsed fields
        """
        self.ensure_one()

        if not parsed_data:
            return

        # Update invoice reference
        if parsed_data.get("ref") and not self.ref:
            self.ref = parsed_data["ref"]

        # Update invoice date
        if parsed_data.get("invoice_date") and not self.invoice_date:
            self.invoice_date = parsed_data["invoice_date"]

        # Update partner if found
        if parsed_data.get("partner_name"):
            partner = self.env["res.partner"].search(
                [("name", "ilike", parsed_data["partner_name"])], limit=1
            )
            if partner:
                self.partner_id = partner
            elif not self.partner_id:
                # Could create partner, but that's optional
                _logger.info(
                    "OCR found vendor name '%s' but no matching partner found",
                    parsed_data["partner_name"],
                )

    def action_process_ocr(self):
        """
        Process OCR on vendor bill attachments.
        Extracts text from images and attempts to populate invoice fields.
        """
        self.ensure_one()

        if not TESSERACT_AVAILABLE:
            raise UserError(
                _(
                    "Tesseract OCR is not available. "
                    "Please install pytesseract and Pillow packages."
                )
            )

        # Check if this is a vendor bill
        if self.move_type != "in_invoice":
            raise UserError(_("OCR processing is only available for vendor bills."))

        # Get image attachments
        attachments = self._get_image_attachments()
        if not attachments:
            raise UserError(
                _("No image attachments found. Please attach an image of the vendor bill.")
            )

        # Process the first image attachment
        attachment = attachments[0]
        try:
            # Extract text from image
            ocr_text = self._extract_text_from_image(attachment.datas)

            # Store OCR text
            self.write(
                {
                    "ocr_text": ocr_text,
                    "ocr_processed": True,
                    "ocr_error": False,
                }
            )

            # Parse OCR text
            parsed_data = self._parse_ocr_text(ocr_text)

            # Apply parsed data to invoice
            self._apply_parsed_data(parsed_data)

            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("OCR Processing Complete"),
                    "message": _(
                        "Successfully extracted text from image. "
                        "Please review the populated fields."
                    ),
                    "type": "success",
                    "sticky": False,
                },
            }

        except UserError:
            raise
        except Exception as e:
            error_msg = str(e)
            _logger.error("OCR processing failed: %s", error_msg, exc_info=True)
            self.write(
                {
                    "ocr_processed": True,
                    "ocr_error": error_msg,
                }
            )
            raise UserError(
                _("OCR processing failed: %s") % error_msg
            ) from e

    def action_view_ocr_text(self):
        """
        Open a wizard to view the extracted OCR text.
        """
        self.ensure_one()
        if not self.ocr_text:
            raise UserError(_("No OCR text available to display."))
        return {
            "name": _("OCR Extracted Text"),
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "view_mode": "form",
            "res_id": self.id,
            "target": "new",
            "views": [
                [
                    self.env.ref("oi_ocr_vendor_bill.view_account_move_ocr_text").id,
                    "form",
                ]
            ],
        }
