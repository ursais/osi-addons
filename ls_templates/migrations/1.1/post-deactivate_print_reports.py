import logging

import odoo.api

_logger = logging.getLogger(__name__)

def remove_from_print_menu(cr, id):
    # NOTE: be careful when using the SUPERUSER_ID! Use the appropriate user when doing this
    env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})

    invoices_report = env['ir.actions.report'].search([('id', '=', id)])
    _logger.info(f'Now deactivating ir.actions.report with name {invoices_report.name} (ID {id})...')

    return invoices_report.filtered('binding_model_id').write({'binding_model_id': False})

def migrate(cr, installed_version):
    _logger.info(f'Start Migration script for: ls_templates v1.1')

    _logger.info(f'Beginning removal of obsolete invoice report templates from Print menues.')
    obsolete_ids = [270, 2431]

    for oid in obsolete_ids:
        res = remove_from_print_menu(cr, id=oid)
        _logger.info(f'...result : {res}')

    _logger.info(f'Migration script Finished for: ls_templates v1.1')
