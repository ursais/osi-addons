from odoo import models
from odoo.addons.osi_ol_decryption.template.ONLTemplate import product_templates
import logging

_logger = logging.getLogger(__name__)


class IrActionsServer(models.Model):
    _inherit = "ir.actions.server"

    def test_xyz(self):
        print("//////////test_xyz///////",product_templates)


    def script_1(self):
        _logger.info("\n\n==Clean Up and Deactivate Duplicate Attributes and Values==Script 1 is start==================")
        cr = self.env.cr

        # DROP UNIQUE CONSTRAINT  the product_attribute_value_value_product_uniq  btree (company_id, product_id, attribute_id) V13 Ref: ls_product_configurator.constraint_product_attribute_value_value_product_uniq
        alter_query = """
             ALTER TABLE product_attribute_value 
             DROP CONSTRAINT IF EXISTS product_attribute_value_value_product_uniq;
        """
        cr.execute(alter_query)

        # #Remove the Tab
        query= """UPDATE product_attribute SET name = ('{"en_US": "' || TRIM(REPLACE(name->>'en_US', '\t', ' ')) || '"}')::json WHERE name->>'en_US' ~ '\t';"""
        cr.execute(query)
        #Remove the Special Character (Double Qutoe)
        query= """UPDATE product_attribute SET name = ('{"en_US": "' || TRIM(REPLACE(name->>'en_US', '"', ' ')) || '"}')::json WHERE name->>'en_US' ~ '"';"""
        cr.execute(query)
        #TRIM Extra Space from Name
        query = """UPDATE product_attribute SET name = ('{"en_US": "' || trim(both from name->>'en_US') || '"}')::json;"""
        cr.execute(query)


        #Remove the Tab
        query= """UPDATE product_attribute_value SET name = ('{"en_US": "' || TRIM(REPLACE(name->>'en_US', '\t', ' ')) || '"}')::json WHERE name->>'en_US' ~ '\t';"""
        cr.execute(query)
        #Remove the Special Character (Double Qutoe)
        query= """UPDATE product_attribute_value SET name = ('{"en_US": "' || TRIM(REPLACE(name->>'en_US', '"', ' ')) || '"}')::json WHERE name->>'en_US' ~ '"';"""
        cr.execute(query)
        #TRIM Extra Space from Name
        query = """UPDATE product_attribute_value SET name = ('{"en_US": "' || trim(both from name->>'en_US') || '"}')::json;"""
        cr.execute(query)

        _logger.info("\n\n==================Cleanup Done==================")

        #DISTINCT Attribute Name
        distinct_attribute_ids = """SELECT DISTINCT ON (name) id, name FROM product_attribute WHERE active = true ORDER BY name, id;"""
        cr.execute(distinct_attribute_ids)
        results = cr.fetchall()
        distinct_attribute_ids = [int(result[0]) for result in results]
        _logger.info("\n\n==================DISTINCT Attributes Done==================%s",len(distinct_attribute_ids))

        #Inactive the Duplicate Records:
        query = """UPDATE product_attribute SET active = false WHERE id NOT IN %s;"""
        cr.execute(query, (tuple(distinct_attribute_ids),))
        _logger.info("\n\n==================Inactive Attributes Done==================")

        query = """UPDATE product_attribute_value
        SET active = false
        WHERE id NOT IN (
            SELECT DISTINCT ON (name) id
            FROM product_attribute_value
            WHERE active = true
            ORDER BY name,id  -- This ensures the DISTINCT ON works as expected
        );"""
        cr.execute(query)
        _logger.info("\n\n==================Inactive Duplicate Attributes Values Done==================")

        for attribute_id in distinct_attribute_ids:
            attribute  = self.env["product.attribute"].browse(attribute_id)
            # _logger.info("\n\n==================Attribute ID==================%s",attribute_id)
            pav_select_query = """SELECT DISTINCT ON (pav.name) pav.attribute_id, pav.name, pa.name, pav.id, pav.active
                                    FROM product_attribute_value AS pav
                                    LEFT JOIN product_attribute AS pa ON pav.attribute_id = pa.id
                                    WHERE pa.name->>'en_US' = %s AND pav.active=true
                                    ORDER BY pav.name, pav.id;"""
            cr.execute(pav_select_query, (attribute.name,))
            pav_results = cr.fetchall()
            for pav in pav_results:
                update_query = """UPDATE product_attribute_value SET active=true,attribute_id=%s where attribute_id = %s AND id = %s;"""
                cr.execute(update_query, (attribute.id,pav[0],pav[3]))
                # _logger.info("\n\n==================Attribute ID===pav_select_query===============%s",pav)
                
        cr.execute("DELETE FROM product_product_attribute_value_qty WHERE qty IN (0, 1);")
        cr.execute(" UPDATE product_template_attribute_line SET required = 't' WHERE required is null;")
        cr.execute("UPDATE product_template_attribute_value SET is_qty_required = false, default_qty = NULL, maximum_qty = NULL WHERE ptav_active=true and default_qty in (0,1) and maximum_qty in (0,1);")
        _logger.info("\n\n==================Script 1 is end==================")

    def script_2(self):
        _logger.info("\n\n==Merge Unique Attribute Values into a Single Attribute==Script 2 is start==================")
        cr = self.env.cr
        cr.execute(
            "UPDATE product_template_attribute_line SET used_in_sale_description = TRUE"
        )
        #=========================================ProductTemplateAttributeLine===================================================
        ProductTemplateAttributeLine = self.env["product.template.attribute.line"]
        templateAttributteLine = ProductTemplateAttributeLine.search([])
        product_attribute_obj = self.env["product.attribute"]
        # attribute_dict = {attribute.name: attribute.id for attribute in product_attribute_obj.search([("active", "=", True)])}
        cr.execute("""
            SELECT name, id 
            FROM product_attribute 
            WHERE active = TRUE;
        """)
        attribute_dict = {name.get('en_US'): attr_id for name, attr_id in cr.fetchall()}
        # lines_to_update = templateAttributteLine.filtered(lambda line: line.product_tmpl_id.active and not line.attribute_id.active)
        lines_to_update = ProductTemplateAttributeLine.search([
            ("product_tmpl_id.active", "=", True),
            ("attribute_id.active", "=", False)
        ])
        update_queries = []
        for line in lines_to_update:
            # Check if the attribute has an active match
            if line.attribute_id.name in attribute_dict:
                active_attribute_id = attribute_dict[line.attribute_id.name]
                # Prepare the update query
                update_queries.append((active_attribute_id, line.id, line.attribute_id.id))
        if update_queries:
            update_query = """UPDATE product_template_attribute_line 
                              SET attribute_id = %s 
                              WHERE id = %s AND attribute_id = %s;"""
            cr.executemany(update_query, update_queries)
            cr.commit()
        _logger.info("\n\n===ProductTemplateAttributeLine Done===")


        #============================================ProductTemplateAttributeValue================================================
        ProductTemplateAttributeValue = self.env["product.template.attribute.value"]
        _logger.info("\n\n===ProductTemplateAttributeValue Start===")
        # active_attribute_dict = {attribute.name: attribute.id for attribute in self.env["product.attribute"].search([("active", "=", True)])}
        active_attribute_dict = attribute_dict
        update_queries = []
        attributes_to_recompute = set()
        select_query = """select id from product_template_attribute_value where ptav_active='t';"""
        cr.execute(select_query)
        ptav_ids = cr.fetchall()
        templateAttributteValue = [ptav[0] for ptav in ptav_ids]
        # templateAttributteValue = ProductTemplateAttributeValue.search([("ptav_active", "=", True)],limit=10)

        for ptav_line in templateAttributteValue:
            line = ProductTemplateAttributeValue.browse(ptav_line)
            if not line.attribute_id.active and line.attribute_id.name in active_attribute_dict:
                active_attribute_id = active_attribute_dict[line.attribute_id.name]
                update_queries.append((active_attribute_id, line.id, line.attribute_id.id))
                # Add the attribute to the recompute set (no duplicates)
                attributes_to_recompute.add(active_attribute_id)

        if update_queries:
            update_query = """UPDATE product_template_attribute_value 
                              SET attribute_id = %s 
                              WHERE id = %s AND attribute_id = %s;"""
            cr.executemany(update_query, update_queries)
            cr.commit()

              

        _logger.info("\n\n===ProductTemplateAttributeValue Done===%s",len(templateAttributteValue))

        #Template Value_ids M2M Relation name: product_attribute_value_product_template_attribute_line_rel
        template_attribute_line_rel_query = """SELECT product_attribute_value_id FROM product_attribute_value_product_template_attribute_line_rel;"""
        cr.execute(template_attribute_line_rel_query)
        line_rel_ids = cr.fetchall()


        # templateAttributeValue = ProductTemplateAttributeValue.search([("ptav_active", "=", True)])
        # templateAttributeValue = ProductTemplateAttributeValue.browse(templateAttributteValue)
        _logger.info("\n\n===Recompute for unique attributes===")  
        active_attributes = product_attribute_obj.browse(attributes_to_recompute)
        active_attributes._compute_products()
        query = """SELECT attribute_line_id from product_template_attribute_value where id in %s;"""
        cr.execute(query,(tuple(templateAttributteValue),))
        value_line_ids = [row[0] for row in cr.fetchall()]

        # attribute_line_ids = templateAttributeValue.mapped("attribute_line_id").ids
        query = """SELECT id from product_template_attribute_line where id in %s;"""
        cr.execute(query,(tuple(value_line_ids),))
        attribute_line_ids = [row[0] for row in cr.fetchall()]
        
        line_rel_ids =[]
        if attribute_line_ids:  # Only run the query if we have some ids to search for
            template_attribute_line_rel_query = """
                SELECT product_attribute_value_id 
                FROM product_attribute_value_product_template_attribute_line_rel 
                WHERE product_template_attribute_line_id in %s;
            """
            cr.execute(template_attribute_line_rel_query, (tuple(attribute_line_ids),))
            line_rel_ids = cr.fetchall()
        
        cr.execute("""
            SELECT id FROM product_config_step_line
            WHERE config_step_id IS NOT NULL
            AND NOT EXISTS (
                SELECT 1 FROM config_step_line_attr_id_rel rel
                WHERE rel.product_config_step_line_id = product_config_step_line.id
            )
        """)
        step_ids_to_delete = [row[0] for row in cr.fetchall()]
        if step_ids_to_delete:
            cr.execute("""
                DELETE FROM product_config_step_line
                WHERE id = ANY(%s)
            """, (step_ids_to_delete,))
            cr.commit()
        _logger.info("\n\n===product_attribute_value_product_template_attribute_line_rel=%s",len(line_rel_ids))
        _logger.info("\n\n==================Script 2 is End==================")
    
    def new_script3(self,template):
        cr = self.env.cr
        def get_ptavs(attribute_id,product_attribute_value_id,p_id,ptav_active=False):
            domain = [
                ("attribute_id", "=",attribute_id),
                ("product_attribute_value_id", "=", product_attribute_value_id),
                ("id", "=", p_id)
            ]
            if ptav_active:
                domain += [("ptav_active", "=", True)]
            ptav = self.env["product.template.attribute.value"].search(domain)
            return ptav

        def update_template_attribute_line_rel(line,active_value_id,old_product_attribute_value_id):
            delete_query = """
                DELETE FROM product_attribute_value_product_template_attribute_line_rel 
                WHERE product_template_attribute_line_id = %s 
                AND (product_attribute_value_id = %s OR product_attribute_value_id = %s);
            """

            insert_query = """
                INSERT INTO product_attribute_value_product_template_attribute_line_rel 
                (product_template_attribute_line_id, product_attribute_value_id) 
                VALUES (%s, %s);
            """

            cr.execute(delete_query, (line.id, active_value_id.id, old_product_attribute_value_id.id))
            cr.commit()
            cr.execute(insert_query, (line.id, active_value_id.id))
            cr.commit()

        
        pav_obj = self.env["product.attribute.value"]
        line_ids = template.attribute_line_ids.ids
        # if not line_ids:
        #     continue

        for line in template.attribute_line_ids:
            all_inactive = all(not ptav.ptav_active for ptav in line.product_template_value_ids)
            line_values = line.value_ids
            if all_inactive:
                name_list = []
                value_ids = line.product_template_value_ids
                for value in value_ids:
                    if value.product_attribute_value_id.name not in name_list:
                        name_list.append(value.product_attribute_value_id.name)
                    else:
                        value.write({"ptav_active":True})
            value_ids = line.product_template_value_ids.filtered(lambda v: v.ptav_active)
            grouped_values = {}
            # Group values based on their names
            name_list = []
            for value in value_ids:
                if len(value_ids) > 1:
                    grouped_values.setdefault(value.name, []).append(value)
                else:
                    grouped_values.setdefault(value.name, []).append(value)
            for name, duplicates in grouped_values.items():
                if len(duplicates) > 1:
                    # Sort duplicates and determine the one to keep
                    duplicates_sorted = sorted(duplicates, key=lambda v: v.id)
                    for_update = duplicates_sorted[0]
                    for_remove = duplicates_sorted[1:]
                    for_remove_list = [line.id for line in for_remove]

                    if for_update.ptav_product_variant_ids:
                        # Update product_variant_combination for the removed duplicates
                        cr.execute("""
                            UPDATE product_variant_combination
                            SET product_template_attribute_value_id = %s
                            WHERE product_template_attribute_value_id IN %s;
                        """, (for_update.id, tuple(for_remove_list)))
                        cr.commit()
                    cr.execute("""
                        UPDATE product_template_attribute_value
                        SET ptav_active = 'f'
                        WHERE id IN %s;
                    """, (tuple(for_remove_list),))
                    cr.commit()
                    # Handle the update of the active value
                    active_value_id = for_update.product_attribute_value_id
                    old_product_attribute_value_id = active_value_id
                    if not active_value_id.active:
                        active_value_id = pav_obj.search([
                            ("name", "=", name),
                            ("attribute_id", "=", for_update.attribute_id.id)
                        ], limit=1)
                        if not active_value_id:
                            update_query = """UPDATE product_attribute_value SET active = TRUE,attribute_id = %s WHERE id =%s;"""
                            cr.execute(update_query,(for_update.attribute_id.id,old_product_attribute_value_id.id))
                            cr.commit()

                    active_ptav = get_ptavs(active_value_id.attribute_id.id, active_value_id.id, duplicates[0].id)
                    active_ptav2 = None
                    if not active_ptav:
                        active_ptav2 = get_ptavs(old_product_attribute_value_id.attribute_id.id, old_product_attribute_value_id.id, duplicates[0].id,ptav_active=True)
                    if active_ptav:
                        # If active_ptav exists and is inactive, activate it
                        if not active_ptav.ptav_active:
                            active_ptav.write({"ptav_active": True})
                        elif active_ptav.ptav_active and active_ptav.product_attribute_value_id.id != active_value_id.id:
                            cr.execute("""
                                UPDATE product_template_attribute_value
                                SET product_attribute_value_id = %s
                                WHERE id = %s AND attribute_id = %s AND ptav_active = true;
                            """, (active_value_id.id, duplicates[0].id, active_value_id.attribute_id.id))
                            cr.commit()
                    elif active_ptav2:
                        active_ptav2.write({"ptav_active": False})

                    if active_value_id and old_product_attribute_value_id:
                        update_template_attribute_line_rel(line,active_value_id,old_product_attribute_value_id)
                elif len(duplicates) == 1:
                    old_product_attribute_value_id = duplicates[0].product_attribute_value_id
                    active_value_id = old_product_attribute_value_id
                    if not old_product_attribute_value_id.active:
                        active_value_id = pav_obj.search([
                            ("name", "=", name),
                            ("attribute_id", "=", duplicates[0].attribute_id.id)
                        ], limit=1)
                        if not active_value_id:
                            update_query = """UPDATE product_attribute_value SET active = TRUE,attribute_id = %s WHERE id =%s;"""
                            cr.execute(update_query,( duplicates[0].attribute_id.id,old_product_attribute_value_id.id))
                            cr.commit()
                    active_ptav = get_ptavs(active_value_id.attribute_id.id, active_value_id.id, duplicates[0].id)
                    active_ptav2 = None
                    if not active_ptav:
                        active_ptav2 = get_ptavs(old_product_attribute_value_id.attribute_id.id, old_product_attribute_value_id.id, duplicates[0].id,ptav_active=True)
                    if active_ptav:
                        if not active_ptav.ptav_active:
                            active_ptav.write({"ptav_active":True})
                        elif active_ptav.ptav_active and active_ptav.product_attribute_value_id.id != active_value_id.id:
                            cr.execute("""
                                UPDATE product_template_attribute_value
                                SET product_attribute_value_id = %s
                                WHERE id = %s AND attribute_id = %s AND ptav_active = true;
                            """, (active_value_id.id, duplicates[0].id, active_value_id.attribute_id.id))
                            cr.commit()
                    elif active_ptav2:
                        active_ptav2.write({"ptav_active": False})
                    if active_value_id and old_product_attribute_value_id:
                        update_template_attribute_line_rel(line,active_value_id,old_product_attribute_value_id)

            if line_values:
                # Filter out 'None' and non-'None' values
                value_with_none = line_values.filtered(lambda ptav: ptav.name == 'None')
                value_with_non_none = line_values.filtered(lambda ptav: ptav.name != 'None')

                # Determine the default value ID safely
                default_val = None
                if value_with_none:
                    default_val = value_with_none[0].id  # Use the first 'None' value if present
                elif value_with_non_none:
                    default_val = value_with_non_none[0].id  # Otherwise, use the first non-'None' value

                # Proceed with the update only if a valid default value is found
                if default_val is not None:
                    cr.execute("""
                        UPDATE product_template_attribute_line
                        SET default_val = %s
                        WHERE id = %s;
                    """, (default_val, line.id))
                    cr.commit()  # Commit the transaction after the update
   
    def script_3(self):
        cr = self.env.cr
        batch_size = 100
        templates = self.env['product.template'].search([("has_configurable_attributes", "=", True)])
        total = len(templates)
        _logger.info("Total products to process: %s", total)
        counter = 0
        for offset in range(0, total, batch_size):
            batch = templates[offset:offset + batch_size]
            _logger.info("Processing batch: Offset=%s, Size=%s", offset, len(batch))
            def get_ptavs(attribute_id,product_attribute_value_id,p_id,ptav_active=False):
                    domain = [
                        ("attribute_id", "=",attribute_id),
                        ("product_attribute_value_id", "=", product_attribute_value_id),
                        ("id", "=", p_id)
                    ]
                    if ptav_active:
                        domain += [("ptav_active", "=", True)]
                    ptav = self.env["product.template.attribute.value"].search(domain)
                    return ptav

            def update_template_attribute_line_rel(line,active_value_id,old_product_attribute_value_id):
                delete_query = """
                    DELETE FROM product_attribute_value_product_template_attribute_line_rel 
                    WHERE product_template_attribute_line_id = %s 
                    AND (product_attribute_value_id = %s OR product_attribute_value_id = %s);
                """

                insert_query = """
                    INSERT INTO product_attribute_value_product_template_attribute_line_rel 
                    (product_template_attribute_line_id, product_attribute_value_id) 
                    VALUES (%s, %s);
                """

                cr.execute(delete_query, (line.id, active_value_id.id, old_product_attribute_value_id.id))
                cr.commit()
                cr.execute(insert_query, (line.id, active_value_id.id))
                cr.commit()
            for template in batch:
                _logger.info("→ Processing Product Template: %s (ID: %s)", template.name, template.id)
                counter += 1
                pav_obj = self.env["product.attribute.value"]
                line_ids = template.attribute_line_ids
                for line in line_ids:
                    all_inactive = all(not ptav.ptav_active for ptav in line.product_template_value_ids)
                    line_values = line.value_ids
                    if all_inactive:
                        name_list = []
                        value_ids = line.product_template_value_ids
                        for value in value_ids:
                            if value.product_attribute_value_id.name not in name_list:
                                name_list.append(value.product_attribute_value_id.name)
                            else:
                                value.write({"ptav_active":True})
                    value_ids = line.product_template_value_ids.filtered(lambda v: v.ptav_active)
                    grouped_values = {}
                    # Group values based on their names
                    name_list = []
                    for value in value_ids:
                        if len(value_ids) > 1:
                            grouped_values.setdefault(value.name, []).append(value)
                        else:
                            grouped_values.setdefault(value.name, []).append(value)
                    for name, duplicates in grouped_values.items():
                        if len(duplicates) > 1:
                            # Sort duplicates and determine the one to keep
                            duplicates_sorted = sorted(duplicates, key=lambda v: v.id)
                            for_update = duplicates_sorted[0]
                            for_remove = duplicates_sorted[1:]
                            for_remove_list = [line.id for line in for_remove]

                            if for_update.ptav_product_variant_ids:
                                # Update product_variant_combination for the removed duplicates
                                cr.execute("""
                                    UPDATE product_variant_combination
                                    SET product_template_attribute_value_id = %s
                                    WHERE product_template_attribute_value_id IN %s;
                                """, (for_update.id, tuple(for_remove_list)))
                                cr.commit()
                            cr.execute("""
                                UPDATE product_template_attribute_value
                                SET ptav_active = 'f'
                                WHERE id IN %s;
                            """, (tuple(for_remove_list),))
                            cr.commit()
                            # Handle the update of the active value
                            active_value_id = for_update.product_attribute_value_id
                            old_product_attribute_value_id = active_value_id
                            if not active_value_id.active:
                                active_value_id = pav_obj.search([
                                    ("name", "=", name),
                                    ("attribute_id", "=", for_update.attribute_id.id)
                                ], limit=1)
                                if not active_value_id:
                                    update_query = """UPDATE product_attribute_value SET active = TRUE,attribute_id = %s WHERE id =%s;"""
                                    cr.execute(update_query,(for_update.attribute_id.id,old_product_attribute_value_id.id))
                                    cr.commit()

                            active_ptav = get_ptavs(active_value_id.attribute_id.id, active_value_id.id, duplicates[0].id)
                            active_ptav2 = None
                            if not active_ptav:
                                active_ptav2 = get_ptavs(old_product_attribute_value_id.attribute_id.id, old_product_attribute_value_id.id, duplicates[0].id,ptav_active=True)
                            if active_ptav:
                                # If active_ptav exists and is inactive, activate it
                                if not active_ptav.ptav_active:
                                    active_ptav.write({"ptav_active": True})
                                elif active_ptav.ptav_active and active_ptav.product_attribute_value_id.id != active_value_id.id:
                                    cr.execute("""
                                        UPDATE product_template_attribute_value
                                        SET product_attribute_value_id = %s
                                        WHERE id = %s AND attribute_id = %s AND ptav_active = true;
                                    """, (active_value_id.id, duplicates[0].id, active_value_id.attribute_id.id))
                                    cr.commit()
                            elif active_ptav2:
                                active_ptav2.write({"ptav_active": False})

                            if active_value_id and old_product_attribute_value_id:
                                update_template_attribute_line_rel(line,active_value_id,old_product_attribute_value_id)
                        elif len(duplicates) == 1:
                            old_product_attribute_value_id = duplicates[0].product_attribute_value_id
                            active_value_id = old_product_attribute_value_id
                            if not old_product_attribute_value_id.active:
                                active_value_id = pav_obj.search([
                                    ("name", "=", name),
                                    ("attribute_id", "=", duplicates[0].attribute_id.id)
                                ], limit=1)
                                if not active_value_id:
                                    update_query = """UPDATE product_attribute_value SET active = TRUE,attribute_id = %s WHERE id =%s;"""
                                    cr.execute(update_query,( duplicates[0].attribute_id.id,old_product_attribute_value_id.id))
                                    cr.commit()
                            active_ptav = get_ptavs(active_value_id.attribute_id.id, active_value_id.id, duplicates[0].id)
                            active_ptav2 = None
                            if not active_ptav:
                                active_ptav2 = get_ptavs(old_product_attribute_value_id.attribute_id.id, old_product_attribute_value_id.id, duplicates[0].id,ptav_active=True)
                            if active_ptav:
                                if not active_ptav.ptav_active:
                                    active_ptav.write({"ptav_active":True})
                                elif active_ptav.ptav_active and active_ptav.product_attribute_value_id.id != active_value_id.id:
                                    cr.execute("""
                                        UPDATE product_template_attribute_value
                                        SET product_attribute_value_id = %s
                                        WHERE id = %s AND attribute_id = %s AND ptav_active = true;
                                    """, (active_value_id.id, duplicates[0].id, active_value_id.attribute_id.id))
                                    cr.commit()
                            elif active_ptav2:
                                active_ptav2.write({"ptav_active": False})
                            if active_value_id and old_product_attribute_value_id:
                                update_template_attribute_line_rel(line,active_value_id,old_product_attribute_value_id)

                    if line_values:
                        # Filter out 'None' and non-'None' values
                        value_with_none = line_values.filtered(lambda ptav: ptav.name == 'None')
                        value_with_non_none = line_values.filtered(lambda ptav: ptav.name != 'None')

                        # Determine the default value ID safely
                        default_val = None
                        if value_with_none:
                            default_val = value_with_none[0].id  # Use the first 'None' value if present
                        elif value_with_non_none:
                            default_val = value_with_non_none[0].id  # Otherwise, use the first non-'None' value

                        # Proceed with the update only if a valid default value is found
                        if default_val is not None:
                            cr.execute("""
                                UPDATE product_template_attribute_line
                                SET default_val = %s
                                WHERE id = %s;
                            """, (default_val, line.id))
                            cr.commit()  # Commit the transaction after the update
                        _logger.info("\n✅ Script 3 completed,Processed count: %s", counter)

    def new_script4(self,template):
        cr = self.env.cr
        active_attribute_line_ids = template.mapped("attribute_line_ids").filtered("active")
        pav_obj = self.env["product.attribute.value"]
        for attribute_line_id in active_attribute_line_ids:
            if attribute_line_id.value_ids and (not attribute_line_id.default_val or not attribute_line_id.default_val.active):
                default_val = attribute_line_id.value_ids[0].id
                cr.execute("""
                    UPDATE product_template_attribute_line
                    SET default_val = %s
                    WHERE id = %s;
                """, (default_val, attribute_line_id.id))
                cr.commit()
            if attribute_line_id.attribute_id.active:
                values_to_fix = attribute_line_id.value_ids.filtered(
                    lambda val: val.active and val.attribute_id.id != attribute_line_id.attribute_id.id
                )
                existing_names = attribute_line_id.attribute_id.value_ids.mapped("name")
                for val in values_to_fix:
                    # Skip if name already exists under correct attribute
                    if val.name in existing_names:
                        continue
                    # # Fetch the active attribute value safely
                    active_value = pav_obj.search([
                        ("name", "=", val.name),
                        ("active", "=", True),
                        ("attribute_id", "=", val.attribute_id.id)
                    ], limit=1)
                    if active_value and not active_value.attribute_id.active:
                        cr.execute("""
                            UPDATE product_attribute_value
                            SET active = TRUE, attribute_id = %s
                            WHERE id = %s;
                        """, (attribute_line_id.attribute_id.id, val.id))
                cr.commit()
                active_ptavs = attribute_line_id.product_template_value_ids.filtered("ptav_active")
                for ptav in active_ptavs:
                    if ptav.attribute_id.id != attribute_line_id.attribute_id.id:
                        cr.execute("""
                            UPDATE product_template_attribute_value
                            SET attribute_id = %s
                            WHERE id = %s AND ptav_active = true;
                        """, (attribute_line_id.attribute_id.id, ptav.id))
                        cr.commit()
                    ptav_name = ptav.product_attribute_value_id.name
                    product_tmpl_id = ptav.product_tmpl_id.id
                    ptav_list = ptav.attribute_line_id.product_template_value_ids

                    # PTAV with inactive value but active PTAV
                    inactive_value_active_ptav = ptav.filtered(
                        lambda l: (
                            l.name == ptav_name and
                            not l.product_attribute_value_id.active and
                            l.ptav_active and
                            l.product_tmpl_id.id == product_tmpl_id
                        )
                    )

                    # PTAV with active value but inactive PTAV
                    active_value_inactive_ptav = ptav.filtered(
                        lambda l: (
                            l.name == ptav_name and
                            l.product_attribute_value_id.active and
                            not l.ptav_active and
                            l.product_tmpl_id.id == product_tmpl_id
                        )
                    )
                    fallback_value = attribute_line_id.value_ids.filtered(lambda v: v.name == ptav_name)
                    if (
                        not inactive_value_active_ptav and 
                        not active_value_inactive_ptav and 
                        not ptav.product_attribute_value_id.active and 
                        fallback_value
                    ):
                        cr.execute("""
                            UPDATE product_template_attribute_value
                            SET product_attribute_value_id = %s
                            WHERE id = %s AND ptav_active = true;
                        """, (fallback_value.id, ptav.id))
                        cr.commit()
                    elif inactive_value_active_ptav and active_value_inactive_ptav:
                        _logger.info("[Fix: Disable Inactive Value PTAV]")
                        inactive_value_active_ptav.ptav_active = False

                    elif not inactive_value_active_ptav and active_value_inactive_ptav:
                        _logger.info("[Fix: Enable Correct Active Value PTAV]")
                        active_value_inactive_ptav.ptav_active = True

                    elif (
                        inactive_value_active_ptav and 
                        not active_value_inactive_ptav and 
                        ptav.product_attribute_value_id.active
                    ):
                        _logger.info(
                            "[Fix: Disable PTAV with Wrong Inactive Value] PTAV ID %s for name %s",
                            ptav.id, ptav_name
                        )
                        inactive_value_active_ptav.ptav_active = False

                    
                    if not ptav.product_attribute_value_id.active:
                        active_value_id = fallback_value
                        alterntive_ptav = self.env["product.template.attribute.value"].search([("product_attribute_value_id","=",active_value_id.id), ("product_tmpl_id","=",template.id),("ptav_active","=",False)])
                        alterntive_ptav2 = self.env["product.template.attribute.value"].search([("name","=",ptav.name), ("product_tmpl_id","=",template.id),("ptav_active","=",True),("attribute_line_id","=",attribute_line_id.id)])
                        if alterntive_ptav:
                            alterntive_ptav.write({"ptav_active":True})
                            ptav.write({"ptav_active":False})
                            cr.commit()
                        elif alterntive_ptav2 and len(alterntive_ptav2)>1:
                            active_ones = alterntive_ptav2.filtered(lambda l :l.product_attribute_value_id.id == active_value_id.id)
                            if not active_ones:
                                min_id = min(alterntive_ptav2.ids)
                                max_id = max(alterntive_ptav2.ids)
                                cr.execute("""
                                        UPDATE product_template_attribute_value
                                        SET product_attribute_value_id = %s
                                        WHERE id = %s AND ptav_active = true;
                                    """, (active_value_id.id,min_id))
                                cr.commit()

                                cr.execute("""
                                        UPDATE product_template_attribute_value
                                        SET ptav_active = 'f'
                                        WHERE id in %s AND ptav_active = true;
                                    """, (tuple(max_id)))
                                cr.commit()
                            else:
                                new_ids = alterntive_ptav2 - active_ones
                                if new_ids:
                                    cr.execute("""
                                        UPDATE product_template_attribute_value
                                        SET ptav_active = FALSE
                                        WHERE id = ANY(%s) AND ptav_active = TRUE;
                                    """, (list(new_ids.ids),)) 
                                    cr.commit()
                        else:
                            cr.execute("""
                                    UPDATE product_template_attribute_value
                                    SET product_attribute_value_id = %s
                                    WHERE id = %s AND ptav_active = true;
                                """, (active_value_id.id,ptav.id))
                            cr.commit()

                    if ptav.attribute_line_id.is_qty_required:
                        query = """
                            UPDATE attribute_value_qty
                            SET product_attribute_id = %s
                            WHERE id = %s;
                        """
                        product_attribute_value_id = ptav.product_attribute_value_id.id
                        attribute_id = ptav.attribute_id.id
                        for qty_val in ptav.attribute_value_qty_ids:
                            if qty_val.product_attribute_id.id != ptav.attribute_id.id:
                                cr.execute(query,(attribute_id,qty_val.id))
                                cr.commit()
                            if qty_val.product_attribute_value_id.id !=  ptav.product_attribute_value_id.id:
                                cr.execute("""
                                    UPDATE attribute_value_qty
                                    SET product_attribute_value_id = %s
                                    WHERE id = %s;
                                """, (product_attribute_value_id,qty_val.id))
                
                values_ids = attribute_line_id.value_ids
                value_ids_set = set(values_ids.ids)
                ptav_value_ids_set = set(active_ptavs.mapped("product_attribute_value_id").ids)
                not_common_ids = list(value_ids_set.symmetric_difference(ptav_value_ids_set))
                if not_common_ids:
                    query = """
                        DELETE FROM product_attribute_value_product_template_attribute_line_rel
                        WHERE product_template_attribute_line_id = %s
                        AND product_attribute_value_id = ANY(%s)
                    """
                    self.env.cr.execute(query, (attribute_line_id.id, not_common_ids))
                    self.env.cr.commit()
        self.new_script3(template)

    def script_4(self):
        cr = self.env.cr
        batch_size = 100
        templates = self.env['product.template'].search([("has_configurable_attributes", "=", True)])
        total = len(templates)
        _logger.info("Total products to process: %s", total)
        counter = 0
        for offset in range(0, total, batch_size):
            batch = templates[offset:offset + batch_size]
            _logger.info("Processing batch: Offset=%s, Size=%s", offset, len(batch))
            for template in batch:
                _logger.info("→ Processing Product Template: %s (ID: %s)", template.name, template.id)
                counter += 1
                active_attribute_line_ids = template.mapped("attribute_line_ids").filtered("active")
                pav_obj = self.env["product.attribute.value"]
                for attribute_line_id in active_attribute_line_ids:
                    if attribute_line_id.value_ids and (not attribute_line_id.default_val or not attribute_line_id.default_val.active):
                        default_val = attribute_line_id.value_ids[0].id
                        cr.execute("""
                            UPDATE product_template_attribute_line
                            SET default_val = %s
                            WHERE id = %s;
                        """, (default_val, attribute_line_id.id))
                        cr.commit()
                    if attribute_line_id.attribute_id.active:
                        values_to_fix = attribute_line_id.value_ids.filtered(
                            lambda val: val.active and val.attribute_id.id != attribute_line_id.attribute_id.id
                        )
                        existing_names = attribute_line_id.attribute_id.value_ids.mapped("name")
                        for val in values_to_fix:
                            # Skip if name already exists under correct attribute
                            if val.name in existing_names:
                                continue
                            # # Fetch the active attribute value safely
                            active_value = pav_obj.search([
                                ("name", "=", val.name),
                                ("active", "=", True),
                                ("attribute_id", "=", val.attribute_id.id)
                            ], limit=1)
                            if active_value and not active_value.attribute_id.active:
                                cr.execute("""
                                    UPDATE product_attribute_value
                                    SET active = TRUE, attribute_id = %s
                                    WHERE id = %s;
                                """, (attribute_line_id.attribute_id.id, val.id))
                        cr.commit()
                        active_ptavs = attribute_line_id.product_template_value_ids.filtered("ptav_active")
                        for ptav in active_ptavs:
                            if ptav.attribute_id.id != attribute_line_id.attribute_id.id:
                                cr.execute("""
                                    UPDATE product_template_attribute_value
                                    SET attribute_id = %s
                                    WHERE id = %s AND ptav_active = true;
                                """, (attribute_line_id.attribute_id.id, ptav.id))
                                cr.commit()
                            ptav_name = ptav.product_attribute_value_id.name
                            product_tmpl_id = ptav.product_tmpl_id.id
                            ptav_list = ptav.attribute_line_id.product_template_value_ids

                            # PTAV with inactive value but active PTAV
                            inactive_value_active_ptav = ptav.filtered(
                                lambda l: (
                                    l.name == ptav_name and
                                    not l.product_attribute_value_id.active and
                                    l.ptav_active and
                                    l.product_tmpl_id.id == product_tmpl_id
                                )
                            )

                            # PTAV with active value but inactive PTAV
                            active_value_inactive_ptav = ptav.filtered(
                                lambda l: (
                                    l.name == ptav_name and
                                    l.product_attribute_value_id.active and
                                    not l.ptav_active and
                                    l.product_tmpl_id.id == product_tmpl_id
                                )
                            )
                            fallback_value = attribute_line_id.value_ids.filtered(lambda v: v.name == ptav_name)
                            if (
                                not inactive_value_active_ptav and 
                                not active_value_inactive_ptav and 
                                not ptav.product_attribute_value_id.active and 
                                fallback_value
                            ):
                                cr.execute("""
                                    UPDATE product_template_attribute_value
                                    SET product_attribute_value_id = %s
                                    WHERE id = %s AND ptav_active = true;
                                """, (fallback_value.id, ptav.id))
                                cr.commit()
                            elif inactive_value_active_ptav and active_value_inactive_ptav:
                                _logger.info("[Fix: Disable Inactive Value PTAV]")
                                inactive_value_active_ptav.ptav_active = False

                            elif not inactive_value_active_ptav and active_value_inactive_ptav:
                                _logger.info("[Fix: Enable Correct Active Value PTAV]")
                                active_value_inactive_ptav.ptav_active = True

                            elif (
                                inactive_value_active_ptav and 
                                not active_value_inactive_ptav and 
                                ptav.product_attribute_value_id.active
                            ):
                                _logger.info(
                                    "[Fix: Disable PTAV with Wrong Inactive Value] PTAV ID %s for name %s",
                                    ptav.id, ptav_name
                                )
                                inactive_value_active_ptav.ptav_active = False

                            
                            if not ptav.product_attribute_value_id.active:
                                active_value_id = fallback_value
                                alterntive_ptav = self.env["product.template.attribute.value"].search([("product_attribute_value_id","=",active_value_id.id), ("product_tmpl_id","=",template.id),("ptav_active","=",False)])
                                alterntive_ptav2 = self.env["product.template.attribute.value"].search([("name","=",ptav.name), ("product_tmpl_id","=",template.id),("ptav_active","=",True),("attribute_line_id","=",attribute_line_id.id)])
                                if alterntive_ptav:
                                    alterntive_ptav.write({"ptav_active":True})
                                    ptav.write({"ptav_active":False})
                                    cr.commit()
                                elif alterntive_ptav2 and len(alterntive_ptav2)>1:
                                    active_ones = alterntive_ptav2.filtered(lambda l :l.product_attribute_value_id.id == active_value_id.id)
                                    if not active_ones:
                                        min_id = min(alterntive_ptav2.ids)
                                        max_id = max(alterntive_ptav2.ids)
                                        cr.execute("""
                                                UPDATE product_template_attribute_value
                                                SET product_attribute_value_id = %s
                                                WHERE id = %s AND ptav_active = true;
                                            """, (active_value_id.id,min_id))
                                        cr.commit()

                                        cr.execute("""
                                                UPDATE product_template_attribute_value
                                                SET ptav_active = 'f'
                                                WHERE id in %s AND ptav_active = true;
                                            """, (tuple(max_id)))
                                        cr.commit()
                                    else:
                                        new_ids = alterntive_ptav2 - active_ones
                                        if new_ids:
                                            cr.execute("""
                                                UPDATE product_template_attribute_value
                                                SET ptav_active = FALSE
                                                WHERE id = ANY(%s) AND ptav_active = TRUE;
                                            """, (list(new_ids.ids),)) 
                                            cr.commit()
                                else:
                                    cr.execute("""
                                            UPDATE product_template_attribute_value
                                            SET product_attribute_value_id = %s
                                            WHERE id = %s AND ptav_active = true;
                                        """, (active_value_id.id,ptav.id))
                                    cr.commit()

                            if ptav.attribute_line_id.is_qty_required:
                                query = """
                                    UPDATE attribute_value_qty
                                    SET product_attribute_id = %s
                                    WHERE id = %s;
                                """
                                product_attribute_value_id = ptav.product_attribute_value_id.id
                                attribute_id = ptav.attribute_id.id
                                for qty_val in ptav.attribute_value_qty_ids:
                                    if qty_val.product_attribute_id.id != ptav.attribute_id.id:
                                        cr.execute(query,(attribute_id,qty_val.id))
                                        cr.commit()
                                    if qty_val.product_attribute_value_id.id !=  ptav.product_attribute_value_id.id:
                                        cr.execute("""
                                            UPDATE attribute_value_qty
                                            SET product_attribute_value_id = %s
                                            WHERE id = %s;
                                        """, (product_attribute_value_id,qty_val.id))
                        
                        values_ids = attribute_line_id.value_ids
                        value_ids_set = set(values_ids.ids)
                        ptav_value_ids_set = set(active_ptavs.mapped("product_attribute_value_id").ids)
                        not_common_ids = list(value_ids_set.symmetric_difference(ptav_value_ids_set))
                        if not_common_ids:
                            query = """
                                DELETE FROM product_attribute_value_product_template_attribute_line_rel
                                WHERE product_template_attribute_line_id = %s
                                AND product_attribute_value_id = ANY(%s)
                            """
                            self.env.cr.execute(query, (attribute_line_id.id, not_common_ids))
                            self.env.cr.commit()
                self.new_script3(template)
                _logger.info("\n✅ Script 4 completed,Processed count: %s", counter)

    def new_script5(self,template):
        attribute_line_ids = template.mapped("attribute_line_ids")
        cr = self.env.cr
        update_query = "UPDATE product_template_attribute_line SET is_qty_required = 't' WHERE id = %s;"
        avq_obj = self.env["attribute.value.qty"]
        pav = self.env["product.attribute.value"]
        qty_vals_to_create = []
        for attribute_line_id in attribute_line_ids:
            v13_data_select = "select id,attribute_id ,attribute_line_id,product_attribute_value_id,default_qty,maximum_qty  from temp_product_template_attribute_value_V13_VP where product_tmpl_id = %s and attribute_line_id = %s and ptav_active = 't' and default_qty >=1 and maximum_qty >1;" 
            cr.execute(v13_data_select, (template.id,attribute_line_id.id),)
            v13_datas = cr.fetchall()
            if attribute_line_id.value_ids and (not attribute_line_id.default_val or not attribute_line_id.default_val.active):
                cr.execute("""
                    UPDATE product_template_attribute_line
                    SET default_val = %s
                    WHERE id = %s;
                """, (attribute_line_id.value_ids[0].id, attribute_line_id.id))
                cr.commit()
            if v13_datas:
                for v13_data in v13_datas:
                    v13_value_id = v13_data[3]
                    v17_ptav = attribute_line_id.product_template_value_ids.filtered(
                        lambda l: l.product_attribute_value_id.id == v13_value_id and l.ptav_active
                    )
                    if not attribute_line_id.is_qty_required:
                        cr.execute(update_query, (attribute_line_id.id,))
                    if v13_value_id in attribute_line_id.value_ids.ids:
                        default_qty = v17_ptav.default_qty
                        maximum_qty = v17_ptav.maximum_qty
                        existing_qty = set(v17_ptav.attribute_value_qty_ids.mapped("qty"))
                        expected_qty = set(range(default_qty, maximum_qty + 1))

                        missing_qty = expected_qty - existing_qty
                        for qty in missing_qty:
                            qty_vals_to_create.append({
                                "name": f"{v17_ptav.product_attribute_value_id.display_name} - Qty {qty}",
                                "product_tmpl_id": v17_ptav.product_tmpl_id.id,
                                "product_attribute_id": v17_ptav.attribute_id.id,
                                "product_attribute_value_id": v17_ptav.product_attribute_value_id.id,
                                "qty": qty,
                                "template_attri_value_id": v17_ptav.id,
                            })
            if attribute_line_id.is_qty_required and 'None' in attribute_line_id.mapped("value_ids.name"):
                ptav_none = attribute_line_id.product_template_value_ids.filtered(
                    lambda l: l.product_attribute_value_id.name == 'None' and l.ptav_active and not l.attribute_value_qty_ids
                )
                if ptav_none:
                    ptav = ptav_none[0]
                    if not ptav.is_qty_required:
                        cr.execute("""
                            UPDATE product_template_attribute_value
                            SET is_qty_required = TRUE
                            WHERE id = %s
                        """, (ptav.id,))
                        cr.commit()
                    qty_range = set(range(ptav_none.default_qty, ptav_none.maximum_qty + 1))
                    existing_qty = set(ptav_none.attribute_value_qty_ids.mapped("qty"))
                    missing_qty = qty_range - existing_qty
                    # qty_vals_to_create = []
                    for qty in missing_qty:
                        qty_vals_to_create.append({
                            'name': f"{ptav.product_attribute_value_id.display_name} - Qty {qty}",
                            'product_tmpl_id': ptav.product_tmpl_id.id,
                            'product_attribute_id': ptav.attribute_id.id,
                            'product_attribute_value_id': ptav.product_attribute_value_id.id,
                            'qty': qty,
                            'template_attri_value_id': ptav.id,
                        })

            product_template_value_ids = attribute_line_id.filtered('is_qty_required').mapped("product_template_value_ids").filtered("ptav_active")
            # qty_vals_to_create = []
            for ptav in product_template_value_ids:
                qty_range = set(range(ptav.default_qty, ptav.maximum_qty + 1))
                existing_qty = set(ptav.attribute_value_qty_ids.mapped('qty'))
                missing_qty = qty_range - existing_qty
                for qty in missing_qty:
                    qty_vals_to_create.append({
                        'name': f"{ptav.product_attribute_value_id.display_name} - Qty {qty}",
                        'product_tmpl_id': ptav.product_tmpl_id.id,
                        'product_attribute_id': ptav.attribute_id.id,
                        'product_attribute_value_id': ptav.product_attribute_value_id.id,
                        'qty': qty,
                        'template_attri_value_id': ptav.id,
                    })
        if qty_vals_to_create:
            avq_obj.create(qty_vals_to_create)
            cr.commit()
        qty_attributes_lines = template.mapped("attribute_line_ids").filtered("is_qty_required")
        product_variant_ids = template.mapped("product_variant_ids").filtered("active")
        attribute_id = qty_attributes_lines.filtered("attribute_id")
        for product_product in product_variant_ids:
            product_attribute_value_qty_ids = product_product.mapped("product_attribute_value_qty_ids")
            for value_qty in product_attribute_value_qty_ids:
                for line in qty_attributes_lines:
                    if value_qty:
                        target_val = value_qty.attr_value_id
                        current_val = value_qty.attribute_value_qty_id.product_attribute_value_id
                        if not current_val or current_val.id != target_val.id:
                            if target_val.attribute_id.name == line.attribute_id.name:
                                active_value_id = pav.search([
                                    ("name", "=", value_qty.attr_value_id.name),
                                    ("attribute_id", "=", line.attribute_id.id)
                                ], limit=1)

                                attribute_value_qty_data = avq_obj.search([
                                    ("product_attribute_value_id", "=", active_value_id.id),
                                    ("product_tmpl_id", "=", template.id),
                                    ("qty", "=", int(value_qty.qty))
                                ], limit=1)

                                if attribute_value_qty_data:
                                    value_qty.write({
                                        "attribute_value_qty_id": attribute_value_qty_data.id,
                                        "attr_value_id": active_value_id.id
                                    })
                                    cr.commit()
                    
    def script_5(self):
        cr = self.env.cr
        batch_size = 100
        templates = self.env['product.template'].search([("has_configurable_attributes", "=", True)])
        total = len(templates)
        _logger.info("Total products to process: %s", total)
        counter = 0
        for offset in range(0, total, batch_size):
            batch = templates[offset:offset + batch_size]
            _logger.info("Processing batch: Offset=%s, Size=%s", offset, len(batch))
            for template in batch:
                _logger.info("→ Processing Product Template: %s (ID: %s)", template.name, template.id)
                counter += 1
                attribute_line_ids = template.mapped("attribute_line_ids")
                update_query = "UPDATE product_template_attribute_line SET is_qty_required = 't' WHERE id = %s;"
                avq_obj = self.env["attribute.value.qty"]
                pav = self.env["product.attribute.value"]
                qty_vals_to_create = []
                for attribute_line_id in attribute_line_ids:
                    v13_data_select = "select id,attribute_id ,attribute_line_id,product_attribute_value_id,default_qty,maximum_qty  from temp_product_template_attribute_value_V13_VP where product_tmpl_id = %s and attribute_line_id = %s and ptav_active = 't' and default_qty >=1 and maximum_qty >1;" 
                    cr.execute(v13_data_select, (template.id,attribute_line_id.id),)
                    v13_datas = cr.fetchall()
                    if attribute_line_id.value_ids and (not attribute_line_id.default_val or not attribute_line_id.default_val.active):
                        cr.execute("""
                            UPDATE product_template_attribute_line
                            SET default_val = %s
                            WHERE id = %s;
                        """, (attribute_line_id.value_ids[0].id, attribute_line_id.id))
                        cr.commit()
                    if v13_datas:
                        for v13_data in v13_datas:
                            v13_value_id = v13_data[3]
                            v17_ptav = attribute_line_id.product_template_value_ids.filtered(
                                lambda l: l.product_attribute_value_id.id == v13_value_id and l.ptav_active
                            )
                            if not attribute_line_id.is_qty_required:
                                cr.execute(update_query, (attribute_line_id.id,))
                            if v13_value_id in attribute_line_id.value_ids.ids:
                                default_qty = v17_ptav.default_qty
                                maximum_qty = v17_ptav.maximum_qty
                                existing_qty = set(v17_ptav.attribute_value_qty_ids.mapped("qty"))
                                expected_qty = set(range(default_qty, maximum_qty + 1))

                                missing_qty = expected_qty - existing_qty
                                for qty in missing_qty:
                                    qty_vals_to_create.append({
                                        "name": f"{v17_ptav.product_attribute_value_id.display_name} - Qty {qty}",
                                        "product_tmpl_id": v17_ptav.product_tmpl_id.id,
                                        "product_attribute_id": v17_ptav.attribute_id.id,
                                        "product_attribute_value_id": v17_ptav.product_attribute_value_id.id,
                                        "qty": qty,
                                        "template_attri_value_id": v17_ptav.id,
                                    })
                    if attribute_line_id.is_qty_required and 'None' in attribute_line_id.mapped("value_ids.name"):
                        ptav_none = attribute_line_id.product_template_value_ids.filtered(
                            lambda l: l.product_attribute_value_id.name == 'None' and l.ptav_active and not l.attribute_value_qty_ids
                        )
                        if ptav_none:
                            ptav = ptav_none[0]
                            if not ptav.is_qty_required:
                                cr.execute("""
                                    UPDATE product_template_attribute_value
                                    SET is_qty_required = TRUE
                                    WHERE id = %s
                                """, (ptav.id,))
                                cr.commit()
                            qty_range = set(range(ptav_none.default_qty, ptav_none.maximum_qty + 1))
                            existing_qty = set(ptav_none.attribute_value_qty_ids.mapped("qty"))
                            missing_qty = qty_range - existing_qty
                            # qty_vals_to_create = []
                            for qty in missing_qty:
                                qty_vals_to_create.append({
                                    'name': f"{ptav.product_attribute_value_id.display_name} - Qty {qty}",
                                    'product_tmpl_id': ptav.product_tmpl_id.id,
                                    'product_attribute_id': ptav.attribute_id.id,
                                    'product_attribute_value_id': ptav.product_attribute_value_id.id,
                                    'qty': qty,
                                    'template_attri_value_id': ptav.id,
                                })

                    product_template_value_ids = attribute_line_id.filtered('is_qty_required').mapped("product_template_value_ids").filtered("ptav_active")
                    # qty_vals_to_create = []
                    for ptav in product_template_value_ids:
                        qty_range = set(range(ptav.default_qty, ptav.maximum_qty + 1))
                        existing_qty = set(ptav.attribute_value_qty_ids.mapped('qty'))
                        missing_qty = qty_range - existing_qty
                        for qty in missing_qty:
                            qty_vals_to_create.append({
                                'name': f"{ptav.product_attribute_value_id.display_name} - Qty {qty}",
                                'product_tmpl_id': ptav.product_tmpl_id.id,
                                'product_attribute_id': ptav.attribute_id.id,
                                'product_attribute_value_id': ptav.product_attribute_value_id.id,
                                'qty': qty,
                                'template_attri_value_id': ptav.id,
                            })
                if qty_vals_to_create:
                    avq_obj.create(qty_vals_to_create)
                    cr.commit()
                qty_attributes_lines = template.mapped("attribute_line_ids").filtered("is_qty_required")
                product_variant_ids = template.mapped("product_variant_ids").filtered("active")
                attribute_id = qty_attributes_lines.filtered("attribute_id")
                for product_product in product_variant_ids:
                    product_attribute_value_qty_ids = product_product.mapped("product_attribute_value_qty_ids")
                    for value_qty in product_attribute_value_qty_ids:
                        for line in qty_attributes_lines:
                            if value_qty:
                                target_val = value_qty.attr_value_id
                                current_val = value_qty.attribute_value_qty_id.product_attribute_value_id
                                if not current_val or current_val.id != target_val.id:
                                    if target_val.attribute_id.name == line.attribute_id.name:
                                        active_value_id = pav.search([
                                            ("name", "=", value_qty.attr_value_id.name),
                                            ("attribute_id", "=", line.attribute_id.id)
                                        ], limit=1)

                                        attribute_value_qty_data = avq_obj.search([
                                            ("product_attribute_value_id", "=", active_value_id.id),
                                            ("product_tmpl_id", "=", template.id),
                                            ("qty", "=", int(value_qty.qty))
                                        ], limit=1)

                                        if attribute_value_qty_data:
                                            value_qty.write({
                                                "attribute_value_qty_id": attribute_value_qty_data.id,
                                                "attr_value_id": active_value_id.id
                                            })
                                            cr.commit()
                _logger.info("\n✅ Script 5 completed,Processed count: %s", counter)