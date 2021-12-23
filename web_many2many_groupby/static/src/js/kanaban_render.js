odoo.define("web_many2many_groupby.KanbanRenderer", function (require) {
    "use strict";

    const KanbanRenderer = require("web.KanbanRenderer");
    KanbanRenderer.include({
        _setState: function () {
            this._super(...arguments);
            var groupByField = this.state.groupedBy[0];
            var cleanGroupByField = this._cleanGroupByField(groupByField);
            var groupByFieldAttrs = this.state.fields[cleanGroupByField];
            if (groupByFieldAttrs) {
                if (groupByFieldAttrs.type === "many2many") {
                    this.columnOptions = _.extend(this.columnOptions, {
                        draggable: false,
                    });
                }
            }
        },
    });
});
