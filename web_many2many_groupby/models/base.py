# Copyright (C) 2021 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import operator
import re

from odoo import _, api, models, tools
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.osv.query import Query
from odoo.tools import OrderedSet

regex_field_agg = re.compile(r"(\w+)(?::(\w+)(?:\((\w+)\))?)?")

# valid SQL aggregation functions
VALID_AGGREGATE_FUNCTIONS = {
    "array_agg",
    "count",
    "count_distinct",
    "bool_and",
    "bool_or",
    "max",
    "min",
    "avg",
    "sum",
}


def lazy_name_get(self):
    """Evaluate self.name_get() lazily."""
    names = tools.lazy(lambda: dict(self.name_get()))
    return [(rid, tools.lazy(operator.getitem, names, rid)) for rid in self.ids]


class Base(models.AbstractModel):
    _inherit = "base"

    def _read_progress_bar(self, domain, group_by, progress_bar):
        records_values = super()._read_progress_bar(domain, group_by, progress_bar)
        group_by_name = group_by.partition(":")[0]
        field_type = self._fields[group_by_name].type
        for record_values in records_values:
            group_by_value = record_values.pop(group_by_name)
            if field_type == "many2many" and isinstance(group_by_value, list):
                record_values[group_by] = str(tuple(group_by_value)) or False
        return records_values

    @api.model
    def _read_group_format_result(self, data, annotated_groupbys, groupby, domain):
        sections = []
        data = super()._read_group_format_result(
            data, annotated_groupbys, groupby, domain
        )
        is_many2many = False
        for gb in annotated_groupbys:
            ftype = gb["type"]
            value = data[gb["groupby"]]

            # full domain for this groupby spec
            d = None
            if value:
                if ftype == "many2many":
                    value = value[0]
                    is_many2many = True
            if is_many2many:
                if d is None:
                    d = [(gb["field"], "=", value)]
                sections.append(d)
        if is_many2many:
            sections.append(domain)
            data["__domain"] = expression.AND(sections)
        return data

    @api.model
    def _read_group_raw(
        self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True
    ):
        self.check_access_rights("read")
        query = self._where_calc(domain)
        fields = fields or [f.name for f in self._fields.values() if f.store]

        groupby = [groupby] if isinstance(groupby, str) else list(OrderedSet(groupby))
        groupby_list = groupby[:1] if lazy else groupby
        annotated_groupbys = [
            self._read_group_process_groupby(gb, query) for gb in groupby_list
        ]
        groupby_fields = [g["field"] for g in annotated_groupbys]
        order = orderby or ",".join([g for g in groupby_list])
        groupby_dict = {gb["groupby"]: gb for gb in annotated_groupbys}

        self._apply_ir_rules(query, "read")
        for gb in groupby_fields:
            if gb not in self._fields:
                raise UserError(_("Unknown field %r in 'groupby'") % gb)
            gb_field = self._fields[gb].base_field
            # TODO: call super instead of overwriting it completely!
            if not (
                (gb_field.store and gb_field.column_type)
                or (gb_field.type == "many2many")
            ):
                raise UserError(
                    _(
                        """Fields in 'groupby' must be
                        database-persisted fields (no computed fields)"""
                    )
                )

        aggregated_fields = []
        select_terms = []
        fnames = []  # list of fields to flush

        for fspec in fields:
            if fspec == "sequence":
                continue
            if fspec == "__count":
                # the web client sometimes adds this pseudo-field in the list
                continue

            match = regex_field_agg.match(fspec)
            if not match:
                raise UserError(_("Invalid field specification %r.", fspec))

            name, func, fname = match.groups()
            if func:
                # we have either 'name:func' or 'name:func(fname)'
                fname = fname or name
                field = self._fields.get(fname)
                if not field:
                    raise ValueError(
                        "Invalid field {!r} on model {!r}".format(fname, self._name)
                    )
                if not (field.base_field.store and field.base_field.column_type):
                    raise UserError(_("Cannot aggregate field %r.", fname))
                if func not in VALID_AGGREGATE_FUNCTIONS:
                    raise UserError(_("Invalid aggregation function %r.", func))
            else:
                # we have 'name', retrieve the aggregator on the field
                field = self._fields.get(name)
                if not field:
                    raise ValueError(
                        "Invalid field {!r} on model {!r}".format(name, self._name)
                    )
                if not (
                    field.base_field.store
                    and field.base_field.column_type
                    and field.group_operator
                ):
                    continue
                func, fname = field.group_operator, name

            fnames.append(fname)

            if fname in groupby_fields:
                continue
            if name in aggregated_fields:
                raise UserError(_("Output name %r is used twice.", name))
            aggregated_fields.append(name)

            expr = self._inherits_join_calc(self._table, fname, query)
            if func.lower() == "count_distinct":
                term = 'COUNT(DISTINCT {}) AS "{}"'.format(expr, name)
            else:
                term = '{}({}) AS "{}"'.format(func, expr, name)
            select_terms.append(term)
        for gb in annotated_groupbys:
            select_terms.append(
                '{} as "{}" '.format(gb["qualified_field"], gb["groupby"])
            )

        self._flush_search(domain, fields=fnames + groupby_fields)

        groupby_terms, orderby_terms = self._read_group_prepare(
            order, aggregated_fields, annotated_groupbys, query
        )
        from_clause, where_clause, where_clause_params = query.get_sql()
        if lazy and (
            len(groupby_fields) >= 2 or not self._context.get("group_by_no_leaf")
        ):
            count_field = groupby_fields[0] if len(groupby_fields) >= 1 else "_"
        else:
            count_field = "_"
        count_field += "_count"

        prefix_terms = (
            lambda prefix, terms: (prefix + " " + ",".join(terms)) if terms else ""
        )
        prefix_term = (
            lambda prefix, term: ("{} {}".format(prefix, term)) if term else ""
        )

        query = """
            SELECT min("%(table)s".id) AS id, count("%(table)s".id) AS
            "%(count_field)s" %(extra_fields)s
            FROM %(from)s
            %(where)s
            %(groupby)s
            %(orderby)s
            %(limit)s
            %(offset)s
        """ % {
            "table": self._table,
            "count_field": count_field,
            "extra_fields": prefix_terms(",", select_terms),
            "from": from_clause,
            "where": prefix_term("WHERE", where_clause),
            "groupby": prefix_terms("GROUP BY", groupby_terms),
            "orderby": prefix_terms("ORDER BY", orderby_terms),
            "limit": prefix_term("LIMIT", int(limit) if limit else None),
            "offset": prefix_term("OFFSET", int(offset) if limit else None),
        }
        self._cr.execute(query, where_clause_params)
        fetched_data = self._cr.dictfetchall()

        if not groupby_fields:
            return fetched_data

        self._read_group_resolve_many2one_fields(fetched_data, annotated_groupbys)

        data = [
            {k: self._read_group_prepare_data(k, v, groupby_dict) for k, v in r.items()}
            for r in fetched_data
        ]

        fill_temporal = self.env.context.get("fill_temporal")
        if (data and fill_temporal) or isinstance(fill_temporal, dict):
            # fill_temporal = {} is equivalent to fill_temporal = True
            # if fill_temporal is a dictionary and there is no data, there is
            # a chance that we
            # want to display empty columns anyway, so we should apply the
            # fill_temporal logic
            if not isinstance(fill_temporal, dict):
                fill_temporal = {}
            data = self._read_group_fill_temporal(
                data, groupby, aggregated_fields, annotated_groupbys, **fill_temporal
            )
        result = [
            self._read_group_format_result(d, annotated_groupbys, groupby, domain)
            for d in data
        ]
        if lazy:
            # Right now, read_group only fill results in lazy mode (by default).
            # If you need to have the empty groups in 'eager' mode, then the
            # method _read_group_fill_results need to be completely reimplemented

            # in a sane way
            result = self._read_group_fill_results(
                domain,
                groupby_fields[0],
                groupby[len(annotated_groupbys) :],
                aggregated_fields,
                count_field,
                result,
                read_group_order=order,
            )
        return result

    def _read_group_resolve_many2one_fields(self, data, fields):
        rec_data = super()._read_group_resolve_many2one_fields(data, fields)
        many2xfields = {
            field["field"] for field in fields if field["type"] == "many2many"
        }
        for field in many2xfields:
            ids_set = {d[field] for d in data if d[field]}
            m2x_records = self.env[self._fields[field].comodel_name].browse(ids_set)
            data_dict = dict(lazy_name_get(m2x_records.sudo()))
            for d in data:
                d[field] = (d[field], data_dict[d[field]]) if d[field] else False
        return rec_data

    @api.model
    def _inherits_join_calc(self, alias, fname, query):
        """
        Adds missing table select and join clause(s) to ``query`` for reaching
        the field coming from an '_inherits' parent table (no duplicates).

        :param alias: name of the initial SQL alias
        :param fname: name of inherited field to reach
        :param query: query object on which the JOIN should be added
        :return: qualified name of field, to be used in SELECT clause
        """
        # INVARIANT: alias is the SQL alias of model._table in query
        model, field = self, self._fields[fname]
        if field.type == "many2many":
            while field.inherited:
                # retrieve the parent model where field is inherited from
                parent_model = self.env[field.related_field.model_name]
                parent_fname = field.related[0]
                # JOIN parent_model._table AS parent_alias
                # ON alias.parent_fname = parent_alias.id
                parent_alias = query.left_join(
                    alias, parent_fname, parent_model._table, "id", parent_fname
                )
                model, alias, field = parent_model, parent_alias, field.related_field
            # special case for many2many fields: prepare a query on the comodel
            # in order to reuse the mechanism _apply_ir_rules, then inject the
            # query as an extra condition of the left join
            comodel = self.env[field.comodel_name]
            subquery = Query(self.env.cr, comodel._table)
            comodel._apply_ir_rules(subquery)
            # add the extra join condition only if there is an actual subquery
            extra, extra_params = None, ()
            if subquery.where_clause:

                subquery_str, extra_params = subquery.select()
                extra = '"{{rhs}}"."{}" IN ({})'.format(field.column2, subquery_str)
            # LEFT JOIN field_relation ON
            #     alias.id = field_relation.field_column1
            #     AND field_relation.field_column2 IN (subquery)
            left_coumn = "id"
            if alias == "sale_report":
                left_coumn = "order_id"
            if alias == "account_invoice_report":
                left_coumn = "move_id"
            rel_alias = query.left_join(
                alias,
                left_coumn,
                field.relation,
                field.column1,
                field.name,
                extra=extra,
                extra_params=extra_params,
            )
            return '"{}"."{}"'.format(rel_alias, field.column2)
        return super()._inherits_join_calc(alias, fname, query)
