# -*- coding: utf-8 -*-
# Copyright 2018 Sodexis
# License OPL-1 (See LICENSE file for full copyright and licensing details).

from lxml import etree

from odoo.addons.payment_authorize.models.authorize_request import AuthorizeAPI

def getTransactionDetailsResponse(self, acquirer_reference):
    root = self._base_tree('getTransactionDetailsRequest')
    print ("getTransactionDetailsResponse called >>>>>>>>>>>>>>>>")
    etree.SubElement(root, "transId").text = acquirer_reference
    response = self._authorize_request(root)
    if response.find('transaction/transactionStatus') is not None:
        auth_response = response.find('transaction/transactionStatus').text
        return auth_response
    else:
        return response.find('messages/message/text').text if response.find('messages/message/text').text else 'not found'

AuthorizeAPI.getTransactionDetailsResponse = getTransactionDetailsResponse
