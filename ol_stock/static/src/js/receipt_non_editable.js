/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { StockMoveX2ManyField, MovesListRenderer } from "@stock/views/picking_form/stock_move_one2many";

patch(StockMoveX2ManyField.prototype, {
    setup(){
        super.setup()
        if (this.props.record.data.picking_type_code == 'incoming'){
            this.activeActions.create = false;
        }
    },
})

patch(MovesListRenderer.prototype, {
    processAllColumn(allColumns, list) {        
        let cols = super.processAllColumn(...arguments);        
        if (list.resModel === "stock.move") {
            if (this.env && this.env.model.root && this.env.model.root.data.picking_type_code == 'incoming'){
                this.props.activeActions.create = false;
            }
        }
        return cols
    },
})