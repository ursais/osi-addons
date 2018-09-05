# -*- coding: utf-8 -*-
# Copyright (C) 2012 - TODAY Ursa Information Systems
# Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>)

from openerp.osv import osv
from openerp.report import report_sxw


class BomStructure(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(BomStructure, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'get_children': self.get_children,
        })

    def get_children(self, object, level=0):
        result = []

        def _get_rec(object, level):
            for l in object:
                res = {}
                res['pname'] = l.product_id.name
                res['pcode'] = l.product_id.default_code
                res['pqty'] = l.product_qty
                res['on_hand'] = l.product_id.qty_available
                res['uname'] = l.product_uom.name
                res['level'] = level
                res['code'] = l.bom_id.code
                result.append(res)
                if l.child_line_ids:
                    if level < 6:
                        level += 1
                    _get_rec(l.child_line_ids, level)
                    if level > 0 and level < 6:
                        level -= 1
            return result
        children = _get_rec(object, level)
        return children


class ReportMrpbomstructure(osv.AbstractModel):
    _name = 'report.mrp_extended.report_mrpbomstructure_ext'
    _inherit = 'report.abstract_report'
    _template = 'mrp_extended.report_mrpbomstructure_ext'
    _wrapped_report_class = BomStructure
