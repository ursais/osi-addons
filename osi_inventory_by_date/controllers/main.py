#################################################################################
#
# Copyright (c) 2015-Present TidyWay Software Solution. (<https://tidyway.in/>)
#
#################################################################################

import base64

from odoo import http
from odoo.http import request

from odoo.addons.http import content_disposition


class Binary(http.Controller):
    @http.route("/web/binary/download_document", type="http", auth="public")
    def download_document(self, model, field, record_id, filename=None, **kw):
        """Download link for files stored as binary fields.
        :param str model: name of the model to fetch the binary from
        :param str field: binary field
        :param str record_id: id of the record from which to fetch the binary
        :param str filename: field holding the file's name, if any
        :returns: :class:`werkzeug.wrappers.Response`
        """
        Model = request.env[model]
        context = request.context
        fields = [field]
        res = Model.browse(int(record_id)).read(fields, context)[0]
        filecontent = base64.b64decode(res.get(field) or "")
        if not filecontent:
            return request.not_found()
        else:
            if not filename:
                filename = "%s_%s" % (model.replace(".", "_"), record_id)
            return request.make_response(
                filecontent,
                [
                    ("Content-Type", "application/octet-stream"),
                    ("Content-Disposition", content_disposition(filename)),
                ],
            )
