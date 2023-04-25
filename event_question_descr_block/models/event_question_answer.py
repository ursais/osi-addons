from odoo import _, api, fields, models
from odoo.exceptions import UserError


class EventQuestionAnswer(models.Model):
    _inherit = "event.question.answer"

    is_blocking = fields.Boolean(string="Is Blocking?")


class EventAnswer(models.Model):
    _inherit = "event.registration.answer"

    @api.constrains("value_answer_id")
    def check_answer_block(self):
        if self.value_answer_id.is_blocking:
            raise UserError(
                _(
                    "The answer you entered for "
                    + str(self.question_id.title)
                    + " is not valid. Unfortunately you cannot "
                    "register for the event."
                )
            )


class EventQuestion(models.Model):
    _inherit = "event.question"

    description = fields.Text()
