from odoo import api, fields, models

class EventEvent(models.Model):
    _name = 'event.event'
    _inherit = ['event.event', 'portal.mixin']

    def check_access_rule(self, operation):
        """ Add Access rules of mail.message for non-employee user:
            - read:
                - raise if the type is comment and subtype NULL (internal note)
        """
        # if self.user_has_groups('base.group_public'):
        #     self.env.cr.execute(
        #         'SELECT id FROM "%s" WHERE website_published IS FALSE AND id = ANY (%%s)' % (self._table), (self.ids,))
        #     if self.env.cr.fetchall():
        #         raise AccessError(
        #             _('The requested operation cannot be completed due to security restrictions. Please contact your system administrator.\n\n(Document type: %s, Operation: %s)') % (
        #             self._description, operation))
        # print("\n\n\n\n 000000000000000000000000000000000000000000000000000000\n\n\n")
        return super(EventEvent, self).check_access_rule(operation=operation)

    def read(self, fields=None, load='_classic_read'):
        """ Override to explicitely call check_access_rule, that is not called
            by the ORM. It instead directly fetches ir.rules and apply them. """
        # self.check_access_rule('read')
        print("\n\n\n\n 000000000000000000000000000000000000000000000000000000\n\n\n")

        return super(EventEvent, self).read(fields=fields, load=load)
