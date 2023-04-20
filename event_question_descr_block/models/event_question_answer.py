from odoo import _, fields, models
from odoo.exceptions import UserError


class EventQuestionAnswer(models.Model):
    _inherit = "event.question.answer"

    is_blocking = fields.Boolean(string="Is Blocking?")


class EventRegistrationAnswer(models.Model):
    _inherit = "event.registration.answer"

    def check_answer_blocking(self, answer_id):
        answer = self.env["event.question.answer"].browse(answer_id)
        if answer and answer.is_blocking:
            raise UserError(
                _(" Based on your Answers you cannot register for this event.")
            )

    def write(self, vals):
        if vals.get("value_answer_id"):
            self.check_answer_blocking(vals.get("value_answer_id"))
        res = super().write(vals)
        return res

    def create(self, vals):
        for val in vals:
            if val.get("value_answer_id"):
                self.check_answer_blocking(val.get("value_answer_id"))
        res = super().create(vals)
        return res


class EventQuestion(models.Model):
    _inherit = "event.question"

    description = fields.Text()
