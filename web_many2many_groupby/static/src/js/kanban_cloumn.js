odoo.define("web_many2many_groupby.KanbanColumn", function (require) {
    "use strict";

    const KanbanColumn = require("web.KanbanColumn");
    var core = require("web.core");
    var _t = core._t;

    KanbanColumn.include({
        init: function (parent, data, options, recordOptions) {
            this.grouped_by_m2m = options.grouped_by_m2m;
            var value = data.value;
            if (options.grouped_by_m2m) {
                this.title = value ? value : _t("Undefined");
            }
            return this._super(parent, data, options, recordOptions);
        },
        _addRecord: function (recordState, options) {
            if (this.grouped_by_m2m) {
                this.record_options.deletable = false;
            }
            return this._super(recordState, options);
        },
    });
});
