odoo.define('website_sale.tour_shop_cart_recovery', function (require) {
    'use strict';

    var ajax = require('web.ajax');
    require('web.dom_ready');

    var btn_find = $('.btn_find_instance');
    var btn_find_anchor = $('#btn_find_anchor');
    if (!btn_find.length) {
        return Promise.reject("DOM doesn't contain '.btn_find_instance'");
    }
    if (!btn_find_anchor.length) {
        return Promise.reject("DOM doesn't contain '.btn_find_instance'");
    }

    btn_find.click(function () {
        ajax.jsonRpc('/website_sale/instance_name', 'call', {
            'data': [
                ['instance_name', '=', $('#input_instance_name').val()],
            ],
        }).then(function (result) {
            if (result > 0) {
                $('#is_unavailble').removeClass('d-none');
                $('#is_availble').addClass('d-none');
            } else {
                $('#is_availble').removeClass('d-none');
                $('#is_unavailble').addClass('d-none');
            }

        });
    });
    btn_find_anchor.click(function () {
        this.$form = $('#instance_form');
        this.$form.trigger('submit', [true]);
    });
});
