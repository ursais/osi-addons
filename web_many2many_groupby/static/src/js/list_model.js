odoo.define("web_many2many_groupby.ListModel", function (require) {
    "use strict";

    const ListModel = require("web.ListModel");
    ListModel.include({
        saveRecords: function (
            listDatapointId,
            referenceRecordId,
            recordIds,
            fieldName,
        ) {
            var self = this;
            var referenceRecord = this.localData[referenceRecordId];
            var list = this.localData[listDatapointId];
            // Generate all record values to ensure that we'll write something
            // (e.g. 2 records selected, edit a many2one in the first one, but
            // reset same value, we still want to save this value on the other
            // record)
            var allChanges = this._generateChanges(referenceRecord, {
                changesOnly: false,
            });
            var changes = _.pick(allChanges, fieldName);
            var records = recordIds.map(function (recordId) {
                return self.localData[recordId];
            });
            var model = records[0].model;
            var recordResIds = _.pluck(records, "res_id");
            var fieldNames = records[0].getFieldNames();
            var context = records[0].getContext();

            return this._rpc({
                model: model,
                method: "write",
                args: [recordResIds, changes],
                context: context,
            })
                .then(function () {
                    return self._rpc({
                        model: model,
                        method: "read",
                        args: [recordResIds, fieldNames],
                        context: context,
                    });
                })
                .then(function (results) {
                    const updateLocalRecord = (id, data) => {
                        const record = self.localData[id];
                        record.data = _.extend({}, record.data, data);
                        record._changes = {};
                        record._isDirty = false;
                        self._parseServerData(fieldNames, record, record.data);
                    };

                    results.forEach(function (data) {
                        const record = _.findWhere(records, {
                            res_id: data.id,
                        });
                        updateLocalRecord(record.id, data);

                        // Also update same resId records
                        self._updateDuplicateRecords(record.id, (id) =>
                            updateLocalRecord(id, data),
                        );
                    });
                })
                .then(function () {
                    if (!list.groupedBy.length) {
                        return Promise.all([
                            self._fetchX2ManysBatched(list),
                            self._fetchReferencesBatched(list),
                        ]);
                    }
                    return Promise.all([
                        self._fetchX2ManysSingleBatch(list),
                        self._fetchReferencesSingleBatch(list),
                    ]);
                });
        },
    });
});
