import functools
import logging
import psycopg2

from odoo import api, models, _
from odoo.tools import mute_logger

_logger = logging.getLogger('odoo.addons.base.partner.merge')


class MergePartnerAutomatic(models.TransientModel):
    _inherit = 'base.partner.merge.automatic.wizard'

    @api.model
    def _update_reference_fields(self, src_partners, dst_partner):
        """ Update all reference fields from the src_partner to dst_partner.
            :param src_partners : merge source res.partner recordset (does not include destination one)
            :param dst_partner : record of destination res.partner
        """
        _logger.debug('_update_reference_fields for dst_partner: %s for src_partners: %r', dst_partner.id, src_partners.ids)

        def update_records(model, src, field_model='model', field_id='res_id'):
            Model = self.env[model] if model in self.env else None
            if Model is None:
                return
            records = Model.sudo().search([(field_model, '=', 'res.partner'), (field_id, '=', src.id)])
            try:
                with mute_logger('odoo.sql_db'), self._cr.savepoint():
                    records.sudo().write({field_id: dst_partner.id})
                    records.env.flush_all()
            except psycopg2.Error:
                # updating fails, most likely due to a violated unique constraint
                # keeping record with nonexistent partner_id is useless, better delete it
                records.sudo().unlink()

        update_records = functools.partial(update_records)

        for partner in src_partners:
            update_records('calendar', src=partner, field_model='model_id.model')
            update_records('ir.attachment', src=partner, field_model='res_model')
            update_records('mail.followers', src=partner, field_model='res_model')
            update_records('mail.activity', src=partner, field_model='res_model')
            update_records('mail.message', src=partner)
            update_records('ir.model.data', src=partner)

        records = self.env['ir.model.fields'].sudo().search([('ttype', '=', 'reference')])
        for record in records:
            try:
                Model = self.env[record.model]
                field = Model._fields[record.name]
            except KeyError:
                # unknown model or field => skip
                continue

            if Model._abstract or field.compute is not None:
                continue

            for partner in src_partners:
                records_ref = Model.sudo().search([(record.name, '=', 'res.partner,%d' % partner.id)])
                values = {
                    record.name: 'res.partner,%d' % dst_partner.id,
                }
                records_ref.sudo().write(values)

        self.env.flush_all()

        # Company-dependent fields
        #OSI Method UPD
        try:
            for src_partner in src_partners:
                with self._cr.savepoint():
                    params = {
                        'destination_id': f'res.partner,{dst_partner.id}',
                        'source_ids': tuple(f'res.partner,{src}' for src in src_partner.ids),
                    }
                    _logger.info("dst_partner %s", dst_partner.id)
                    _logger.info("src_partners %s", src_partner.ids)
                    self._cr.execute("""
                UPDATE ir_property AS _ip1
                SET res_id = %(destination_id)s
                WHERE res_id IN %(source_ids)s
                AND NOT EXISTS (
                    SELECT
                    FROM ir_property AS _ip2
                    WHERE _ip2.res_id = %(destination_id)s
                    AND _ip2.fields_id = _ip1.fields_id
                    AND _ip2.company_id IS NOT DISTINCT FROM _ip1.company_id
                )""", params)
        except psycopg2.Error:
            _logger.info(f'Could not move ir.property from partners: {src_partners.ids} to partner: {dst_partner.id}')


class IrActionsServer(models.Model):
    _inherit = "ir.actions.server"


    def merge_partner_data(self):
        self= self.sudo()
        env = self.env
        obj_merge = env['base.partner.merge.automatic.wizard']
        obj_resp = env['res.partner']
        env.cr.execute("alter table res_partner drop constraint IF EXISTS res_partner_name_uniq;")
        batch_size = 2
        env.cr.execute("""SELECT 
            rollup_customer_id, 
            ARRAY_AGG(id) AS partner_ids, 
            MAX(customer_id) AS primary_partner_id
        FROM
                res_partner
        WHERE
                rollup_customer_id IS NOT NULL
                -- and rollup_customer_id = 45116
        GROUP BY
                rollup_customer_id
        HAVING
                COUNT(*) > 1
        -- LIMIT 2000;

        """)
        count = 1
        datas =  env.cr.dictfetchall() 
        _logger.info("\ndata==========%s", len(datas))
        for partner in datas:
            env.cr.execute("select partner_id from res_customer where id = %s" % (partner.get('rollup_customer_id')))
            src_partner_id = env.cr.fetchone()
            _logger.info("\nsrc_partner_id==========%s", src_partner_id)
            
            _logger.info("\nsccccccccccccccccccccccccc==========%s", count)
            
            dest_partner_ids = partner.get('partner_ids')
            if src_partner_id and src_partner_id[0] in dest_partner_ids:
                
                _logger.info("\ndest_partner_ids==========%s", dest_partner_ids)
                if src_partner_id[0] in (198303,982434,1557239,1409315,236979,128408,1476522,26684,571350,1196062,981782,1209104,1211507, 1564211, 1766198,1203590,1210725,1563795,1373245,1452184,859996,245829,):
                    continue
                src_partner_id = obj_resp.browse(src_partner_id[0])
                child_ids = self.env['res.partner']
                child_ids |= src_partner_id.search([('id', 'child_of', [src_partner_id.id])]) - src_partner_id
                if child_ids:
                    _logger.info("\nData sikp You cannot merge a contact with one of his parent %s", child_ids)
                    continue
                dest_partner_ids = (obj_resp.browse(dest_partner_ids) - src_partner_id).ids
                    
                if len(dest_partner_ids) > 3:
                    for i in range(0, len(dest_partner_ids), batch_size):
                        # _logger.info("\niiiiiiiiiiiiiiiiiiiiiiiiiiii  %s", i)
                        batch = dest_partner_ids[i : batch_size]
                        obj_merge._merge(batch, src_partner_id, False)
                else:
                    obj_merge._merge(dest_partner_ids,src_partner_id, False)
            env.cr.commit()
            count += 1
                

