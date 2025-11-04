# OnLogic Migration Scripts - Comprehensive Documentation

## Overview
This document provides comprehensive documentation for all migration scripts in the `osi_ol_decryption/models` directory. These scripts handle critical data migration operations during the OnLogic Odoo migration, including data decryption, partner merging, product attribute consolidation, and various data transformations.

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [File Structure](#file-structure)
3. [Script Interconnections](#script-interconnections)
4. [Detailed Function Documentation](#detailed-function-documentation)
5. [Data Flow Diagrams](#data-flow-diagrams)
6. [Dependencies and Prerequisites](#dependencies-and-prerequisites)

---

## Architecture Overview

The migration scripts are organized into four main files, each handling specific migration aspects:

- **ir_server_action.py**: Data decryption operations (encrypted fields)
- **ir_server_action_1.py**: Business logic migrations (RMA, stock, inspections, etc.)
- **ir_server_action_2.py**: Product attribute consolidation and cleanup
- **base_partner_merge.py**: Partner record deduplication and merging

All scripts inherit from `ir.actions.server` model, allowing them to be executed as Odoo server actions.

---

## File Structure

### ir_server_action.py
**Purpose**: Handles decryption of encrypted database fields using PostgreSQL pgcrypto extension.

**Functions**:
- `decrypt_char_field()` - Decrypts character/text fields
- `decrypt_number_field()` - Decrypts numeric fields
- `decrypt_json_field()` - Decrypts JSONB fields

### ir_server_action_1.py
**Purpose**: Handles various business logic migrations including RMA, stock transfers, inspections, and configuration.

**Functions**:
- `migrate_helpdesk_rma_to_ticket()` - Migrates RMA records to helpdesk tickets
- `update_inspections()` - Updates sale order inspections
- `tranfer_stock()` - Transfers stock between locations
- `split_mo()` - Splits manufacturing orders
- `set_timezones()` - Updates timezone mappings
- `clear_analytic_account_refs()` - Clears analytic account references
- `update_cost_center_distribution()` - Migrates cost centers to analytic accounts
- `recompute_tax_id_on_contacts()` - Recomputes tax IDs on contact records
- `update_saleorder_substate()` - Updates sale order substates
- `configure_account_sepa_direct_debit()` - Configures SEPA direct debit
- `create_onlogic_locations_and_route()` - Creates stock locations and routes

### ir_server_action_2.py
**Purpose**: Handles product attribute consolidation, deduplication, and synchronization.

**Functions**:
- `script_1()` - Cleans up duplicate attributes and values
- `script_2()` - Merges unique attribute values into single attributes
- `script_3()` - Updates product templates with unique attributes
- `script_4()` - Synchronizes attribute values in product variants

### base_partner_merge.py
**Purpose**: Extends Odoo's partner merge functionality with custom reference field updates.

**Functions**:
- `_update_reference_fields()` - Updates reference fields during partner merge
- `merge_partner_data()` - Merges partners based on rollup_customer_id

---

## Script Interconnections

### Execution Order Dependencies

```
1. Decryption Scripts (ir_server_action.py)
   ├── decrypt_char_field() [First - decrypts text data]
   ├── decrypt_number_field() [Second - decrypts numeric data]
   └── decrypt_json_field() [Third - decrypts JSON data]
   
2. Business Logic Migrations (ir_server_action_1.py)
   ├── set_timezones() [Early - fixes timezone issues]
   ├── clear_analytic_account_refs() [Before cost center migration]
   ├── update_cost_center_distribution() [After clearing refs]
   ├── migrate_helpdesk_rma_to_ticket() [Independent]
   ├── update_inspections() [Independent]
   ├── tranfer_stock() [Independent]
   ├── split_mo() [Independent]
   ├── recompute_tax_id_on_contacts() [Independent]
   ├── update_saleorder_substate() [Independent]
   ├── configure_account_sepa_direct_debit() [Independent]
   └── create_onlogic_locations_and_route() [Independent]
   
3. Partner Merging (base_partner_merge.py)
   └── merge_partner_data() [Can run after decryption]

4. Product Attribute Migration (ir_server_action_2.py)
   ├── script_1() [First - cleanup duplicates]
   ├── script_2() [Second - merge attributes]
   ├── script_3() [Third - update templates]
   └── script_4() [Fourth - sync variants]
```

### Data Flow Relationships

- **Decryption → Business Logic**: Decrypted data is used by business logic migrations
- **Partner Merge → Product Attributes**: Merged partners may affect product ownership
- **Attribute Scripts**: Sequential execution required (script_1 → script_2 → script_3 → script_4)

---

## Detailed Function Documentation

### ir_server_action.py

#### decrypt_char_field(all_data=False)
**Purpose**: Decrypts encrypted character/text fields across all database tables using PostgreSQL pgcrypto.

**Process Flow**:
1. Reads decryption key from `/home/odoo/decryption.txt`
2. Creates pgcrypto extension if not exists
3. Queries information_schema to find all character/text columns
4. Filters columns based on:
   - Field type: character varying, character, text, "char", name
   - Field length: > 64 characters or NULL
   - Excludes: ir_*, mail_*, report_* tables
   - Excludes specific tables and columns
5. For each table/column combination:
   - Validates table and column existence
   - Processes records in batches (default 100,000, project_task: 10,000)
   - For each record:
     - Checks if data starts with `\xc30` (encrypted marker)
     - Validates data integrity (skips corrupted records)
     - Uses `pgp_sym_decrypt()` to decrypt field
     - Updates record with decrypted value
   - Commits changes per table

**Key Features**:
- Batch processing for large tables
- Corruption detection (checks for HTML tags, special characters)
- Progress logging every 100k records
- Special handling for account_move_line (offset: 7,400,000)

**Parameters**:
- `all_data` (bool): If True, processes only non-decrypted data

**Dependencies**:
- PostgreSQL pgcrypto extension
- Decryption key file: `/home/odoo/decryption.txt`

---

#### decrypt_number_field()
**Purpose**: Decrypts encrypted numeric fields by dividing stored values by 5 (encryption multiplier).

**Process Flow**:
1. Queries information_schema to find numeric columns (double precision, numeric)
2. Filters columns based on:
   - Excludes: ir_*, specific tables
   - Special handling for dyn_saleorderlines (only sales_price column)
3. For each table/column:
   - Validates column existence
   - Checks `ir_model.is_decimal_encryption` flag
   - Skips if already decrypted
   - Processes all records:
     - Divides numeric values by 5
     - Updates records one-by-one (with commit per record)
   - Sets `is_decimal_encryption = false` after completion

**Key Features**:
- Uses `ir_model.is_decimal_encryption` flag to track progress
- Processes one record at a time (with commit)
- Error handling with logging

**Note**: This function processes records individually rather than in batches, which may be slow for large tables.

---

#### decrypt_json_field()
**Purpose**: Decrypts encrypted JSONB fields containing JSON data.

**Process Flow**:
1. Reads decryption key from `/home/odoo/decryption.txt`
2. Creates pgcrypto extension if not exists
3. Queries information_schema to find JSONB columns
4. Filters similar to `decrypt_char_field()`:
   - Only JSONB data type
   - Excludes transient models
   - Excludes specific tables and columns starting with 'analytic%'
5. For each table/column:
   - Validates existence
   - Processes records:
     - Extracts `en_US` key from JSON
     - Checks for encryption marker (`\xc30`)
     - Validates data integrity
     - Decrypts using pgcrypto
     - Updates JSON with decrypted value

**Key Features**:
- Handles JSON structure (`{"en_US": "encrypted_value"}`)
- Similar corruption detection as char fields
- Processes all records at once (no batching)

---

### ir_server_action_1.py

#### migrate_helpdesk_rma_to_ticket()
**Purpose**: Migrates RMA (Return Merchandise Authorization) records from legacy `helpdesk_rma` table to new `helpdesk.ticket` model.

**Process Flow**:
1. Gets reference to helpdesk teams (US and EU)
2. Queries all RMA records from `helpdesk_rma` table
3. For each RMA:
   - Maps RMA state to helpdesk ticket stage
   - Finds related RMA lines from `temp_helpdesk_rma_line`
   - Finds historical repair orders from `temp_support_repair_order`
   - Creates helpdesk ticket with mapped fields:
     - State → Stage mapping
     - Rush flag → Priority (2 if rush, 0 otherwise)
     - Links sale order, partner, repair orders
   - Updates repair orders with ticket_id
   - Updates stock lot warranty expiration if single repair order
4. Commits every 10,000 records

**State Mapping**:
- `new` → `helpdesk_stage_rma_requested`
- `accepted` → `helpdesk_stage_rma_accepted`
- `in_progress` → `helpdesk_stage_rma_in_progress`
- `resolved` → `helpdesk_stage_rma_resolved`
- `cancelled` → `helpdesk_stage_rma_cancelled`

**Dependencies**:
- Temporary tables: `temp_helpdesk_rma_line`, `temp_support_repair_order`
- Helpdesk teams: `ol_helpdesk_repair_batch.helpdesk_team_customer_rma`

---

#### update_inspections()
**Purpose**: Migrates sale order workflow holds to inspection records.

**Process Flow**:
1. Finds inspection records by name:
   - Finance Manual Exception (check_id: 55, 69)
   - Do Not Build (check_id: 63)
   - Do Not Ship (check_id: 72)
2. Queries `temp_sale_workflow_hold` for each check_id
3. Creates many-to-many relationships in `sale_order_sale_order_inspection_rel`
4. For other checks:
   - Finds matching inspection by name
   - Creates relationships for all related sale orders

**Note**: Uses `ON CONFLICT DO NOTHING` to avoid duplicates.

---

#### tranfer_stock()
**Purpose**: Transfers stock from old locations to new locations based on property data.

**Process Flow**:
1. Finds stock quants in locations 12 and 72
2. For each quant:
   - Queries `temp_ir_property_v13_vp` for location properties:
     - `loc_row`, `loc_rack`, `loc_case`
   - Builds location name: `"{loc_row} {loc_rack} {loc_case}"`
   - Finds new location by name
   - Creates internal transfer picking:
     - Source: current location
     - Destination: new location
     - Quantity: quant quantity
   - Assigns and validates transfer
   - Handles package IDs if present

**Dependencies**:
- Temporary table: `temp_ir_property_v13_vp`
- Stock picking types: Internal Transfers (US/EU)

---

#### split_mo()
**Purpose**: Splits manufacturing orders with quantity > 1.

**Process Flow**:
1. Finds all MOs with state='confirmed' and product_qty > 1
2. Orders by product_qty (ascending)
3. For each MO:
   - Calls `sale_order_id.split_mo()` with delay (async)

**Note**: Uses Odoo's delay mechanism for async processing.

---

#### set_timezones()
**Purpose**: Updates legacy US timezone names to PostgreSQL-compatible names.

**Process Flow**:
1. Maps old timezone names to new:
   - `US/Eastern` → `America/New_York`
   - `US/Central` → `America/Chicago`
   - `US/Mountain` → `America/Denver`
   - `US/Pacific` → `America/Los_Angeles`
2. Updates `res_partner.tz` field for all partners

**Reason**: PostgreSQL doesn't recognize `US/XXXX` format, requires `America/XXXX`.

---

#### clear_analytic_account_refs()
**Purpose**: Clears all references to analytic accounts before migration.

**Process Flow**:
1. Finds all many2one fields referencing `account.analytic.account`
2. Sets all foreign key references to NULL
3. Deletes all many2many relationship records
4. Deletes all analytic account records

**Dependencies**: Run before `update_cost_center_distribution()`.

---

#### update_cost_center_distribution()
**Purpose**: Migrates cost centers to analytic distribution format.

**Process Flow**:
1. Calls `clear_analytic_account_refs()` to clear existing data
2. Imports analytic plan from CSV: `osi_ol_decryption/data/account.analytic.plan.csv`
3. Imports analytic accounts from CSV: `osi_ol_decryption/data/account.analytic.account.csv`
4. Maps cost center IDs to analytic account names:
   - Cost center 1 → Account "11000"
   - Cost center 2 → Account "12000"
   - etc.
5. Updates `account_move_line.analytic_distribution`:
   - Creates JSONB object: `{analytic_account_id: 100.0}`
   - Sets 100% distribution for matching cost_center_id

**Dependencies**:
- CSV files: `account.analytic.plan.csv`, `account.analytic.account.csv`
- Requires `clear_analytic_account_refs()` to run first

---

#### recompute_tax_id_on_contacts()
**Purpose**: Copies VAT number from parent/commercial partner to contacts.

**Process Flow**:
1. Finds all active contacts (is_company=False)
2. For each contact:
   - Traverses up parent hierarchy to find company
   - Gets VAT from parent company
   - If no parent VAT, gets from commercial_partner_id
   - Updates contact VAT if different

**Note**: Processes contacts individually with commit per record.

---

#### update_saleorder_substate()
**Purpose**: Updates sale order substates based on detailed_state field.

**Process Flow**:
1. Finds all substates for sale.order model
2. Maps detailed_state to substate:
   - `done_partial`, `done` → "Complete"
   - `review` → "Legacy Order Review"
   - `sale` → "Waiting"
   - `in_production`, `invoiced`, `invoiced_partial`, `ship_hold`, `ship_ready` → "In Production"

**Dependencies**: `base.substate` model with sale.order substates.

---

#### configure_account_sepa_direct_debit()
**Purpose**: Configures SEPA direct debit for EU company (company_id=2).

**Process Flow**:
1. Enables SEPA direct debit module for company 2
2. Sets initiating party name: "OnLogic B.V"
3. Creates Rabobank bank record
4. Updates bank account (id=2) with:
   - Bank ID: Rabobank
   - Account holder: "Onlogic B.V"
   - Currency: EUR
   - Company: 2
5. Updates journals:
   - Wire journal (lgx_aj.11020-03)
   - Credit Card Purchase Journal
   - Sets bank_account_id and bank_statements_source
   - Updates payment method lines with AP account

**Dependencies**: 
- Journal reference: `lgx_aj.11020-03`
- Bank account ID: 2

---

#### create_onlogic_locations_and_route()
**Purpose**: Creates stock locations and replenishment routes for US and EU companies.

**Process Flow**:
1. Calls `set_warehouse_locations()` (not shown in file)
2. Creates US locations:
   - Primary (under Stock)
   - Overstock (under WH)
3. Creates EU locations:
   - Primary (under Stock)
   - Overstock (under EU)
4. Creates route "Overstock Replenishment" for US:
   - Pull rule from Overstock → Primary
   - Uses Internal Transfers picking type
5. Creates route "Overstock Replenishment" for EU:
   - Similar pull rule

**Dependencies**: Requires `set_warehouse_locations()` method (may be in another file).

---

### ir_server_action_2.py

#### script_1()
**Purpose**: Cleans up duplicate product attributes and values, removes special characters.

**Process Flow**:
1. **Cleanup Phase**:
   - Drops unique constraint `product_attribute_value_value_product_uniq`
   - Removes tabs from attribute names (JSON fields)
   - Removes double quotes from attribute names
   - Trims whitespace from attribute names
   - Same cleanup for attribute values

2. **Deduplication Phase**:
   - Finds distinct attributes by name (keeping first ID)
   - Deactivates duplicate attributes (`active = false`)
   - Deactivates duplicate attribute values (keeps first by name)

3. **Reassignment Phase**:
   - For each distinct attribute:
     - Finds all values with matching attribute name
     - Reassigns values to the distinct attribute ID

4. **Cleanup Phase**:
   - Deletes zero/one quantity records from `product_product_attribute_value_qty`
   - Sets `required = true` for null required fields
   - Deactivates template values with qty 0 or 1

**Key Operations**:
- Uses `DISTINCT ON` to find first record per name
- Updates JSON fields: `{"en_US": "value"}`

---

#### script_2()
**Purpose**: Merges inactive attributes into active ones, updates relationships.

**Process Flow**:
1. **ProductTemplateAttributeLine Update**:
   - Finds attributes with active=False
   - Maps to active attributes by name
   - Updates `product_template_attribute_line.attribute_id`

2. **ProductTemplateAttributeValue Update**:
   - Finds template values with inactive attributes
   - Updates to active attribute IDs
   - Collects attributes for recomputation

3. **Recomputation**:
   - Calls `_compute_products()` on updated attributes
   - Updates many-to-many relationship table:
     - `product_attribute_value_product_template_attribute_line_rel`

**Key Operations**:
- Uses `executemany()` for bulk updates
- Recomputes product variants after attribute merge

---

#### script_3()
**Purpose**: Updates product templates to use unique attribute values, removes duplicates.

**Process Flow**:
1. Processes products in batches (100 per batch)
2. For each product template:
   - Sets `used_in_sale_description = true` for all attribute lines
   - For each attribute line:
     - Checks if all values are inactive
     - Reactivates duplicates if needed
     - Groups values by name
     - For duplicate groups:
       - Keeps first value (lowest ID)
       - Deactivates duplicates
       - Updates `product_variant_combination` references
       - Ensures active attribute value is linked
       - Updates many-to-many relationship table
     - Sets default value:
       - Prefers "None" value if exists
       - Otherwise uses first non-None value

**Key Operations**:
- Batch processing (100 products)
- Handles duplicate value deduplication
- Updates variant combinations
- Maintains many-to-many relationships

---

#### script_4()
**Purpose**: Synchronizes attribute values in product variants, ensures consistency.

**Process Flow**:
1. Processes products in batches (100 per batch)
2. For each product template:
   - Removes empty config steps
   - For each attribute line:
     - Sets default value if missing
     - Finds values with wrong attribute_id
     - Updates values to correct attribute_id
     - Handles inactive values:
       - Finds inactive value with active PTAV
       - Finds active value with inactive PTAV
       - Deactivates inactive PTAV if active exists
       - Activates inactive PTAV if no active exists
       - Updates references to use active values

**Key Operations**:
- Batch processing (100 products)
- Handles attribute ID mismatches
- Activates/deactivates template values based on attribute value status
- Updates variant combinations

---

### base_partner_merge.py

#### _update_reference_fields(src_partners, dst_partner)
**Purpose**: Updates all reference fields when merging partners.

**Process Flow**:
1. **Standard Reference Updates**:
   - Updates calendar records
   - Updates attachments (ir.attachment)
   - Updates mail followers
   - Updates mail activities
   - Updates mail messages
   - Updates ir.model.data

2. **Generic Reference Field Updates**:
   - Finds all reference fields (ttype='reference')
   - Updates records with format `'res.partner,{id}'`
   - Skips abstract models and computed fields

3. **Company-Dependent Fields (ir_property)**:
   - Updates `ir_property` records
   - Uses SQL to avoid conflicts:
     - Only updates if destination doesn't have same field/company
     - Handles company_id NULL cases

**Key Features**:
- Uses savepoints for error handling
- Deletes records if update fails (due to constraints)
- Handles company-dependent properties

---

#### merge_partner_data()
**Purpose**: Merges partners based on `rollup_customer_id` field.

**Process Flow**:
1. Drops unique constraint `res_partner_name_uniq`
2. Groups partners by `rollup_customer_id`:
   - Finds groups with COUNT(*) > 1
   - Gets primary partner ID (MAX customer_id)
   - Gets all partner IDs in group
3. For each group:
   - Gets source partner from `res_customer` table
   - Validates source partner is in group
   - Skips specific partner IDs (hardcoded exclusion list)
   - Checks for parent-child relationships (prevents merging)
   - Merges in batches (batch_size=2):
     - If > 3 partners: merges 2 at a time
     - Otherwise: merges all at once
   - Commits after each merge

**Key Features**:
- Batch merging (2 partners at a time for large groups)
- Parent-child relationship validation
- Hardcoded exclusion list for specific partners
- Uses `base.partner.merge.automatic.wizard._merge()` method

**Dependencies**:
- Table: `res_customer` (rollup_customer_id → partner_id mapping)
- Model: `base.partner.merge.automatic.wizard`

---

## Data Flow Diagrams

### Decryption Flow
```
[Database] → [Query Schema] → [Filter Columns] → [Batch Process] → [Decrypt] → [Update] → [Commit]
     ↓              ↓               ↓                 ↓              ↓           ↓          ↓
  Encrypted      Find Text      Exclude         100k batch    pgcrypto    SET column   Table-level
  Fields         Columns        Tables          chunks        decrypt     = value      commit
```

### Partner Merge Flow
```
[Query Partners] → [Group by rollup] → [Find Primary] → [Validate] → [Batch Merge] → [Update Refs] → [Commit]
        ↓               ↓                  ↓              ↓            ↓              ↓              ↓
   res_partner    COUNT > 1        MAX(customer_id)  Skip list   _merge(2)     _update_refs   Per merge
```

### Product Attribute Flow
```
[script_1] → [Clean Duplicates] → [script_2] → [Merge Attributes] → [script_3] → [Update Templates] → [script_4] → [Sync Variants]
     ↓              ↓                    ↓              ↓                  ↓              ↓                  ↓              ↓
  Cleanup        Deactivate          Find Active   Update Lines     Deduplicate    Update PTAV      Sync Values   Final State
  Special        Duplicates          Attributes    & Values         Values         References      Consistency
  Characters
```

---

## Dependencies and Prerequisites

### External Dependencies
1. **PostgreSQL Extensions**:
   - `pgcrypto` (for decryption functions)

2. **File System**:
   - `/home/odoo/decryption.txt` (decryption key)

3. **CSV Files**:
   - `osi_ol_decryption/data/account.analytic.plan.csv`
   - `osi_ol_decryption/data/account.analytic.account.csv`

### Temporary Tables (Must Exist)
- `temp_helpdesk_rma_line`
- `temp_support_repair_order`
- `temp_sale_workflow_hold`
- `temp_sale_workflow_check`
- `temp_ir_property_v13_vp`

### Odoo Models/Dependencies
- `helpdesk.ticket`, `helpdesk.ticket.type`
- `repair.order`
- `sale.order.inspection`
- `stock.picking`, `stock.move`
- `product.template`, `product.attribute`, `product.attribute.value`
- `base.partner.merge.automatic.wizard`

### Execution Prerequisites
1. Database must be in maintenance mode
2. All temporary tables must be populated
3. Decryption key file must exist
4. CSV files must be present (for cost center migration)
5. Required Odoo modules must be installed

---

## Performance Considerations

### Known Performance Issues
1. **decrypt_number_field()**: Processes records one-by-one (slow for large tables)
2. **recompute_tax_id_on_contacts()**: Processes contacts individually with commits
3. **script_3()** and **script_4()**: Process 100 products per batch (may be slow for large catalogs)

### Optimization Opportunities
1. Batch processing for numeric decryption
2. Bulk updates instead of individual commits
3. Use `executemany()` for bulk operations
4. Add progress indicators for long-running operations
5. Parallel processing where possible

---

## Error Handling

### Common Error Scenarios
1. **Missing Decryption Key**: Function returns early with error log
2. **Missing Tables**: Scripts skip missing tables and log warnings
3. **Missing Columns**: Scripts skip missing columns and log warnings
4. **Constraint Violations**: Partner merge uses savepoints to handle errors
5. **Corrupted Data**: Decryption scripts skip corrupted records

### Error Recovery
- Most scripts use try/except blocks
- Some scripts use savepoints for transaction safety
- Logging is comprehensive for debugging

---

## Testing Recommendations

1. **Test on Small Dataset First**: Run scripts on subset of data
2. **Verify Decryption**: Check sample records before/after decryption
3. **Validate Relationships**: Ensure foreign keys are maintained
4. **Check Performance**: Monitor execution time for large tables
5. **Verify Data Integrity**: Compare record counts before/after migration

---

## Maintenance Notes

- These scripts are **one-time migration scripts** and should not be run multiple times
- Always backup database before running
- Monitor logs for errors and warnings
- Some scripts modify data structure (drops constraints, etc.)
- Hardcoded IDs and values may need adjustment for different environments
