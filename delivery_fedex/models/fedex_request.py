# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import binascii
import logging
import os
import re

from datetime import datetime, date
from zeep import Client, Plugin, Settings
from zeep.exceptions import Fault


_logger = logging.getLogger(__name__)
# uncomment to enable logging of Zeep requests and responses
# logging.getLogger('zeep.transports').setLevel(logging.DEBUG)


STATECODE_REQUIRED_COUNTRIES = ['US', 'CA', 'PR ', 'IN']


class LogPlugin(Plugin):
    """ Small plugin for zeep that catches out/ingoing XML requests and logs them"""
    def __init__(self, debug_logger):
        self.debug_logger = debug_logger

    def egress(self, envelope, http_headers, operation, binding_options):
        self.debug_logger(envelope, 'fedex_request')
        return envelope, http_headers

    def ingress(self, envelope, http_headers, operation):
        self.debug_logger(envelope, 'fedex_response')
        return envelope, http_headers

    def marshalled(self, context):
        context.envelope = context.envelope.prune()


class FedexRequest():
    """ Low-level object intended to interface Odoo recordsets with FedEx,
        through appropriate SOAP requests """

    def __init__(self, debug_logger, request_type="shipping", prod_environment=False, ):
        self.debug_logger = debug_logger
        self.hasCommodities = False
        self.hasOnePackage = False

        if request_type == "shipping":
            if not prod_environment:
                wsdl_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../api/test/ShipService_v15.wsdl')
            else:
                wsdl_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../api/prod/ShipService_v15.wsdl')
            self.start_shipping_transaction(wsdl_path)

        elif request_type == "rating":
            if not prod_environment:
                wsdl_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../api/test/RateService_v16.wsdl')
            else:
                wsdl_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../api/prod/RateService_v16.wsdl')
            self.start_rating_transaction(wsdl_path)

    # Authentification stuff

    def web_authentication_detail(self, key, password):
        WebAuthenticationCredential = self.factory.WebAuthenticationCredential()
        WebAuthenticationCredential.Key = key
        WebAuthenticationCredential.Password = password
        self.WebAuthenticationDetail = self.factory.WebAuthenticationDetail()
        self.WebAuthenticationDetail.UserCredential = WebAuthenticationCredential

    def transaction_detail(self, transaction_id):
        self.TransactionDetail = self.factory.TransactionDetail()
        self.TransactionDetail.CustomerTransactionId = transaction_id

    def client_detail(self, account_number, meter_number):
        self.ClientDetail = self.factory.ClientDetail()
        self.ClientDetail.AccountNumber = account_number
        self.ClientDetail.MeterNumber = meter_number

    # Common stuff

    def set_shipper(self, company_partner, warehouse_partner):
        Contact = self.factory.Contact()
        Contact.PersonName = company_partner.name if not company_partner.is_company else ''
        Contact.CompanyName = company_partner.name if company_partner.is_company else ''
        Contact.PhoneNumber = warehouse_partner.phone or ''
        # TODO fedex documentation asks for TIN number, but it seems to work without

        Address = self.factory.Address()
        Address.StreetLines = [warehouse_partner.street or '', warehouse_partner.street2 or '']
        Address.City = warehouse_partner.city or ''
        if warehouse_partner.country_id.code in STATECODE_REQUIRED_COUNTRIES:
            Address.StateOrProvinceCode = warehouse_partner.state_id.code or ''
        else:
            Address.StateOrProvinceCode = ''
        Address.PostalCode = warehouse_partner.zip or ''
        Address.CountryCode = warehouse_partner.country_id.code or ''

        self.RequestedShipment.Shipper = self.factory.Party()
        self.RequestedShipment.Shipper.Contact = Contact
        self.RequestedShipment.Shipper.Address = Address

    def set_recipient(self, recipient_partner):
        Contact = self.factory.Contact()
        if recipient_partner.is_company:
            Contact.PersonName = ''
            Contact.CompanyName = recipient_partner.name
        else:
            Contact.PersonName = recipient_partner.name
            Contact.CompanyName = recipient_partner.parent_id.name or ''
        Contact.PhoneNumber = recipient_partner.phone or ''

        Address = self.factory.Address()
        Address.StreetLines = [recipient_partner.street or '', recipient_partner.street2 or '']
        Address.City = recipient_partner.city or ''
        if recipient_partner.country_id.code in STATECODE_REQUIRED_COUNTRIES:
            Address.StateOrProvinceCode = recipient_partner.state_id.code or ''
        else:
            Address.StateOrProvinceCode = ''
        Address.PostalCode = recipient_partner.zip or ''
        Address.CountryCode = recipient_partner.country_id.code or ''

        self.RequestedShipment.Recipient = self.factory.Party()
        self.RequestedShipment.Recipient.Contact = Contact
        self.RequestedShipment.Recipient.Address = Address

    def shipment_request(self, dropoff_type, service_type, packaging_type, overall_weight_unit, saturday_delivery):
        self.RequestedShipment = self.factory.RequestedShipment()
        self.RequestedShipment.ShipTimestamp = datetime.now()
        self.RequestedShipment.DropoffType = dropoff_type
        self.RequestedShipment.ServiceType = service_type
        self.RequestedShipment.PackagingType = packaging_type
        # Resuest estimation of duties and taxes for international shipping
        if service_type in ['INTERNATIONAL_ECONOMY', 'INTERNATIONAL_PRIORITY']:
            self.RequestedShipment.EdtRequestType = 'ALL'
        else:
            self.RequestedShipment.EdtRequestType = 'NONE'
        self.RequestedShipment.PackageCount = 0
        self.RequestedShipment.TotalWeight = self.factory.Weight()
        self.RequestedShipment.TotalWeight.Units = overall_weight_unit
        self.RequestedShipment.TotalWeight.Value = 0
        self.listCommodities = []
        if saturday_delivery:
            timestamp_day = self.RequestedShipment.ShipTimestamp.strftime("%A")
            if (service_type == 'FEDEX_2_DAY' and timestamp_day == 'Thursday') or (service_type in ['PRIORITY_OVERNIGHT', 'FIRST_OVERNIGHT', 'INTERNATIONAL_PRIORITY'] and timestamp_day == 'Friday'):
                SpecialServiceTypes = self.factory.ShipmentSpecialServiceType('SATURDAY_DELIVERY')
                self.RequestedShipment.SpecialServicesRequested = self.factory.PackageSpecialServicesRequested()
                self.RequestedShipment.SpecialServicesRequested.SpecialServiceTypes = SpecialServiceTypes

    def set_currency(self, currency):
        self.RequestedShipment.PreferredCurrency = currency
        # self.RequestedShipment.RateRequestTypes = 'PREFERRED'

    def set_master_package(self, total_weight, package_count, master_tracking_id=False):
        self.RequestedShipment.TotalWeight.Value = total_weight
        self.RequestedShipment.PackageCount = package_count
        if master_tracking_id:
            self.RequestedShipment.MasterTrackingId = self.factory.TrackingId()
            self.RequestedShipment.MasterTrackingId.TrackingIdType = 'FEDEX'
            self.RequestedShipment.MasterTrackingId.TrackingNumber = master_tracking_id

    def add_package(self, weight_value, package_code=False, package_height=0, package_width=0, package_length=0, sequence_number=False, mode='shipping'):
        # TODO remove in master and change the signature of a public method
        return self._add_package(weight_value=weight_value, package_code=package_code, package_height=package_height, package_width=package_width,
                                 package_length=package_length, sequence_number=sequence_number, mode=mode, po_number=False, dept_number=False)

    def _add_package(self, weight_value, package_code=False, package_height=0, package_width=0, package_length=0, sequence_number=False, mode='shipping', po_number=False, dept_number=False, reference=False):
        package = self.factory.RequestedPackageLineItem()
        package_weight = self.factory.Weight()
        package_weight.Value = weight_value
        package_weight.Units = self.RequestedShipment.TotalWeight.Units

        package.PhysicalPackaging = 'BOX'
        if package_code == 'YOUR_PACKAGING':
            package.Dimensions = self.factory.Dimensions()
            package.Dimensions.Height = package_height
            package.Dimensions.Width = package_width
            package.Dimensions.Length = package_length
            # TODO in master, add unit in product packaging and perform unit conversion
            package.Dimensions.Units = "IN" if self.RequestedShipment.TotalWeight.Units == 'LB' else 'CM'
        if po_number:
            po_reference = self.factory.CustomerReference()
            po_reference.CustomerReferenceType = 'P_O_NUMBER'
            po_reference.Value = po_number
            package.CustomerReferences.append(po_reference)
        if dept_number:
            dept_reference = self.factory.CustomerReference()
            dept_reference.CustomerReferenceType = 'DEPARTMENT_NUMBER'
            dept_reference.Value = dept_number
            package.CustomerReferences.append(dept_reference)
        if reference:
            customer_reference = self.factory.CustomerReference()
            customer_reference.CustomerReferenceType = 'CUSTOMER_REFERENCE'
            customer_reference.Value = reference
            package.CustomerReferences.append(customer_reference)

        package.Weight = package_weight
        if mode == 'rating':
            package.GroupPackageCount = 1
        if sequence_number:
            package.SequenceNumber = sequence_number
        else:
            self.hasOnePackage = True

        if mode == 'rating':
            self.RequestedShipment.RequestedPackageLineItems.append(package)
        else:
            self.RequestedShipment.RequestedPackageLineItems = package

    # Rating stuff

    def start_rating_transaction(self, wsdl_path):
        settings = Settings(strict=False)
        self.client = Client('file:///%s' % wsdl_path.lstrip('/'), plugins=[LogPlugin(self.debug_logger)], settings=settings)
        self.factory = self.client.type_factory('ns0')
        self.VersionId = self.factory.VersionId()
        self.VersionId.ServiceId = 'crs'
        self.VersionId.Major = '16'
        self.VersionId.Intermediate = '0'
        self.VersionId.Minor = '0'

    def rate(self):
        formatted_response = {'price': {}}
        del self.ClientDetail['Region']
        if self.hasCommodities:
            self.RequestedShipment.CustomsClearanceDetail.Commodities = self.listCommodities

        try:
            self.response = self.client.service.getRates(WebAuthenticationDetail=self.WebAuthenticationDetail,
                                                         ClientDetail=self.ClientDetail,
                                                         TransactionDetail=self.TransactionDetail,
                                                         Version=self.VersionId,
                                                         RequestedShipment=self.RequestedShipment)
            if (self.response.HighestSeverity != 'ERROR' and self.response.HighestSeverity != 'FAILURE'):
                if not getattr(self.response, "RateReplyDetails", False):
                    raise Exception("No rating found")
                for rating in self.response.RateReplyDetails[0].RatedShipmentDetails:
                    formatted_response['price'][rating.ShipmentRateDetail.TotalNetFedExCharge.Currency] = float(rating.ShipmentRateDetail.TotalNetFedExCharge.Amount)
                if len(self.response.RateReplyDetails[0].RatedShipmentDetails) == 1:
                    if 'CurrencyExchangeRate' in self.response.RateReplyDetails[0].RatedShipmentDetails[0].ShipmentRateDetail and self.response.RateReplyDetails[0].RatedShipmentDetails[0].ShipmentRateDetail['CurrencyExchangeRate']:
                        formatted_response['price'][self.response.RateReplyDetails[0].RatedShipmentDetails[0].ShipmentRateDetail.CurrencyExchangeRate.FromCurrency] = float(self.response.RateReplyDetails[0].RatedShipmentDetails[0].ShipmentRateDetail.TotalNetFedExCharge.Amount) / float(self.response.RateReplyDetails[0].RatedShipmentDetails[0].ShipmentRateDetail.CurrencyExchangeRate.Rate)
            else:
                errors_message = '\n'.join([("%s: %s" % (n.Code, n.Message)) for n in self.response.Notifications if (n.Severity == 'ERROR' or n.Severity == 'FAILURE')])
                formatted_response['errors_message'] = errors_message

            if any([n.Severity == 'WARNING' for n in self.response.Notifications]):
                warnings_message = '\n'.join([("%s: %s" % (n.Code, n.Message)) for n in self.response.Notifications if n.Severity == 'WARNING'])
                formatted_response['warnings_message'] = warnings_message

        except Fault as fault:
            formatted_response['errors_message'] = fault
        except IOError:
            formatted_response['errors_message'] = "Fedex Server Not Found"
        except Exception as e:
            formatted_response['errors_message'] = e.args[0]

        return formatted_response

    # Shipping stuff

    def start_shipping_transaction(self, wsdl_path):
        self.client = Client('file:///%s' % wsdl_path.lstrip('/'), plugins=[LogPlugin(self.debug_logger)])
        self.factory = self.client.type_factory("ns0")
        self.VersionId = self.factory.VersionId()
        self.VersionId.ServiceId = 'ship'
        self.VersionId.Major = '15'
        self.VersionId.Intermediate = '0'
        self.VersionId.Minor = '0'

    def shipment_label(self, label_format_type, image_type, label_stock_type, label_printing_orientation, label_order):
        LabelSpecification = self.factory.LabelSpecification()
        LabelSpecification.LabelFormatType = label_format_type
        LabelSpecification.ImageType = image_type
        LabelSpecification.LabelStockType = label_stock_type
        LabelSpecification.LabelPrintingOrientation = label_printing_orientation
        LabelSpecification.LabelOrder = label_order
        self.RequestedShipment.LabelSpecification = LabelSpecification

    def commercial_invoice(self, document_stock_type, send_etd=False):
        shipping_document = self.factory.ShippingDocumentSpecification()
        shipping_document.ShippingDocumentTypes = "COMMERCIAL_INVOICE"
        commercial_invoice_detail = self.factory.CommercialInvoiceDetail()
        commercial_invoice_detail.Format = self.factory.ShippingDocumentFormat()
        commercial_invoice_detail.Format.ImageType = "PDF"
        commercial_invoice_detail.Format.StockType = document_stock_type
        shipping_document.CommercialInvoiceDetail = commercial_invoice_detail
        self.RequestedShipment.ShippingDocumentSpecification = shipping_document
        if send_etd:
            self.RequestedShipment.SpecialServicesRequested.SpecialServiceTypes.append('ELECTRONIC_TRADE_DOCUMENTS')
            etd_details = self.factory.EtdDetail()
            etd_details.RequestedDocumentCopies.append('COMMERCIAL_INVOICE')
            self.RequestedShipment.SpecialServicesRequested.EtdDetail = etd_details

    def shipping_charges_payment(self, shipping_charges_payment_account):
        self.RequestedShipment.ShippingChargesPayment = self.factory.Payment()
        self.RequestedShipment.ShippingChargesPayment.PaymentType = 'SENDER'
        Payor = self.factory.Payor()
        Payor.ResponsibleParty = self.factory.Party()
        Payor.ResponsibleParty.AccountNumber = shipping_charges_payment_account
        self.RequestedShipment.ShippingChargesPayment.Payor = Payor

    def duties_payment(self, sender_party, responsible_account_number, payment_type):
        self.RequestedShipment.CustomsClearanceDetail.DutiesPayment = self.factory.Payment()
        self.RequestedShipment.CustomsClearanceDetail.DutiesPayment.PaymentType = payment_type
        if payment_type == 'SENDER':
            Payor = self.factory.Payor()
            Payor.ResponsibleParty = self.factory.Party()
            Payor.ResponsibleParty.Address = self.factory.Address()
            Payor.ResponsibleParty.Address.CountryCode = sender_party.country_id.code
            Payor.ResponsibleParty.AccountNumber = responsible_account_number
            self.RequestedShipment.CustomsClearanceDetail.DutiesPayment.Payor = Payor

    def customs_value(self, customs_value_currency, customs_value_amount, document_content):
        self.RequestedShipment.CustomsClearanceDetail = self.factory.CustomsClearanceDetail()
        self.RequestedShipment.CustomsClearanceDetail.CustomsValue = self.factory.Money()
        self.RequestedShipment.CustomsClearanceDetail.CustomsValue.Currency = customs_value_currency
        self.RequestedShipment.CustomsClearanceDetail.CustomsValue.Amount = customs_value_amount
        if self.RequestedShipment.Shipper.Address.CountryCode == "IN" and self.RequestedShipment.Recipient.Address.CountryCode == "IN":
            self.RequestedShipment.CustomsClearanceDetail.CommercialInvoice.Purpose = 'SOLD'
            del self.RequestedShipment.CustomsClearanceDetail.CommercialInvoice.TaxesOrMiscellaneousChargeType

        # Old keys not requested anymore but still in WSDL; not removing them causes crash
        del self.RequestedShipment.CustomsClearanceDetail['ClearanceBrokerage']
        del self.RequestedShipment.CustomsClearanceDetail['FreightOnValue']

        self.RequestedShipment.CustomsClearanceDetail.DocumentContent = document_content

    def commodities(self, commodity_currency, commodity_amount, commodity_number_of_piece, commodity_weight_units,
                    commodity_weight_value, commodity_description, commodity_country_of_manufacture, commodity_quantity,
                    commodity_quantity_units, commodity_harmonized_code):
        self.hasCommodities = True
        commodity = self.factory.Commodity()
        commodity.UnitPrice = self.factory.Money()
        commodity.UnitPrice.Currency = commodity_currency
        commodity.UnitPrice.Amount = commodity_amount
        commodity.NumberOfPieces = commodity_number_of_piece
        commodity.CountryOfManufacture = commodity_country_of_manufacture

        commodity_weight = self.factory.Weight()
        commodity_weight.Value = commodity_weight_value
        commodity_weight.Units = commodity_weight_units

        commodity.Weight = commodity_weight
        commodity.Description = re.sub(r'[\[\]<>;={}"|]', '', commodity_description)
        commodity.Quantity = commodity_quantity
        commodity.QuantityUnits = commodity_quantity_units
        customs_value = self.factory.Money()
        customs_value.Currency = commodity_currency
        customs_value.Amount = commodity_quantity * commodity_amount
        commodity.CustomsValue = customs_value

        commodity.HarmonizedCode = commodity_harmonized_code

        self.listCommodities.append(commodity)

    def return_label(self, tracking_number, origin_date):
        shipment_special_services = self.factory.ShipmentSpecialServicesRequested()
        shipment_special_services.SpecialServiceTypes = ["RETURN_SHIPMENT"]
        return_details = self.factory.ReturnShipmentDetail()
        return_details.ReturnType = "PRINT_RETURN_LABEL"
        if tracking_number and origin_date:
            return_association = self.factory.ReturnAssociationDetail()
            return_association.TrackingNumber = tracking_number
            return_association.ShipDate = origin_date
            return_details.ReturnAssociation = return_association
        shipment_special_services.ReturnShipmentDetail = return_details
        self.RequestedShipment.SpecialServicesRequested = shipment_special_services
        if self.hasCommodities:
            bla = self.factory.CustomsOptionDetail()
            bla.Type = "FAULTY_ITEM"
            self.RequestedShipment.CustomsClearanceDetail.CustomsOptions = bla

    def process_shipment(self):
        if self.hasCommodities:
            self.RequestedShipment.CustomsClearanceDetail.Commodities = self.listCommodities
        formatted_response = {'tracking_number': 0.0,
                              'price': {},
                              'master_tracking_id': None,
                              'date': None}

        try:
            self.response = self.client.service.processShipment(WebAuthenticationDetail=self.WebAuthenticationDetail,
                                                                ClientDetail=self.ClientDetail,
                                                                TransactionDetail=self.TransactionDetail,
                                                                Version=self.VersionId,
                                                                RequestedShipment=self.RequestedShipment)

            if (self.response.HighestSeverity != 'ERROR' and self.response.HighestSeverity != 'FAILURE'):
                formatted_response['tracking_number'] = self.response.CompletedShipmentDetail.CompletedPackageDetails[0].TrackingIds[0].TrackingNumber
                if 'CommitDate' in self.response.CompletedShipmentDetail.OperationalDetail:
                    formatted_response['date'] = self.response.CompletedShipmentDetail.OperationalDetail.CommitDate
                else:
                    formatted_response['date'] = date.today()

                if (self.RequestedShipment.RequestedPackageLineItems.SequenceNumber == self.RequestedShipment.PackageCount) or self.hasOnePackage:
                    if 'ShipmentRating' in self.response.CompletedShipmentDetail and self.response.CompletedShipmentDetail.ShipmentRating:
                        for rating in self.response.CompletedShipmentDetail.ShipmentRating.ShipmentRateDetails:
                            formatted_response['price'][rating.TotalNetFedExCharge.Currency] = float(rating.TotalNetFedExCharge.Amount)
                            if 'CurrencyExchangeRate' in rating and rating.CurrencyExchangeRate:
                                formatted_response['price'][rating.CurrencyExchangeRate.FromCurrency] = float(rating.TotalNetFedExCharge.Amount / rating.CurrencyExchangeRate.Rate)
                    else:
                        formatted_response['price']['USD'] = 0.0
                if 'MasterTrackingId' in self.response.CompletedShipmentDetail:
                    formatted_response['master_tracking_id'] = self.response.CompletedShipmentDetail.MasterTrackingId.TrackingNumber

            else:
                errors_message = '\n'.join([("%s: %s" % (n.Code, n.Message)) for n in self.response.Notifications if (n.Severity == 'ERROR' or n.Severity == 'FAILURE')])
                formatted_response['errors_message'] = errors_message

            if any([n.Severity == 'WARNING' for n in self.response.Notifications]):
                warnings_message = '\n'.join([("%s: %s" % (n.Code, n.Message)) for n in self.response.Notifications if n.Severity == 'WARNING'])
                formatted_response['warnings_message'] = warnings_message

        except Fault as fault:
            formatted_response['errors_message'] = fault
        except IOError:
            formatted_response['errors_message'] = "Fedex Server Not Found"

        return formatted_response

    def _get_labels(self, file_type):
        labels = [self.get_label()]
        if file_type.upper() in ['PNG'] and self.response.CompletedShipmentDetail.CompletedPackageDetails[0].PackageDocuments:
            for auxiliary in self.response.CompletedShipmentDetail.CompletedPackageDetails[0].PackageDocuments[0].Parts:
                labels.append(auxiliary.Image)

        return labels

    def get_label(self):
        return self.response.CompletedShipmentDetail.CompletedPackageDetails[0].Label.Parts[0].Image

    def get_document(self):
        if self.response.CompletedShipmentDetail.ShipmentDocuments:
            return self.response.CompletedShipmentDetail.ShipmentDocuments[0].Parts[0].Image
        else:
            return False

    # Deletion stuff

    def set_deletion_details(self, tracking_number):
        self.TrackingId = self.factory.TrackingId()
        self.TrackingId.TrackingIdType = 'FEDEX'
        self.TrackingId.TrackingNumber = tracking_number

        self.DeletionControl = self.factory.DeletionControlType('DELETE_ALL_PACKAGES')

    def delete_shipment(self):
        formatted_response = {'delete_success': False}
        try:
            # Here, we send the Order 66
            self.response = self.client.service.deleteShipment(WebAuthenticationDetail=self.WebAuthenticationDetail,
                                                               ClientDetail=self.ClientDetail,
                                                               TransactionDetail=self.TransactionDetail,
                                                               Version=self.VersionId,
                                                               TrackingId=self.TrackingId,
                                                               DeletionControl=self.DeletionControl)

            if (self.response.HighestSeverity != 'ERROR' and self.response.HighestSeverity != 'FAILURE'):
                formatted_response['delete_success'] = True
            else:
                errors_message = '\n'.join([("%s: %s" % (n.Code, n.Message)) for n in self.response.Notifications if (n.Severity == 'ERROR' or n.Severity == 'FAILURE')])
                formatted_response['errors_message'] = errors_message

            if any([n.Severity == 'WARNING' for n in self.response.Notifications]):
                warnings_message = '\n'.join([("%s: %s" % (n.Code, n.Message)) for n in self.response.Notifications if n.Severity == 'WARNING'])
                formatted_response['warnings_message'] = warnings_message

        except Fault as fault:
            formatted_response['errors_message'] = fault
        except IOError:
            formatted_response['errors_message'] = "Fedex Server Not Found"

        return formatted_response
