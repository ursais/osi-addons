odoo.define('osi_fsm_timeline.osi_fsm_timeline', function (require) {
"use strict";

    var core = require('web.core');
    var data = require('web.data');
    var session = require('web.session');
    var TimelineRenderer = require('web_timeline.TimelineRenderer');

    var _t = core._t;
    var _lt = core._lt;
    var QWeb = core.qweb;


TimelineRenderer.include({
    init: function (parent, state, params) {
        var self = this;
        this._super.apply(this, arguments);
        this.modelName = params.model;
        this.mode = params.mode;
        this.options = params.options;
        this.permissions = params.permissions;
        this.timeline = params.timeline;
        this.date_start = params.date_start;
        this.date_stop = params.date_stop;
        this.date_delay = params.date_delay;
        this.colors = params.colors;
        this.fieldNames = params.fieldNames;
        this.dependency_arrow = params.dependency_arrow;
        this.view = params.view;
        this.modelClass = this.view.model;
        self.res_users = [];
        self.res_users_ids = [];
        
        // Find their matching names
        this._rpc({
            model: 'fsm.person',
            method: 'get_person_information',
            args: [[session.uid], {}],
        }).then(function (result) {
            self.res_users.push(result);
            for(var r in result){
                self.res_users_ids.push(result[r]['id']);
            }
        });
    },
    
    on_data_loaded_2: function (events, group_bys, adjust_window) {
        var self = this;
        var data = [];
        var groups = [];
        this.grouped_by = group_bys;
        _.each(events, function (event) {
            if (event[self.date_start]) {
                data.push(self.event_data_transform(event));
            }
        });
        var groups = self.split_groups(events, group_bys);
        if (group_bys[0]=="fsm_person_id"){
            var groups_user_ids = [];
            for(var g in groups){
                groups_user_ids.push(groups[g]['id']);
            }
            for(var u in self.res_users_ids){
                if(!(self.res_users_ids[u] in groups_user_ids) || self.res_users_ids[u] != -1){
                    // Get User Name
                    var user_name = '-';
                    for (var n in self.res_users[0]){
                        if (self.res_users[0][n]['id'] == self.res_users_ids[u]){
                            user_name = self.res_users[0][n]['name'];
                        }
                    }
                    var is_available=false;
                    for (var i in groups){
                        if(groups[i]['id']==self.res_users_ids[u]){
                            is_available = true;
                        }
                    }
                    if(!is_available){
                        groups.push({id:self.res_users_ids[u], content: _t(user_name)});
                    }
                }
            }
        }
        this.timeline.setGroups(groups);
        this.timeline.setItems(data);
        var mode = !this.mode || this.mode === 'fit';
        var adjust = _.isUndefined(adjust_window) || adjust_window;
        if (mode && adjust) {
            this.timeline.fit();
        }
    },
});

});