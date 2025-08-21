from odoo import fields
from odoo.http import request
from datetime import datetime,timedelta
from dateutil.relativedelta import relativedelta
import pytz


def compute_domain(domain_tuple,model):
    """
    This function takes a tuple of a domain and a model name as input. It parses
    the domain and replaces 0 with the current user's ID or the current company's
    ID if the field on the left-hand side of the domain is a many2one or many2many
    field that references res.users or res.company. It then returns the modified
    domain.
    
    :param domain_tuple: A tuple of a domain and a model name
    :type domain_tuple: tuple
    :return: The modified domain
    :rtype: tuple
    """
    left_value = domain_tuple[0]
    operator_value = domain_tuple[1]
    right_value = domain_tuple[2]
    left_value_split_list = left_value.split('.')
    left_user = False
    left_company = False
    field_obj = request.env['ir.model.fields'].sudo()
    model_obj = request.env[model]._name
    for field in left_value_split_list:
        left_user = False
        left_company = False
        model_field = field_obj.search([('model_id.model','=',model_obj),('name','=',field)],limit=1)
        field_type = model_field.ttype
        if field_type in ['many2one', 'many2many', 'one2many']:
            model_obj = model_field.relation
            field_relation = model_field.relation
            relation_model = field_relation
            if relation_model == 'res.users':
                left_user = True
            if relation_model == 'res.company': 
                left_company = True
    
    if left_user:
        if operator_value in ['in', 'not in']:
            if isinstance(right_value, list) and 0 in right_value:
                zero_index = right_value.index(0)
                right_value[zero_index] = request.env.user.id

    if left_company:
        if operator_value in ['in', 'not in']:
            if isinstance(right_value, list) and 0 in right_value:
                zero_index = right_value.index(0)
                right_value[zero_index] = request.env.company.id

def prepare_domain_v2(domain):
    if isinstance(domain, tuple) or isinstance(domain, list):
        field_name = domain[0]
        operator = domain[1]
        val = domain[2]

        # Initialize timezone
        user_tz = request.env.user.tz or 'UTC'
        tz = pytz.timezone(user_tz)
        current_date = datetime.now(tz).replace(hour=0, minute=0, second=0, microsecond=0)

        if operator != "date_filter":
            return [tuple(domain)]

        if val == "today":
            start_of_today = current_date
            end_of_today = start_of_today + timedelta(days=1)
            return ["&", (field_name, ">=", fields.Datetime.to_string(start_of_today)),
                    (field_name, "<", fields.Datetime.to_string(end_of_today))]

        if val == "this_week":
            start_of_week = current_date - timedelta(days=current_date.weekday())
            end_of_week = start_of_week + timedelta(days=7)
            return ["&", (field_name, ">=", fields.Datetime.to_string(start_of_week)),
                    (field_name, "<", fields.Datetime.to_string(end_of_week))]

        if val == "this_month":
            start_of_month = current_date.replace(day=1)
            end_of_month = start_of_month + relativedelta(months=1)
            return ["&", (field_name, ">=", fields.Datetime.to_string(start_of_month)),
                    (field_name, "<", fields.Datetime.to_string(end_of_month))]

        if val == "this_quarter":
            quarter_start_month = ((current_date.month - 1) // 3) * 3 + 1
            start_of_quarter = current_date.replace(month=quarter_start_month, day=1)
            end_of_quarter = start_of_quarter + relativedelta(months=3)
            return ["&", (field_name, ">=", fields.Datetime.to_string(start_of_quarter)),
                    (field_name, "<", fields.Datetime.to_string(end_of_quarter))]

        if val == "this_year":
            start_of_year = current_date.replace(month=1, day=1)
            end_of_year = start_of_year + relativedelta(years=1)
            return ["&", (field_name, ">=", fields.Datetime.to_string(start_of_year)),
                    (field_name, "<", fields.Datetime.to_string(end_of_year))]

        if val == "last_day":
            start_of_yesterday = current_date - timedelta(days=1)
            end_of_yesterday = current_date
            return ["&", (field_name, ">=", fields.Datetime.to_string(start_of_yesterday)),
                    (field_name, "<", fields.Datetime.to_string(end_of_yesterday))]

        if val == "last_week":
            end_of_last_week = current_date - timedelta(days=current_date.weekday())
            start_of_last_week = end_of_last_week - timedelta(days=7)
            return ["&", (field_name, ">=", fields.Datetime.to_string(start_of_last_week)),
                    (field_name, "<", fields.Datetime.to_string(end_of_last_week))]

        if val == "last_month":
            start_of_last_month = current_date.replace(day=1) - relativedelta(months=1)
            end_of_last_month = current_date.replace(day=1)
            return ["&", (field_name, ">=", fields.Datetime.to_string(start_of_last_month)),
                    (field_name, "<", fields.Datetime.to_string(end_of_last_month))]

        if val == "last_quarter":
            quarter_start_month = ((current_date.month - 1) // 3) * 3 + 1
            end_of_last_quarter = current_date.replace(month=quarter_start_month, day=1)
            start_of_last_quarter = end_of_last_quarter - relativedelta(months=3)
            return ["&", (field_name, ">=", fields.Datetime.to_string(start_of_last_quarter)),
                    (field_name, "<", fields.Datetime.to_string(end_of_last_quarter))]

        if val == "last_year":
            start_of_last_year = current_date.replace(year=current_date.year - 1, month=1, day=1)
            end_of_last_year = current_date.replace(month=1, day=1)
            return ["&", (field_name, ">=", fields.Datetime.to_string(start_of_last_year)),
                    (field_name, "<", fields.Datetime.to_string(end_of_last_year))]

        if val == "last_7_days":
            start_of_last_7_days = current_date - timedelta(days=6)
            return [(field_name, ">=", fields.Datetime.to_string(start_of_last_7_days))]

        if val == "last_30_days":
            start_of_last_30_days = current_date - timedelta(days=29)
            return [(field_name, ">=", fields.Datetime.to_string(start_of_last_30_days))]

        if val == "last_90_days":
            start_of_last_90_days = current_date - timedelta(days=89)
            return [(field_name, ">=", fields.Datetime.to_string(start_of_last_90_days))]

        if val == "last_365_days":
            start_of_last_365_days = current_date - timedelta(days=364)
            return [(field_name, ">=", fields.Datetime.to_string(start_of_last_365_days))]

        if val == "next_day":
            start_of_next_day = current_date + timedelta(days=1)
            end_of_next_day = start_of_next_day + timedelta(days=1)
            return ["&", (field_name, ">=", fields.Datetime.to_string(start_of_next_day)),
                    (field_name, "<", fields.Datetime.to_string(end_of_next_day))]

        if val == "next_week":
            start_of_next_week = current_date + timedelta(days=(7 - current_date.weekday()))
            end_of_next_week = start_of_next_week + timedelta(days=7)
            return ["&", (field_name, ">=", fields.Datetime.to_string(start_of_next_week)),
                    (field_name, "<", fields.Datetime.to_string(end_of_next_week))]

        if val == "next_month":
            start_of_next_month = current_date.replace(day=1) + relativedelta(months=1)
            end_of_next_month = start_of_next_month + relativedelta(months=1)
            return ["&", (field_name, ">=", fields.Datetime.to_string(start_of_next_month)),
                    (field_name, "<", fields.Datetime.to_string(end_of_next_month))]

        if val == "next_quarter":
            quarter_start_month = ((current_date.month - 1) // 3) * 3 + 1
            end_of_current_quarter = current_date.replace(month=quarter_start_month, day=1) + relativedelta(months=3)
            start_of_next_quarter = end_of_current_quarter
            end_of_next_quarter = start_of_next_quarter + relativedelta(months=3)
            return ["&", (field_name, ">=", fields.Datetime.to_string(start_of_next_quarter)),
                    (field_name, "<", fields.Datetime.to_string(end_of_next_quarter))]

        if val == "next_year":
            start_of_next_year = current_date.replace(year=current_date.year + 1, month=1, day=1)
            end_of_next_year = start_of_next_year + relativedelta(years=1)
            return ["&", (field_name, ">=", fields.Datetime.to_string(start_of_next_year)),
                    (field_name, "<", fields.Datetime.to_string(end_of_next_year))]

    return [tuple(domain)]

# def prepare_domain(domain):
#     prepared_domain =[]
#     if isinstance(domain, tuple) or isinstance(domain, list):
#         left_value = domain[0]
#         operator_value = domain[1]
#         right_value = domain[2]
#         if operator_value == 'date_filter':
        
#             current_date=datetime.now()
#             dom_list=list(domain)

#             if right_value == 'today':
                
#                 dom_list[1]='='
#                 dom_list[2]=current_date
            
#             elif right_value == 'this_week':
#                 dom_list[1]='>'
#                 current_day_of_week = current_date.weekday()
#                 if current_day_of_week == 6:
#                     first_date_of_week = current_date
#                 else:
#                     days_until_start_of_week = current_day_of_week + 1
#                     first_date_of_week = current_date - timedelta(days=days_until_start_of_week)

#                 dom_list[2]=first_date_of_week
                
#             elif right_value == 'this_month':
#                 dom_list[1]='>='
#                 first_date_of_month=current_date.replace(day=1)
#                 dom_list[2]=first_date_of_month
                
#             elif right_value == 'this_quarter':
#                 dom_list[1]='>='
#                 current_month = current_date.month
#                 current_quarter = (current_month - 1) // 3 + 1
#                 current_year = current_date.year
#                 quarter_start_month = (current_quarter - 1) * 3 + 1
#                 quarter_start_date = datetime(current_year, quarter_start_month, 1)

#                 quarter_end_month = quarter_start_month + 2
#                 quarter_end_date = datetime(current_year, quarter_end_month, 1)
#                 quarter_end_date = quarter_end_date.replace(day=quarter_end_date.day, hour=23, minute=59, second=59)
                
#                 dom_list[2]=quarter_start_date

#                 this_qua_end_dom_list.append(dom_list[0])
#                 this_qua_end_dom_list.append('<=')
#                 this_qua_end_dom_list.append(quarter_end_date)

#             elif right_value == 'this_year':
#                 dom_list[1]='>='
#                 first_this_year_date=datetime(current_date.year, 1, 1)
#                 last_date_of_year = datetime(current_date.year, 12, 31)
#                 dom_list[2]=first_this_year_date

#                 this_year_end_dom_list.append(dom_list[0])
#                 this_year_end_dom_list.append('<=')
#                 this_year_end_dom_list.append(last_date_of_year)

            
#             elif right_value == 'last_day':
                
#                 dom_list[1]='>'
#                 last_day_date=current_date+ timedelta(days=-1)
#                 dom_list[2]=last_day_date

#             elif right_value == 'last_week':
#                 dom_list[1]='>='
                
#                 last_week_start = current_date - timedelta(days=current_date.weekday() + 8)
#                 last_week_end = last_week_start + timedelta(days=6)
#                 dom_list[2]=last_week_start

#                 last_week_end_date_dom_list.append(dom_list[0])
#                 last_week_end_date_dom_list.append('<=')
#                 last_week_end_date_dom_list.append(last_week_end)

#             elif right_value == 'last_month':
                
#                 dom_list[1]='>='

#                 last_month_end_date=current_date.replace(day=1)- timedelta(days=1)
#                 if last_month_end_date.strftime('%d')=='31':
#                     last_month_start_date=last_month_end_date-timedelta(days=30)

#                 elif last_month_end_date.strftime('%d')=='30':
#                     last_month_start_date=last_month_end_date-timedelta(days=29)

#                 elif last_month_end_date.strftime('%d')=='29':
#                     last_month_start_date=last_month_end_date-timedelta(days=28)

#                 elif last_month_end_date.strftime('%d')=='28':
#                     last_month_start_date=last_month_end_date-timedelta(days=27)
                
#                 dom_list[2]=last_month_start_date

#                 last_month_end_date_dom_list.append(dom_list[0])
#                 last_month_end_date_dom_list.append('<=')
#                 last_month_end_date_dom_list.append(last_month_end_date)

#             elif right_value == 'last_quarter':
#                 dom_list[1]='>='
#                 current_month = current_date.month
#                 current_quarter = (current_month - 1) // 3 + 1
#                 current_year = current_date.year

#                 if current_quarter == 1:
#                     last_quarter_start = datetime(current_year - 1, 10, 1)
#                 else:
#                     last_quarter_start = datetime(current_year, (current_quarter - 2) * 3 + 1, 1)

#                 if current_quarter == 1:
#                     last_quarter_end = datetime(current_year - 1, 12, 31)
#                 else:
#                     last_quarter_end = datetime(current_year, (current_quarter - 1) * 3, 1) - timedelta(days=1)

                
#                 dom_list[2]=last_quarter_start

#                 last_qua_end_dom_list.append(dom_list[0])
#                 last_qua_end_dom_list.append('<=')
#                 last_qua_end_dom_list.append(last_quarter_end)

#             elif right_value == 'last_year':
#                 dom_list[1]='>='
#                 last_year = current_date.year - 1
#                 first_date_of_last_year = datetime(last_year, 1, 1)
#                 last_date_of_last_year = datetime(last_year, 12, 31)
#                 dom_list[2]=first_date_of_last_year
                
#                 last_year_end_dom_list.append(dom_list[0])
#                 last_year_end_dom_list.append('<=')
#                 last_year_end_dom_list.append(last_date_of_last_year)

#             elif right_value == 'last_7_days':
#                 dom_list[1]='>='
#                 last_7_days_date=current_date+ timedelta(days=-7)
#                 dom_list[2]=last_7_days_date

#             elif right_value == 'last_30_days':
#                 dom_list[1]='>='
#                 last_30_days_date=current_date+ timedelta(days=-30)
#                 dom_list[2]=last_30_days_date
                
#             elif right_value == 'last_90_days':
#                 dom_list[1]='>='
#                 last_90_days_date=current_date+ timedelta(days=-90)
#                 dom_list[2]=last_90_days_date

#             elif right_value == 'last_365_days':
#                 dom_list[1]='>='
#                 last_365_days_date=current_date+ timedelta(days=-365)
#                 dom_list[2]=last_365_days_date
               
#             elif right_value == "next_day":
#                 next_day_date=current_date+ timedelta(days=+1)
#                 dom_list[1]='>'
#                 last_365_days_date=current_date+ timedelta(days=-365)
#                 dom_list[2]=last_365_days_date
#                 pass
#             elif right_value == "next_week":
#                 pass
#             elif right_value == "next_month":
#                 pass
#             elif right_value == "next_year":
#                 pass


#         else:
#             prepared_domain.append(dom_tuple)
#     return prepared_domain














# def prepare_domain(domain):
#     prepared_domain =[]
#     if isinstance(domain, tuple) or isinstance(domain, list):
#         left_value = domain[0]
#         operator_value = domain[1]
#         right_value = domain[2]
#         if operator_value == 'date_filter':
        
#             current_date=datetime.now()
#             dom_list=list(domain)
#             today_end_time=[]
#             this_qua_end_dom_list=[]
#             last_qua_end_dom_list=[]
#             this_year_end_dom_list=[]
#             last_year_end_dom_list=[]
#             last_week_end_date_dom_list=[]
#             last_month_end_date_dom_list=[]

#             if right_value == 'today':
                
#                 dom_list[1]='='
#                 dom_list[2]=current_date
            
#             elif right_value == 'this_week':
#                 dom_list[1]='>'
#                 current_day_of_week = current_date.weekday()
#                 if current_day_of_week == 6:
#                     first_date_of_week = current_date
#                 else:
#                     days_until_start_of_week = current_day_of_week + 1
#                     first_date_of_week = current_date - timedelta(days=days_until_start_of_week)

#                 dom_list[2]=first_date_of_week
                
#             elif right_value == 'this_month':
#                 dom_list[1]='>='
#                 first_date_of_month=current_date.replace(day=1)
#                 dom_list[2]=first_date_of_month
                
#             elif right_value == 'this_quarter':
#                 dom_list[1]='>='
#                 current_month = current_date.month
#                 current_quarter = (current_month - 1) // 3 + 1
#                 current_year = current_date.year
#                 quarter_start_month = (current_quarter - 1) * 3 + 1
#                 quarter_start_date = datetime(current_year, quarter_start_month, 1)

#                 quarter_end_month = quarter_start_month + 2
#                 quarter_end_date = datetime(current_year, quarter_end_month, 1)
#                 quarter_end_date = quarter_end_date.replace(day=quarter_end_date.day, hour=23, minute=59, second=59)
                
#                 dom_list[2]=quarter_start_date

#                 this_qua_end_dom_list.append(dom_list[0])
#                 this_qua_end_dom_list.append('<=')
#                 this_qua_end_dom_list.append(quarter_end_date)

#             elif right_value == 'this_year':
#                 dom_list[1]='>='
#                 first_this_year_date=datetime(current_date.year, 1, 1)
#                 last_date_of_year = datetime(current_date.year, 12, 31)
#                 dom_list[2]=first_this_year_date

#                 this_year_end_dom_list.append(dom_list[0])
#                 this_year_end_dom_list.append('<=')
#                 this_year_end_dom_list.append(last_date_of_year)

            
#             elif right_value == 'last_day':
                
#                 dom_list[1]='>'
#                 last_day_date=current_date+ timedelta(days=-1)
#                 dom_list[2]=last_day_date

#             elif right_value == 'last_week':
#                 dom_list[1]='>='
                
#                 last_week_start = current_date - timedelta(days=current_date.weekday() + 8)
#                 last_week_end = last_week_start + timedelta(days=6)
#                 dom_list[2]=last_week_start

#                 last_week_end_date_dom_list.append(dom_list[0])
#                 last_week_end_date_dom_list.append('<=')
#                 last_week_end_date_dom_list.append(last_week_end)

#             elif right_value == 'last_month':
                
#                 dom_list[1]='>='

#                 last_month_end_date=current_date.replace(day=1)- timedelta(days=1)
#                 if last_month_end_date.strftime('%d')=='31':
#                     last_month_start_date=last_month_end_date-timedelta(days=30)

#                 elif last_month_end_date.strftime('%d')=='30':
#                     last_month_start_date=last_month_end_date-timedelta(days=29)

#                 elif last_month_end_date.strftime('%d')=='29':
#                     last_month_start_date=last_month_end_date-timedelta(days=28)

#                 elif last_month_end_date.strftime('%d')=='28':
#                     last_month_start_date=last_month_end_date-timedelta(days=27)
                
#                 dom_list[2]=last_month_start_date

#                 last_month_end_date_dom_list.append(dom_list[0])
#                 last_month_end_date_dom_list.append('<=')
#                 last_month_end_date_dom_list.append(last_month_end_date)

#             elif right_value == 'last_quarter':
#                 dom_list[1]='>='
#                 current_month = current_date.month
#                 current_quarter = (current_month - 1) // 3 + 1
#                 current_year = current_date.year

#                 if current_quarter == 1:
#                     last_quarter_start = datetime(current_year - 1, 10, 1)
#                 else:
#                     last_quarter_start = datetime(current_year, (current_quarter - 2) * 3 + 1, 1)

#                 if current_quarter == 1:
#                     last_quarter_end = datetime(current_year - 1, 12, 31)
#                 else:
#                     last_quarter_end = datetime(current_year, (current_quarter - 1) * 3, 1) - timedelta(days=1)

                
#                 dom_list[2]=last_quarter_start

#                 last_qua_end_dom_list.append(dom_list[0])
#                 last_qua_end_dom_list.append('<=')
#                 last_qua_end_dom_list.append(last_quarter_end)

#             elif right_value == 'last_year':
#                 dom_list[1]='>='
#                 last_year = current_date.year - 1
#                 first_date_of_last_year = datetime(last_year, 1, 1)
#                 last_date_of_last_year = datetime(last_year, 12, 31)
#                 dom_list[2]=first_date_of_last_year
                
#                 last_year_end_dom_list.append(dom_list[0])
#                 last_year_end_dom_list.append('<=')
#                 last_year_end_dom_list.append(last_date_of_last_year)

#             elif right_value == 'last_7_days':
#                 dom_list[1]='>='
#                 last_7_days_date=current_date+ timedelta(days=-7)
#                 dom_list[2]=last_7_days_date

#             elif right_value == 'last_30_days':
#                 dom_list[1]='>='
#                 last_30_days_date=current_date+ timedelta(days=-30)
#                 dom_list[2]=last_30_days_date
                
#             elif right_value == 'last_90_days':
#                 dom_list[1]='>='
#                 last_90_days_date=current_date+ timedelta(days=-90)
#                 dom_list[2]=last_90_days_date

#             elif right_value == 'last_365_days':
#                 dom_list[1]='>='
#                 last_365_days_date=current_date+ timedelta(days=-365)
#                 dom_list[2]=last_365_days_date
               
#             elif right_value == "next_day":
#                 next_day_date=current_date+ timedelta(days=+1)
#                 dom_list[1]='>'
#                 last_365_days_date=current_date+ timedelta(days=-365)
#                 dom_list[2]=last_365_days_date
#                 pass
#             elif right_value == "next_week":
#                 pass
#             elif right_value == "next_month":
#                 pass
#             elif right_value == "next_year":
#                 pass

#             dom_tuple = dom_list
#             prepared_domain.append(tuple(dom_list))
#             if today_end_time:
#                 prepared_domain.append(tuple(today_end_time))
#             if this_qua_end_dom_list:
#                 prepared_domain.append(tuple(this_qua_end_dom_list))
#             if last_qua_end_dom_list:
#                 prepared_domain.append(tuple(last_qua_end_dom_list))
#             if last_year_end_dom_list:
#                 prepared_domain.append(tuple(last_year_end_dom_list))
#             if this_year_end_dom_list:
#                 prepared_domain.append(tuple(this_year_end_dom_list))
#             if last_week_end_date_dom_list:
#                 prepared_domain.append(tuple(last_week_end_date_dom_list))
#             if last_month_end_date_dom_list:
#                 prepared_domain.append(tuple(last_month_end_date_dom_list))

#         else:
#             prepared_domain.append(dom_tuple)
#     return prepared_domain
    



