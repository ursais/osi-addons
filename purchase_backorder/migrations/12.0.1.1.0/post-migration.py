from odoo import api, SUPERUSER_ID


def recompute_po_lines(env):
    lines = env['purchase.order.line'].search([])
    lines._compute_bo_qty_value()


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    recompute_po_lines(env)
