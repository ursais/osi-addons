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
        # TODO: Implement environment check to make sure we can't use this on production
        if self.user_has_groups("ol_base.dev_team"):
            # User has to be a member of the development team
            # OnLogic Environment has to be defined and be `development`
            # We never ever want to allow this on non development environments
            print(f"Python Debug started for: {self}")
            ipdb.set_trace()
            asyncio.set_event_loop(asyncio.new_event_loop())
        return True
