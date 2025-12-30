================================
OSI OCR Vendor Bill
================================

This module adds OCR (Optical Character Recognition) functionality for vendor bills
using the Tesseract OCR engine. It automatically extracts text from vendor bill
images and populates invoice fields accordingly.

Features
========

* Extract text from vendor bill images using Tesseract OCR
* Automatically parse invoice information (invoice number, date, amount, vendor name)
* Populate invoice fields with extracted data
* View extracted OCR text for manual review
* Support for multiple image formats (JPEG, PNG, GIF, BMP, TIFF, WebP)

Installation
============

1. Install Tesseract OCR engine on your system:

   * Ubuntu/Debian: ``sudo apt-get install tesseract-ocr``
   * CentOS/RHEL: ``sudo yum install tesseract``
   * macOS: ``brew install tesseract``
   * Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki

2. Install Python dependencies (automatically installed via Odoo):

   * pytesseract
   * Pillow

3. Install the module in Odoo:

   * Go to Apps menu
   * Remove the "Apps" filter
   * Search for "OSI OCR Vendor Bill"
   * Click Install

Usage
=====

1. Create a new vendor bill (Vendor Bills > Create)
2. Attach an image of the vendor bill to the invoice
3. Click the "Process OCR" button in the invoice form header
4. Review the populated fields and extracted OCR text
5. Click "View OCR Text" to see the raw extracted text

The module will attempt to extract:
* Invoice number/reference
* Invoice date
* Total amount
* Vendor name (and match with existing partners)

Configuration
=============

No additional configuration is required. The module works out of the box once
Tesseract OCR is installed on the system.

Technical Details
=================

* Inherits from ``account.move`` model
* Uses Tesseract OCR engine via pytesseract Python library
* Processes image attachments automatically
* Stores extracted text for review and debugging
* Handles errors gracefully with user-friendly messages

Limitations
===========

* OCR accuracy depends on image quality
* Text parsing uses basic regex patterns and may need customization
* Currently processes only the first image attachment
* Date parsing is basic and may need enhancement for different formats
* Vendor name matching is case-insensitive but may need fuzzy matching

Future Enhancements
===================

* Support for multiple image attachments
* Advanced date parsing with multiple format support
* Fuzzy matching for vendor names
* Machine learning-based field extraction
* Support for PDF documents
* Multi-language OCR support

Author
======

Open Source Integrators

Maintainers
===========

* Open Source Integrators

Website
=======

https://github.com/ursais/osi-addons

License
=======

AGPL-3
