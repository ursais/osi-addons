# onlogic specific

KEY = "ZbSjuPJpRkpEB"

# For Exclusion Report
# env.cr.execute(
#     """
# select col.table_name,
#       col.column_name
# from information_schema.columns col
# join information_schema.tables tab on tab.table_schema = col.table_schema
#                                   and tab.table_name = col.table_name
#                                   and tab.table_type = 'BASE TABLE'

# JOIN
#     ir_model_fields imf ON imf.model = REPLACE(col.table_name, '_', '.') AND imf.name = col.column_name
# where col.data_type in ('character varying', 'character', 'text', '"char"', 'name') and imf.ttype != 'selection'
#     and col.table_schema not in ('information_schema', 'pg_catalog')
#       and (col.table_name like 'ir%' or tab.table_name like 'mail%'
#       or col.table_name like 'report%' or col.table_name in  (
#       'mrp_automation_result_line',
#       'sale_order_estimated_ship_date',
#       'res_config_settings',
#       'res_country',
#       'res_country_group',
#       'res_groups',
#       'res_lang',
#       'res_users'
#     ) )
# order by col.table_name, col.ordinal_position;"""
# )
# base_excluded_list = env.cr.fetchall()
# base_excluded_table_columns_dict = {}
# for table, column in base_excluded_list:
#     if table in base_excluded_table_columns_dict and column not in base_excluded_table_columns_dict[table]:
#         base_excluded_table_columns_dict[table].append(column)
#     else:
#         base_excluded_table_columns_dict[table] = [column]
# raise Warning(base_excluded_table_columns_dict.items())

# --------------- START -------------------------
# Index drop
env.cr.execute("drop index IF EXISTS account_move_line_partner_id_ref_idx;")
env.cr.execute("drop index IF EXISTS account_move_line_ref_index;")
env.cr.execute("drop index IF EXISTS crm_lead_email_from_index;")
env.cr.commit()

# env.cr.execute(
#     """
# select col.table_name,
#       col.column_name
# from information_schema.columns col
# join information_schema.tables tab on tab.table_schema = col.table_schema
#                                   and tab.table_name = col.table_name
#                                   and tab.table_type = 'BASE TABLE'

# JOIN
#     ir_model_fields imf ON imf.model = REPLACE(col.table_name, '_', '.') AND imf.name = col.column_name
# where col.data_type in ('character varying', 'character', 'text', '"char"', 'name') and imf.ttype != 'selection'
#     and col.table_schema not in ('information_schema', 'pg_catalog')
#       and col.table_name not like 'ir%' and (col.character_maximum_length is null) and tab.table_name not like 'mail%'
#       and col.table_name not like 'report%' and col.table_name not in  ('res_config_settings','res_country','res_country_group','res_groups','res_lang', 'res_users')
# order by col.table_name, col.ordinal_position;"""
# )

# table_columns_list_set = env.cr.fetchall()
table_columns_list_set = [
    # ('mrp_automation_result_line', 'value'),
    ("mrp_automation_result_line", "key"),
]

# This will store the tables that need to be excluded
excluded_tables = {
    # exclude due to errors
    "sale_order_estimated_ship_date",
    "mrp_automation_result_line",
    # exclude because they are working and were already done
    "avatax_transaction",
    "account_payment",
    "bus_bus",
    "calendar_attendee",
    "connector_checkpoint",
    "corrective_action",
    "crm_lead",
    "graphql_queue",
    "internal_purchase_request",
    "internal_purchase_request_line",
    "product_hts",
    "purchase_order",
    "res_company",
    "res_partner_address",
    "tracking_number",
    "crm_event_log",
    "account_account",
    "account_account_tag",
    "account_account_template",
    "account_account_type",
    "account_analytic_account",
    "account_analytic_group",
    "account_analytic_line",
    "account_analytic_tag",
    "account_auto_reconciliation",
    "account_auto_reconciliation_wizard",
    "account_bank_statement",
    "account_bank_statement_line",
    "account_cash_rounding",
    "account_chart_template",
    "account_cost_center",
    "account_financial_html_report",
    "account_financial_html_report_line",
    "account_fiscal_position",
    "account_fiscal_position_template",
    "account_fiscal_year",
    "account_full_reconcile",
    "account_group",
    "account_incoterms",
    "account_journal",
    "account_journal_group",
    "account_move",
    "account_move_line",
    "account_move_reversal",
    "account_payment_method",
    "account_payment_term",
    "account_reconcile_model",
    "account_reconcile_model_template",
    "account_report_footnote",
    "account_report_manager",
    "account_setup_bank_manual_config",
    "account_tax",
    "account_tax_group",
    "account_tax_report_line",
    "account_tax_template",
    "account_transfer_model",
    "api_client",
    "auth_oauth_provider",
    "auto_stock_allocation",
    "avalara_salestax",
    "avalara_salestax_address_validate",
    "avalara_salestax_ping",
    "bank_acc_rec_statement",
    "base_automation",
    "base_automation_lead_test",
    "base_automation_line_test",
    "base_language_export",
    "base_language_import",
    "base_module_upgrade",
    "base_partner_merge_line",
    "build_profile_viewer_wizard",
    "calendar_alarm",
    "calendar_event",
    "calendar_event_type",
    "cash_box_out",
    "change_confirmation",
    "change_password_user",
    "choose_delivery_carrier",
    "connector_config_settings",
    "constrained_sku_result_wizard_line",
    "constrained_sku_search_wizard",
    "corrective_action_department",
    "corrective_action_issue_cause",
    "corrective_action_stage",
    "corrective_action_trend",
    "coupon_code",
    "crm_lead2dead_partner",
    "crm_lead_competitor",
    "crm_lead_interest",
    "crm_lead_lost",
    "crm_lead_scoring_frequency",
    "crm_lead_software",
    "crm_lead_tag",
    "crm_lost_reason",
    "crm_note",
    "crm_opportunity2phonecall",
    "crm_phonecall_category",
    "crm_stage",
    "crm_team",
    "currency_rate_update_service",
    "ddmrp_product_plan_custom",
    "decimal_precision",
    "delivery_carrier",
    "delivery_configuration_line",
    "delivery_configurator",
    "delivery_configurator_line",
    "delivery_price_rule",
    "digest_digest",
    "digest_tip",
    "estimated_ship_date_wizard",
    "exemption_code",
    "external_system",
    "failure_reason",
    "fetchmail_server",
    "forward_confirmation_email_wizard",
    "helpdesk_it_service",
    "helpdesk_jira_config",
    "helpdesk_rma",
    "helpdesk_rma_line",
    "helpdesk_rma_resolve_wizard",
    "helpdesk_rma_tags",
    "helpdesk_sla",
    "helpdesk_stage",
    "helpdesk_tag",
    "helpdesk_team",
    "helpdesk_ticket",
    "helpdesk_ticket_type",
    "hr_applicant",
    "hr_applicant_category",
    "hr_contract",
    "hr_department",
    "hr_departure_wizard",
    "hr_employee",
    "hr_employee_category",
    "hr_expense",
    "hr_expense_refuse_wizard",
    "hr_expense_sheet",
    "hr_expense_sheet_register_payment_wizard",
    "hr_job",
    "hr_leave",
    "hr_leave_allocation",
    "hr_leave_type",
    "hr_plan",
    "hr_plan_activity_type",
    "hr_recruitment_degree",
    "hr_recruitment_stage",
    "hr_work_entry",
    "hr_work_entry_type",
    "import_tc_pdf_wizard",
    "inbound_shipping_type",
    "invoice_reminder",
    "invoice_reminder_scheduled_item",
    "invoice_reminder_severity_level",
    "jira_issue",
    "jira_project",
    "lead_time_calculator_wizard",
    "link_tracker",
    "link_tracker_click",
    "link_tracker_code",
    "ls_delivery_sale_order_carrier_wizard",
    "ls_partner_type_wizard",
    "ls_templates_wizard",
    "magento_account_invoice",
    "magento_address",
    "magento_backend",
    "magento_bom_option_name",
    "magento_product_category",
    "magento_product_product",
    "magento_res_partner",
    "magento_res_partner_category",
    "magento_sale_order",
    "magento_sale_order_line",
    "magento_stock_picking_out",
    "magento_store",
    "magento_storeview",
    "magento_website",
    "marketing_activity",
    "marketing_campaign",
    "marketing_participant",
    "marketing_source",
    "marketing_trace",
    "merge_purchase_order",
    "metrics_dashboard",
    "migration_domain",
    "migration_job",
    "migration_result",
    "migration_run",
    "mrp_assembly_check",
    "mrp_assembly_stage",
    "mrp_automation_step_wizard",
    "mrp_automation_task",
    "mrp_automation_task_line",
    "mrp_automation_task_type",
    "mrp_bom",
    "mrp_bom_line",
    "mrp_bom_option",
    "mrp_label",
    "mrp_label_selector",
    "mrp_label_selector_category",
    "mrp_label_template",
    "mrp_labelprinter",
    "mrp_labelprinter_location",
    "mrp_production",
    "mrp_production_add_serial_wizard_line",
    "mrp_production_plan_multiple",
    "mrp_production_product_line",
    "mrp_production_serial_transfer_wizard",
    "mrp_routing",
    "mrp_routing_workcenter",
    "mrp_test",
    "mrp_test_line",
    "mrp_test_type",
    "mrp_unbuild",
    "mrp_workcenter",
    "mrp_workcenter_productivity",
    "mrp_workcenter_productivity_loss",
    "mrp_workorder",
    "order_edit_pricing_line",
    "order_edit_wizard",
    "order_scheduler_exclusions",
    "order_status_label",
    "payment_acquirer",
    "payment_acquirer_onboarding_wizard",
    "payment_icon",
    "payment_link_wizard",
    "payment_method",
    "payment_method_wizard",
    "payment_token",
    "payment_transaction",
    "paypal_verification",
    "phone_blacklist",
    "portal_share",
    "portal_wizard",
    "portal_wizard_user",
    "print_prenumbered_checks",
    "procurement_group",
    "product_attribute",
    "product_attribute_classification",
    "product_attribute_custom_value",
    "product_attribute_value",
    "product_category",
    "product_ls_stock_status",
    "product_packaging",
    "product_pricelist",
    "product_pricelist_item",
    "product_product",
    "product_removal",
    "product_supplierinfo",
    "product_tax_code",
    "product_template",
    "project_project",
    "project_tags",
    "project_task",
    "project_task_create_timesheet",
    "project_task_type",
    "purchase_order_line",
    "quality_alert",
    "quality_alert_stage",
    "quality_alert_team",
    "quality_check",
    "quality_point",
    "quality_reason",
    "quality_tag",
    "queue_job",
    "queue_job_channel",
    "queue_job_function",
    "queue_worker",
    "queued_email",
    "quote_configuration",
    "rating_rating",
    "reformat_all_phonenumbers",
    "related_component_stock_line",
    "repair_fee",
    "repair_line",
    "repair_order",
    "repair_tags",
    "res_bank",
    "res_country_state",
    "res_currency",
    "res_customer",
    "res_customer_bulk_change",
    "res_customer_bulk_change_line",
    "res_customer_bulk_change_wizard",
    "res_partner",
    "res_partner_bank",
    "res_partner_category",
    "res_partner_industry",
    "res_partner_title",
    "res_paypref",
    "resource_calendar",
    "resource_calendar_attendance",
    "resource_calendar_leaves",
    "resource_resource",
    "resource_test",
    "rma_failure_reason",
    "rma_rma",
    "rma_vendor",
    "sale_bom",
    "sale_bom_line",
    "sale_booking",
    "sale_booking_line",
    "sale_exception",
    "sale_holiday",
    "sale_ignore_cancel",
    "sale_metric",
    "sale_metric_goal_holiday",
    "sale_metric_type",
    "sale_order",
    "sale_order_line",
    "sale_order_option",
    "sale_order_payment_method",
    "sale_order_payment_method_base",
    "sale_order_template",
    "sale_order_template_line",
    "sale_order_template_option",
    "sale_payment_acquirer_onboarding_wizard",
    "sale_price_line",
    "sale_price_tier",
    "sale_trigger_lockdown",
    "sale_vertical",
    "sale_workflow_check",
    "sale_workflow_hold",
    "sale_workflow_notification",
    "sale_workflow_process",
    "scrap_creation_wizard",
    "scrapping_reason_requirement",
    "stage_lookup_bulk_edit_wizard",
    "stage_lookup_line",
    "stage_lookup_line_priority",
    "stage_lookup_line_priority_setting",
    "stage_lookup_rules_viewer_wizard",
    "stock_assign_serial",
    "stock_inventory",
    "stock_inventory_line",
    "stock_location",
    "stock_location_route",
    "stock_move",
    "stock_move_line",
    "stock_move_scrap",
    "stock_picking",
    "stock_picking_start_multiple",
    "stock_picking_transfer_multiple",
    "stock_picking_type",
    "stock_production_lot",
    "stock_quant_package",
    "stock_rule",
    "stock_scrap",
    "stock_valuation_layer",
    "stock_warehouse",
    "stock_warehouse_orderpoint",
    "stripe_charge",
    "stripe_event",
    "stripe_saved_card",
    "supplier_return",
    "supplier_return_line",
    "support_repair_order",
    "system_relation_cleaner_wizard_line",
    "system_stock_status_result_wizard",
    "tax_adjustments_wizard",
    "tier_price_check_wizard",
    "turn_product_quarter",
    "uom_category",
    "uom_uom",
    "utm_campaign",
    "utm_medium",
    "utm_source",
    "utm_stage",
    "utm_tag",
    "voip_phonecall",
    "voip_phonecall_log_wizard",
    "voip_phonecall_transfer_wizard",
    "webhook",
    "webhook_broadcast_date",
    "webhook_event",
    "website",
    "website_menu",
    "website_page",
    "website_rewrite",
    "website_route",
    "website_track",
    "website_visitor",
    "wizard_csv_loader",
    "wizard_ir_model_menu_create",
    "wizard_positive_pay",
    "wizard_stock_move",
    "wizard_stock_picking",
}

# This will store the columns that need to be excluded
excluded_table_columns = {
    #'tracking_number':['number'],# value too long for type (128)
}

table_columns_dict = {}
for table, column in table_columns_list_set:
    if table in excluded_tables:
        continue
    if table in excluded_table_columns and column in excluded_table_columns[table]:
        continue
    if table in table_columns_dict and column not in table_columns_dict[table]:
        table_columns_dict[table].append(column)
    else:
        table_columns_dict[table] = [column]
# raise Warning(table_columns_dict.items())
# ------------------------------------------- CHAR Fields -------------------------------------------------
# env.cr.execute(
#     """
# select col.table_name,
#       col.column_name
# from information_schema.columns col
# join information_schema.tables tab on tab.table_schema = col.table_schema
#                                   and tab.table_name = col.table_name
#                                   and tab.table_type = 'BASE TABLE'

# JOIN
#     ir_model_fields imf ON imf.model = REPLACE(col.table_name, '_', '.') AND imf.name = col.column_name
# where col.data_type in ('character varying', 'character', 'text', '"char"', 'name') and imf.ttype != 'selection'
#     and col.table_schema not in ('information_schema', 'pg_catalog')
#       and col.table_name not like 'ir%' and (col.character_maximum_length is not null) and tab.table_name not like 'mail%'
#       and col.table_name not like 'report%' and col.table_name not in  ('res_config_settings','res_country','res_country_group','res_groups','res_lang', 'res_users')
# order by col.table_name, col.ordinal_position;"""
# )

# char_limit_table_columns_list_set = env.cr.fetchall()

# # Char Limit Fields to Include - change limit then add to list
# exclude_char_limit_table_columns = {
#   'account_account':['shortcut','code'],
#   'account_account_template':['shortcut','code'],
#   'account_incoterms':['code'],
#   'asterisk_server':['context','out_prefix'],
#   'account_journal':['code'],
#   'stock_warehouse':['code'],
#   'base_language_import':['code'],
#   'account_analytic_line':['code'],
#   'product_packaging':['ean'],
#   'product_product':['ic_id','fcc_id','manufacturer_pref','variants'],
#   'product_template':['ic_id','fcc_id'],
#   'product_hts':['hts','schedule_b'],
#   'account_account_type':['code'],
#   'account_payment_term_line':['name'],
#   'barcode_nomenclature':['name'],
#   'barcode_rule':['alias','name','pattern'],
#   'crm_lead':['close_stage','order_id','ref2','ref'],
#   'hr_attendance':['day'],
#   'res_currency':['name'],
#   'account_journal_column':['name'],
#   'account_journal_view':['name'],
#   'bank_acc_rec_statement':['name'],
#   'bank_acc_rec_statement_line':['name','ref'],
#   'board_board':['name'],
#   'hr_applicant':['title_action'],
#   'rma_tags':['name'],
#   'stock_production_lot':['prefix'],
#   'calendar_attendee':['dir','ref'],
#   'base_automation':['act_email_from','act_email_to','act_mail_to_email','act_method','act_reply_to','regex_history','regex_name'],
#   'connector_checkpoint':['backend_id'],
#   'corrective_action':['ref'],
#   'crm_event_log':['event'],
#   'res_company':['rml_footer1','automation_engine_url','paypal_account'],
#   'calendar_event':['exrule'],
#   'tracking_number':['notes','number'], # "cannot alter type of a column used by a view or rule DETAIL:  rule _RETURN on view vw_tracking_number depends on column "notes" "cannot alter type of a column used by a view or rule DETAIL:  rule _RETURN on view vw_tracking_number depends on column "number"

#   #worked
#   'asterisk_server':['login','password','name','ip_address','alert_info'],
#   'base_automation':['act_email_cc'],
#   'calendar_attendee':['delegated_from','sent_by','member','delegated_to'],
#   'calendar_event':['email_from','organizer','base_calendar_url'],
#   'crm_lead':['birthdate','budget','lastname','firstname','phone_ext','email','keyword_details'],
#   'crm_lead_pain':['name'],
#   'crm_partner2opportunity':['name'],
#   'crm_phonecall2opportunity':['name'],
#   'crm_team':['complete_name'],
#   'hr_applicant':['partner_mobile','partner_phone','email_from'],
#   'internal_purchase_request':['name','subject','hyperlink'],
#   'internal_purchase_request_alternate_line':['hyperlink'],
#   'internal_purchase_request_line':['name','hyperlink'],
#   'number_not_found':['e164_number','calling_number'],
#   'product_hts':['name','short_description'],
#   'product_product':['manufacturer_pname'],
#   'project_project':['reply_to'],
#   'purchase_order':['shipping_notes','contact_name'],
#   'res_partner':['phone_ext'],
#   'res_partner_address':['zip','fax','phone','name','mobile','birthdate','function','street2','street','city','email'],
#   'res_partner_bank':['bank_bic','zip'],
#   'res_payterm':['name'],
#   'tracking_number':['custom_title'],
#   'voip_phonecall':['phone_ext'],
# }
# char_limit_table_columns_dict = {}
# for table, column in char_limit_table_columns_list_set:
#     if table in exclude_char_limit_table_columns and column in exclude_char_limit_table_columns[table]:
#       continue
#     if table in table_columns_dict and column not in table_columns_dict[table]:
#         table_columns_dict[table].append(column)
#         char_limit_table_columns_dict[table].append(column)
#     else:
#         table_columns_dict[table] = [column]
#         char_limit_table_columns_dict[table] = [column]

# # log("Excluded" + str(exclude_char_limit_table_columns.items()), level="Excluded")
# # log("Included" + str(table_columns_dict.items()), level="Included")
# raise Warning(table_columns_dict.items())

# # Change character_maximum_length to a high number
# varchar_log = ""
# for table, columns in char_limit_table_columns_dict.items():
#   for col in columns:
#     varchar_query = """SELECT column_name, character_maximum_length
#                       FROM information_schema.columns
#                       WHERE column_name = '%s' AND table_name = '%s'""" % (col,table)
#     env.cr.execute(varchar_query)
#     original_varchar = env.cr.fetchall()

#     query = """ ALTER TABLE %s ALTER COLUMN %s TYPE VARCHAR(10000);""" % (table,col)
#     varchar_log += "character_maximum_length on " + str(original_varchar) + " has been changed to 10000 by the following query: " + query + "\n"
#     env.cr.execute(query)
#     env.cr.commit()

# log(varchar_log, level="Info")

# -------------------- END CHAR LIMITE FIELDS ------------------------------------

# -------------------- PERFORM ENCRYPTION ----------------------------------------
log(str(table_columns_dict), level="START")

env.cr.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")
env.cr.commit()

for table, columns in table_columns_dict.items():
    runningerrorLog = ""
    query = "SELECT id, {}  FROM {} ORDER BY id".format(
        ", ".join(['"%s"' % c for c in columns]), table
    )
    env.cr.execute(query)
    table_data = env.cr.fetchall()

    log(
        "\n\nGoing Through Table: %s for Columns: %s with %s records"
        % (table, str(columns), len(table_data)),
        level="Info",
    )

    rec_updated_ids = []
    for col_data in table_data:
        id = col_data[0]
        set_data = []

        for col, col_data in zip(columns, col_data[1:]):
            if col_data:
                set_data.append(
                    (
                        col,
                        col_data,
                    )
                )
                rec_updated_ids.append(id)

        if not set_data:
            continue
        set_data_str = ",".join(
            [
                """"%s" = pgp_sym_encrypt('%s', '%s')"""
                % (col, col_data.replace("'", "''"), KEY)
                for col, col_data in set_data
            ]
        )

        try:
            query = """ UPDATE %s SET %s  where id = %s ;""" % (
                table,
                set_data_str,
                id,
            )
            env.cr.execute(query)

        except Exception as e:
            raise Warning("ERROR: %s \n WHEN RUNNING QUERY: \n%s\n" % (e, query))
    env.cr.commit()
    log(
        "Updated data for %s records from table %s: \n %s \n"
        % (len(rec_updated_ids), table, runningerrorLog),
        level="Info",
    )

log("Completed Encryption Script", level="END")
