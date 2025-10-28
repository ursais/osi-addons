/** @odoo-module **/

import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { useBus, useService } from "@web/core/utils/hooks";
import { Component, xml } from "@odoo/owl";

export class OnLogicBarcodeHandlerField extends Component {
    /*
    This class is a new version of the BarcodeHandlerField specifically for use in the Put in Pack app.
    The differences with this field is that we not letting the barcode scanning be asynchronous, rather
    waiting for each function to finish in sequence so that we can explicitly save the record. This would
    be the same as if the user clicked the save button on a form view.
    */
    setup() {
        const barcode = useService("barcode");
        useBus(barcode.bus, "barcode_scanned", this.onBarcodeScanned);
    }
    async onBarcodeScanned(event) {
        const { barcode } = event.detail;
        await this.props.record.update({ [this.props.name]: barcode });
        await this.props.record.save()
    }


}

OnLogicBarcodeHandlerField.template = xml``;
OnLogicBarcodeHandlerField.props = { ...standardFieldProps };

export const onlogicBarcodeHandlerField = {
    component: OnLogicBarcodeHandlerField,
};

registry.category("fields").add("onlogic_barcode_handler", onlogicBarcodeHandlerField);
