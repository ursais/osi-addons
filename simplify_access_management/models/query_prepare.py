from odoo.tools import SQL


def search_data(self, from_model, search_model=False, condition=False, operator=False, limit=0):
    try:
        if from_model:
            self.env[from_model].exists()
            from_model_table = self.env[from_model]._table
            company_ids = tuple(self.env.company.ids)
            if condition:
                if condition[0] in self.env[from_model]._fields:
                    sql_condition = " ".join(map(str, condition))
                    params = (self.env.user.id, company_ids)
                    if from_model_table == 'access_management':
                        sql_condition = "am." + sql_condition
                        
                        query = """SELECT am.id
                                FROM access_management AS am
                                WHERE am.active = TRUE
                                AND EXISTS (
                                    SELECT 1 FROM access_management_users_rel_ah AS rel 
                                    WHERE rel.access_management_id = am.id AND rel.user_id = %s
                                )
                                AND (
                                    am.is_apply_on_without_company = TRUE
                                    OR EXISTS (
                                        SELECT 1 FROM access_management_comapnay_rel AS rel_com
                                        WHERE rel_com.access_management_id = am.id AND rel_com.company_id IN %s
                                    )
                                )
                                {operator} {sql_condition}""".format(operator=operator, sql_condition=sql_condition)
                        self._cr.execute(query, params)
                        if limit > 0:
                            row = self._cr.fetchone()
                            result = row[0] if row else False
                        else:
                            result = [x[0] for x in self._cr.fetchall()]
                        return self.env[from_model].sudo().browse(result)
                    else:
                        if search_model:
                            self.env[search_model].exists()
                            search_model_table = self.env[search_model]._table
                            sql_condition = "ft." + sql_condition
                            
                            query = """SELECT ft.id
                                    FROM {from_model_table} AS ft
                                    WHERE EXISTS (
                                        SELECT 1
                                        FROM access_management AS am
                                        JOIN access_management_users_rel_ah AS rel_user 
                                        ON am.id = rel_user.access_management_id
                                        WHERE rel_user.user_id = %s
                                        AND am.active
                                        AND am.id = ft.access_management_id
                                    )
                                    AND EXISTS (
                                        SELECT 1
                                        FROM ir_model AS im
                                        WHERE im.id = ft.model_id
                                        AND im.model = %s
                                    )
                                    AND (
                                        (SELECT am.is_apply_on_without_company
                                        FROM access_management am
                                        WHERE am.id = ft.access_management_id)
                                    OR EXISTS (
                                        SELECT 1
                                        FROM access_management_comapnay_rel AS rel_comp 
                                        WHERE rel_comp.access_management_id = ft.access_management_id
                                            AND rel_comp.company_id = %s
                                    )
                                    )
                                    {operator} {sql_condition}""".format(from_model_table=from_model_table,operator=operator, sql_condition=sql_condition)
                            self._cr.execute(query, (self.env.user.id, search_model, company_ids))
                            if limit > 0:
                                row = self._cr.fetchone()
                                result = row[0] if row else False
                            else:
                                result = [x[0] for x in self._cr.fetchall()]
                            return self.env[from_model].sudo().browse(result)   

            else:
                if from_model == 'access.management':
                    pass
                else:
                    if search_model:
                        
                        self.env[search_model].exists()
                        params = (self.env.user.id,search_model, company_ids)
                        query = """SELECT ft.id
                                    FROM {from_model_table} AS ft
                                    WHERE EXISTS (
                                        SELECT 1
                                        FROM access_management AS am
                                        JOIN access_management_users_rel_ah AS rel_user 
                                        ON am.id = rel_user.access_management_id
                                        WHERE rel_user.user_id = %s
                                        AND am.active
                                        AND am.id = ft.access_management_id
                                    )
                                    AND EXISTS (
                                        SELECT 1
                                        FROM ir_model AS im
                                        WHERE im.id = ft.model_id
                                        AND im.model = %s
                                    )
                                    AND (
                                        (SELECT am.is_apply_on_without_company
                                        FROM access_management am
                                        WHERE am.id = ft.access_management_id)
                                    OR EXISTS (
                                        SELECT 1
                                        FROM access_management_comapnay_rel AS rel_comp 
                                        WHERE rel_comp.access_management_id = ft.access_management_id
                                            AND rel_comp.company_id = %s
                                    )
                                    )"""
                        self._cr.execute(query.format(from_model_table=from_model_table), params)
                        if limit > 0:
                            result = self._cr.fetchone()[0]
                        else:
                            result = [x[0] for x in self._cr.fetchall()]
                        if result:
                            return self.env[from_model].sudo().browse(result)
                        else:
                            return False    
                    
            return False
    except Exception as e:
        raise e
            