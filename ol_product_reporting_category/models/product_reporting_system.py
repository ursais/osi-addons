# Import Odoo libs
from odoo import api, fields, models


class ProductReportingSystem(models.Model):
    """Add object for product reporting system."""

    _name = "product.reporting.system"
    _description = "Product Reporting System"
    _rec_name = "display_name"

    # COLUMNS ###

    name = fields.Char(string="Name", required=True)
    series_id = fields.Many2one(
        comodel_name="product.reporting.series",
        string="Series",
    )
    display_name = fields.Char(
        string="Display Name", compute="_compute_display_name", store=True
    )

    # END #######
    # METHOD ###

    @api.depends("series_id", "series_id.line_id", "series_id.line_id.category_id")
    def _compute_display_name(self):
        """Computes the `display_name` for the `product.reporting.system` record.
        This method constructs a string for the `display_name` field by concatenating
        the names of the related `category`, `line`, `series`, and the reporting system's
        `name`. The format is as follows:
        "Category Name/Line Name/Series Name/Reporting System Name.
        """
        for rec in self:
            if (
                rec.series_id
                and rec.series_id.line_id
                and rec.series_id.line_id.category_id
            ):
                rec.display_name = f"{rec.series_id.line_id.category_id.name}/{rec.series_id.line_id.name}/{rec.series_id.name}/{rec.name}"
            else:
                rec.display_name = rec.name

    # END #######
