# Import Python libs
import logging
import uuid as uuid_lib

# Import Odoo libs
from odoo import models, api
from odoo.exceptions import ValidationError
from odoo.addons.ol_base.fields import fields as ol_fields
from odoo.tools.misc import OrderedSet

_logger = logging.getLogger(__name__)


class Uuid(models.AbstractModel):
    _name = "res.uuid"
    _description = "UUID"
    _uses_uuid_mixin = True

    # COLUMNS #####
    uuid = ol_fields.Uuid(
        string="UUID",
        help="Unique identifier that is used to identify this record between different systems.",
        required=True,
        copy=False,
        index=True,
    )
    # END #########

    _sql_constraints = [("uuid", "unique(uuid)", "The UUID field must be unique!")]

    @api.model
    def check_field_access_rights(self, operation, field_names):
        """
        Odoo classes that inherit the UUID mixin we always want to include the UUID in the read results
        """
        result = super().check_field_access_rights(
            operation=operation, field_names=field_names
        )

        if operation != "read":
            # We only want to change reads
            return result

        if "uuid" not in result and "uuid" in self._fields:
            if isinstance(result, list):
                result.append("uuid")
            elif isinstance(result, OrderedSet):
                result.add("uuid")

        return result

    @api.model
    def create(self, values):
        """
        Always generate a UUID for newly created records
        """
        if not values.get("uuid", False):
            uuid = self.env[self._name].get_uuid(force_new=True)
            values["uuid"] = uuid
        res = super().create(values)
        return res

    def write(self, values):
        """
        If the UUID of a record changes make sure we log it!
        """
        if "uuid" in values:
            _logger.warning(
                f"UUID: Odoo records UUID changed {self} Old: `{self.mapped('uuid')}` New: `{values['uuid']}`"
            )
        return super().write(values)

    def get_uuid(self, string=True, force_new=False):
        """
        Override the `ls_base` version
        so we return the existing UUID if it already exists.
        """
        if self.uuid and not force_new:
            return self.uuid
        return super().get_uuid(string=string, force_new=force_new)

    def get_by_uuid(self, uuid, raise_error=False):
        """
        Find record(s) based on the passed UUID
        """

        # First validate the value

        if not self.is_valid_uuid(uuid, raise_error=raise_error):
            return self.env[self._name]

        if isinstance(uuid, (list, tuple)):
            query = f"""
                SELECT id
                FROM {self._table}
                WHERE uuid in %(uuid)s
            """
            query_args = {"uuid": tuple(uuid)}
            self.env.cr.execute(query, query_args)
            record_ids = [x[0] for x in self.env.cr.fetchall()]
            return self.env[self._name].browse(record_ids)

        query = f"""
            SELECT id
            FROM {self._table}
            WHERE uuid = %(uuid)s
        """
        query_args = {"uuid": uuid}
        self.env.cr.execute(query, query_args)
        record_ids = [x[0] for x in self.env.cr.fetchall()]
        return self.env[self._name].browse(record_ids)

    def is_valid_uuid(self, uuid, raise_error=True):
        """
        Test if the passed UUID is valid or not
        """

        def check_uuid(uuid):
            if not uuid:
                if raise_error:
                    raise ValidationError(f"Missing UUID value for: {self._name}!")
                return False
            try:
                uuid_lib.UUID(uuid, version=4)
            except ValueError:
                if raise_error:
                    raise ValidationError(
                        f"Invalid UUID value! `{uuid}` for: {self._name}"
                    )
                return False
            return True

        if isinstance(uuid, (list, tuple)):
            # If this is a list check every uuid separately
            results = []
            for uuid_item in uuid:
                results.append(check_uuid(uuid_item))
            return all(results)

        return check_uuid(uuid)
