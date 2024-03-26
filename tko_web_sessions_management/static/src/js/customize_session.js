/** @odoo-module */

    /* ---------------------------------------------------------
     * Odoo Session Expired
     *---------------------------------------------------------*/

$( document ).ready(function () {
    $("body").click(function () {
        $.getJSON("/ajax/session/", function ( data ) {
            if (data) {
                if (data.result === 'true') {
                    location.reload();
                }
            }
        });
    });
});
