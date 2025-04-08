# Import Odoo libs
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    # COLUMNS #####
    placeholder_image_product = fields.Image(
        string="Product Placeholder Image",
        max_width=1024,
        max_height=1024,
        store=True,
    )
    placeholder_image_phone_icon = fields.Image(
        string="Phone Icon Placeholder Image",
        max_width=1024,
        max_height=1024,
        store=True,
    )
    placeholder_image_email_icon = fields.Image(
        string="Email Icon Placeholder Image",
        max_width=1024,
        max_height=1024,
        store=True,
    )
    placeholder_image_profile_picture = fields.Image(
        string="Profile Placeholder Image",
        max_width=1024,
        max_height=1024,
        store=True,
    )
    linkedin_image = fields.Image(
        string="LinkedIN Image",
        max_width=1024,
        max_height=1024,
        store=True,
    )
    template_logo = fields.Image(
        string="Logo",
        max_width=1024,
        max_height=1024,
        store=True,
    )
    twitter_image = fields.Image(
        string="Twitter Image",
        max_width=1024,
        max_height=1024,
        store=True,
    )
    youtube_image = fields.Image(
        string="YouTube Image",
        max_width=1024,
        max_height=1024,
        store=True,
    )
    facebook_image = fields.Image(
        string="Facebook Image",
        max_width=1024,
        max_height=1024,
        store=True,
    )
    # END #########
