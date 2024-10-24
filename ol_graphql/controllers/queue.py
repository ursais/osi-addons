# Import Odoo libs
from odoo.addons.queue_job.controllers.main import RunJobController

class OnLogicRunJobController(RunJobController):
    def _try_perform_job(self, env, job):
        
        # Get the context passed to the function of the queue_job 
        new_context = job.kwargs.get('context_values', {})
        # Update it with the context of the Job it self,
        # just to make sure we don't lose data from the core OCA module
        new_context.update(env.context)
        # Apply the new context
        env.context = new_context
        return super()._try_perform_job(env, job)