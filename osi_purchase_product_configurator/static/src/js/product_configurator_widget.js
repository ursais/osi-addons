odoo.define('osi_purchase_product_configurator.osi_product_configurator', function (require) {
"use strict";

var OSIProductConfiguratorWidget = require('sale_product_configurator.product_configurator');

OSIProductConfiguratorWidget.include({
    _onEditProductConfiguration: function () {
        if (!this.recordData.is_configurable_product) {
            // if line should be edited by another configurator
            // or simply inline.
            this._super.apply(this, arguments);
            return;
        }
        this.restoreProductTemplateId = this.recordData.product_template_id;
        // If line has been set up through the product_configurator:
        if (this.model === 'purchase.order.line') {
            this._openProductConfigurator({
                configuratorMode: 'edit',
                default_product_template_id: this.recordData.product_template_id.data.id,
                default_pricelist_id: this._getPricelistId(),
                default_product_template_attribute_value_ids: this._convertFromMany2Many(
                    this.recordData.product_template_attribute_value_ids
                ),
                default_product_no_variant_attribute_value_ids: this._convertFromMany2Many(
                    this.recordData.product_no_variant_attribute_value_ids
                ),
                default_product_custom_attribute_value_ids: this._convertFromOne2Many(
                    this.recordData.product_custom_attribute_value_ids
                ),
                default_quantity: this.recordData.product_qty
            },
            this.dataPointID
            );
        }
        else {
            this._openProductConfigurator({
                configuratorMode: 'edit',
                default_product_template_id: this.recordData.product_template_id.data.id,
                default_pricelist_id: this._getPricelistId(),
                default_product_template_attribute_value_ids: this._convertFromMany2Many(
                    this.recordData.product_template_attribute_value_ids
                ),
                default_product_no_variant_attribute_value_ids: this._convertFromMany2Many(
                    this.recordData.product_no_variant_attribute_value_ids
                ),
                default_product_custom_attribute_value_ids: this._convertFromOne2Many(
                    this.recordData.product_custom_attribute_value_ids
                ),
                default_quantity: this.recordData.product_uom_qty
            },
            this.dataPointID
            );
        }
    },

    _getMainProductChanges: function (mainProduct) {
        var res = this._super.apply(this, arguments);
        if (this.model === 'purchase.order.line') {
            res.product_qty = res.product_uom_qty;
        }
        return res;
    },

});
});
