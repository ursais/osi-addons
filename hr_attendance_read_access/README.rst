Overview
========

Allow users who only have read access to attendances to open the
*Attendances* list and form views without getting an access error.

Problem
=======

``hr.attendance`` stores several computed fields (``worked_hours``,
``overtime_hours``, ``validated_overtime_hours``, ``expected_hours`` and
``overtime_status``). When a dependency changes - for example when overtime
rules or working schedules are updated - the affected attendance records are
flagged for recomputation.

The next time those records are read, the ORM recomputes the values and flushes
them to the database. Because that flush is a ``write`` on ``hr.attendance``, a
user granted read-only access hits::

    AccessError: You can only read this record. (hr.attendance - write)

simply by opening *Time Off / Attendances*.

Solution
========

The module inherits ``hr.attendance`` and extends the common fetch path
(``_fetch_query``). For users that lack write access, any pending recomputation
of the stored computed fields is recomputed and flushed with elevated
privileges *before* the user's read triggers it. The system persists its own
computed values without granting the reading user any write capability, and
users who already have write access keep the standard behaviour.

Usage
=====

Install the module. No configuration is required.


Credits
=======

Contributors
------------

* Open Source Integrators <http://www.opensourceintegrators.com>
