/** @odoo-module **/

import { registry } from "@web/core/registry";
import { formatDateTime } from "@web/core/l10n/dates";
import { localization } from "@web/core/l10n/localization";
import { QtyAtDateWidget, QtyAtDatePopover } from "@sale_stock/widgets/qty_at_date_widget";
import { usePopover } from "@web/core/popover/popover_hook";
import { useService } from "@web/core/utils/hooks";

// ------------------------
// Custom Popover Component
// This extends Odoo's standard `QtyAtDatePopover` used in the "Quantity at Date" widget (sale_stock) to use in estimate lines.
// ------------------------
export class CustomQtyAtDatePopover extends QtyAtDatePopover {
    setup() {
        super.setup();
        this.orm = useService("orm");  
    }

    async openForecast() {
        if (!this.props.record) return;

        // Use the ORM service to call the server method
        const [record] = await this.orm.read("sale.estimate.line.job", [this.props.record.resId], [
            "id"
        ]);

        // Call the method
        const action = await this.orm.call("sale.estimate.line.job", "action_product_forecast_report", [[record.id]]);

        if (action) {
            this.actionService.doAction(action);
        }
    }
}

CustomQtyAtDatePopover.template = "estimate_widget";

// --------------
//  Custom Widget
// --------------
export class CustomQtyAtDateWidget extends QtyAtDateWidget {
    setup() {
        super.setup();
        // Point the popover to the custom one
        this.popover = usePopover(CustomQtyAtDatePopover, { position: "top" });
    }
 
    initCalcData() {
        // calculate data not in record
        const { data } = this.props.record;
        if (data.scheduled_date) {
            this.calcData.will_be_fulfilled = data.virtual_available_at_date >= data.product_uom_qty;
            this.calcData.will_be_late = data.forecast_expected_date && data.forecast_expected_date > data.scheduled_date;
            if (['draft', 'sent'].includes(data.state)) {
                // Moves aren't created yet, then the forecasted is only based on virtual_available of quant
                this.calcData.forecasted_issue = !this.calcData.will_be_fulfilled;
            } else {
                // Moves are created, using the forecasted data of related moves
                this.calcData.forecasted_issue = !this.calcData.will_be_fulfilled || this.calcData.will_be_late;
            }
        }
    }
    updateCalcData() {
        // popup specific data
        const { data } = this.props.record; 
        if (!data.scheduled_date) {
            return;
        }
        this.calcData.delivery_date = formatDateTime(data.scheduled_date, { format: localization.dateFormat });
        if (data.forecast_expected_date) {
            this.calcData.forecast_expected_date_str = formatDateTime(data.forecast_expected_date, { format: localization.dateFormat });
        }
    }

    showPopup(ev) {
        this.updateCalcData();
        this.popover.open(ev.currentTarget, {
            record: this.props.record,
            calcData: this.calcData,
        });
    }
}

// --------------------
//  Register the Widget
// --------------------
registry.category("view_widgets").add(
    "qty_at_date_widget_estimate",
    { component: CustomQtyAtDateWidget },
    { force: true }
);
