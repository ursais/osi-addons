from odoo import models


class DutchECSalesReportCustomHandler(models.AbstractModel):
    _inherit = "account.ec.sales.report.handler"

    def _get_query_sums(self, report, options):
        if not self.env.context.get("partner_shipping_report"):
            return super()._get_query_sums(report, options)

        """Construct a query retrieving all the aggregated sums to build the report. It includes:
        - sums for all partners.
        - sums for the initial balances.
        :param options:             The report options.
        :return:                    (query, params)
        """
        params = []
        queries = []
        # Create the currency table.
        ct_query = report._get_query_currency_table(options)
        allowed_ids = self._get_tag_ids_filtered(options)

        # In the case of the generic report, we don't have a country defined. So no reliable tax report whose
        # tag_ids can be used. So we have a fallback to tax_ids.

        lang = self.env.user.lang or get_lang(self.env).code
        if options.get("sales_report_taxes", {}).get("use_taxes_instead_of_tags"):
            tax_elem_table = "account_tax"
            aml_rel_table = "account_move_line_account_tax_rel"
            tax_elem_table_name = (
                f"COALESCE(account_tax.name->>'{lang}', account_tax.name->>'en_US')"
                if self.pool["account.tax"].name.translate
                else "account_tax.name"
            )
        else:
            tax_elem_table = "account_account_tag"
            aml_rel_table = "account_account_tag_account_move_line_rel"
            tax_elem_table_name = (
                f"COALESCE(account_account_tag.name->>'{lang}', account_account_tag.name->>'en_US')"
                if self.pool["account.account.tag"].name.translate
                else "account_account_tag.name"
            )

        for (
            column_group_key,
            column_group_options,
        ) in report._split_options_per_column_group(options).items():
            tables, where_clause, where_params = report._query_get(
                column_group_options, "strict_range"
            )
            params.append(column_group_key)
            params += where_params
            if allowed_ids:
                where_clause += (
                    f" AND {tax_elem_table}.id IN %s"  # Add the tax element filter.
                )
                params.append(tuple(allowed_ids))
            queries.append(
                f"""
                SELECT
                    %s                              AS column_group_key,
                    partner_shipping.id             AS groupby,
                    partner_shipping.vat            AS vat_number,
                    res_country.code                AS country_code,
                    -SUM(account_move_line.balance) AS balance,
                    {tax_elem_table_name}           AS sales_type_code,
                    {tax_elem_table}.id             AS tax_element_id,
                    (comp_partner.country_id = partner_shipping.country_id) AS same_country
                FROM {tables}
                JOIN {ct_query} ON currency_table.company_id = account_move_line.company_id
                JOIN {aml_rel_table} ON {aml_rel_table}.account_move_line_id = account_move_line.id
                JOIN {tax_elem_table} ON {aml_rel_table}.{tax_elem_table}_id = {tax_elem_table}.id
                JOIN res_partner ON account_move_line.partner_id = res_partner.id
                JOIN res_country ON res_partner.country_id = res_country.id
                JOIN res_company ON res_company.id = account_move_line.company_id
                JOIN res_partner comp_partner ON comp_partner.id = res_company.partner_id
                LEFT JOIN account_move AS move_id 
                    ON account_move_line.move_id = move_id.id
                LEFT JOIN res_partner AS partner_shipping 
                    ON partner_shipping.id = move_id.partner_shipping_id
                WHERE {where_clause}
                
                GROUP BY {tax_elem_table}.id, {tax_elem_table}.name, partner_shipping.id,
                partner_shipping.vat, res_country.code, comp_partner.country_id, partner_shipping.country_id
            """
            )
        return " UNION ALL ".join(queries), params
