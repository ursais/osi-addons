/** @odoo-module **/
/*eslint-disable*/
import {patch} from "@web/core/utils/patch";
import {Many2OneField} from "@web/views/fields/many2one/many2one_field";

patch(Many2OneField.prototype, {
    computeActiveActions(props) {
        var element = super.computeActiveActions(...arguments);
        if (element === undefined) {
            return $();
        }
        return element;
    },
});
