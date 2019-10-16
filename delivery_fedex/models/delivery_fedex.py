# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
import time

from odoo import api, models, fields, _, tools
from odoo.exceptions import UserError
from odoo.tools import pdf

from .fedex_request import FedexRequest


_logger = logging.getLogger(__name__)

# Why using standardized ISO codes? It's way more fun to use made up codes...
# https://www.fedex.com/us/developer/WebHelp/ws/2014/dvg/WS_DVG_WebHelp/Appendix_F_Currency_Codes.htm
FEDEX_CURR_MATCH = {
    u'UYU': u'UYP',
    u'XCD': u'ECD',
    u'MXN': u'NMP',
    u'KYD': u'CID',
    u'CHF': u'SFR',
    u'GBP': u'UKL',
    u'IDR': u'RPA',
    u'DOP': u'RDD',
    u'JPY': u'JYE',
    u'KRW': u'WON',
    u'SGD': u'SID',
    u'CLP': u'CHP',
    u'JMD': u'JAD',
    u'KWD': u'KUD',
    u'AED': u'DHS',
    u'TWD': u'NTD',
    u'ARS': u'ARN',
    u'LVL': u'EURO',
}

FEDEX_STOCK_TYPE = [
    ('PAPER_4X6', 'PAPER_4X6'),
    ('PAPER_4X8', 'PAPER_4X8'),
    ('PAPER_4X9', 'PAPER_4X9'),
    ('PAPER_7X4.75', 'PAPER_7X4.75'),
    ('PAPER_8.5X11_BOTTOM_HALF_LABEL', 'PAPER_8.5X11_BOTTOM_HALF_LABEL'),
    ('PAPER_8.5X11_TOP_HALF_LABEL', 'PAPER_8.5X11_TOP_HALF_LABEL'),
    ('PAPER_LETTER', 'PAPER_LETTER'),
    ('STOCK_4X6', 'STOCK_4X6'),
    ('STOCK_4X6.75_LEADING_DOC_TAB', 'STOCK_4X6.75_LEADING_DOC_TAB'),
    ('STOCK_4X6.75_TRAILING_DOC_TAB', 'STOCK_4X6.75_TRAILING_DOC_TAB'),
    ('STOCK_4X8', 'STOCK_4X8'),
    ('STOCK_4X9_LEADING_DOC_TAB', 'STOCK_4X9_LEADING_DOC_TAB'),
    ('STOCK_4X9_TRAILING_DOC_TAB', 'STOCK_4X9_TRAILING_DOC_TAB')
]


class ProviderFedex(models.Model):
    _inherit = 'delivery.carrier'

    delivery_type = fields.Selection(selection_add=[('fedex', "FedEx")])

    fedex_developer_key = fields.Char(string="Developer Key", groups="base.group_system")
    fedex_developer_password = fields.Char(string="Password", groups="base.group_system")
    fedex_account_number = fields.Char(string="FedEx Account Number", groups="base.group_system")
    fedex_meter_number = fields.Char(string="Meter Number", groups="base.group_system")
    fedex_droppoff_type = fields.Selection([('BUSINESS_SERVICE_CENTER', 'BUSINESS_SERVICE_CENTER'),
                                            ('DROP_BOX', 'DROP_BOX'),
                                            ('REGULAR_PICKUP', 'REGULAR_PICKUP'),
                                            ('REQUEST_COURIER', 'REQUEST_COURIER'),
                                            ('STATION', 'STATION')],
                                           string="Fedex drop-off type",
                                           default='REGULAR_PICKUP')
    fedex_default_packaging_id = fields.Many2one('product.packaging', string="Default Package Type")
    fedex_service_type = fields.Selection([('INTERNATIONAL_ECONOMY', 'INTERNATIONAL_ECONOMY'),
                                           ('INTERNATIONAL_PRIORITY', 'INTERNATIONAL_PRIORITY'),
                                           ('FEDEX_GROUND', 'FEDEX_GROUND'),
                                           ('FEDEX_2_DAY', 'FEDEX_2_DAY'),
                                           ('FEDEX_2_DAY_AM', 'FEDEX_2_DAY_AM'),
                                           ('FEDEX_3_DAY_FREIGHT', 'FEDEX_3_DAY_FREIGHT'),
                                           ('FIRST_OVERNIGHT', 'FIRST_OVERNIGHT'),
                                           ('PRIORITY_OVERNIGHT', 'PRIORITY_OVERNIGHT'),
                                           ('STANDARD_OVERNIGHT', 'STANDARD_OVERNIGHT'),
                                           ('FEDEX_NEXT_DAY_EARLY_MORNING', 'FEDEX_NEXT_DAY_EARLY_MORNING'),
                                           ('FEDEX_NEXT_DAY_MID_MORNING', 'FEDEX_NEXT_DAY_MID_MORNING'),
                                           ('FEDEX_NEXT_DAY_AFTERNOON', 'FEDEX_NEXT_DAY_AFTERNOON'),
                                           ('FEDEX_NEXT_DAY_END_OF_DAY', 'FEDEX_NEXT_DAY_END_OF_DAY'),
                                           ],
                                          default='INTERNATIONAL_PRIORITY')
    fedex_duty_payment = fields.Selection([('SENDER', 'Sender'), ('RECIPIENT', 'Recipient')], required=True, default="SENDER")
    fedex_weight_unit = fields.Selection([('LB', 'LB'),
                                          ('KG', 'KG')],
                                         default='LB')
    # Note about weight units: Odoo (v9) currently works with kilograms.
    # --> Gross weight of each products are expressed in kilograms.
    # For some services, FedEx requires weights expressed in pounds, so we
    # convert them when necessary.
    fedex_label_stock_type = fields.Selection(FEDEX_STOCK_TYPE, string='Label Type', default='PAPER_LETTER')
    fedex_label_file_type = fields.Selection([('PDF', 'PDF'),
                                              ('EPL2', 'EPL2'),
                                              ('PNG', 'PNG'),
                                              ('ZPLII', 'ZPLII')],
                                             default='PDF', string="FEDEX Label File Type")
    fedex_document_stock_type = fields.Selection(FEDEX_STOCK_TYPE, string='Commercial Invoice Type', default='PAPER_LETTER')
    fedex_saturday_delivery = fields.Boolean(string="FedEx Saturday Delivery", help="""Special service:Saturday Delivery, can be requested on following days.
                                                                                 Thursday:\n1.FEDEX_2_DAY.\nFriday:\n1.PRIORITY_OVERNIGHT.\n2.FIRST_OVERNIGHT.
                                                                                 3.INTERNATIONAL_PRIORITY.\n(To Select Countries)""")

    def _compute_can_generate_return(self):
        super(ProviderFedex, self)._compute_can_generate_return()
        for carrier in self:
            if not carrier.can_generate_return:
                if carrier.delivery_type == 'fedex':
                    carrier.can_generate_return = True

    @api.onchange('fedex_service_type')
    def on_change_fedex_service_type(self):
        self.fedex_saturday_delivery = False

    def fedex_rate_shipment(self, order):
        max_weight = self._fedex_convert_weight(self.fedex_default_packaging_id.max_weight, self.fedex_weight_unit)
        price = 0.0
        is_india = order.partner_shipping_id.country_id.code == 'IN' and order.company_id.partner_id.country_id.code == 'IN'

        # Estimate weight of the sales order; will be definitely recomputed on the picking field "weight"
        est_weight_value = sum([(line.product_id.weight * line.product_uom_qty) for line in order.order_line]) or 0.0
        weight_value = self._fedex_convert_weight(est_weight_value, self.fedex_weight_unit)

        # Some users may want to ship very lightweight items; in order to give them a rating, we round the
        # converted weight of the shipping to the smallest value accepted by FedEx: 0.01 kg or lb.
        # (in the case where the weight is actually 0.0 because weights are not set, don't do this)
        if weight_value > 0.0:
            weight_value = max(weight_value, 0.01)

        order_currency = order.currency_id
        superself = self.sudo()

        # Authentication stuff
        srm = FedexRequest(self.log_xml, request_type="rating", prod_environment=self.prod_environment)
        srm.web_authentication_detail(superself.fedex_developer_key, superself.fedex_developer_password)
        srm.client_detail(superself.fedex_account_number, superself.fedex_meter_number)

        # Build basic rating request and set addresses
        srm.transaction_detail(order.name)
        srm.shipment_request(
            self.fedex_droppoff_type,
            self.fedex_service_type,
            self.fedex_default_packaging_id.shipper_package_code,
            self.fedex_weight_unit,
            self.fedex_saturday_delivery,
        )
        pkg = self.fedex_default_packaging_id

        srm.set_currency(_convert_curr_iso_fdx(order_currency.name))
        srm.set_shipper(order.company_id.partner_id, order.warehouse_id.partner_id)
        srm.set_recipient(order.partner_shipping_id)

        if max_weight and weight_value > max_weight:
            total_package = int(weight_value / max_weight)
            last_package_weight = weight_value % max_weight

            for sequence in range(1, total_package + 1):
                srm.add_package(
                    max_weight,
                    package_code=pkg.shipper_package_code,
                    package_height=pkg.height,
                    package_width=pkg.width,
                    package_length=pkg.length,
                    sequence_number=sequence,
                    mode='rating',
                )
            if last_package_weight:
                total_package = total_package + 1
                srm.add_package(
                    last_package_weight,
                    package_code=pkg.shipper_package_code,
                    package_height=pkg.height,
                    package_width=pkg.width,
                    package_length=pkg.length,
                    sequence_number=total_package,
                    mode='rating',
                )
            srm.set_master_package(weight_value, total_package)
        else:
            srm.add_package(
                weight_value,
                package_code=pkg.shipper_package_code,
                package_height=pkg.height,
                package_width=pkg.width,
                package_length=pkg.length,
                mode='rating',
            )
            srm.set_master_package(weight_value, 1)

        # Commodities for customs declaration (international shipping)
        if self.fedex_service_type in ['INTERNATIONAL_ECONOMY', 'INTERNATIONAL_PRIORITY'] or is_india:
            total_commodities_amount = 0.0
            commodity_country_of_manufacture = order.warehouse_id.partner_id.country_id.code

            for line in order.order_line.filtered(lambda l: l.product_id.type in ['product', 'consu']):
                commodity_amount = line.price_reduce_taxinc
                total_commodities_amount += (commodity_amount * line.product_uom_qty)
                commodity_description = line.product_id.name
                commodity_number_of_piece = '1'
                commodity_weight_units = self.fedex_weight_unit
                commodity_weight_value = self._fedex_convert_weight(line.product_id.weight * line.product_uom_qty, self.fedex_weight_unit)
                commodity_quantity = line.product_uom_qty
                commodity_quantity_units = 'EA'
                commodity_harmonized_code = line.product_id.hs_code or ''
                srm.commodities(_convert_curr_iso_fdx(order_currency.name), commodity_amount, commodity_number_of_piece, commodity_weight_units, commodity_weight_value, commodity_description, commodity_country_of_manufacture, commodity_quantity, commodity_quantity_units, commodity_harmonized_code)
            srm.customs_value(_convert_curr_iso_fdx(order_currency.name), total_commodities_amount, "NON_DOCUMENTS")
            srm.duties_payment(order.warehouse_id.partner_id, superself.fedex_account_number, superself.fedex_duty_payment)

        request = srm.rate()

        warnings = request.get('warnings_message')
        if warnings:
            _logger.info(warnings)

        if not request.get('errors_message'):
            if _convert_curr_iso_fdx(order_currency.name) in request['price']:
                price = request['price'][_convert_curr_iso_fdx(order_currency.name)]
            else:
                _logger.info("Preferred currency has not been found in FedEx response")
                company_currency = order.company_id.currency_id
                if _convert_curr_iso_fdx(company_currency.name) in request['price']:
                    amount = request['price'][_convert_curr_iso_fdx(company_currency.name)]
                    price = company_currency._convert(amount, order_currency, order.company_id, order.date_order or fields.Date.today())
                else:
                    amount = request['price']['USD']
                    price = company_currency._convert(amount, order_currency, order.company_id, order.date_order or fields.Date.today())
        else:
            return {'success': False,
                    'price': 0.0,
                    'error_message': _('Error:\n%s') % request['errors_message'],
                    'warning_message': False}

        return {'success': True,
                'price': price,
                'error_message': False,
                'warning_message': _('Warning:\n%s') % warnings if warnings else False}

    def fedex_send_shipping(self, pickings):
        res = []

        for picking in pickings:

            srm = FedexRequest(self.log_xml, request_type="shipping", prod_environment=self.prod_environment)
            superself = self.sudo()
            srm.web_authentication_detail(superself.fedex_developer_key, superself.fedex_developer_password)
            srm.client_detail(superself.fedex_account_number, superself.fedex_meter_number)

            srm.transaction_detail(picking.id)

            package_type = picking.package_ids and picking.package_ids[0].packaging_id.shipper_package_code or self.fedex_default_packaging_id.shipper_package_code
            srm.shipment_request(self.fedex_droppoff_type, self.fedex_service_type, package_type, self.fedex_weight_unit, self.fedex_saturday_delivery)
            srm.set_currency(_convert_curr_iso_fdx(picking.company_id.currency_id.name))
            srm.set_shipper(picking.company_id.partner_id, picking.picking_type_id.warehouse_id.partner_id)
            srm.set_recipient(picking.partner_id)

            srm.shipping_charges_payment(superself.fedex_account_number)

            srm.shipment_label('COMMON2D', self.fedex_label_file_type, self.fedex_label_stock_type, 'TOP_EDGE_OF_TEXT_FIRST', 'SHIPPING_LABEL_FIRST')

            order = picking.sale_id
            company = order.company_id or picking.company_id or self.env.company
            order_currency = picking.sale_id.currency_id or picking.company_id.currency_id

            net_weight = self._fedex_convert_weight(picking.shipping_weight, self.fedex_weight_unit)

            # Commodities for customs declaration (international shipping)
            if self.fedex_service_type in ['INTERNATIONAL_ECONOMY', 'INTERNATIONAL_PRIORITY'] or (picking.partner_id.country_id.code == 'IN' and picking.picking_type_id.warehouse_id.partner_id.country_id.code == 'IN'):

                commodity_currency = order_currency
                total_commodities_amount = 0.0
                commodity_country_of_manufacture = picking.picking_type_id.warehouse_id.partner_id.country_id.code

                for operation in picking.move_line_ids:
                    commodity_amount = operation.move_id.sale_line_id.price_reduce_taxinc or operation.product_id.list_price
                    total_commodities_amount += (commodity_amount * operation.qty_done)
                    commodity_description = operation.product_id.name
                    commodity_number_of_piece = '1'
                    commodity_weight_units = self.fedex_weight_unit
                    commodity_weight_value = self._fedex_convert_weight(operation.product_id.weight * operation.qty_done, self.fedex_weight_unit)
                    commodity_quantity = operation.qty_done
                    commodity_quantity_units = 'EA'
                    commodity_harmonized_code = operation.product_id.hs_code or ''
                    srm.commodities(_convert_curr_iso_fdx(commodity_currency.name), commodity_amount, commodity_number_of_piece, commodity_weight_units, commodity_weight_value, commodity_description, commodity_country_of_manufacture, commodity_quantity, commodity_quantity_units, commodity_harmonized_code)
                srm.customs_value(_convert_curr_iso_fdx(commodity_currency.name), total_commodities_amount, "NON_DOCUMENTS")
                srm.duties_payment(picking.picking_type_id.warehouse_id.partner_id, superself.fedex_account_number, superself.fedex_duty_payment)
                send_etd = self.env['ir.config_parameter'].get_param("delivery_fedex.send_etd")
                srm.commercial_invoice(self.fedex_document_stock_type, send_etd)

            package_count = len(picking.package_ids) or 1

            # For india picking courier is not accepted without this details in label.
            po_number = order.display_name or False
            dept_number = False
            if picking.partner_id.country_id.code == 'IN' and picking.picking_type_id.warehouse_id.partner_id.country_id.code == 'IN':
                po_number = 'B2B' if picking.partner_id.commercial_partner_id.is_company else 'B2C'
                dept_number = 'BILL D/T: SENDER'

            # TODO RIM master: factorize the following crap

            ################
            # Multipackage #
            ################
            if package_count > 1:

                # Note: Fedex has a complex multi-piece shipping interface
                # - Each package has to be sent in a separate request
                # - First package is called "master" package and holds shipping-
                #   related information, including addresses, customs...
                # - Last package responses contains shipping price and code
                # - If a problem happens with a package, every previous package
                #   of the shipping has to be cancelled separately
                # (Why doing it in a simple way when the complex way exists??)

                master_tracking_id = False
                package_labels = []
                carrier_tracking_ref = ""

                for sequence, package in enumerate(picking.package_ids, start=1):

                    package_weight = self._fedex_convert_weight(package.shipping_weight, self.fedex_weight_unit)
                    packaging = package.packaging_id
                    srm._add_package(
                        package_weight,
                        package_code=packaging.shipper_package_code,
                        package_height=packaging.height,
                        package_width=packaging.width,
                        package_length=packaging.length,
                        sequence_number=sequence,
                        po_number=po_number,
                        dept_number=dept_number,
                        reference=picking.display_name,
                    )
                    srm.set_master_package(net_weight, package_count, master_tracking_id=master_tracking_id)
                    request = srm.process_shipment()
                    package_name = package.name or sequence

                    warnings = request.get('warnings_message')
                    if warnings:
                        _logger.info(warnings)

                    # First package
                    if sequence == 1:
                        if not request.get('errors_message'):
                            master_tracking_id = request['master_tracking_id']
                            package_labels.append((package_name, srm.get_label()))
                            carrier_tracking_ref = request['tracking_number']
                        else:
                            raise UserError(request['errors_message'])

                    # Intermediary packages
                    elif sequence > 1 and sequence < package_count:
                        if not request.get('errors_message'):
                            package_labels.append((package_name, srm.get_label()))
                            carrier_tracking_ref = carrier_tracking_ref + "," + request['tracking_number']
                        else:
                            raise UserError(request['errors_message'])

                    # Last package
                    elif sequence == package_count:
                        # recuperer le label pdf
                        if not request.get('errors_message'):
                            package_labels.append((package_name, srm.get_label()))

                            if _convert_curr_iso_fdx(order_currency.name) in request['price']:
                                carrier_price = request['price'][_convert_curr_iso_fdx(order_currency.name)]
                            else:
                                _logger.info("Preferred currency has not been found in FedEx response")
                                company_currency = picking.company_id.currency_id
                                if _convert_curr_iso_fdx(company_currency.name) in request['price']:
                                    amount = request['price'][_convert_curr_iso_fdx(company_currency.name)]
                                    carrier_price = company_currency._convert(
                                        amount, order_currency, company, order.date_order or fields.Date.today())
                                else:
                                    amount = request['price']['USD']
                                    carrier_price = company_currency._convert(
                                        amount, order_currency, company, order.date_order or fields.Date.today())

                            carrier_tracking_ref = carrier_tracking_ref + "," + request['tracking_number']

                            logmessage = _("Shipment created into Fedex<br/>"
                                           "<b>Tracking Numbers:</b> %s<br/>"
                                           "<b>Packages:</b> %s") % (carrier_tracking_ref, ','.join([pl[0] for pl in package_labels]))
                            if self.fedex_label_file_type != 'PDF':
                                attachments = [('LabelFedex-%s.%s' % (pl[0], self.fedex_label_file_type), pl[1]) for pl in package_labels]
                            if self.fedex_label_file_type == 'PDF':
                                attachments = [('LabelFedex.pdf', pdf.merge_pdf([pl[1] for pl in package_labels]))]
                            picking.message_post(body=logmessage, attachments=attachments)
                            shipping_data = {'exact_price': carrier_price,
                                             'tracking_number': carrier_tracking_ref}
                            res = res + [shipping_data]
                        else:
                            raise UserError(request['errors_message'])

            # TODO RIM handle if a package is not accepted (others should be deleted)

            ###############
            # One package #
            ###############
            elif package_count == 1:
                packaging = picking.package_ids[:1].packaging_id or picking.carrier_id.fedex_default_packaging_id
                srm._add_package(
                    net_weight,
                    package_code=packaging.shipper_package_code,
                    package_height=packaging.height,
                    package_width=packaging.width,
                    package_length=packaging.length,
                    po_number=po_number,
                    dept_number=dept_number,
                    reference=picking.display_name,
                )
                srm.set_master_package(net_weight, 1)

                # Ask the shipping to fedex
                request = srm.process_shipment()

                warnings = request.get('warnings_message')
                if warnings:
                    _logger.info(warnings)

                if not request.get('errors_message'):

                    if _convert_curr_iso_fdx(order_currency.name) in request['price']:
                        carrier_price = request['price'][_convert_curr_iso_fdx(order_currency.name)]
                    else:
                        _logger.info("Preferred currency has not been found in FedEx response")
                        company_currency = picking.company_id.currency_id
                        if _convert_curr_iso_fdx(company_currency.name) in request['price']:
                            amount = request['price'][_convert_curr_iso_fdx(company_currency.name)]
                            carrier_price = company_currency._convert(
                                amount, order_currency, company, order.date_order or fields.Date.today())
                        else:
                            amount = request['price']['USD']
                            carrier_price = company_currency._convert(
                                amount, order_currency, company, order.date_order or fields.Date.today())

                    carrier_tracking_ref = request['tracking_number']
                    logmessage = (_("Shipment created into Fedex <br/> <b>Tracking Number : </b>%s") % (carrier_tracking_ref))

                    fedex_labels = [('LabelFedex-%s-%s.%s' % (carrier_tracking_ref, index, self.fedex_label_file_type), label)
                                    for index, label in enumerate(srm._get_labels(self.fedex_label_file_type))]
                    picking.message_post(body=logmessage, attachments=fedex_labels)
                    shipping_data = {'exact_price': carrier_price,
                                     'tracking_number': carrier_tracking_ref}
                    res = res + [shipping_data]
                else:
                    raise UserError(request['errors_message'])

            ##############
            # No package #
            ##############
            else:
                raise UserError(_('No packages for this picking'))
            if self.return_label_on_delivery and request.get('date'):
                self.get_return_label(picking, tracking_number=request['tracking_number'], origin_date=request['date'])
            commercial_invoice = srm.get_document()
            if commercial_invoice:
                fedex_documents = [('DocumentFedex.pdf', commercial_invoice)]
                picking.message_post(body='Fedex Documents', attachments=fedex_documents)
        return res


    def fedex_get_return_label(self, picking, tracking_number=None, origin_date=None):
        srm = FedexRequest(self.log_xml, request_type="shipping", prod_environment=self.prod_environment)
        superself = self.sudo()
        srm.web_authentication_detail(superself.fedex_developer_key, superself.fedex_developer_password)
        srm.client_detail(superself.fedex_account_number, superself.fedex_meter_number)

        srm.transaction_detail(picking.id)

        package_type = picking.package_ids and picking.package_ids[0].packaging_id.shipper_package_code or self.fedex_default_packaging_id.shipper_package_code
        srm.shipment_request(self.fedex_droppoff_type, self.fedex_service_type, package_type, self.fedex_weight_unit, self.fedex_saturday_delivery)
        srm.set_currency(_convert_curr_iso_fdx(picking.company_id.currency_id.name))
        srm.set_shipper(picking.partner_id, picking.partner_id)
        srm.set_recipient(picking.company_id.partner_id)

        srm.shipping_charges_payment(superself.fedex_account_number)

        srm.shipment_label('COMMON2D', self.fedex_label_file_type, self.fedex_label_stock_type, 'TOP_EDGE_OF_TEXT_FIRST', 'SHIPPING_LABEL_FIRST')
        estimated_weight = sum([move.product_qty * move.product_id.weight for move in picking.move_lines])
        net_weight = self._fedex_convert_weight(picking.shipping_weight, self.fedex_weight_unit) or self._fedex_convert_weight(picking.weight, self.fedex_weight_unit)
        packaging = packaging = picking.package_ids[:1].packaging_id or picking.carrier_id.fedex_default_packaging_id
        order = picking.sale_id
        po_number = order.display_name or False
        dept_number = False
        srm._add_package(
            net_weight,
            package_code=packaging.shipper_package_code,
            package_height=packaging.height,
            package_width=packaging.width,
            package_length=packaging.length,
            reference=picking.display_name,
            po_number=po_number,
            dept_number=dept_number,
        )
        srm.set_master_package(net_weight, 1)
        if self.fedex_service_type in ['INTERNATIONAL_ECONOMY', 'INTERNATIONAL_PRIORITY'] or (picking.partner_id.country_id.code == 'IN' and picking.picking_type_id.warehouse_id.partner_id.country_id.code == 'IN'):

            order_currency = picking.sale_id.currency_id or picking.company_id.currency_id
            commodity_currency = order_currency
            total_commodities_amount = 0.0
            commodity_country_of_manufacture = picking.picking_type_id.warehouse_id.partner_id.country_id.code

            for operation in picking.move_line_ids:
                commodity_amount = operation.move_id.sale_line_id.price_unit or operation.product_id.list_price
                total_commodities_amount += (commodity_amount * operation.qty_done)
                commodity_description = operation.product_id.name
                commodity_number_of_piece = '1'
                commodity_weight_units = self.fedex_weight_unit
                if operation.state == 'done':
                    commodity_weight_value = self._fedex_convert_weight(operation.product_id.weight * operation.qty_done, self.fedex_weight_unit)
                    commodity_quantity = operation.qty_done
                else:
                    commodity_weight_value = self._fedex_convert_weight(operation.product_id.weight * operation.product_uom_qty, self.fedex_weight_unit)
                    commodity_quantity = operation.product_uom_qty
                commodity_quantity_units = 'EA'
                commodity_harmonized_code = operation.product_id.hs_code or ''
                srm.commodities(_convert_curr_iso_fdx(commodity_currency.name), commodity_amount, commodity_number_of_piece, commodity_weight_units, commodity_weight_value, commodity_description, commodity_country_of_manufacture, commodity_quantity, commodity_quantity_units, commodity_harmonized_code)
            srm.customs_value(_convert_curr_iso_fdx(commodity_currency.name), total_commodities_amount, "NON_DOCUMENTS")
            # We consider that returns are always paid by the company creating the label
            srm.duties_payment(picking.picking_type_id.warehouse_id.partner_id, superself.fedex_account_number, 'SENDER')
        srm.return_label(tracking_number, origin_date)
        response = srm.process_shipment()
        fedex_labels = [('%s-%s-%s.%s' % (self.get_return_label_prefix(), response['tracking_number'], index, self.fedex_label_file_type), label)
                        for index, label in enumerate(srm._get_labels(self.fedex_label_file_type))]
        picking.message_post(body='Return Label', attachments=fedex_labels)

    def fedex_get_tracking_link(self, picking):
        return 'https://www.fedex.com/apps/fedextrack/?action=track&trackingnumber=%s' % picking.carrier_tracking_ref

    def fedex_cancel_shipment(self, picking):
        request = FedexRequest(self.log_xml, request_type="shipping", prod_environment=self.prod_environment)
        superself = self.sudo()
        request.web_authentication_detail(superself.fedex_developer_key, superself.fedex_developer_password)
        request.client_detail(superself.fedex_account_number, superself.fedex_meter_number)
        request.transaction_detail(picking.id)

        master_tracking_id = picking.carrier_tracking_ref.split(',')[0]
        request.set_deletion_details(master_tracking_id)
        result = request.delete_shipment()

        warnings = result.get('warnings_message')
        if warnings:
            _logger.info(warnings)

        if result.get('delete_success') and not result.get('errors_message'):
            picking.message_post(body=_(u'Shipment N° %s has been cancelled' % master_tracking_id))
            picking.write({'carrier_tracking_ref': '',
                           'carrier_price': 0.0})
        else:
            raise UserError(result['errors_message'])

    def _fedex_get_default_custom_package_code(self):
        return 'YOUR_PACKAGING'


    def _fedex_convert_weight(self, weight, unit='KG'):
        weight_uom_id = self.env['product.template']._get_weight_uom_id_from_ir_config_parameter()
        if unit == 'KG':
            return weight_uom_id._compute_quantity(weight, self.env.ref('uom.product_uom_kgm'), round=False)
        elif unit == 'LB':
            return weight_uom_id._compute_quantity(weight, self.env.ref('uom.product_uom_lb'), round=False)
        else:
            raise ValueError

def _convert_curr_fdx_iso(code):
    curr_match = {v: k for k, v in FEDEX_CURR_MATCH.items()}
    return curr_match.get(code, code)

def _convert_curr_iso_fdx(code):
    return FEDEX_CURR_MATCH.get(code, code)
