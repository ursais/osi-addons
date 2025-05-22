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
            _logger.info("\n\n==================Attribute ID==================%s",attribute_id)
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
                _logger.info("\n\n==================Attribute ID===pav_select_query===============%s",pav)
                
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
        attribute_dict = {attribute.name: attribute.id for attribute in self.env["product.attribute"].search([("active", "=", True)])}
        lines_to_update = templateAttributteLine.filtered(lambda line: line.product_tmpl_id.active and not line.attribute_id.active)
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
        active_attribute_dict = {attribute.name: attribute.id for attribute in self.env["product.attribute"].search([("active", "=", True)])}
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

        _logger.info("\n\n===Recompute for unique attributes===")

        for attribute_id in attributes_to_recompute:
            active_attribute = self.env["product.attribute"].browse(attribute_id)
            active_attribute._compute_products()  # Only recompute for unique attributes

        _logger.info("\n\n===ProductTemplateAttributeValue Done===%s",len(templateAttributteValue))

        #Template Value_ids M2M Relation name: product_attribute_value_product_template_attribute_line_rel
        template_attribute_line_rel_query = """SELECT product_attribute_value_id FROM product_attribute_value_product_template_attribute_line_rel;"""
        cr.execute(template_attribute_line_rel_query)
        line_rel_ids = cr.fetchall()
        ProductAttributeValue = self.env["product.attribute.value"]


        # templateAttributeValue = ProductTemplateAttributeValue.search([("ptav_active", "=", True)])
        templateAttributeValue = ProductTemplateAttributeValue.browse(templateAttributteValue)

        attribute_line_ids = templateAttributeValue.mapped("attribute_line_id").ids
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
            for product_template in batch_products:
                _logger.info("\n\n\n\n===============product_template##########%s==ID:::%s:::Counter::%s",product_template.name,product_template,counter)
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
                    if line_values:
                        value_with_none = line_values.filtered(lambda ptav: ptav.name == 'None')
                        value_with_non_none = line_values.filtered(lambda ptav: ptav.name != 'None')
                        if value_with_none:
                            # Update default value using SQL
                            cr.execute("""
                                UPDATE product_template_attribute_line
                                SET default_val = %s
                                WHERE id = %s;
                            """, (value_with_none[0].id, line.id))
                            cr.commit()
                        
                        else:
                            cr.execute("""
                                UPDATE product_template_attribute_line
                                SET default_val = %s
                                WHERE id = %s;
                            """, (value_with_non_none[0].id, line.id))
                            cr.commit()
                counter += 1
            offset += batch_size
            self.env.cr.commit()  # Commit changes after processing each batch
            _logger.info("Batch processed. Offset moved to %s", offset)
        _logger.info("Processing completed!")
        _logger.info("\n\n==================Script 3 is Done==================")

    def script_4(self):
        _logger.info("\n\n==Sync Attribute Values in Product Variants===Script 4 is start==================")
        batch_size = 10  # Define batch size
        #PRODUCT-TEMPLATE ID Which id Need to take care [5593,24607,5172,32379,24337,25216,26588,6518,4696,103791,102630,102736,101999]
        ProductTemplates = self.env['product.template'].search([("has_configurable_attributes","=",True),("id","not in",[5593,24607,5172,32379,24337,25216,26588,6518,4696,103791,102630,102736,101999])])
        total_products = len(ProductTemplates)  # Total number of products to process
        offset = 0
        counter = 1
        cr = self.env.cr
        _logger.info("Total products to process: %s", total_products)
        while offset < total_products:
            batch_products = ProductTemplates[offset:offset + batch_size]  # Slice the records to get the current batch
            _logger.info("Processing batch: Offset %s, Batch Size %s", offset, len(batch_products))
            for product_template in batch_products:
                _logger.info("\n\n\n\n===============product_template##########%s==ID:::%s:::Counter::%s",product_template.name,product_template,counter)
                config_step_id = product_template.config_step_line_ids.filtered(lambda l:l.config_step_id and not l.attribute_line_ids)
                config_step_id.unlink()
                cr.commit()
                for attrbute_line_id in product_template.mapped("attribute_line_ids").filtered("active"):
                    if (attrbute_line_id.value_ids and (not attrbute_line_id.default_val or not attrbute_line_id.default_val.active)):
                        cr.execute("""
                            UPDATE product_template_attribute_line
                            SET default_val = %s
                            WHERE id = %s;
                        """, (attrbute_line_id.value_ids[0].id, attrbute_line_id.id))
                        cr.commit()
                    if attrbute_line_id.attribute_id.active:
                        values_ids = attrbute_line_id.value_ids.filtered(lambda l:l.active and l.attribute_id.id != attrbute_line_id.attribute_id.id)
                        product_template_value_ids = attrbute_line_id.product_template_value_ids.filtered("ptav_active")
                        for value in values_ids:
                            active_value_id = self.env["product.attribute.value"].search([("name","=",value.name),("active","=",True),("attribute_id","=",value.attribute_id.id)])
                            if not active_value_id.attribute_id.active and value.name not in attrbute_line_id.attribute_id.value_ids.mapped("name"):
                                _logger.info("\n\n\n\n==============Values IDS:Name:%s:%s:%s:%s:active_value_id::%s",value.name,value,attrbute_line_id.attribute_id,value.attribute_id,active_value_id.attribute_id.active)
                                update_query = """UPDATE product_attribute_value SET active = TRUE,attribute_id = %s WHERE id =%s;"""
                                cr.execute(update_query,(attrbute_line_id.attribute_id.id,value.id))
                                cr.commit()
                                
                        for ptav_line in product_template_value_ids:
                            if ptav_line.attribute_id != attrbute_line_id.attribute_id:
                                _logger.info("\n\n\n\n==============PTAV==Values IDS::%s::%s::%s",ptav_line.attribute_id,attrbute_line_id.attribute_id, attrbute_line_id.attribute_id.name)
                                cr.execute("""
                                        UPDATE product_template_attribute_value
                                        SET attribute_id = %s
                                        WHERE id = %s AND ptav_active = true;
                                    """, (attrbute_line_id.attribute_id.id,ptav_line.id))
                                cr.commit()
                            if not ptav_line.product_attribute_value_id.active:
                                
                                active_value_id = attrbute_line_id.value_ids.filtered(lambda v:v.name == ptav_line.product_attribute_value_id.name )
                                _logger.info("\n\n\n\n==============PTAV==Values ID:%s==%s:%s::%s",ptav_line.product_attribute_value_id.name,attrbute_line_id.attribute_id.name,ptav_line.product_attribute_value_id,active_value_id)
                                cr.execute("""
                                        UPDATE product_template_attribute_value
                                        SET product_attribute_value_id = %s
                                        WHERE id = %s AND ptav_active = true;
                                    """, (active_value_id.id,ptav_line.id))
                                cr.commit()
                            if ptav_line.product_attribute_value_id.active and ptav_line.product_attribute_value_id.id not in attrbute_line_id.value_ids.ids:
                                _logger.info("\n\n\n\n========2322======PTAV==Values ID%s==%s",ptav_line.product_attribute_value_id.name,attrbute_line_id.attribute_id.name)
                            
                            if ptav_line.attribute_line_id.is_qty_required:
                                # _logger.info("\n\n\n\n======3333========PTAV==%s",ptav_line.product_attribute_value_id.name)
                                for qty_val in ptav_line.attribute_value_qty_ids:
                                    if qty_val.product_attribute_id.id != ptav_line.attribute_id.id:
                                        _logger.info("\n\n\n\n======3333========PTAV==%s",ptav_line.product_attribute_value_id.name)
                                        cr.execute("""
                                            UPDATE attribute_value_qty
                                            SET product_attribute_id = %s
                                            WHERE id = %s;
                                        """, (ptav_line.attribute_id.id,qty_val.id))
                                        cr.commit()
                                    if qty_val.product_attribute_value_id.id !=  ptav_line.product_attribute_value_id.id:
                                        _logger.info("\n\n\n\n======3333========PTAV==%s",ptav_line.product_attribute_value_id.name)
                                        cr.execute("""
                                            UPDATE attribute_value_qty
                                            SET product_attribute_value_id = %s
                                            WHERE id = %s;
                                        """, (ptav_line.product_attribute_value_id.id,qty_val.id))
                                        cr.commit()
                                        
                        #TODO VANDAN: 24/04/2025
                        # if len(values_ids.ids) != len(product_template_value_ids.ids):
                        #     less_lines = len(values_ids.ids) >= len(product_template_value_ids.ids)
                        #     less_value_ids = len(values_ids.ids) <= len(product_template_value_ids.ids)
                        #     if less_lines:
                        #         missing_attributes = set(values_ids.mapped("name")) - set(product_template_value_ids.mapped("product_attribute_value_id.name"))
                        #         _logger.info("\n\n\n\n===Missing Attribute Found at Less Line %s(%s) at Product Template missing Values names %s and Attribute %s",product_template.name,product_template,list(missing_attributes),attrbute_line_id.attribute_id.name)
                                
                        #     if less_value_ids:
                        #         missing_attributes = set(values_ids.mapped("name")) - set(product_template_value_ids.mapped("product_attribute_value_id.name"))
                        #         _logger.info("\n\n\n\n===Missing Attribute Found at Less Value IDS %s(%s) at Product Template missing Values names %s and Attribute %s",product_template.name,product_template,list(missing_attributes),attrbute_line_id.attribute_id.name)
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
                _logger.info("\n\n\n\n===============product_template##########%s==ID:::%s:::Counter::%s",pro_template.name,pro_template,counter)
                for attrbute_line_id in pro_template.mapped("attribute_line_ids"):
                    v13_data_select = "select id,attribute_id ,attribute_line_id,product_attribute_value_id,default_qty,maximum_qty  from product_template_attribute_value_V13_VP where product_tmpl_id = %s and attribute_line_id = %s and ptav_active = 't' and default_qty >=1 and maximum_qty >1;" 
                    cr.execute(v13_data_select, (pro_template.id,attrbute_line_id.id),)
                    v13_datas = cr.fetchall()
                    if attrbute_line_id.value_ids and (not attrbute_line_id.default_val or not attrbute_line_id.default_val.active):
                        cr.execute("""
                            UPDATE product_template_attribute_line
                            SET default_val = %s
                            WHERE id = %s;
                        """, (attrbute_line_id.value_ids[0].id, attrbute_line_id.id))
                        cr.commit()
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
        _logger.info("\n\n== Generate Scaffolding BOM==Script 6 is start==================")
        batch_size = 10  # Define batch size
        ProductTemplates = self.env['product.template'].search([("has_configurable_attributes","=",True)])
        total_products = len(ProductTemplates)  # Total number of products to process
        offset = 0
        counter = 1
        cr = .self.env.cr  # Cursor for direct SQL operations
        _logger.info("Total products to process: %s", total_products)
        while offset < total_products:
            batch_products = ProductTemplates[offset:offset + batch_size]  # Slice the records to get the current batch
            _logger.info("Processing batch: Offset %s, Batch Size %s", offset, len(batch_products))
            for product_template in batch_products:
                _logger.info("\n\n\n\n==1==SCAFFOLD BOM CREATION Start for Product####%s==ID:::%s:::Counter::%s", 
                             product_template.name, product_template.id, counter)
                # Check for existing scaffold BOMs
                existing_scaffold_bom_query = """SELECT id FROM mrp_bom WHERE scaffolding_bom = true AND product_tmpl_id = %s"""
                cr.execute(existing_scaffold_bom_query, (product_template.id,))
                existing_scaffold_bom = cr.fetchall() 
                if not existing_scaffold_bom:
                    # Find all attribute lines related to the product template
                    attribute_lines = self.env['product.template.attribute.line'].search([('product_tmpl_id', '=', product_template.id)])
                    # Create a Bill of Materials for the product template
                    bom_vals = {
                        'product_tmpl_id': product_template.id,
                        'product_qty': 1.0,
                        'type': 'normal',  # Adjust type if needed
                        'scaffolding_bom': True,
                    }
                    new_bom = self.env['mrp.bom'].create(bom_vals)
                    _logger.info("\n\n\n\n==3==New BOM Creation Done::%s", new_bom)            
                    # Add BoM lines for each product associated with the attribute values
                    for line in attribute_lines:
                        attribute_values = line.value_ids
                        for value in attribute_values:
                            product = value.product_id
                            if product:
                                # Attempt to find or create a configuration set
                                bom_line_config_set = self.env['mrp.bom.line.configuration.set'].search(
                                    [("name", "=", product.display_name)], limit=1
                                )
                                if not bom_line_config_set:
                                    bom_line_config_set = self.env['mrp.bom.line.configuration.set'].create({"name": product.display_name})                        
                                # Ensure value_ids is a list of IDs
                                value_ids = [(6, 0, [value.id])] if value else []
                                select_query = """select * from mrp_bom_line_configuration_product_attribute_value_rel where product_attribute_value_id = %s"""
                                cr.execute(select_query, (value.id,))
                                value_new = cr.fetchall()
                                if not value_new:
                                    self.env['mrp.bom.line.configuration'].create(
                                        {
                                            "config_set_id": bom_line_config_set.id,
                                            "value_ids": value_ids,
                                        }
                                    )                        
                                bom_line_vals = {
                                    'bom_id': new_bom.id,
                                    'product_id': product.id,
                                    'product_qty': 1.0,
                                    "config_set_id": bom_line_config_set.id,
                                }
                                self.env['mrp.bom.line'].create(bom_line_vals)            
                    _logger.info("\n\n\n\n==4==SCAFFOLD BOM CREATION PROCESS Done::%s for Product Template", product_template.name)
                counter += 1    
            offset += batch_size
            self.env.cr.commit()  # Commit changes after processing each batch
            _logger.info("Batch processed. Offset moved to %s", offset)
        _logger.info("Processing completed!")
        _logger.info("\n\n==================Script 6 is End==================")

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


        _logger.info("\n\n==Script 8: Phantom BOM Migration=")
        cr = self.env.cr
        select_query = """SELECT res_id,value_reference,company_id from temp_ir_property_v13_vp where name = 'phantom_bom_id';
         """
        cr.execute(select_query)
        phantom_bom_ids = cr.fetchall()
        product_to_exclude = []
        counter = 0
        for phantom_bom in phantom_bom_ids:
            product_template_id = phantom_bom[0].split(',')[1]
            mrp_bom_id = phantom_bom[1].split(',')[1]
            company_id = phantom_bom[2]
            counter+=1
            if int(company_id) == 1:
                phantom_bom_id = self.env["mrp.bom"].search([("id","=",int(mrp_bom_id)),("product_tmpl_id","=",int(product_template_id)),("type","=","phantom"),("company_id","=",int(company_id))])
                extra_phantom_bom_ids = self.env["mrp.bom"].search([("id","!=",phantom_bom_id.id),("product_tmpl_id","=",int(product_template_id)),("type","=","phantom"),("company_id","=",int(company_id))])
                product_to_exclude.append(int(product_template_id))
                extra_phantom_bom_ids.write({"active":False})
                cr.commit()
            elif int(company_id) == 2 and int(product_template_id) not in product_to_exclude:
                phantom_bom_id = self.env["mrp.bom"].search([("id","=",int(mrp_bom_id)),("product_tmpl_id","=",int(product_template_id)),("type","=","phantom"),("company_id","=",int(company_id))])
                extra_phantom_bom_ids = self.env["mrp.bom"].search([("id","!=",phantom_bom_id.id),("product_tmpl_id","=",int(product_template_id)),("type","=","phantom"),("company_id","=",int(company_id))])
                extra_phantom_bom_ids.write({"active":False})
                cr.commit()
                
        _logger.info("\n\n==Script 8: Lifecycle_status  Migration Data=")
        cr.execute("select res_id,value_text from temp_ir_property_v13_vp where name = 'lifecycle_status';")
        lifecycle_status = cr.fetchall()
        for lifecycle in lifecycle_status:
            _logger.info("\n\n\n\n===============lifecycle%s",lifecycle)
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

        _logger.info("\n\n==Script 8:Pim_category Migration Data=")
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

        _logger.info("\n\n==Script 8:Public_destination Migration=")
        cr.execute("update product_template as pt set public_destination = (select tpt.public_destination from temp_product_temp_v13_vp as tpt where tpt.id=pt.id); ")
        
        _logger.info("\n\n==Script 8:Company IDS Many2Many Product Template Migration=")
        cr.execute("INSERT INTO product_template_company_display_rel (product_template_id, company_id) SELECT product_template_id, res_company_id FROM temp_product_template_res_company_rel_v13_VP;")

        AttributeValues = self.env["product.attribute.value"].search([("active","=",True),("product_id","!=",False)])
        AttributeValues._compute_company_ids()

        _logger.info("\n\n==Script 8:country_of_manufacture in Product Template Migration=")
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
        _logger.info("\n\n\n\n=================DONE=======")
        _logger.info("\n\n==================Script 8 is Done==================")



    def drop_temp_tables(self):
        _logger.info("\n\n============Droping Tables Start")
        cr.execute("drop table temp_ir_property_v13_vp;")
        cr.execute("drop table temp_product_temp_v13_vp;")
        cr.execute("drop table temp_product_template_res_company_rel_v13_VP;")
        _logger.info("\n\n============Tables Droped")