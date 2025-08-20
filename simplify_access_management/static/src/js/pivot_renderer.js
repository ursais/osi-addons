/** @odoo-module **/

const {PivotRenderer} = require("@web/views/pivot/pivot_renderer"); 
const {patch} = require("@web/core/utils/patch");
const {useService} = require("@web/core/utils/hooks");  
const {onWillStart} = require("@odoo/owl");
patch(PivotRenderer.prototype, {
    setup() {
        super.setup(...arguments);
        this.orm = useService("orm"); 
        onWillStart(async()=>{  
            const res = await this.orm.call("access.management", "get_hidden_field", ["",
                this?.env?.searchModel?.resModel,
            ]);
            this.restricted_fields = res;
        });
    },
});