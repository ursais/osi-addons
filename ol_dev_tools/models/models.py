# Import Python libs
import ipdb
import asyncio

# Import Odoo libs
from odoo import models


class BaseModel(models.AbstractModel):
    _inherit = "base"

    @staticmethod
    def start_python_debug(self, res_id, res_model):
        """
        Trigger a Python debugger breakpoint
        """
        self = self.env[res_model].browse(res_id)
        
        
        def delete_views_that_inherit(views):
            for view in views:
                views_that_inherit = self.env["ir.ui.view"].search([('inherit_id', '=', view.id)])
                print(f"VIEW: {view.name} ({view.id}): {views_that_inherit}")
                if views_that_inherit:
                    delete_views_that_inherit(views_that_inherit)
                else:
                    try:
                        print(f"Delete view: {view.name} ({view.id})")
                        view.unlink()
                    except Exception as e:
                        print(f"Error deleting view {view.name} ({view.id}): {e}")
                        
                        
        delete_views_that_inherit(self.env["ir.ui.view"].sudo().browse([11645,239,220,2716,238,10371]))
        return        
        # TODO: Implement environment check to make sure we can't use this on production
        if self.user_has_groups("ol_base.dev_team"):
            # User has to be a member of the development team
            # OnLogic Environment has to be defined and be `development`
            # We never ever want to allow this on non development environments
            print(f"Python Debug started for: {self}")
            ipdb.set_trace()
            asyncio.set_event_loop(asyncio.new_event_loop())
        return True
