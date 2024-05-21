/** @odoo-module **/
import { registry } from "@web/core/registry";
import { Component } from "@odoo/owl";
import { session } from '@web/session';
import { _t } from "@web/core/l10n/translation";

export class LoginAs extends Component {
    static props = {};
    static template = "oi_login_as.LoginAs";

    setup() {
        
    }

    get impersonate() {
        return session.impersonate;
    }

    _onClick() {
        let action;
        if (this.impersonate) {
            action = {
                type: 'ir.actions.act_url',
                url: '/web/login_back',
                target: 'self'
            }
        }
        else {
            action = {
                type: 'ir.actions.act_window',
                name: _t('Login as'),
                views: [[false, 'form']],
                res_model: 'login.as',
                target: 'new',
            }
        }
        this.env.services.action.doAction(action);
    }
}

export const systrayItem = {
    Component: LoginAs,
    isDisplayed: (env) => (env.debug && env.services.user.isSystem) || session.impersonate,
};

registry.category("systray").add("LoginAsSystrayItem", systrayItem, { sequence: 1 });
