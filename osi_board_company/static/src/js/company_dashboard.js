odoo.define('osi_board_company.CompanyDashboardView', function (require) {
    "use strict";

    var AbstractAction = require('web.AbstractAction');
    var ajax = require('web.ajax');
    var core = require('web.core');
    var field_utils = require('web.field_utils');
    var utils = require('web.utils');

    var _t = core._t;
    var _lt = core._lt;
    var QWeb = core.qweb;

    var CompanyDashboard = AbstractAction.extend({
        cssLibs: ['/osi_board_employee/static/src/css/dashboard.css'],

        willStart: function () {
            var self = this;
            return $.when(ajax.loadLibs(this), this._super());
        },
        start: function () {
            var self = this;
            return this._super().then(function () {
                self.render_dashboard();
            });
        },

        render_dashboard: function () {
            var self = this;

            self.get_data();
        },

        get_data: function () {
            var self = this;
            this._rpc({
                model: 'company.dashboard',
                method: 'get_company_data',
                args: [
                    []
                ]
            }).then(function (details) {
                self.$el.append(QWeb.render('company_dashboard', {
                    widget: self,
                    details: details
                }));
                $('#open_employee_dashboard').on('click', function (event) {
                    self.do_action("employee_dashboard");
                });
                $('#open_employee_timesheet').on('click', function (event) {
                    self.do_action({
                        type: 'ir.actions.act_window',
                        name: "My Timesheet",
                        res_model: 'account.analytic.line',
                        views: [[false, 'list'], [false, 'form']],
                        domain: [['project_id', '!=', false]],
                        context : {'search_default_mine':1},
                        target: 'current'
                    });
                });
            });
        },

        formate_date: function (value) {
            return field_utils.format.date(field_utils.parse.date(value))
        },
        formate_float: function (value) {
            value = value.toString()
            return field_utils.format.float(field_utils.parse.float(value))
        },
        float_time: function (number) {
            // Check sign of given number
            var sign = (number >= 0) ? 1 : -1;

            // Set positive value of number of sign negative
            number = number * sign;

            // Separate the int from the decimal part
            var hour = Math.floor(number);
            var decpart = number - hour;

            var min = 1 / 60;
            // Round to nearest minute
            decpart = min * Math.round(decpart / min);

            var minute = Math.floor(decpart * 60) + '';

            // Add padding if need
            if (minute.length < 2) {
                minute = '0' + minute;
            }

            // Add Sign in final result
            sign = sign == 1 ? '' : '-';

            // Concate hours and minutes
            var time = sign + hour + ':' + minute;

            return time;
        },
    });

    core.action_registry.add('company_dashboard', CompanyDashboard);

    return CompanyDashboard;

});
