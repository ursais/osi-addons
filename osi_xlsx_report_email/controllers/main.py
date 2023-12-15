import base64
import functools
import json
import logging
import operator

import werkzeug
import werkzeug.exceptions
import werkzeug.utils
import werkzeug.wrappers
import werkzeug.wsgi

from odoo import http
from odoo.http import request, serialize_exception as _serialize_exception

from odoo.addons.web.controllers.main import ExcelExport, ExportFormat, GroupsTreeNode

_logger = logging.getLogger(__name__)


def serialize_exception(f):
    @functools.wraps(f)
    def wrap(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            _logger.exception("An exception occured during an http request")
            se = _serialize_exception(e)
            error = {"code": 200, "message": "Odoo Server Error", "data": se}
            return werkzeug.exceptions.InternalServerError(json.dumps(error))

    return wrap


class StockExportFormat(ExportFormat):
    def custom_base(self, data, token):
        print("\n\n\n CUSTOM BASE CALLED ")
        params = json.loads(data)
        model, fields, ids, domain, import_compat = operator.itemgetter(
            "model", "fields", "ids", "domain", "import_compat"
        )(params)

        Model = request.env[model].with_context(
            import_compat=import_compat, **params.get("context", {})
        )
        if not Model._is_an_ordinary_table():
            fields = [field for field in fields if field["name"] != "id"]

        field_names = [f["name"] for f in fields]
        if import_compat:
            columns_headers = field_names
        else:
            columns_headers = [val["label"].strip() for val in fields]

        groupby = params.get("groupby")
        if not import_compat and groupby:
            groupby_type = [Model._fields[x.split(":")[0]].type for x in groupby]
            domain = [("id", "in", ids)] if ids else domain
            groups_data = Model.read_group(
                domain,
                [x if x != ".id" else "id" for x in field_names],
                groupby,
                lazy=False,
            )

            # read_group(lazy=False) returns a dict only for final groups (with actual data),
            # not for intermediary groups. The full group tree must be re-constructed.
            tree = GroupsTreeNode(Model, field_names, groupby, groupby_type)
            for leaf in groups_data:
                tree.insert_leaf(leaf)

            response_data = self.from_group_data(fields, tree)
        else:
            records = (
                Model.browse(ids)
                if ids
                else Model.search(domain, offset=0, limit=False, order=False)
            )

            export_data = records.export_data(field_names).get("datas", [])
            response_data = self.from_data(columns_headers, export_data)

        return response_data


class StockExcelExport(ExcelExport, StockExportFormat):
    @http.route("/web/export/custom/xlsx", type="json", auth="user")
    @serialize_exception
    def index_custom(self, **kwargs):
        print("\n\n\n\n CUSTOM XLSX CALLED")
        data = kwargs.get("data")
        token = kwargs.get("token")
        b_content = None
        try:
            data = json.dumps(data)
            data_fetched = self.custom_base(data, token)
            b_content = base64.encodebytes(data_fetched)

        except Exception as e:
            error_msg = e
        if b_content:
            return {"output": {"code": 200, "data": b_content}}
        else:
            return {"error": {"code": 400, "message": error_msg}}
