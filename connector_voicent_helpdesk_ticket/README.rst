.. image:: https://img.shields.io/badge/licence-LGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/lgpl-3.0-standalone.html
   :alt: License: LGPL-3

=================================
Voicent Helpdesk Ticket Connector
=================================

Odoo Helpdesk App does not provide an automated way to trigger phone calls when a ticket reaches a specific stage in the process.

For companies with a large number of tickets or when a ticket impacts many people, calling everyone one by one is a time-consuming option.

This module aims to automate calls to customer or impacted third parties when a ticket reaches a specific stage.

Configuration
=============

* Go to Connectors > Backends > Voicent Backends
* Create a Voicent Backend with the host, port, caller ID, number of lines
* Create Time lines to determine at which time of the day the calls are made
* Create Call lines to determine at which stage in the process the calls are made

+------------+-----+----------------+--------------+
|            |     | Ticket has a parent           |
+------------+-----+----------------+--------------+
|            |     | Yes            | No           |
+------------+-----+----------------+--------------+
| Must Have  | Yes | Call           | No Call      |
+            +-----+----------------+--------------+
| a Parent   | No  | Call                          |
+------------+-----+----------------+--------------+

* Create Contact Info to create the structure of the CSV file to send to Voicent
* Create Replies to determine what to do based on the replies (See example below)
* Go to Contacts
* Review customers to set the "Accepts Voicent Calls" checkbox or not

Example
-------

Here is a server action to retry a call up to 3 times:

.. code-block:: python

    count = record.call_count + 1
    if count < 3:
      line = env['backend.voicent.call.line'].browse(env.context.get('call_line_id'))
      if not (line.has_parent is True and record.parent_id is False):
        eta = line.backend_id.next_call + datetime.timedelta(days=1)
        record.with_delay(eta=eta).voicent_start_campaign(line)
    else:
      count = 0
    record.write({'call_count': count})

Usage
=====

To use this module, you need to:

* Go to Helpdesk
* Create a ticket and assign it to a customer who accepts phone calls
* Move the ticket to the stage specified in the call lines of the backend
* Check the chatter for the call status

ROADMAP
=======

* This module does not support all the message types provided by Voicent yet:

+-----------------------+-----------------+
| Voicent Message Type  | Supported       |
+=======================+=================+
| Audio                 | No              |
+-----------------------+-----------------+
| IVR                   | No              |
+-----------------------+-----------------+
| Survey                | No              |
+-----------------------+-----------------+
| Template              | Yes             |
+-----------------------+-----------------+
| Text-To-Speech        | Yes             |
+-----------------------+-----------------+

Contributors
------------

* Maxime Chambreuil <mchambreuil@opensourceintegrators.com>
* Murtuza Saleh <murtuza.saleh@serpentcs.com>
