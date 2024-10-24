# Import Python libs

# Import Odoo libs
from odoo import models


class ProjectTask(models.Model):
    """
    Add webhook compatibility to project tasks
    """

    _name = 'project.task'
    _inherit = ['project.task', 'webhook.mixin']
