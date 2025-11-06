# Import Python libs
import uuid

# Import Odoo libs
from odoo import models


def all_computed_fields(self, fields):
    if not fields:
        return False

    # get the field records
    def is_compute_field(field_name):
        field_rec = self._fields[field_name]
        compute_field = bool(field_rec.compute)
        company_dependent = field_rec.company_dependent

        return compute_field and not company_dependent

    field_list = map(is_compute_field, fields)

    # If all of the provided fields are computed we want to return true
    return all(field_list)


# Add a `all_computed_fields` function to the base model. Other models can override if they want
models.BaseModel.all_computed_fields = all_computed_fields


class BaseModel(models.AbstractModel):
    _inherit = "base"

    def get_uuid(self, string=True, force_new=False):
        """
        Generate a new UUID, and return it directly or as a string
        """
        uuid_value = uuid.uuid4()
        return str(uuid_value) if string else uuid_value

    def get_default_window_action(self):
        """
        This function is intended to be overridden in later modules
        """
        # By default try to find the earliest (possible core odoo action) that is for a `tree`
        return self.env["ir.actions.act_window"].search(
            [("res_model", "=", self._name), ("view_mode", "like", "%tree%")],
            order="id asc",
            limit=1,
        )

    def get_url(self):
        """
        Get the URL linking to the given odoo record
        """

        if not self.exists():
            return None

        base_url = f"{self.get_base_url()}/web#"
        action = self.get_default_window_action()
        if action:
            # If we have an action add it, this ensures that the correct form is loaded
            base_url = f"{base_url}action={action.id}&"

        return f"{base_url}id={self.id}&view_type=form&model={self._name}"

    def get_record_dates_data(self):
        """
        Return a dictionary with the information about the records important dates
        """
        return {
            "create_date": self.create_date,
            "write_date": self.write_date,
        }
