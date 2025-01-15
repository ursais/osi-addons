/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.WebsiteSale.include({
    /**
     * Update the root product during an Add process.
     *
     * @private
     * @param {Object} $form
     * @param {Number} productId
     */
    // eslint-disable-next-line no-unused-vars
    _updateRootProduct($form, productId) {
        // Call the original method to keep existing functionality
        this._super.apply(this, arguments);

        // Extend the rootProduct to include the `config_session_id`
        this.rootProduct.config_session_id = $form
            .find('input[name="config_session_id"]')
            .val();
    },
});
