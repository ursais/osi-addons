# -*- coding: utf-8 -*-
# Copyright 2024 Open Source Integrators Inc
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from psycopg2 import IntegrityError
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools import mute_logger

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    """Inherit account.move to fix duplicate name issues in concurrent posting.

    This module fixes the issue where interbank transfers create multiple
    journal entries simultaneously, causing duplicate name conflicts when
    using the OCA account_move_name_sequence module.

    The fix implements:
    1. Duplicate detection in current recordset before database check
    2. Retry mechanism for handling concurrent sequence generation
    3. Graceful error handling for constraint violations
    """

    _inherit = "account.move"

    @api.depends("state", "journal_id", "date")
    def _compute_name_by_sequence(self):
        """Override to handle duplicate names in concurrent posting scenarios.

        When multiple journal entries are posted simultaneously (e.g., during
        interbank transfers), they may attempt to get the same sequence number
        before any commit occurs. This method adds duplicate detection and
        retry logic to handle such conflicts gracefully.
        """
        # Separate moves that need names from those that already have them
        moves_to_process = self.filtered(
            lambda m: m.state == "posted"
            and (not m.name or m.name == "/")
            and m.journal_id
            and m.journal_id.sequence_id
        )

        if not moves_to_process:
            # Call inverse for consistency even if no moves to process
            self._inverse_name()
            return

        # Group moves by journal, date, and move_type to process efficiently
        moves_by_key = {}
        for move in moves_to_process:
            key = (move.journal_id.id, move.date, move.move_type)
            if key not in moves_by_key:
                moves_by_key[key] = []
            moves_by_key[key].append(move)

        # Track assigned names across all groups to avoid duplicates
        assigned_names = set()

        # Process each group
        for (journal_id, date, move_type), moves in moves_by_key.items():
            journal = moves[0].journal_id

            # Determine the correct sequence (regular or refund)
            if (
                move_type in ("out_refund", "in_refund")
                and journal.type in ("sale", "purchase")
                and journal.refund_sequence
                and journal.refund_sequence_id
            ):
                seq = journal.refund_sequence_id
            else:
                seq = journal.sequence_id

            # Process moves one by one to avoid conflicts
            for move in moves:
                if move.name and move.name != "/":
                    continue

                max_retries = 10
                retry_count = 0
                name_assigned = False

                while retry_count < max_retries and not name_assigned:
                    try:
                        # Get the next sequence number with date context
                        name = seq.with_context(ir_sequence_date=date).next_by_id()

                        if not name:
                            _logger.warning(
                                "Sequence %s returned empty name for move %s",
                                seq.name,
                                move.id,
                            )
                            break

                        # Check if name is already assigned in current batch
                        if name in assigned_names:
                            retry_count += 1
                            _logger.debug(
                                "Name %s already assigned in current batch for move %s. "
                                "Retry attempt %s/%s",
                                name,
                                move.id,
                                retry_count,
                                max_retries,
                            )
                            continue

                        # Check if name exists in database (including draft moves)
                        existing = self.env["account.move"].search_count(
                            [
                                ("name", "=", name),
                                ("journal_id", "=", journal_id),
                                ("id", "!=", move.id),
                            ],
                            limit=1,
                        )

                        if existing:
                            retry_count += 1
                            _logger.debug(
                                "Duplicate name %s found in database for move %s. "
                                "Retry attempt %s/%s",
                                name,
                                move.id,
                                retry_count,
                                max_retries,
                            )
                            continue

                        # Name appears unique, try to assign it
                        move.name = name

                        # Try to flush to check for database constraint violations
                        try:
                            with mute_logger("odoo.sql_db"):
                                move.flush_recordset(["name"])
                            # Successfully assigned
                            assigned_names.add(name)
                            name_assigned = True
                            break
                        except IntegrityError:
                            # Database constraint violation - name already exists
                            # Rollback and retry
                            self.env.cr.rollback()
                            move.invalidate_recordset(["name"])
                            move.name = "/"
                            retry_count += 1
                            _logger.debug(
                                "Database constraint violation for move %s: %s. "
                                "Retry attempt %s/%s",
                                move.id,
                                name,
                                retry_count,
                                max_retries,
                            )
                            continue

                    except IntegrityError:
                        # Database constraint violation during assignment
                        self.env.cr.rollback()
                        move.invalidate_recordset(["name"])
                        move.name = "/"
                        retry_count += 1
                        if retry_count >= max_retries:
                            _logger.error(
                                "Failed to generate name for move %s after %s retries "
                                "due to constraint violations",
                                move.id,
                                max_retries,
                            )
                            raise ValidationError(
                                _(
                                    "Unable to generate unique journal entry name for "
                                    "move %s after %s attempts. Please try again or "
                                    "contact system administrator.",
                                    move.name or move.id,
                                    max_retries,
                                )
                            )
                        continue
                    except Exception as e:
                        _logger.error(
                            "Error generating sequence for move %s: %s",
                            move.id,
                            str(e),
                        )
                        retry_count += 1
                        if retry_count >= max_retries:
                            _logger.error(
                                "Failed to generate name for move %s after %s retries",
                                move.id,
                                max_retries,
                            )
                            raise

                if not name_assigned:
                    _logger.error(
                        "Failed to generate unique name for move %s after %s retries",
                        move.id,
                        max_retries,
                    )
                    # Set temporary name - will be regenerated on next compute
                    move.name = "/"

        # Call the inverse method to ensure consistency
        self._inverse_name()

    def _post(self, soft=True):
        """Override _post to ensure names are generated before posting.

        This ensures that names are properly assigned before the move is posted,
        preventing duplicate name errors during the posting process.
        """
        # Ensure names are computed before posting
        moves_to_name = self.filtered(
            lambda m: m.state != "posted"
            and (not m.name or m.name == "/")
            and m.journal_id
            and m.journal_id.sequence_id
        )
        if moves_to_name:
            moves_to_name._compute_name_by_sequence()
            # Flush to ensure names are saved before posting
            moves_to_name.flush_recordset(["name"])

        return super()._post(soft=soft)
