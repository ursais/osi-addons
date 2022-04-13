odoo.define("web_many2many_groupby.GroupByMenu", function (require) {
    "use strict";

    const GroupByMenu = require("web.GroupByMenu");
    const {GROUPABLE_TYPES} = require("web.searchUtils");

    GroupByMenu.prototype._validateField = function (field) {
        return (
            (field.sortable &&
                GROUPABLE_TYPES.includes(field.type) &&
                field.name !== "id") ||
            (field.type === "many2many" && field.store)
        );
    };
    GROUPABLE_TYPES.push("many2many");
});
