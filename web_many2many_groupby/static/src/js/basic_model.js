odoo.define("web_many2many_groupby.BasicModel", function (require) {
    "use strict";

    const BasicModel = require("web.BasicModel");
    var utils = require("web.utils");

    BasicModel.include({
        __get: function (id, options) {
            if (!(id in this.localData)) {
                return null;
            }
            var list = this._super(id, options);
            var element = this.localData[id];
            if (element.type !== "record") {
                list.isM2MGrouped = element.isM2MGrouped;
            }
            return list;
        },
        save: function (recordID, options) {
            var self = this;
            var prom = this._super(recordID, options);
            prom.then(function () {
                var record = self.localData[recordID];
                self._updateDuplicateRecords(record.id, (id) => {
                    Object.assign(self.localData[id].data, record.data);
                });
            });
            return prom;
        },
        _updateDuplicateRecords (recordID, updateFn) {
            const {model, res_id} = this.localData[recordID];
            // Get the topmost groupedby m2m list
            const getTopmostID = () => {
                let element = this.localData[recordID];
                while (
                    element.parentID &&
                    this.localData[element.parentID].type === "list"
                ) {
                    element = this.localData[element.parentID];
                }
                return element.type === "list" && element.isM2MGrouped
                    ? element.id
                    : false;
            };
            const topmostID = getTopmostID();
            if (!topmostID) {
                return;
            }
            const topmostList = this.get(topmostID);
            utils.traverse_records(topmostList, (r) => {
                if (r.res_id === res_id && r.id !== recordID) {
                    updateFn(r.id);
                }
            });
        },
        _makeDataPoint: function (params) {
            var type = params.type || "domain" in params && "list" || "record";
            var dataPoint = this._super(params);
            const groupedBy = params.groupedBy || [];
            let isM2MGrouped = false;

            if (type != "record") {
                var fields = _.extend(
                    {
                        display_name: {type: "char"},
                        id: {type: "integer"},
                    },
                    params.fields,
                );
                isM2MGrouped = groupedBy.some((group) => {
                    const [fieldName] = group.split(":");
                    return fields[fieldName].type === "many2many";
                });
            }
            dataPoint.isM2MGrouped = isM2MGrouped;
            return dataPoint;
        },
        _reload: function (id, options) {
            options = options || {};
            var element = this.localData[id];
            element.isM2MGrouped = element.groupedBy.some((group) => {
                const [fieldName] = group.split(":");
                return element.fields[fieldName].type === "many2many";
            });
            return this._super(id, options);
        },
    });
});
