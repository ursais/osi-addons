# Copyright (C) 2020 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import calendar
import datetime
from datetime import timedelta

import numpy

from odoo import api, fields, models


class EmpData(models.Model):
    _name = "company.dashboard"

    name = fields.Char()

    @api.model
    def get_company_data(self):
        vals = {}
        hr_emp_obj = self.env["hr.employee"]
        emp_id = hr_emp_obj.search([("user_id", "=", self.env.user.id)])
        date = fields.Date.context_today(self)
        mnth_start = datetime.datetime(date.year, date.month, 1)
        mnth_end = datetime.datetime(
            date.year, date.month, calendar.mdays[date.month]
        ).date()
        wk_start = date - timedelta(days=date.weekday())
        wk_end = wk_start + timedelta(days=6)
        yr_start = datetime.datetime(date.year, 1, 1)
        yr_end = yr_start.replace(month=12, day=31)

        holidays_and_leaves = self.get_holidays_and_leaves(
            wk_start, wk_end, mnth_start, mnth_end, yr_start, yr_end
        )

        month_holidays_cnt = holidays_and_leaves.get("month_holidays_cnt")
        tot_mnth_leaves = holidays_and_leaves.get("tot_mnth_leaves")

        goals = self.get_monthly_goals(
            mnth_start, mnth_end, month_holidays_cnt, tot_mnth_leaves, date
        )
        forecast_compliance = self.get_forecast_compliance(emp_id, wk_start, wk_end)
        badges = self.get_badges()
        employee_data = self.get_employee_data(wk_start, wk_end)
        department_employee_data = self.get_department_employee_data(wk_start, wk_end)
        vals.update(
            {
                "month_plan": goals.get("month_plan"),
                "cumulative_target_actual": round(
                    goals.get("cumulative_target_actual"), 2
                ),
                "remaining_hours": goals.get("remaining_hours"),
                "daily_target": round(goals.get("daily_target"), 2),
                "daily_target_actual": round(goals.get("daily_target_actual"), 2),
                "cumulative_target": round(goals.get("cumulative_target"), 2),
                "daily_variance": round(goals.get("daily_variance"), 2),
                "cumulative_variance": round(goals.get("cumulative_variance"), 2),
                "planned_billable_hours": forecast_compliance.get(
                    "planned_billable_hours"
                ),
                "badges": badges.get("badges"),
                "total_days": goals.get("total_days"),
                "days_passed": goals.get("days_passed"),
                "days_left": goals.get("days_left"),
                "employee_data": employee_data,
                "department_employee_data": department_employee_data,
            }
        )
        return vals

    def get_department_employee_data(self, wk_start, wk_end):
        sql_query = """select
            sum(case when pp.partner_id = %s then unit_amount else 0 end) as non_billable,
            sum(case when pp.partner_id != %s or pp.partner_id IS NULL
            then unit_amount else 0 end) as billable,
            sum(case when pp.partner_id != %s or pp.partner_id IS NULL
            then unit_amount else 0 end)
            / sum(unit_amount) * 100 as total_per, sum(unit_amount) as total,
            sum(case when pp.partner_id != %s then unit_amount else 0 end)  /
            (%s - (SELECT count(number_of_days)
            FROM hr_leave as hl
            left join hr_employee as he on (he.id = hl.employee_id)
            WHERE
            (request_date_from>=%s AND request_date_from<=%s)
            AND (request_date_to>=%s AND request_date_to<=%s)
            AND state='validate' and employee_id = he.id) -
            (SELECT count(id) from hr_holidays_public_line WHERE date>= %s AND date<= %s ))
            as working_day,
            hd.name as department_name , hd.id as hd_id,
            he.name as name from account_analytic_line as aal
            left join project_project as pp on (pp.id = aal.project_id)
            left join hr_employee as he on (he.id = aal.employee_id)
            left join hr_department as hd on (he.department_id = hd.id)
            where project_id IS NOT NULL and aal.date >= %s and aal.date <= %s
            group by he.name, hd.name,  hd.id"""
        partner_id = self.env.user.company_id.partner_id.id
        holiday_num = numpy.busday_count(wk_start, wk_end)
        self.env.cr.execute(
            sql_query,
            tuple(
                [
                    partner_id,
                    partner_id,
                    partner_id,
                    partner_id,
                    int(holiday_num),
                    wk_start,
                    wk_end,
                    wk_start,
                    wk_end,
                    wk_start,
                    wk_end,
                    wk_start,
                    wk_end,
                ]
            ),
        )
        employee_data = self.env.cr.dictfetchall()

        category_detials = {}
        for rec in employee_data:
            if category_detials.get(rec.get("hd_id")):
                category_detials.get(rec.get("hd_id")).get("data").append(rec)
            else:
                category_detials.update(
                    {
                        rec.get("hd_id"): {
                            "name": rec.get("department_name"),
                            "data": [rec],
                        }
                    }
                )
        return category_detials

    def get_holidays_and_leaves(
        self, wk_start, wk_end, mnth_start, mnth_end, yr_start, yr_end
    ):
        month_holidays_cnt = 0
        week_hoildays_cnt = 0
        year_holidays_cnt = 0

        # HOLIDAYS IN CURRENT MONTH
        holidays_query = """
                    SELECT date from hr_holidays_public_line WHERE date>=%s AND date<=%s
                """
        self.env.cr.execute(holidays_query, (mnth_start.date(), mnth_end))
        month_holidays = self.env.cr.fetchall()
        month_holiday_list = []
        for h in month_holidays:
            if h[0].weekday() not in [5, 6]:
                month_holidays_cnt += 1
                month_holiday_list.append(h[0])

        # HOLIDAYS IN CURRENT WEEK
        self.env.cr.execute(holidays_query, (wk_start, wk_end))
        week_holidays = self.env.cr.fetchall()
        week_holiday_list = []
        for h in week_holidays:
            if h[0].weekday() not in [5, 6]:
                week_hoildays_cnt += 1
                week_holiday_list.append(h[0])

        # HOLIDAYS IN CURRENT YEAR
        self.env.cr.execute(holidays_query, (yr_start, yr_end))
        year_holidays = self.env.cr.fetchall()
        year_holiday_list = []
        for h in year_holidays:
            if h[0].weekday() not in [5, 6]:
                year_holidays_cnt += 1
                year_holiday_list.append(h[0])

        # LEAVES OF CURRENT MONTH
        leaves_query = """
                    SELECT number_of_days,request_date_from,request_date_to
                    FROM hr_leave WHERE
                    (request_date_from>=%s AND request_date_from<=%s)
                    AND (request_date_to>=%s AND request_date_to<=%s)
                    AND state='validate'
                """
        self.env.cr.execute(
            leaves_query, (mnth_start.date(), mnth_end, mnth_start.date(), mnth_end)
        )
        month_leaves = self.env.cr.fetchall()
        tot_mnth_leaves = 0
        for leave in month_leaves:
            days = leave[0]
            date_generated = [
                leave[1] + datetime.timedelta(days=x)
                for x in range(0, (leave[2] - leave[1]).days + 1)
            ]
            for date in date_generated:
                if date in month_holiday_list:
                    days -= 1
            tot_mnth_leaves += days

        # LEAVES OF CURRENT WEEK
        self.env.cr.execute(leaves_query, (wk_start, wk_end, wk_start, wk_end))
        week_leaves = self.env.cr.fetchall()
        tot_week_leaves = 0
        for leave in week_leaves:
            days = leave[0]
            date_generated = [
                leave[1] + datetime.timedelta(days=x)
                for x in range(0, (leave[2] - leave[1]).days + 1)
            ]
            for date in date_generated:
                if date in week_holiday_list:
                    days -= 1
            tot_week_leaves += days

        # LEAVES OF CURRENT YEAR
        self.env.cr.execute(leaves_query, (yr_start, yr_end, yr_start, yr_end))
        year_leaves = self.env.cr.fetchall()
        tot_year_leaves = 0
        for leave in year_leaves:
            days = leave[0]
            date_generated = [
                leave[1] + datetime.timedelta(days=x)
                for x in range(0, (leave[2] - leave[1]).days + 1)
            ]
            for date in date_generated:
                if date in year_holiday_list:
                    days -= 1
            tot_year_leaves += days

        return {
            "week_hoildays_cnt": week_hoildays_cnt,
            "month_holidays_cnt": month_holidays_cnt,
            "year_holidays_cnt": year_holidays_cnt,
            "tot_week_leaves": tot_week_leaves,
            "tot_mnth_leaves": tot_mnth_leaves,
            "tot_year_leaves": tot_year_leaves,
        }

    def get_employee_data(self, wk_start, wk_end):
        sql_query = """select
             sum(case when pp.partner_id = %s then unit_amount else 0 end) as non_billable,
            sum(case when pp.partner_id != %s or pp.partner_id IS NULL
            then unit_amount else 0 end) as billable,
            sum(case when pp.partner_id != %s or pp.partner_id IS NULL
            then unit_amount else 0 end)
            / sum(unit_amount) * 100 as total_per, sum(unit_amount) as total,
            sum(case when pp.partner_id != %s then unit_amount else 0 end)  /
            (%s - (SELECT count(number_of_days)
            FROM hr_leave as hl
            left join hr_employee as he on (he.id = hl.employee_id)
            WHERE
            (request_date_from>=%s AND request_date_from<=%s)
            AND (request_date_to>=%s AND request_date_to<=%s)
            AND state='validate' and employee_id = he.id) -
            (SELECT count(id) from hr_holidays_public_line WHERE date>= %s AND date<= %s ))
            as working_day,
            he.name as name from account_analytic_line as aal
            left join project_project as pp on (pp.id = aal.project_id)
            left join hr_employee as he on (he.id = aal.employee_id)
            where project_id IS NOT NULL and aal.date >= %s and aal.date <= %s
            group by he.name"""
        partner_id = self.env.user.company_id.partner_id.id
        holiday_num = numpy.busday_count(wk_start, wk_end)
        self.env.cr.execute(
            sql_query,
            tuple(
                [
                    partner_id,
                    partner_id,
                    partner_id,
                    partner_id,
                    int(holiday_num),
                    wk_start,
                    wk_end,
                    wk_start,
                    wk_end,
                    wk_start,
                    wk_end,
                    wk_start,
                    wk_end,
                ]
            ),
        )
        employee_data = self.env.cr.dictfetchall()
        return employee_data

    def get_forecast_compliance(self, emp_id, wk_start, wk_end):
        # TOTAL FORECASTED HOURS OF THE WEEK
        query = """
            SELECT sum(t.resource_hours) FROM project_forecast as t
            WHERE  start_date >= '%s'
            AND end_date <= '%s'
        """ % (
            wk_start,
            wk_end,
        )
        self.env.cr.execute(query)
        weekly_plan_hours = self.env.cr.fetchall()[0][0] or 0

        # TOTAL BILLABLE HOURS OF PLANNED TASKS
        query = """
                    SELECT sum(l.unit_amount) FROM account_analytic_line as l
                    LEFT JOIN project_task as p ON p.id = l.task_id
                    WHERE l.date >= '%s' AND l.date <= '%s'
                    AND(l.timesheet_invoice_type='billable_time'
                    OR l.timesheet_invoice_type='billable_fixed')
                    AND p.planned_hours > 0
                """ % (
            wk_start,
            wk_end,
        )
        self.env.cr.execute(query)
        # self.planned_billable_hours = self.env.cr.fetchall()[0][0]
        planned_billable_hours = self.env.cr.fetchall()[0][0] or 0

        # TOTAL BILLABLE HOURS OF UNPLANNED TASKS
        query = """
                            SELECT sum(l.unit_amount) FROM account_analytic_line as l
                            LEFT JOIN project_task as p ON p.id=l.task_id
                            WHERE l.date>='%s' AND l.date<='%s'
                            AND (l.timesheet_invoice_type='billable_time'
                            OR l.timesheet_invoice_type='billable_fixed')
                            AND p.planned_hours<=0
                        """ % (
            wk_start,
            wk_end,
        )
        self.env.cr.execute(query)
        unplanned_billable_hours = self.env.cr.fetchall()[0][0] or 0

        if weekly_plan_hours:
            per_planned_billable_hrs = (
                planned_billable_hours / weekly_plan_hours
            ) * 100
        else:
            per_planned_billable_hrs = 0

        return {
            "weekly_plan_hours": weekly_plan_hours,
            "planned_billable_hours": planned_billable_hours,
            "unplanned_billable_hours": unplanned_billable_hours,
            "per_planned_billable_hrs": per_planned_billable_hrs,
        }

    def get_leverage(self, emp_id, mnth_start, mnth_end, yr_start, yr_end, date):
        monthly_leverage = 0
        yearly_leverage = 0
        # TOTAL MONTHLY BILLABLE HOURS OF PROJECTS AS PM
        billable_pm_query = """
                    SELECT sum(l.unit_amount) FROM account_analytic_line as l
                    LEFT JOIN project_project as p ON p.id=l.project_id
                    WHERE l.date>=%s AND l.date<=%s
                    AND (l.timesheet_invoice_type='billable_time'
                    OR l.timesheet_invoice_type='billable_fixed')
                    AND p.user_id=%s
                """
        self.env.cr.execute(
            billable_pm_query, (mnth_start.date(), mnth_end, self.env.user.id)
        )
        my_proj_total_bill_hours_monthly = self.env.cr.fetchall()[0][0]

        # TOTAL YEARLY BILLABLE HOURS OF PROJECTS AS PM
        self.env.cr.execute(billable_pm_query, (yr_start, yr_end, self.env.user.id))
        my_proj_total_bill_hours_yearly = self.env.cr.fetchall()[0][0]

        # TOTAL MONTHLY HOURS WORKED IN THE PROJECT BY SELF
        worked_query = """
                    SELECT sum(l.unit_amount) FROM account_analytic_line as l
                    LEFT JOIN project_project as p ON p.id=l.project_id
                    WHERE l.date>=%s AND l.date<=%s
                    AND (l.timesheet_invoice_type='billable_time'
                    OR l.timesheet_invoice_type='billable_fixed')
                    AND p.user_id=%s
                """
        self.env.cr.execute(worked_query, (mnth_start.date(), date, self.env.user.id))
        my_total_bill_hours_monthly = self.env.cr.fetchall()[0][0]

        if my_proj_total_bill_hours_monthly:
            monthly_leverage = (
                my_total_bill_hours_monthly / my_proj_total_bill_hours_monthly
            ) * 100

        # TOTAL YEARLY HOURS WORKED IN THE PROJECT BY SELF
        self.env.cr.execute(worked_query, (emp_id.id, yr_start, date, self.env.user.id))
        my_total_bill_hours_yearly = self.env.cr.fetchall()[0][0]

        if my_proj_total_bill_hours_yearly:
            yearly_leverage = (
                my_total_bill_hours_yearly / my_proj_total_bill_hours_yearly
            ) * 100

        return {
            "monthly_leverage": monthly_leverage,
            "yearly_leverage": yearly_leverage,
        }

    def get_badges(self):
        # LAST 5 BADGES
        query = """
                select he.name as name , count(gbu) as total
                from gamification_badge_user as gbu
                left join hr_employee as he on he.id = gbu.employee_id
                group by name
                order by total desc
            """
        self.env.cr.execute(query)
        badges = self.env.cr.dictfetchall()
        return {"badges": badges}

    def get_monthly_goals(
        self, mnth_start, mnth_end, month_holidays_cnt, tot_mnth_leaves, date
    ):
        daily_variance = 0
        cumulative_variance = 0
        working_days_month = numpy.busday_count(mnth_start.date(), mnth_end)
        total_days = working_days_month - month_holidays_cnt - tot_mnth_leaves
        working_days_passed = numpy.busday_count(mnth_start.date(), date)
        days_passed = working_days_passed

        days_left = total_days - days_passed

        # TOTAL FORECASTED HOURS OF THE MONTH
        query = """
                    SELECT sum(t.resource_hours) FROM project_forecast as t
                    WHERE start_date>='%s'
                    AND end_date<='%s'
                """ % (
            mnth_start.date(),
            mnth_end,
        )
        self.env.cr.execute(query)

        month_plan = self.env.cr.fetchall()[0][0]

        # TOTAL HOURS WORKED IN THE MONTH
        query = """
                    SELECT sum(t.effective_hours) FROM project_forecast as t
                    WHERE start_date>='%s'
                    AND end_date<='%s'
                """ % (
            mnth_start.date(),
            mnth_end,
        )
        self.env.cr.execute(query)

        cumulative_target_actual = self.env.cr.fetchall()[0][0]

        remaining_hours = month_plan - cumulative_target_actual

        try:
            if days_passed and cumulative_target_actual:
                daily_target = month_plan / (days_left + days_passed)
                daily_target_actual = cumulative_target_actual / days_passed
                cumulative_target = daily_target * days_passed
                daily_variance = ((daily_target_actual - daily_target) / daily_target) * 100
                cumulative_variance = (
                    (cumulative_target_actual - cumulative_target) / cumulative_target
                ) * 100
            else:
                daily_target = 0
                daily_target_actual = 0
                cumulative_target = 0
                daily_variance = 0
                cumulative_variance = 0
        except ZeroDivisionError:
            daily_target = 0
            daily_target_actual = 0
            cumulative_target = 0
            daily_variance = 0
            cumulative_variance = 0
        return {
            "month_plan": month_plan,
            "daily_target": daily_target,
            "cumulative_target": cumulative_target,
            "total_days": total_days,
            "cumulative_target_actual": cumulative_target_actual,
            "daily_target_actual": daily_target_actual,
            "days_passed": days_passed,
            "remaining_hours": remaining_hours,
            "daily_variance": daily_variance,
            "cumulative_variance": cumulative_variance,
            "days_left": days_left,
        }
