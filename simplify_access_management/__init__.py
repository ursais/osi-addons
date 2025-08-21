from . import models
from . import controllers


from odoo import api, SUPERUSER_ID


def uninstall_hook(env):
    env['ir.config_parameter'].search([('key', '=', 'uninstall_check')]).unlink()


def post_install_action_dup_hook(env):
    action_data_obj = env['action.data']
    menu_item_obj = env['menu.item']
    for action in env['ir.actions.actions'].search([]):
        action_data_obj.create({'name': action.name, 'action_id': action.id})
    for menu in env['ir.ui.menu'].search([]):
        menu_item_obj.create({'name': menu.display_name, 'menu_id': menu.id})
