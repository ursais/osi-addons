from odoo import models
import logging

_logger = logging.getLogger(__name__)


class IrActionsServer(models.Model):
    _inherit = "ir.actions.server"

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
        _logger.info("\n\n===product_attribute_value_product_template_attribute_line_rel=%s",len(line_rel_ids))
        _logger.info("\n\n==================Script 2 is End==================")


    def script_3(self):
        _logger.info("\n\n==Update Product Templates with Unique Attributes and Values==Script 3 is start==================")
        batch_size = 100  # Define batch size
        ProductTemplates = self.env['product.template'].search([("has_configurable_attributes","=",True)])
        total_products = len(ProductTemplates)  # Total number of products to process
        offset = 0
        counter = 1
        cr = self.env.cr
        _logger.info("Total products to process: %s", total_products)
        while offset < total_products:
            batch_products = ProductTemplates[offset:offset + batch_size]  # Slice the records to get the current batch
            _logger.info("Processing batch: Offset %s, Batch Size %s", offset, len(batch_products))
            for product_template in batch_products:
                # _logger.info("\n\n\n\n====Script 3===========product_template##########%s==ID:::%s:::Counter::%s",product_template.name,product_template,counter)
                if product_template.attribute_line_ids:
                    update_query = """UPDATE product_template_attribute_line SET used_in_sale_description = true WHERE id IN %s;"""
                    cr.execute(update_query, (tuple(product_template.attribute_line_ids.ids),))
                    cr.commit()
                    
                for line in product_template.attribute_line_ids:
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
                    # Process each group of values
                    
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
                                active_value_id = self.env["product.attribute.value"].search([
                                    ("name", "=", name),
                                    ("attribute_id", "=", for_update.attribute_id.id)
                                ], limit=1)
                                if not active_value_id:
                                    update_query = """UPDATE product_attribute_value SET active = TRUE,attribute_id = %s WHERE id =%s;"""
                                    cr.execute(update_query,(for_update.attribute_id.id,old_product_attribute_value_id.id))
                                    cr.commit()
            
                                # cr.execute("""
                                #     UPDATE product_template_attribute_value
                                #     SET product_attribute_value_id = %s
                                #     WHERE id = %s AND attribute_id = %s;
                                # """, (active_value_id.id, for_update.id, for_update.attribute_id.id))
                                # cr.commit()
            
                                # # Update the relationship table
                                # cr.execute("""
                                #     UPDATE product_attribute_value_product_template_attribute_line_rel
                                #     SET product_attribute_value_id = %s
                                #     WHERE product_template_attribute_line_id = %s AND product_attribute_value_id = %s;
                                # """, (active_value_id.id, for_update.attribute_line_id.id, old_product_attribute_value_id.id))
                                # cr.commit()
                                
                            active_ptav = self.env["product.template.attribute.value"].search([("attribute_id","=",active_value_id.attribute_id.id),("product_attribute_value_id","=",active_value_id.id),("id","=",duplicates[0].id)])
                            active_ptav2 = self.env["product.template.attribute.value"].search([("attribute_id","=",old_product_attribute_value_id.attribute_id.id),("product_attribute_value_id","=",old_product_attribute_value_id.id),("id","=",duplicates[0].id),("ptav_active","=",True)])
                            if active_ptav and not active_ptav.ptav_active:
                                active_ptav.write({"ptav_active":True})
                            elif active_ptav.ptav_active and active_ptav.product_attribute_value_id.id == active_value_id.id :
                                pass
                            elif active_ptav.ptav_active and active_ptav.product_attribute_value_id.id != active_value_id.id :
                                # ,("ptav_active","=",True)
                                cr.execute("""
                                    UPDATE product_template_attribute_value
                                    SET product_attribute_value_id = %s
                                    WHERE id = %s AND attribute_id = %s AND ptav_active = true;
                                """, (active_value_id.id, duplicates[0].id,active_value_id.attribute_id.id))
                            elif active_ptav2:
                                active_ptav.write({"ptav_active":False})
                                
                            delete_query = """DELETE FROM product_attribute_value_product_template_attribute_line_rel 
                                  WHERE product_template_attribute_line_id = %s AND (product_attribute_value_id = %s or product_attribute_value_id = %s);"""
                            if active_value_id:
                                
                                cr.execute(delete_query, (line.id,active_value_id.id,old_product_attribute_value_id.id))
                                cr.commit()  # Commit the transaction
                                insert_query = """INSERT INTO product_attribute_value_product_template_attribute_line_rel (product_template_attribute_line_id, product_attribute_value_id)  VALUES (%s, %s);"""
                                cr.execute(insert_query, (line.id,active_value_id.id))
                            cr.commit()
                                
                            
                        elif len(duplicates) == 1:
                            # Only one duplicate, ensure it's active and update the relation
                            old_product_attribute_value_id = duplicates[0].product_attribute_value_id
                            active_value_id = old_product_attribute_value_id
                            if not old_product_attribute_value_id.active:
                                active_value_id = self.env["product.attribute.value"].search([
                                    ("name", "=", name),
                                    ("attribute_id", "=", duplicates[0].attribute_id.id)
                                ], limit=1)
                            
                                if not active_value_id:
                                    update_query = """UPDATE product_attribute_value SET active = TRUE,attribute_id = %s WHERE id =%s;"""
                                    cr.execute(update_query,( duplicates[0].attribute_id.id,old_product_attribute_value_id.id))
                                    cr.commit()
                                
                            active_ptav = self.env["product.template.attribute.value"].search([("attribute_id","=",active_value_id.attribute_id.id),("product_attribute_value_id","=",active_value_id.id),("id","=",duplicates[0].id)])
                            active_ptav2 = self.env["product.template.attribute.value"].search([("attribute_id","=",old_product_attribute_value_id.attribute_id.id),("product_attribute_value_id","=",old_product_attribute_value_id.id),("id","=",duplicates[0].id),("ptav_active","=",True)])
                            if active_ptav and not active_ptav.ptav_active:
                                active_ptav.write({"ptav_active":True})
                            elif active_ptav.ptav_active and active_ptav.product_attribute_value_id.id == active_value_id.id :
                                pass
                            elif active_ptav.ptav_active and active_ptav.product_attribute_value_id.id != active_value_id.id :
                                # ,("ptav_active","=",True)
                                cr.execute("""
                                    UPDATE product_template_attribute_value
                                    SET product_attribute_value_id = %s
                                    WHERE id = %s AND attribute_id = %s AND ptav_active = true;
                                """, (active_value_id.id, duplicates[0].id,active_value_id.attribute_id.id))
                            elif active_ptav2:
                                active_ptav.write({"ptav_active":False})
                                
                            delete_query = """DELETE FROM product_attribute_value_product_template_attribute_line_rel 
                                  WHERE product_template_attribute_line_id = %s AND (product_attribute_value_id = %s or product_attribute_value_id = %s);"""
                            if active_value_id:
                                cr.execute(delete_query, (line.id,active_value_id.id,old_product_attribute_value_id.id))
                                cr.commit()  # Commit the transaction
                                insert_query = """INSERT INTO product_attribute_value_product_template_attribute_line_rel (product_template_attribute_line_id, product_attribute_value_id)  VALUES (%s, %s);"""
                                cr.execute(insert_query, (line.id,active_value_id.id))
                            cr.commit()
                    # if line_values:
                    #     value_with_none = line_values.filtered(lambda ptav: ptav.name == 'None')
                    #     value_with_non_none = line_values.filtered(lambda ptav: ptav.name != 'None')
                    #     if value_with_none:
                    #         # Update default value using SQL
                    #         cr.execute("""
                    #             UPDATE product_template_attribute_line
                    #             SET default_val = %s
                    #             WHERE id = %s;
                    #         """, (value_with_none[0].id, line.id))
                    #         cr.commit()
                        
                    #     else:
                    #         cr.execute("""
                    #             UPDATE product_template_attribute_line
                    #             SET default_val = %s
                    #             WHERE id = %s;
                    #         """, (value_with_non_none[0].id, line.id))
                    #         cr.commit()
                counter += 1
            offset += batch_size
            self.env.cr.commit()  # Commit changes after processing each batch
            _logger.info("Batch processed. Offset moved to %s", offset)
        _logger.info("Processing completed!")

        _logger.info("\n\n==================Script 3 is Done==================")
    
    def script_4(self):
        _logger.info("\n\n==Sync Attribute Values in Product Variants===Script 4 is start==================")
        batch_size = 100  # Define batch size
        #PRODUCT-TEMPLATE ID Which id Need to take care [5593,24607,5172,32379,24337,25216,26588,6518,4696,103791,102630,102736,101999]
        ProductTemplates = self.env['product.template'].search([("has_configurable_attributes","=",True),("active","=",True)])
        total_products = len(ProductTemplates)  # Total number of products to process
        offset = 0
        counter = 1
        cr = self.env.cr
        _logger.info("Total products to process: %s", total_products)
        while offset < total_products:
            batch_products = ProductTemplates[offset:offset + batch_size]  # Slice the records to get the current batch
            _logger.info("Processing batch: Offset %s, Batch Size %s", offset, len(batch_products))
            for product_template in batch_products:
                # _logger.info("\n\n\n\n======Script 4=========product_template##########%s==ID:::%s:::Counter::%s",product_template.name,product_template,counter)
                config_step_id = product_template.config_step_line_ids.filtered(lambda l:l.config_step_id and not l.attribute_line_ids)
                config_step_id.unlink()
                cr.commit()
                for attrbute_line_id in product_template.mapped("attribute_line_ids").filtered("active"):
                    # if (attrbute_line_id.value_ids and (not attrbute_line_id.default_val or not attrbute_line_id.default_val.active)):
                    #     cr.execute("""
                    #         UPDATE product_template_attribute_line
                    #         SET default_val = %s
                    #         WHERE id = %s;
                    #     """, (attrbute_line_id.value_ids[0].id, attrbute_line_id.id))
                    #     cr.commit()
                    if attrbute_line_id.attribute_id.active:
                        values_ids = attrbute_line_id.value_ids.filtered(lambda l:l.active and l.attribute_id.id != attrbute_line_id.attribute_id.id)
                        product_template_value_ids = attrbute_line_id.product_template_value_ids.filtered("ptav_active")
                        for value in values_ids:
                            active_value_id = self.env["product.attribute.value"].search([("name","=",value.name),("active","=",True),("attribute_id","=",value.attribute_id.id)])
                            if not active_value_id.attribute_id.active and value.name not in attrbute_line_id.attribute_id.value_ids.mapped("name"):
                                # _logger.info("\n\n\n\n==============Values IDS:Name:%s:%s:%s:%s:active_value_id::%s",value.name,value,attrbute_line_id.attribute_id,value.attribute_id,active_value_id.attribute_id.active)
                                update_query = """UPDATE product_attribute_value SET active = TRUE,attribute_id = %s WHERE id =%s;"""
                                cr.execute(update_query,(attrbute_line_id.attribute_id.id,value.id))
                                cr.commit()
                        values_ids = attrbute_line_id.value_ids
                        for ptav_line in product_template_value_ids:
                            if ptav_line.attribute_id != attrbute_line_id.attribute_id:
                                # _logger.info("\n\n\n\n==============PTAV==Values IDS::%s::%s::%s",ptav_line.attribute_id,attrbute_line_id.attribute_id, attrbute_line_id.attribute_id.name)
                                cr.execute("""
                                        UPDATE product_template_attribute_value
                                        SET attribute_id = %s
                                        WHERE id = %s AND ptav_active = true;
                                    """, (attrbute_line_id.attribute_id.id,ptav_line.id))
                                cr.commit()
                            inactive_value_active_ptav = ptav_line.attribute_line_id.product_template_value_ids.filtered(lambda l:l.name == ptav_line.product_attribute_value_id.name and not l.product_attribute_value_id.active and l.ptav_active and l.product_tmpl_id.id == ptav_line.product_tmpl_id.id)
                            active_value_inactive_ptav = ptav_line.attribute_line_id.product_template_value_ids.filtered(lambda l:l.name == ptav_line.product_attribute_value_id.name and l.product_attribute_value_id.active and not l.ptav_active and l.product_tmpl_id.id == ptav_line.product_tmpl_id.id)
                            if not inactive_value_active_ptav and not active_value_inactive_ptav and not ptav_line.product_attribute_value_id.active:
                                active_value_id = attrbute_line_id.value_ids.filtered(lambda v:v.name == ptav_line.product_attribute_value_id.name )
                                # _logger.info("\n\n\n\n====BOTH Inactive==========PTAV==Values ID:%s==%s:%s::%s",ptav_line.product_attribute_value_id.name,attrbute_line_id.attribute_id.name,ptav_line.product_attribute_value_id,active_value_id)
                                cr.execute("""
                                        UPDATE product_template_attribute_value
                                        SET product_attribute_value_id = %s
                                        WHERE id = %s AND ptav_active = true;
                                    """, (active_value_id.id,ptav_line.id))
                                cr.commit()
                            if inactive_value_active_ptav and active_value_inactive_ptav:
                                _logger.info("\n\n\n\n>>inactive_value_active_ptav")
                                inactive_value_active_ptav.ptav_active = False
                                cr.commit()
                            if not inactive_value_active_ptav and active_value_inactive_ptav:
                                active_value_inactive_ptav.ptav_active = True
                                cr.commit()
                            if inactive_value_active_ptav and not active_value_inactive_ptav and ptav_line.product_attribute_value_id.active:
                                active_value_id = attrbute_line_id.value_ids.filtered(lambda v:v.name == ptav_line.product_attribute_value_id.name )
                                # _logger.info("\n\n\n\n==============PTAV==Values ID:%s==%s:%s::%s",ptav_line.product_attribute_value_id.name,attrbute_line_id.attribute_id.name,ptav_line.product_attribute_value_id,active_value_id)
                                inactive_value_active_ptav.ptav_active = False
                                cr.commit()
                            if not ptav_line.product_attribute_value_id.active:
                                active_value_id = attrbute_line_id.value_ids.filtered(lambda v:v.name == ptav_line.product_attribute_value_id.name )
                                # _logger.info("\n\n\n\n==============PTAV==Values ID:%s==%s:%s::%s",ptav_line.product_attribute_value_id.name,attrbute_line_id.attribute_id.name,ptav_line.product_attribute_value_id,active_value_id)
                                cr.execute("""
                                        UPDATE product_template_attribute_value
                                        SET product_attribute_value_id = %s
                                        WHERE id = %s AND ptav_active = true;
                                    """, (active_value_id.id,ptav_line.id))
                                cr.commit()

                                   
                            # if ptav_line.product_attribute_value_id.active and ptav_line.product_attribute_value_id.id not in attrbute_line_id.value_ids.ids:
                                # _logger.info("\n\n\n\n========2322======PTAV==Values ID%s==%s",ptav_line.product_attribute_value_id.name,attrbute_line_id.attribute_id.name)
                            
                            if ptav_line.attribute_line_id.is_qty_required:
                                # _logger.info("\n\n\n\n======3333========PTAV==%s",ptav_line.product_attribute_value_id.name)
                                for qty_val in ptav_line.attribute_value_qty_ids:
                                    if qty_val.product_attribute_id.id != ptav_line.attribute_id.id:
                                        # _logger.info("\n\n\n\n======3333========PTAV==%s",ptav_line.product_attribute_value_id.name)
                                        cr.execute("""
                                            UPDATE attribute_value_qty
                                            SET product_attribute_id = %s
                                            WHERE id = %s;
                                        """, (ptav_line.attribute_id.id,qty_val.id))
                                        cr.commit()
                                    if qty_val.product_attribute_value_id.id !=  ptav_line.product_attribute_value_id.id:
                                        # _logger.info("\n\n\n\n======3333========PTAV==%s",ptav_line.product_attribute_value_id.name)
                                        cr.execute("""
                                            UPDATE attribute_value_qty
                                            SET product_attribute_value_id = %s
                                            WHERE id = %s;
                                        """, (ptav_line.product_attribute_value_id.id,qty_val.id))
                                        cr.commit()
                        not_common = list(set(values_ids.ids).symmetric_difference(set(product_template_value_ids.mapped("product_attribute_value_id").ids)))
                        if not_common:
                            line_id = attrbute_line_id.id
                            value_ids = tuple(not_common)
                            query = """
                                DELETE FROM product_attribute_value_product_template_attribute_line_rel
                                WHERE product_template_attribute_line_id = %s
                                AND product_attribute_value_id = ANY(%s)
                            """

                            self.env.cr.execute(query, (line_id, list(value_ids)))
                            self.env.cr.commit() 
                counter += 1
            offset += batch_size
            self.env.cr.commit()  # Commit changes after processing each batch
            _logger.info("Batch processed. Offset moved to %s", offset)
        _logger.info("Processing completed!")
        _logger.info("\n\n==================Script 4 is End==================")

    def script_5(self):
        _logger.info("\n\n==Update Quantity-Related Data in Attribute Lines and Product Variants==Script 5 is start==================")
        cr = self.env.cr

        # ProductTemplates = env["product.template"].search([("id","=",104183)])
        batch_size = 10  # Define batch size
        ProductTemplates = self.env['product.template'].search([("has_configurable_attributes","=",True)])
        total_products = len(ProductTemplates)  # Total number of products to process
        offset = 0
        counter = 1
        cr = self.env.cr
        _logger.info("Total products to process: %s", total_products)
        while offset < total_products:
            batch_products = ProductTemplates[offset:offset + batch_size]  # Slice the records to get the current batch
            _logger.info("Processing batch: Offset %s, Batch Size %s", offset, len(batch_products))
            for pro_template in batch_products:
                _logger.info("\n\n\n\n====Script 5===========product_template##########%s==ID:::%s:::Counter::%s",pro_template.name,pro_template,counter)
                for attrbute_line_id in pro_template.mapped("attribute_line_ids"):
                    v13_data_select = "select id,attribute_id ,attribute_line_id,product_attribute_value_id,default_qty,maximum_qty  from temp_product_template_attribute_value_V13_VP where product_tmpl_id = %s and attribute_line_id = %s and ptav_active = 't' and default_qty >=1 and maximum_qty >1;" 
                    cr.execute(v13_data_select, (pro_template.id,attrbute_line_id.id),)
                    v13_datas = cr.fetchall()
                    # if attrbute_line_id.value_ids and (not attrbute_line_id.default_val or not attrbute_line_id.default_val.active):
                    #     cr.execute("""
                    #         UPDATE product_template_attribute_line
                    #         SET default_val = %s
                    #         WHERE id = %s;
                    #     """, (attrbute_line_id.value_ids[0].id, attrbute_line_id.id))
                    #     cr.commit()
                    if v13_datas:
                        for v13_data in v13_datas:
                            v13_attribute_value_id = v13_data[3]
                            v17_product_template_value_id = attrbute_line_id.product_template_value_ids.filtered(lambda l :l.product_attribute_value_id.id == v13_attribute_value_id and l.ptav_active)
                            _logger.info("\n\n\n\n======v13_data:%s::%s:%s",attrbute_line_id.attribute_id.name,v17_product_template_value_id.name,v13_data)
                            if not attrbute_line_id.is_qty_required:
                                update_query = "UPDATE product_template_attribute_line SET is_qty_required = 't' WHERE id = %s;"
                                cr.execute(update_query, (attrbute_line_id.id,))  # Note the comma inside the tuple
                                cr.commit()
                            if v13_attribute_value_id in attrbute_line_id.mapped("value_ids").ids:
                                qty_range = set(range(v17_product_template_value_id.default_qty,v17_product_template_value_id.maximum_qty+1))
                                existing_quantities = set(v17_product_template_value_id.attribute_value_qty_ids.mapped('qty'))
                                missing_quantities = qty_range - existing_quantities
                                _logger.info("\n\n\n\n======missing_quantities=========product_template##########%s==ID:::%s:::Counter::%s",v17_product_template_value_id.attribute_value_qty_ids,qty_range,missing_quantities)
                                for qty in missing_quantities:
                                    v17_product_template_value_id.attribute_value_qty_ids.create({
                                        'name': f"{v17_product_template_value_id.mapped('product_attribute_value_id').display_name} - Qty {qty}",
                                        'product_tmpl_id': v17_product_template_value_id.product_tmpl_id.id,
                                        'product_attribute_id': v17_product_template_value_id.attribute_id.id,
                                        'product_attribute_value_id': v17_product_template_value_id.product_attribute_value_id.id,
                                        'qty': qty,
                                        'template_attri_value_id': v17_product_template_value_id.id,
                                    })
                                    cr.commit()
                    if attrbute_line_id.is_qty_required and 'None' in attrbute_line_id.mapped("value_ids.name"):
                        v17_product_template_none_value_id = attrbute_line_id.product_template_value_ids.filtered(lambda l :l.product_attribute_value_id.name == 'None' and l.ptav_active and not l.attribute_value_qty_ids)
                        update_query = "UPDATE product_template_attribute_value SET is_qty_required = 't' WHERE id = %s;"
                        if v17_product_template_none_value_id:
                            cr.execute(update_query, (v17_product_template_none_value_id.id,))  # Note the comma inside the tuple
                            cr.commit()
                        qty_range = set(range(v17_product_template_none_value_id.default_qty,v17_product_template_none_value_id.maximum_qty+1))
                        existing_quantities = set(v17_product_template_none_value_id.attribute_value_qty_ids.mapped('qty'))
                        missing_quantities = qty_range - existing_quantities
                        for qty in missing_quantities:
                            v17_product_template_none_value_id.attribute_value_qty_ids.create({
                                'name': f"{v17_product_template_none_value_id.mapped('product_attribute_value_id').display_name} - Qty {qty}",
                                'product_tmpl_id': v17_product_template_none_value_id.product_tmpl_id.id,
                                'product_attribute_id': v17_product_template_none_value_id.attribute_id.id,
                                'product_attribute_value_id': v17_product_template_none_value_id.product_attribute_value_id.id,
                                'qty': qty,
                                'template_attri_value_id': v17_product_template_none_value_id.id,
                            })
                            cr.commit()
                        _logger.info("\n\n==##NONE### ==%s",v17_product_template_none_value_id)
                    product_template_value_ids = attrbute_line_id.filtered('is_qty_required').mapped("product_template_value_ids").filtered("ptav_active")
                    for template_value_line in product_template_value_ids:
                        qty_range = set(range(template_value_line.default_qty,template_value_line.maximum_qty+1))
                        existing_quantities = set(template_value_line.attribute_value_qty_ids.mapped('qty'))
                        missing_quantities = qty_range - existing_quantities
                        _logger.info("\n\n\n\n======template_value_line=====%s==%s,",template_value_line.name,missing_quantities)
                        for qty in missing_quantities:
                            template_value_line.attribute_value_qty_ids.create({
                                'name': f"{template_value_line.mapped('product_attribute_value_id').display_name} - Qty {qty}",
                                'product_tmpl_id': template_value_line.product_tmpl_id.id,
                                'product_attribute_id': template_value_line.attribute_id.id,
                                'product_attribute_value_id': template_value_line.product_attribute_value_id.id,
                                'qty': qty,
                                'template_attri_value_id': template_value_line.id,
                            })
                            cr.commit()
                        
                    
                product_template = pro_template
                qty_attributes_lines = product_template.mapped("attribute_line_ids").filtered("is_qty_required")
                for product_product in product_template.mapped("product_variant_ids").filtered("active"):
                    for value_qty in product_product.mapped("product_attribute_value_qty_ids"):
                        attribute_id = qty_attributes_lines.filtered(lambda l:l.attribute_id.name)
                        for line in qty_attributes_lines:
                            if value_qty and value_qty.attribute_value_qty_id.product_attribute_value_id.id != value_qty.attr_value_id.id or not value_qty.attribute_value_qty_id.product_attribute_value_id:
                                _logger.info("\n\n\n\n======444444=====%s===%s=%s:%s**%s",value_qty.product_id,value_qty.attr_value_id.attribute_id.name,line.attribute_id.name,value_qty.attr_value_id.name,value_qty.qty)
                                if value_qty.attr_value_id.attribute_id.name == line.attribute_id.name:
                                    _logger.info("\n\n===product_product==%s==%s===%s",product_product,product_product.product_attribute_value_qty_ids.mapped("attr_value_id.name"),product_product.product_attribute_value_qty_ids.mapped("qty"))
                                    active_value_id = self.env["product.attribute.value"].search([("name","=",value_qty.attr_value_id.name),("attribute_id","=",line.attribute_id.id)])
                                    attribute_value_qty_data = self.env["attribute.value.qty"].search([('product_attribute_value_id','=',active_value_id.id),("product_tmpl_id","=",product_template.id),("qty","=",int(value_qty.qty))])
                                    value_qty.write({'attribute_value_qty_id':attribute_value_qty_data.id,"attr_value_id":active_value_id.id})
                                    cr.commit()
                counter += 1
            offset += batch_size
            self.env.cr.commit()  # Commit changes after processing each batch
            _logger.info("Batch processed. Offset moved to %s", offset)
        _logger.info("Processing completed!")
        _logger.info("\n\n==================Script 5 is End==================")


    def script_6(self):
        import time
        self = self.sudo()
        MrpBom = self.env["mrp.bom"].with_context(is_data_migration=True).sudo()
        _logger.info("\n\n== Generate Scaffolding BOM == Script 6 Start ==================")

        batch_size = 1000
        cr = self.env.cr

        # Ticket Ref: 70233
        domain = [
            '|',
                ('code', 'ilike', 'TA BOM'),
                '|',
                    ('product_id.active', '=', False),
                    ('product_tmpl_id.active', '=', False),
            ('active', '=', True),
        ]

        boms_to_archive = MrpBom.search(domain)
        _logger.info(">>>>>>>>>>>>>>>boms_to_archive>>>>>>>>>>>>>>%s",len(boms_to_archive))
        if boms_to_archive:
            cr.execute(
                "UPDATE mrp_bom SET active = FALSE WHERE id IN %s",
                (tuple(set(boms_to_archive.ids)),)
            )

        boms_to_archive = MrpBom.search([])
        boms_to_archive = boms_to_archive.filtered(lambda l:not l.bom_line_ids)
        boms_to_archive.write({"active":False})

        # Define models
        ProductTemplate = self.env['product.template'].sudo()
        ProductTemplateAttributeLine = self.env['product.template.attribute.line'].sudo()
        MrpBomLine = self.env['mrp.bom.line'].sudo()
        MrpBomLineConfigSet = self.env['mrp.bom.line.configuration.set'].sudo()
        MrpBomLineConfig = self.env['mrp.bom.line.configuration'].sudo()
        self._cr.execute("""
        INSERT INTO ir_config_parameter (key, value, create_uid, write_uid, create_date, write_date)
        VALUES ('Bypass Migration Compute', '1', 1, 1, NOW(), NOW())
        ON CONFLICT (key)
        DO UPDATE SET value = EXCLUDED.value, write_date = NOW();
        """)
        # Preload all config sets into a dict for caching
        t0 = time.time()
        existing_config_sets = MrpBomLineConfigSet.search([])
        config_set_map = {rec.name: rec for rec in existing_config_sets}

        # Get all templates with configurable attributes
        t0 = time.time()
        cr.execute("SELECT id, name FROM product_template WHERE has_configurable_attributes = TRUE")
        all_templates = cr.fetchall()
        total_products = len(all_templates)
        _logger.info("[Timing] Fetching product templates: %.3f sec", time.time() - t0)
        _logger.info("Total products to process: %s", total_products)

        offset = 0
        counter = 1
#        print ("=============total_products===========", total_products)
        while offset < total_products:
            batch_templates = all_templates[offset:offset + batch_size]
            _logger.info("Processing batch: Offset=%s, Size=%s", offset, len(batch_templates))
            for template_id, template_name in batch_templates:
                # _logger.info("==> Processing Product: %s (ID: %s) [#%s]", template_name, template_id, counter)
                # Check for existing BOM
                t_check = time.time()
                cr.execute("SELECT id FROM mrp_bom WHERE scaffolding_bom = TRUE AND product_tmpl_id = %s", (template_id,))
                if cr.fetchone():
                    _logger.info("[Skipped] Existing BOM for: %s [%.3f sec]", template_name, time.time() - t_check)
                    counter += 1
                    continue
                # Create BOM
                
                new_bom = MrpBom.with_context(is_data_migration=True).create({
                    'product_tmpl_id': template_id,
                    'product_qty': 1.0,
                    'type': 'normal',
                    'scaffolding_bom': True,
                    'existing_scaffolding_bom': False,
                })
                new_bom_id = new_bom.id
                new_bom._compute_available_config_components()
                # Get attribute lines
                attribute_lines = ProductTemplateAttributeLine.search([('product_tmpl_id', '=', template_id)])
                for line in attribute_lines:
                    valid_values = line.value_ids.filtered(lambda v: v.product_id)

                    for value in valid_values:
                        product = value.product_id
                        display_name = product.display_name
                        product_id = product.id
                        product_tmpl_id = product.product_tmpl_id.id
                        value_id = value.id
                        

                        # Lookup or create config set using cached dict
                        config_set = config_set_map.get(display_name)
                        if not config_set:
                            config_set = MrpBomLineConfigSet.create({"name": display_name})
                            config_set_map[display_name] = config_set
                        # Check if config link exists in DB
                        cr.execute("""
                            SELECT 1 FROM mrp_bom_line_configuration_product_attribute_value_rel
                            WHERE product_attribute_value_id = %s
                        """, (value_id,))
                        if not cr.fetchone():
                            MrpBomLineConfig.create({
                                "config_set_id": config_set.id,
                                "value_ids": [(6, 0, [value_id])]
                            })  
                        # Create BOM line
                        MrpBomLine.create({
                            'bom_id': new_bom_id,
                            'product_id': product_id,
                            'product_qty': 1.0,
                            'config_set_id': config_set.id,
                            'product_tmpl_id': product_tmpl_id
                        })
                        

                #_logger.info("✅ Finished BOM creation for: %s", template_name)
                counter += 1
            self._cr.commit()
            offset += batch_size
            _logger.info("Batch committed. Offset now at: %s", offset)

        _logger.info("==> All products processed. Script 6 Completed.")
        _logger.info("================== Script 6 End ==================\n\n")


    def script_7(self):
        _logger.info("\n\n==Adding classification_id in Scaffolding Bill of Martial Lines==Script 7 is start==================")
        ScaffoldingBoMs = self.env["mrp.bom"].search([("scaffolding_bom","=", True)])
        total_products = len(ScaffoldingBoMs)  # Total number of products to process
        batch_size = 10  # Define batch size
        offset = 0
        counter = 1
        _logger.info("Total products to process: %s", total_products)
        cr = self.env.cr  # Cursor for direct SQL operations
        bom_line_ids = ScaffoldingBoMs.mapped("bom_line_ids")
        while offset < total_products:
            batch_products = bom_line_ids[offset:offset + batch_size]  # Slice the records to get the current batch
            _logger.info("Processing batch: Offset %s, Batch Size %s", offset, len(batch_products))
            for line in batch_products:
                attribute_value = line.bom_id.product_tmpl_id.mapped("attribute_line_ids.value_ids").filtered(lambda x:x.product_id.id == line.product_id.id)
                if attribute_value:
                    classification_id = attribute_value.attribute_id.classification_id
                    if len(classification_id) >1:
                        classification_id = classification_id[0]
                    update_query = """UPDATE mrp_bom_line set classification_id =%s where id = %s; """
                    self.env.cr.execute(update_query,(classification_id.id,line.id))
                counter += 1    
            offset += batch_size
            self.env.cr.commit()  # Commit changes after processing each batch
            _logger.info("Batch processed. Offset moved to %s", offset)
        _logger.info("Processing completed!")
        _logger.info("\n\n==================Script 7 is End==================")


    def script_8(self):
        cr = self.env.cr
        _logger.info("\n\n==================Script 8 is Start==================")

        # ::Server Action based Script::
        # Update the phantom_bom_id data in MRP BOM inactivate the relative (Same Product) Kit BOM if the Kit BOM is not associated with a Phantom BOM ID in Product Template.
        # Company ID = 1  USA and 2 is EU
        # Pre Migration Steps
        # 1. create table temp_ir_property_v13_vp as select * from  ir_property;
        # 1. create table temp_product_temp_v13_vp as select * from  product_template;
        # 1. create table temp_product_template_res_company_rel_v13_VP as select * from  product_template_res_company_rel;
        # 2. pg_dump -d V13DBNAME -t temp_phantom_bom_id > /home/odoo/temp_phantom_bom_id.sql;
        # 3. psql -d V17DBNAME -f /home/odoo/temp_phantom_bom_id.sql   
        # Created by Vandan Pandeji
                
        _logger.info("\n==Script 8: Lifecycle_status  Migration Data=")
        cr.execute("select res_id,value_text from temp_ir_property_v13_vp where name = 'lifecycle_status';")
        lifecycle_status = cr.fetchall()
        for lifecycle in lifecycle_status:
            # lifecycle = dict(lifecycle)
            product_template_id = lifecycle[0].split(',')[1]
            code = lifecycle[1]
            # code = lifecycle.get("value_text")
            if code in ['coming_soon','in_development']:
                code = "draft"
            elif code == 'available':
                code = "active"
            elif code == 'preorder':
                code = "pre_order"
            elif code == 'end_of_life':
                    code = "end"
            elif code == False:
                code = "new"
            # product_id = lifecycle.get("res_id") and lifecycle.get("res_id").split(",")[1] or env["product.template"]
            product_state_id = self.env["product.state"].search([("code","ilike",code)])
            # print("product_state_id===",code)
            if product_state_id:
                cr.execute(
                    "update product_template set product_state_id = %s where id = %s"
                    % (product_state_id.id, int(product_template_id))
                )

        _logger.info("\n==Script 8:Pim_category Migration Data=")
        cr.execute("select id,pim_category from temp_product_temp_v13_vp;")
        pim_category = cr.fetchall()
        for pim in pim_category:
            product_template_id = pim[0]
            code = pim[1]
            if code == "Power Supplies":
                code = "power_supplies"
            elif code =="Panel PCs":
                code = "panel_pcs"
            elif code == "Assembly & Validation":
                code = "assembly_validation"
            
            attribute_set_id = self.env["attribute.set"].search([("name","ilike",code)])
            if attribute_set_id and code:
                cr.execute(
                    "update product_template set attribute_set_id = %s where id = %s"
                    % (attribute_set_id.id, product_template_id)
                )

        _logger.info("\n==Script 8:Public_destination Migration=")
        cr.execute("update product_template as pt set public_destination = (select tpt.public_destination from temp_product_temp_v13_vp as tpt where tpt.id=pt.id); ")
        
        _logger.info("\n==Script 8:Company IDS Many2Many Product Template Migration=")
        cr.execute("INSERT INTO product_template_company_display_rel (product_template_id, company_id) SELECT product_template_id, res_company_id FROM temp_product_template_res_company_rel_v13_VP;")

        AttributeValues = self.env["product.attribute.value"].search([("active","=",True),("product_id","!=",False)])
        AttributeValues._compute_company_ids()

        _logger.info("\n==Script 8:country_of_manufacture in Product Template Migration=")
        select_query = """SELECT value_reference,res_id from temp_ir_property_v13_vp where name='country_of_manufacture';"""
        cr.execute(select_query)
        v13datas = cr.fetchall()
        for data in v13datas:
            product_template_id = data[1].split(',')[1]
            product_template_id = self.env["product.template"].browse(int(product_template_id))
            country_id = data[0].split(",")[1]
            country_id = self.env["res.country"].browse(int(country_id))
            if product_template_id.exists() and country_id.exists():
                update_query = """UPDATE product_template set country_of_origin = %s where id = %s; """
                cr.execute(update_query,(country_id.id,product_template_id.id))

        _logger.info("\n==Script 8: Payment Ref in Contacts=")
        select_query = """SELECT value_reference,res_id,company_id from temp_ir_property_v13_vp where name='payment_preference';"""
        cr.execute(select_query)
        v13datas = cr.fetchall()
        field = self.env["ir.model.fields"].search(
            [
                ("model_id.model", "=", "res.partner"),
                ("name", "=", "payment_preference"),
            ]
        )
        PartnerObj = self.env["res.partner"]
        PayPrefObj = self.env["res.paypref"]
        payment_property_vals = []
        for data in v13datas:
            partner = data[1].split(",")[1]
            partner_id = PartnerObj.browse(int(partner))
            payment_ref = data[0].split(",")[1]
            payemnt_ref_id = PayPrefObj.browse(int(payment_ref))
            if field and partner_id.exists() and payemnt_ref_id.exists():
                payment_property_vals.append(
                    {
                        "name": "payment_preference",
                        "company_id": int(data[2]),
                        "fields_id": field.id,
                        "res_id": data[1],
                        "value_reference": data[0],
                    }
                )
 
        self.env["ir.property"].sudo().create(payment_property_vals)


        # OSI-ONL Ticket for # 66470 Attribute Value Visibility on System Not Respecting Migrated Values
        # create table temp_product_attribute_value_v13 as select * from  product_attribute_value;

        cr.execute("""
            UPDATE product_attribute_value pav
            SET visible_to_user = tmp.visible_to_user
            FROM temp_product_attribute_value_v13 tmp
            WHERE pav.id = tmp.id
              AND pav.active = TRUE
        """)
        cr.commit()
        _logger.info(">>> product_attribute_value visible_to_user is done")
        cr.execute("""
            UPDATE product_template_attribute_value ptav
            SET visible_to_user = pav.visible_to_user
            FROM product_attribute_value pav
            WHERE ptav.product_attribute_value_id = pav.id
              AND pav.active = TRUE
        """)
        cr.commit()
        _logger.info(">>> product_template_attribute_value visible_to_user is done")


        # _logger.info("\n\n\n\n===Task: 929566975 and 927975110 Done")


        # Ticket Ref: 69813
        putaway_location = self.env.ref("stock.stock_location_company",False)
        if putaway_location:
            putaway_location.sudo().write({"name":"Loading Dock"})
            cr.commit()
        input_location = self.env["stock.location"].sudo().search([
            ("name", "=", "Input"),
            ("usage", "=", "internal"),
            ("company_id", "=", self.env.ref("ol_base.onlogic_eu", raise_if_not_found=False).id),
        ])
        if input_location:
            input_location.sudo().write({"name":"Loading Dock"})
            cr.commit()

        # Ticket Ref: 70232
        # cr.execute("update mrp_production set sale_order_line_id=origin_sale_line_id;")
        # cr.commit()

        boms = self.env["mrp.bom"].search([("product_id","!=",False),("type","=","normal")])
        operation_vals = []
        for bom in boms:
            if not bom.operation_ids and bom.bom_line_ids:
                scaff_bom = self.env["mrp.bom"].search([("scaffolding_bom","=",True),("product_tmpl_id","=",bom.product_tmpl_id.id)])
                for oper in scaff_bom.operation_ids:
                    sequence = oper.sequence
                    if oper.workcenter_id.id == self.env.ref("mrp_batch.import_build",False).id and oper.sequence != 1:
                        sequence = 1
                    elif oper.workcenter_id.id == self.env.ref("mrp_batch.import_test",False).id and oper.sequence != 2:
                        sequence = 2
                    elif oper.workcenter_id.id == self.env.ref("mrp_batch.import_box",False).id and oper.sequence != 3:
                        sequence = 3
                    operation_vals.append({
                        "name": oper.name,
                        "workcenter_id": oper.workcenter_id.id,
                        "sequence": sequence,
                        "bom_id": bom.id,
                    })
        operations = env["mrp.routing.workcenter"].create(operation_vals)
        self.env.cr.commit()
        _logger.info("\n==BoMs Operations are created,%s",len(operations))

        _logger.info("\n==================Script 8 is Done==================")

    def removing_none_values(self):
        # Made by Vandan Pandeji
        # Script is Used for Removing None Values from Product template attribute Line, Product Template Attribute Values and Product.Product Varints Bubble.

        cr = self.env.cr
        # Step 1: Fetch "None" values
        cr.execute("""
            SELECT id 
            FROM product_attribute_value 
            WHERE name ->> 'en_US' = 'None' AND active = 't';
        """)
        none_values = cr.fetchall()
        none_values_recs = [row[0] for row in none_values]

        if none_values_recs:
            placeholders = ', '.join(['%s'] * len(none_values_recs))

            # Step 2: Delete from M2M relation table
            cr.execute(f"""
                DELETE FROM product_attribute_value_product_template_attribute_line_rel 
                WHERE product_attribute_value_id IN ({placeholders});
            """, tuple(none_values_recs))
            _logger.info("== Deleted from M2M table")

            # Step 3: Update product_template_attribute_line
            cr.execute(f"""
                UPDATE product_template_attribute_line 
                SET required = 'f', default_val = NULL 
                WHERE default_val IN ({placeholders});
            """, tuple(none_values_recs))
            _logger.info("== Updated product_template_attribute_line")

            # Step 4: Update product_template_attribute_value
            cr.execute(f"""
                UPDATE product_template_attribute_value 
                SET ptav_active = 'f' 
                WHERE product_attribute_value_id IN ({placeholders}) AND ptav_active = 't';
            """, tuple(none_values_recs))
            _logger.info("== Updated product_template_attribute_value")

            # Step 5: Delete from product_variant_combination
            cr.execute(f"""
                DELETE FROM product_variant_combination 
                WHERE product_template_attribute_value_id IN ({placeholders});
            """, tuple(none_values_recs))
            _logger.info("== Deleted from product_variant_combination")

            # Commit changes once at the end
            cr.commit()

    def update_ptal(self):
        cr = self.env.cr

        # Fetch all inactive product_template_variant_value records with necessary fields
        variant_values = self.env["product.product"].search([]).product_template_variant_value_ids.filtered(
            lambda x: not x.ptav_active and x.attribute_line_id and x.name
        )
        _logger.info("Updating Variant from Old Product Template attribute value to New PTAV")
        for variant_value in variant_values:
            attribute_line_id = variant_value.attribute_line_id.id
            name = variant_value.name

            # Use JOIN instead of subquery
            query = """
                SELECT ptav.id
                FROM product_template_attribute_value ptav
                JOIN product_attribute_value pav 
                ON ptav.product_attribute_value_id = pav.id
                WHERE ptav.attribute_line_id = %s
                AND ptav.ptav_active = 't'
                AND pav.name ->> 'en_US' = %s
                AND pav.active = TRUE
                LIMIT 1;
            """
            cr.execute(query, (attribute_line_id, name))
            ptav_data = cr.fetchone()

            if ptav_data:
                unique_ptav_id = ptav_data[0]
                # Update product_variant_combination with correct ptav
                update_query = """
                    UPDATE product_variant_combination
                    SET product_template_attribute_value_id = %s
                    WHERE product_template_attribute_value_id = %s;
                """
                cr.execute(update_query, (unique_ptav_id, variant_value.id))
                cr.commit()

    # def setting_default_val(self):
    #     #======================OLD CODE ===============
    #     # IRProperty = self.env["ir.property"]
    #     # ResCompany = self.env["res.company"]
    #     # Field = self.env["ir.model.fields"]

    #     # # Fetch everything in bulk (fewer queries)
    #     # templates = self.env['product.template'].search([("has_configurable_attributes", "=", True)])
    #     # companies = ResCompany.search([("short_name", "in", ["eu", "us"])])
    #     # field = Field.search(
    #     #     [("model_id.model", "=", "product.template.attribute.line"),
    #     #      ("name", "=", "default_val")],
    #     #     limit=1
    #     # )
    #     # companies_ids= tuple(companies.ids)
    #     # if companies_ids:
    #     #     select_query = """
    #     #         SELECT id
    #     #         FROM ir_property 
    #     #         WHERE field_id = %s 
    #     #           AND company_id IN %s
    #     #     """
    #     #     self.env.cr.execute(select_query, (field.id, companies_ids))
    #     #     data = [row[0] for row in self.env.cr.fetchall()]

    #     #     # 2. Delete if found
    #     #     if data:
    #     #         unlink_query = "DELETE FROM ir_property WHERE id IN %s"
    #     #         self.env.cr.execute(unlink_query, (tuple(data),))
    #     #         self.env.cr.commit()


    #     # if not field or not companies:
    #     #     return  # nothing to do

    #     # vals_to_create = []

    #     # for template in templates:
    #     #     for line in template.attribute_line_ids:
    #     #         if line.required and line.value_ids and not line.default_val:
    #     #             default_val = line.value_ids[0]
    #     #             res_id = f"{line._name},{line.id}"
    #     #             value_reference = f"{default_val._name},{default_val.id}"

    #     #             for company in companies:
    #     #                 vals_to_create.append({
    #     #                     "name": "default_val",
    #     #                     "company_id": company.id,
    #     #                     "fields_id": field.id,
    #     #                     "res_id": res_id,
    #     #                     "value_reference": value_reference,
    #     #                 })

    #     # if vals_to_create:
    #     #     IRProperty.create(vals_to_create)
    #     #     self.env.cr.commit()
    #     #======================OLD CODE ===============

    #     # New Script Made on Sep 30 2025
    #     # Fetch Data from Version 13 and update it in veriosn 17 
    #     # v13 table name: temp_product_template_attribute_line_default_val_v13
    #     """ New Query
    #             -- Drop if exists
    #         DROP TABLE IF EXISTS temp_product_template_attribute_line_default_val_v13;

    #         -- Create table
    #         CREATE TABLE temp_product_template_attribute_line_default_val_v13 (
    #             line_id                    INT,
    #             attribute_id               INT,
    #             product_tmpl_id            INT,
    #             attribute_name             VARCHAR(255),
    #             value_id                   INT,
    #             value_attribute_id         INT,
    #             product_attribute_value_id INT,
    #             is_default                 BOOLEAN
    #         );

    #         -- Insert data
    #         INSERT INTO temp_product_template_attribute_line_default_val_v13 (
    #             line_id, attribute_id, product_tmpl_id, attribute_name,
    #             value_id, value_attribute_id, product_attribute_value_id, is_default
    #         )
    #         SELECT 
    #             ptal.id AS line_id,
    #             ptal.attribute_id,
    #             ptal.product_tmpl_id,
    #             pa.name AS attribute_name,
    #             ptav.id AS value_id,
    #             ptav.attribute_id AS value_attribute_id,
    #             ptav.product_attribute_value_id,
    #             ptav.is_default
    #         FROM product_template_attribute_line ptal
    #         JOIN product_attribute pa
    #                ON pa.id = ptal.attribute_id
    #         JOIN product_template_attribute_value ptav
    #                ON ptav.attribute_line_id = ptal.id
    #               AND ptav.ptav_active = 't'  
    #               AND ptav.is_default = 't'
    #         WHERE ptal.active = 't';


    #     """


    #     cr = self.env.cr
    #     AttributeValue = self.env["product.attribute.value"].with_context(prefetch_fields=False)
    #     AttributeLine = self.env["product.template.attribute.line"].sudo().with_context(prefetch_fields=False)
    #     IRProperty = self.env["ir.property"].with_context(prefetch_fields=False)
    #     ResCompany = self.env["res.company"].with_context(prefetch_fields=False)
    #     companies = ResCompany.search([("short_name", "in", ["eu", "us"])])
    #     Field = self.env["ir.model.fields"].with_context(prefetch_fields=False)
    #     field = Field.search(
    #         [("model_id.model", "=", "product.template.attribute.line"),
    #          ("name", "=", "default_val")],
    #         limit=1
    #     )

    #     companies_ids = tuple(companies.ids)
    #     if companies_ids:
    #         # Delete old property records in one go
    #         cr.execute("""
    #             DELETE FROM ir_property
    #             WHERE fields_id = %s 
    #               AND company_id IN %s
    #         """, (field.id, companies_ids))
    #         cr.commit()

    #     lines = AttributeLine.search([("active", "=", True)])

    #     # Removed ("required", "=", True)
    #     # From OSI-Odoo Ticket Ref: 69135 

    #     vals_lists = []
    #     company_ids = companies.ids  # cache once

    #     for line in lines:
    #         cr.execute("""
    #             SELECT product_attribute_value_id
    #             FROM temp_product_template_attribute_line_default_val_v13
    #             WHERE line_id = %s
    #             LIMIT 1;
    #         """, (line.id,))
    #         row = cr.fetchone()
    #         value_id = row[0] if row else False
    #         if not value_id:
    #             continue

    #         value = AttributeValue.browse(value_id)
            
    #         if not value.exists():
    #             continue

    #         tobe_update_value = value
    #         # 1. If line is required and value is active → keep value
    #         if line.required and value.active:
    #             tobe_update_value = value

    #         # 2. If line is required but value is NOT active → fetch active value with same name
    #         elif line.required and not value.active:
    #             cr.execute("""
    #                 SELECT id
    #                 FROM product_attribute_value
    #                 WHERE name->>'en_US' = %s
    #                 AND attribute_id = %s
    #                 AND active = TRUE
    #                 LIMIT 1
    #             """, (value.name, line.attribute_id.id))

    #             row = cr.fetchone()
    #             tobe_update_value = AttributeValue.browse(row[0]) if row else False

    #         # 3. Ticket Ref: 69135 If NOT required + current value is literal "None" → replace with first line default value
    #         elif not line.required and value.name == "None" and line.value_ids:
    #             tobe_update_value = line.value_ids[0]

    #         #_logger.info("tobe_update_value: %s records", tobe_update_value)
    #         if not tobe_update_value:
    #             continue

    #         default_val = tobe_update_value
    #         value_reference = f"{default_val._name},{default_val.id}"
    #         res_id = f"{line._name},{line.id}"

    #         # Create values for all companies at once (no loop inside)
    #         vals_lists.extend([
    #             {
    #                 "name": "default_val",
    #                 "company_id": cid,
    #                 "fields_id": field.id,
    #                 "res_id": res_id,
    #                 "value_reference": value_reference,
    #             }
    #             for cid in company_ids
    #         ])

    #     if vals_lists:
    #         IRProperty.sudo().create(vals_lists)
    #         _logger.info("Data Creation DONE:::: %s records", len(vals_lists))
    #         cr.commit()

    def setting_default_val(self):
        #======================OLD CODE ===============
        # IRProperty = self.env["ir.property"]
        # ResCompany = self.env["res.company"]
        # Field = self.env["ir.model.fields"]

        # # Fetch everything in bulk (fewer queries)
        # templates = self.env['product.template'].search([("has_configurable_attributes", "=", True)])
        # companies = ResCompany.search([("short_name", "in", ["eu", "us"])])
        # field = Field.search(
        #     [("model_id.model", "=", "product.template.attribute.line"),
        #      ("name", "=", "default_val")],
        #     limit=1
        # )
        # companies_ids= tuple(companies.ids)
        # if companies_ids:
        #     select_query = """
        #         SELECT id
        #         FROM ir_property 
        #         WHERE field_id = %s 
        #           AND company_id IN %s
        #     """
        #     self.env.cr.execute(select_query, (field.id, companies_ids))
        #     data = [row[0] for row in self.env.cr.fetchall()]

        #     # 2. Delete if found
        #     if data:
        #         unlink_query = "DELETE FROM ir_property WHERE id IN %s"
        #         self.env.cr.execute(unlink_query, (tuple(data),))
        #         self.env.cr.commit()


        # if not field or not companies:
        #     return  # nothing to do

        # vals_to_create = []

        # for template in templates:
        #     for line in template.attribute_line_ids:
        #         if line.required and line.value_ids and not line.default_val:
        #             default_val = line.value_ids[0]
        #             res_id = f"{line._name},{line.id}"
        #             value_reference = f"{default_val._name},{default_val.id}"

        #             for company in companies:
        #                 vals_to_create.append({
        #                     "name": "default_val",
        #                     "company_id": company.id,
        #                     "fields_id": field.id,
        #                     "res_id": res_id,
        #                     "value_reference": value_reference,
        #                 })

        # if vals_to_create:
        #     IRProperty.create(vals_to_create)
        #     self.env.cr.commit()
        #======================OLD CODE ===============

        # New Script Made on Sep 30 2025
        # Fetch Data from Version 13 and update it in veriosn 17 
        # v13 table name: temp_product_template_attribute_line_default_val_v13
        """ New Query
                -- Drop if exists
            DROP TABLE IF EXISTS temp_product_template_attribute_line_default_val_v13;

            -- Create table
            CREATE TABLE temp_product_template_attribute_line_default_val_v13 (
                line_id                    INT,
                attribute_id               INT,
                product_tmpl_id            INT,
                attribute_name             VARCHAR(255),
                value_id                   INT,
                value_attribute_id         INT,
                product_attribute_value_id INT,
                is_default                 BOOLEAN,
                company_id                 INT
            );

            -- Insert data
            INSERT INTO temp_product_template_attribute_line_default_val_v13 (
                line_id, attribute_id, product_tmpl_id, attribute_name,
                value_id, value_attribute_id, product_attribute_value_id, is_default,company_id
            )
            SELECT 
                ptal.id AS line_id,
                ptal.attribute_id,
                ptal.product_tmpl_id,
                pa.name AS attribute_name,
                ptav.id AS value_id,
                ptav.attribute_id AS value_attribute_id,
                ptav.product_attribute_value_id,
                ptav.is_default,
                ptav.company_id
            FROM product_template_attribute_line ptal
            JOIN product_attribute pa
                   ON pa.id = ptal.attribute_id
            JOIN product_template_attribute_value ptav
                   ON ptav.attribute_line_id = ptal.id
                  AND ptav.ptav_active = 't'  
                  AND ptav.is_default = 't'
            WHERE ptal.active = 't';
        """

        cr = self.env.cr
        AttributeValue = self.env["product.attribute.value"].with_context(prefetch_fields=False)
        AttributeLine = self.env["product.template.attribute.line"].sudo().with_context(prefetch_fields=False)
        IRProperty = self.env["ir.property"].with_context(prefetch_fields=False)
        ResCompany = self.env["res.company"].with_context(prefetch_fields=False)
        companies = ResCompany.search([("short_name", "in", ["eu", "us"])])
        Field = self.env["ir.model.fields"].with_context(prefetch_fields=False)
        field = Field.search(
            [("model_id.model", "=", "product.template.attribute.line"),
             ("name", "=", "default_val")],
            limit=1
        )

        companies_ids = tuple(companies.ids)
        if companies_ids:
            # Delete old property records in one go
            cr.execute("""
                DELETE FROM ir_property
                WHERE fields_id = %s 
                  AND company_id IN %s
            """, (field.id, companies_ids))
            cr.commit()

        lines = AttributeLine.search([("active", "=", True)])

        vals_lists = []
        exception_records = []     # 🔹 store failed records
        seen_keys = set()
        BATCH_SIZE = 1000

        for line in lines:
            cr.execute("""
                SELECT DISTINCT ON (company_id)
                    line_id,
                    product_attribute_value_id,
                    company_id
                FROM temp_product_template_attribute_line_default_val_v13
                WHERE line_id = %s ORDER BY company_id, product_attribute_value_id;
            """, (line.id,))
            rows = cr.fetchall()
            if not rows:
                continue
            for row in rows:
                try:
                    line_id = row[0]
                    value_id = row[1]
                    company_id = row[2]

                    value = AttributeValue.browse(value_id)
                    if not value.exists():
                        continue

                    tobe_update_value = value
                    if not value.active:
                        cr.execute("""
                            SELECT id
                            FROM product_attribute_value
                            WHERE name->>'en_US' = %s
                            AND attribute_id = %s
                            AND active = TRUE
                            LIMIT 1
                        """, (value.name, line.attribute_id.id))
                        r = cr.fetchone()
                        tobe_update_value = AttributeValue.browse(r[0]) if r else False

                    if tobe_update_value and tobe_update_value.name == "None" and line.value_ids:
                        tobe_update_value = line.value_ids[0]

                    if not tobe_update_value:
                        continue

                    default_val = tobe_update_value
                    value_reference = f"{default_val._name},{default_val.id}"
                    res_id = f"{line._name},{line.id}"
                    unique_key = (res_id, value_reference, company_id)

                    if unique_key in seen_keys:
                        continue

                    seen_keys.add(unique_key)

                    vals_lists.append({
                        "name": "default_val",
                        "company_id": company_id,
                        "fields_id": field.id,
                        "res_id": res_id,
                        "value_reference": value_reference,
                    })

                    # 🔹 Batch insert
                    if len(vals_lists) >= BATCH_SIZE:
                        IRProperty.sudo().create(vals_lists)
                        cr.commit()
                        _logger.info("Created batch of %s records", len(vals_lists))
                        vals_lists.clear()

                except Exception as e:
                    cr.rollback()
                    exception_records.append({
                        "line_id": line.id,
                        "product_tmpl_id": line.product_tmpl_id.id,
                        "value_id": value_id,
                        "company_id": company_id,
                        "error": str(e),
                    })

        # 🔹 Final remaining batch
        if vals_lists:
            IRProperty.sudo().create(vals_lists)
            cr.commit()
            _logger.info("Created final batch of %s records", len(vals_lists))

        _logger.info("PROCESS DONE")
        _logger.info("Total failed records: %s", exception_records)
    
    def update_ar_ap_followup_contacts(self):
        # task ref: https://osi.mavenlink.com/workspaces/44078089/#tracker/932728167
        # psql VERSION13DB
        # create table temp_res_partner_contact_type_v13 as select * from res_partner_contact_type;
        # pg_dump -d odoo13 -t temp_res_partner_contact_type_v13 > /home/odoo/temp_res_partner_contact_type_v13.sql;
        # psql -d 17.0.0.13.0 -f /home/odoo/temp_res_partner_contact_type_v13.sql

        cr = self.env.cr
        select_query = """
            SELECT contact_id, ar, ap, followup 
            FROM temp_res_partner_contact_type_v13;
        """
        cr.execute(select_query)
        datas = cr.fetchall()

        for contact_id, ar, ap, followup in datas:
            update_query = """
                UPDATE res_partner 
                SET ar = %s, ap = %s, followup = %s 
                WHERE id = %s;
            """
            cr.execute(update_query, (ar, ap, followup, contact_id))

        # Commit once after loop
        _logger.info("update_ar_ap_followup_contacts Script Completed")

        self.env.cr.commit()

    def update_phantoms_bom_data(self):
        batch_size = 10  # Define batch size
        ProductTemplates = self.env['product.template'].search([("has_configurable_attributes","=",True)])
        # --- Setup ---
        MrpBom = self.env["mrp.bom"]
        Company = self.env["res.company"].sudo()
        companies = Company.search([])
        total_products = len(ProductTemplates)  # Total number of products to process
        offset = 0
        counter = 1
        cr = self.env.cr
        _logger.info("Total products to process: %s", total_products)

        # =====================================================
        # STEP 1: Normalize company assignments and clean up
        # =====================================================

        # Clear company_id on phantom BoMs that belong to global products
        # (Only do this if both the BoM and product are intended to be global)
        cr.execute("""
            UPDATE mrp_bom
               SET company_id = NULL
             WHERE type = 'phantom'
               AND company_id IS NOT NULL
               AND product_tmpl_id IN (
                   SELECT id FROM product_template WHERE company_id IS NULL
               )
        """)

        # Clear company_id on phantom BoM lines linked to global BoMs/products
        cr.execute("""
            UPDATE mrp_bom_line
               SET company_id = NULL
             WHERE company_id IS NOT NULL
               AND bom_id IN (
                   SELECT b.id
                     FROM mrp_bom b
                     JOIN product_template pt ON b.product_tmpl_id = pt.id
                    WHERE b.type = 'phantom'
                      AND b.company_id IS NULL
                      AND pt.company_id IS NULL
               )
        """)
        cr.commit()

        # Archive phantom BoMs that have no lines
        empty_boms = MrpBom.search([
            ('type', '=', 'phantom'),
            ('bom_line_ids', '=', False),
            ('active', '=', True),
        ])
        if empty_boms:
            empty_boms.write({'active': False})
            cr.commit()

        # =====================================================
        # STEP 2: Process all products with phantom BoMs
        # - Deduplicate equivalent BoMs
        # - Ensure all companies point to the same master BoM
        # - Archive unused BoMs
        # =====================================================

        products = self.env["product.template"].search([
            ("bom_ids.type", "=", "phantom")
        ])

        def boms_are_equivalent(bom1, bom2):
            """Helper to check if two phantom BoMs are functionally equivalent."""
            if bom1.type != "phantom" or bom2.type != "phantom":
                return False
            if bom1.code and bom2.code and bom1.code != bom2.code:
                return False
            # Compare sorted (product_id, qty) tuples
            lines1 = sorted(
                [(l.product_id.id, l.product_qty) for l in bom1.bom_line_ids],
                key=lambda x: (x[0], x[1])
            )
            lines2 = sorted(
                [(l.product_id.id, l.product_qty) for l in bom2.bom_line_ids],
                key=lambda x: (x[0], x[1])
            )
            return lines1 == lines2
        for product in products:
            phantom_boms = self.env["mrp.bom"]
            master_bom = self.env["mrp.bom"]
            used_boms = self.env["mrp.bom"]

            # Collect phantom_bom_id across all companies
            for company in companies:
                phantom_bom = product.sudo().with_company(company).phantom_bom_id
                if phantom_bom:
                    phantom_boms |= phantom_bom
                    used_boms |= phantom_bom
            # Fetch all phantom BoMs for this product
            all_boms = MrpBom.search([
                ("product_tmpl_id", "=", product.id),
                ("type", "=", "phantom"),
            ])

            if phantom_boms:
                master_bom = phantom_boms[0]

            # Deduplicate equivalent phantom BoMs
            for bom in phantom_boms:
                if bom != master_bom and boms_are_equivalent(master_bom, bom):
                    bom.write({"active": False})
                    # Update phantom_bom_id references to master BoM
                    for company in companies:
                        if product.sudo().with_company(company).phantom_bom_id == bom:
                            product.sudo().with_company(company).write({
                                "phantom_bom_id": master_bom.id
                            })
            # Ensure all companies consistently point to master BoM
            for company in companies:
                if product.sudo().with_company(company).phantom_bom_id != master_bom:
                    product.sudo().with_company(company).write({
                        "phantom_bom_id": master_bom.id
                    })

            # Archive unused phantom BoMs not referenced by any company
            unused_boms = all_boms - used_boms
            if unused_boms:
                unused_boms.write({"active": False})
                cr.commit()

    def update_workcenter_mo(self):
        #TASK Ref: https://osi.mavenlink.com/workspaces/44078089/#tracker/928787261
        MrpBom = self.env["mrp.bom"]
        RoutingWorkcenter = self.env["mrp.routing.workcenter"]

        scaffolding_boms = MrpBom.search([("scaffolding_bom", "=", True),("type","=","normal")])

        # Try to fetch workcenters safely
        def safe_ref(xml_id):
            try:
                return self.env.ref(xml_id)
            except ValueError:
                return False

        test_workcenter = safe_ref("mrp_batch.import_test")
        build_workcenter = safe_ref("mrp_batch.import_build")
        box_workcenter = safe_ref("mrp_batch.import_box")
        workcenter_lines = []
        if all([test_workcenter, build_workcenter, box_workcenter]):
            for bom in scaffolding_boms:
                for wc in [test_workcenter, build_workcenter, box_workcenter]:
                    workcenter_lines.append({
                        "workcenter_id": wc.id,
                        "name": wc.name,
                        "type": wc.type,
                        "time_cycle_manual": 0.0,
                        "bom_id": bom.id,
                        "sequence": 10 if wc == test_workcenter else 20 if wc == build_workcenter else 30,
                    })

        if workcenter_lines:
            RoutingWorkcenter.create(workcenter_lines)
            _logger.info("\n\n============RoutingWorkcenter Done")


    def update_stock_inventory(self):
        # Task Ref: https://pm.opensourceintegrators.com/web#id=67417&menu_id=218&cids=1&action=1093&model=helpdesk.ticket&view_type=form
        #Queries
        # 1. create table temp_stock_inventory_vp13 as select * from stock_inventory;
        # 2. create table temp_product_product_stock_inventory_rel_vp13 as select * from product_product_stock_inventory_rel;
        # 3. create table temp_stock_inventory_stock_location_rel_vp13 as select * from temp_stock_inventory_stock_location_rel_vp13;
        # 4. create table temp_stock_move_vp13 as SELECT * FROM stock_move WHERE inventory_id IS NOT NULL;
        cr = self.env.cr

        # Fetch all rows from the temporary table
        cr.execute("""
            SELECT *
            FROM temp_stock_inventory_vp13
        """)
        records = cr.fetchall()
        columns = [desc[0] for desc in cr.description]
        # Convert query result into list of dictionaries
        result = [dict(zip(columns, row)) for row in records]

        
        counter = 0
        for rec in result:
            current_id = rec.get("id",False)  # or whatever your variable is for stock_inventory_id
            state_value = rec.get('state')
            product_selection = "all"
            name = rec.get('name') or ''
            if state_value == 'confirm':
                state_value = 'in_progress'

            cr.execute("""
                SELECT *
                FROM temp_product_product_stock_inventory_rel_vp13
                WHERE stock_inventory_id = %s
            """, (current_id,)) 
            records = cr.fetchall()
            columns = [desc[0] for desc in cr.description]
            # Convert query result into list of dictionaries
            result = [dict(zip(columns, row)) for row in records]
            if result and len(result) > 1:
                product_selection = "manual"
            if result and len(result) == 1:
                product_selection = "one"

            # Build INSERT SQL
            cr.execute("""
                INSERT INTO stock_inventory (
                    id, name, date, state, company_id, create_uid, write_uid, write_date, create_date,product_selection
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s,%s)
            """, (
                rec.get('id'),
                name,
                rec.get('date'),
                state_value,
                rec.get('company_id'),
                rec.get('create_uid'),
                rec.get('write_uid'),
                rec.get('write_date'),
                rec.get('create_date'),
                product_selection,
            ))

            cr.execute("""
                INSERT INTO product_product_stock_inventory_rel (stock_inventory_id, product_product_id)
                SELECT stock_inventory_id, product_product_id
                FROM temp_product_product_stock_inventory_rel_vp13
                WHERE stock_inventory_id = %s
            """, (current_id,))

            cr.execute("""
                INSERT INTO stock_inventory_stock_location_rel (stock_inventory_id, stock_location_id)
                SELECT stock_inventory_id, stock_location_id
                FROM temp_stock_inventory_stock_location_rel_vp13
                WHERE stock_inventory_id = %s
            """, (current_id,))
            cr.commit()
            cr.execute("""
                SELECT *
                FROM temp_stock_move_vp13
                WHERE inventory_id = %s
            """, (current_id,)) 
            move_records = cr.fetchall()
            columns = [desc[0] for desc in cr.description]
            # Convert query result into list of dictionaries
            move_result = [dict(zip(columns, row)) for row in move_records]
            for move in move_result:
                lines = self.env['stock.move.line'].search([('move_id','=',move.get("id"))])
                if lines:
                    lines.sudo().write({"inventory_adjustment_id":current_id})
        _logger.info("\n\n=update_stock_inventory Done")

    def update_credit_limit_data(self):
        """
            1. create table temp_res_partner_vp as SELECT id,terms_partner_id FROM res_partner WHERE terms_partner_id IS NOT NULL;
            2. pg_dump -d V13DBNAME -t temp_res_partner_vp > /home/odoo/temp_res_partner_vp.sql;
            3. psql -d V17DBNAME -f /home/odoo/temp_res_partner_vp.sql

            Task Ref: https://pm.opensourceintegrators.com/web#id=69054&cids=1&menu_id=218&action=1093&model=helpdesk.ticket&view_type=form
        """
        cr = self.env.cr
        cr.execute("""DELETE FROM ir_property WHERE name = 'credit_limit' AND res_id LIKE 'res.partner,%';""")

        # 1️⃣ UPDATE the partners
        cr.execute("""
            UPDATE res_partner AS rs
            SET  partner_rollup_id = tres.terms_partner_id
            FROM temp_res_partner_vp AS tres
            WHERE tres.id = rs.id;
        """)

        # 2️⃣ FETCH updated ids
        cr.execute("""
            SELECT tres.id
            FROM temp_res_partner_vp AS tres
            JOIN res_partner AS rs ON rs.id = tres.id
        """)
        ids = [row[0] for row in cr.fetchall()]

        # 3️⃣ PROCESS each partner
        Partner = self.env["res.partner"].sudo()   # performance + avoids access errors
        select_query = """SELECT value_float,res_id,company_id from temp_ir_property_v13_vp where name='credit_limit';"""
        cr.execute(select_query)
        v13datas = cr.fetchall()
        field = self.env["ir.model.fields"].search(
            [
                ("model_id.model", "=", "res.partner"),
                ("name", "=", "credit_limit"),
            ]
        )
        credit_limit_property_vals = []
        for data in v13datas:
            partner = data[1].split(",")[1]
            partner_id = Partner.browse(int(partner))
            if field and partner_id.exists():
                credit_limit_property_vals.append(
                    {
                        "name": "credit_limit",
                        'type':'float',
                        "company_id": int(data[2]),
                        "fields_id": field.id,
                        "res_id": data[1],
                        "value_float": data[0],
                    }
                )

        self.env["ir.property"].sudo().create(credit_limit_property_vals)
        _logger.info("Credit limit property data created.")


        for partner_id in ids:
            partner = Partner.browse(partner_id)

            if not partner.exists():
                continue

            partner.with_delay()._compute_outstanding_receivable()
            partner.with_delay()._compute_credit_hold()
            partner.with_delay()._compute_open_so_balance()
            partner.with_delay()._compute_remaining_credit()
            partner.with_delay()._compute_customer_deposit_balance()
            partner.with_delay()._compute_open_bo_balance()

            _logger.info("Updated partner ID: %s", partner_id)
    
    def drop_temp_tables(self):
        cr = self.env.cr
        _logger.info("\n\n============Droping Tables Start")
        cr.execute("DROP TABLE IF EXISTS temp_ir_property_v13_vp;")
        cr.execute("DROP TABLE IF EXISTS temp_product_temp_v13_vp;")
        cr.execute("DROP TABLE IF EXISTS temp_product_template_res_company_rel_v13_vp;")
        cr.execute("DROP TABLE IF EXISTS temp_product_template_attribute_value_v13_vp;")
        cr.execute("DROP TABLE IF EXISTS temp_ir_property_inbound_shipping_method;")
        cr.execute("DROP TABLE IF EXISTS temp_ir_property;")
        cr.execute("DROP TABLE IF EXISTS temp_res_users;")
        cr.execute("DROP TABLE IF EXISTS temp_product_attribute_value_v13;")
        cr.execute("DROP TABLE IF EXISTS temp_stock_inventory_vp13;")
        cr.execute("DROP TABLE IF EXISTS temp_product_product_stock_inventory_rel_vp13;")
        cr.execute("DROP TABLE IF EXISTS temp_stock_inventory_stock_location_rel_vp13;")
        cr.execute("DROP TABLE IF EXISTS temp_stock_move_vp13;")
        cr.execute("DROP TABLE IF EXISTS temp_ir_property_row_rack_case;")
        cr.execute("DROP TABLE IF EXISTS temp_res_partner_vp;")
        
        _logger.info("\n\n============Tables Droped")