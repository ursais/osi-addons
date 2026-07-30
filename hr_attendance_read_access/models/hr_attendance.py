# Copyright (C) 2026 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import models

_logger = logging.getLogger(__name__)


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    def _flush_pending_computations_as_superuser(self):
        """Persist pending recomputations of stored computed fields as superuser.

        ``hr.attendance`` owns several ``store=True`` computed fields
        (``worked_hours``, ``overtime_hours``, ``validated_overtime_hours``,
        ``expected_hours``, ``overtime_status``). Whenever a dependency changes
        - for instance when overtime rules or working schedules are updated -
        the related attendance records are marked for recomputation.

        The next time those records are read (e.g. when a user simply opens the
        *Attendances* list or form) the ORM recomputes the values and flushes
        them back to the database. That flush is a ``write`` on
        ``hr.attendance``, so a user who was granted read-only access to
        attendances hits ``AccessError: ... (hr.attendance - write)`` even
        though they only intended to *view* the records.

        Recomputing and flushing the values with elevated privileges lets the
        system persist its own computed values without granting the reading
        user any write capability over the records. Officers and managers, who
        already have write access, keep the standard behaviour and are not
        impacted.
        """
        # ``sudo()`` recomputations re-enter this hook; the elevated call has
        # nothing left to defer, so skip it and avoid infinite recursion.
        if self.env.su:
            return

        attendance_model = self.env["hr.attendance"]

        # Only users lacking write access are affected by the regression.
        # Skipping the extra flush for everyone else keeps the read path as
        # light as possible.
        if attendance_model.has_access("write"):
            return

        # ``flush_model`` first recomputes every pending stored field of the
        # model and then writes the dirty values. Running it as superuser
        # guarantees the persistence never fails for read-only users while
        # keeping the exact same values the standard recomputation would store.
        attendance_model.sudo().flush_model()

    def _fetch_query(self, query, fields):
        # ``_fetch_query`` is the single method every read path funnels through
        # (``read``/``web_read`` for the form view and ``search_fetch`` for the
        # list view), which makes it the right place to neutralise the pending
        # recomputation before the current user triggers the write.
        self._flush_pending_computations_as_superuser()
        return super()._fetch_query(query, fields)
