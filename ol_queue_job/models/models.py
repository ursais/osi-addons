import logging

_logger = logging.getLogger(__name__)

from odoo.addons.queue_job.job import Job

_logger = logging.getLogger(__name__)


# ==================================================================
# Monkey patch OCA module's `perform` method
# ==================================================================
OLD_PERFORM = Job.perform


def new_perform(self):
    """
    If new jobs have been enqueued with the same identity keys
    we don't want to run the current job.
    """
    if self.identity_key and self.env["ir.config_parameter"].sudo().get_as_boolean(
        "ol_queue_job.reverse_identity_key", False
    ):
        # Find other jobs with the same identity key
        existing = self.job_record_with_same_identity_key()
        if existing:
            # Reverse identity_key enabled! Skipping job run as other jobs exists with the same identity key
            # This job is going to be marked as done!
            return True
    return OLD_PERFORM(self)


Job.perform = new_perform

# ==================================================================
# Monkey patch OCA module's `enqueue` method
# ==================================================================
OLD_ENQUEUE = Job.enqueue


def new_enqueue(
    func,
    args=None,
    kwargs=None,
    priority=None,
    eta=None,
    max_retries=None,
    description=None,
    channel=None,
    identity_key=None,
):
    """
    @ol_upgrade: Full override of the OCA module functionality to enable reverse_identity_key

    Create a Job and enqueue it in the queue. Return the job uuid.

    This expects the arguments specific to the job to be already extracted
    from the ones to pass to the job function.

    If the identity key is the same than the one in a pending job,
    no job is created and the existing job is returned

    """
    new_job = Job(
        func=func,
        args=args,
        kwargs=kwargs,
        priority=priority,
        eta=eta,
        max_retries=max_retries,
        description=description,
        channel=channel,
        identity_key=identity_key,
    )
    # Only run this part of the code if reverse identity_key is not enabled!
    # If it would be enabled we would skip the similar identity key check while enqueuing!
    # @ol_upgrade: (-1/+1)
    if new_job.identity_key and not new_job.env[
        "ir.config_parameter"
    ].sudo().get_as_boolean("ol_queue_job.reverse_identity_key", False):
        existing = new_job.job_record_with_same_identity_key()
        if existing:
            _logger.debug(
                "a job has not been enqueued due to having the same identity key (%s) than job %s",
                new_job.identity_key,
                existing.uuid,
            )
            return Job._load_from_db_record(existing)
    new_job.store()
    _logger.debug(
        "enqueued %s:%s(*%r, **%r) with uuid: %s",
        new_job.recordset,
        new_job.method_name,
        new_job.args,
        new_job.kwargs,
        new_job.uuid,
    )
    return new_job


Job.enqueue = new_enqueue
