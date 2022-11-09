odoo.define('osi_purchase_product_configurator.osi_purchase_product_configurator', function (require) {

    var ProductConfiguratorWidget = require('sale.product_configurator');
    ProductConfiguratorWidget.include({ 
        _openConfigurator: function (result, productTemplateId, dataPointId) {
            if (this.model === 'purchase.order.line'){
                if (!result.mode || result.mode === 'configurator') {
                    this._openProductConfigurator({
                            configuratorMode: result && result.has_optional_products ? 'options' : 'add',
                            default_product_template_id: productTemplateId
                        },
                        dataPointId
                    );
                    return Promise.resolve(true);
                }
                return Promise.resolve(false);
            }
            return this._super.apply(this, arguments);

        },
    })

});