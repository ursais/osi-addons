odoo.define('osi_analytic_segments.bank_reconciliation_renderer', function (require) {
    "use strict";

    var ReconciliationRenderer = require('account.ReconciliationRenderer');
    var relational_fields = require('web.relational_fields');
    var core = require('web.core');
    var qweb = core.qweb;
    var _t = core._t;

    console.log("File has been called.");
    var Renderer = {
        /**
         * create account_id, tax_id, analytic_account_id, analytic_tag_ids, label and amount fields
         *
         * @private
         * @param {object} state - statement line
         */
        _renderCreate: function (state) {
            console.log("IT SHOULD BE CALLED!");
            this._super(state);
            var self = this;
            this.model.makeRecord('account.bank.statement.line', [{
                relation: 'analytic.segment.one',
                type: 'many2one',
                name: 'analytic_segment_one_id'
            },{
                relation: 'analytic.segment.two',
                type: 'many2one',
                name: 'analytic_segment_two_id'
            }], {
                analytic_segment_one_id: {string: _t("Segment One")},
                analytic_segment_two_id: {string: _t("Segment Two")},
            }).then(function (recordID) {
                self.handleCreateRecord = recordID;
                var record = self.model.get(self.handleCreateRecord);

                self.fields.analytic_segment_one_id = new relational_fields.FieldMany2One(self,
                    'analytic_segment_one_id', record, {mode: 'edit'});
                self.fields.analytic_segment_two_id = new relational_fields.FieldMany2One(self,
                    'analytic_segment_two_id', record, {mode: 'edit'});

                var $create = $(qweb.render("reconciliation.line.create", {'state': state}));
                self.fields.analytic_segment_one_id.appendTo($create.find('.create_analytic_segment_one_id .o_td_field'))
                    .then(addRequiredStyle.bind(self, self.fields.analytic_segment_one_id));
                self.fields.analytic_segment_two_id.appendTo($create.find('.create_analytic_segment_two_id .o_td_field'))
                    .then(addRequiredStyle.bind(self, self.fields.analytic_segment_two_id));
                self.$('.create').append($create);

                function addRequiredStyle(widget) {
                    widget.$el.addClass('o_required_modifier');
                }
            });
        },
    };
    ReconciliationRenderer.LineRenderer.include(Renderer);
});
