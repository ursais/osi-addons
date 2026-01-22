# OnLogic Decryption and Post-Migration Process Analysis

## Executive Summary

This document analyzes the `osi_ol_decryption` Odoo module used for database decryption and post-migration data processing during the OnLogic v13 to v17 migration.

**Current State (Actual Timings):**

| Phase | Duration (min) | Duration (hrs) |
|-------|----------------|----------------|
| Decryption | 148 | 2.5 |
| Uninstall Old Module | 9 | 0.2 |
| Module Installations | 114 | 1.9 |
| After Decryption | 18 | 0.3 |
| Post Migration Scripts | 226 | 3.8 |
| Product Migration Scripts | 223 | 3.7 |
| MO, RMA, Other Scripts | 112 | 1.9 |
| **Total** | **850** | **~14.2 hours** |

**Optimization Potential (see Section 3.9 for details):**

| Scenario | Savings | Final Runtime | Reduction |
|----------|---------|---------------|-----------|
| A: Safe Optimizations Only | 150-220 min | 10.5-11.7 hrs | 18-26% |
| B: Safe + Medium Risk | 175-265 min | 9.8-11.3 hrs | 20-31% |
| C: All Optimizations | 200-300 min | 9.2-10.8 hrs | 24-35% |

- Primary optimization opportunities:
  - Batch commit consolidation: 180 commit calls found, many inside loops
  - SQL bulk operations replacing row-by-row processing
  - Prefetching data before loops to eliminate repeated queries
  - Limited parallelization across isolated table domains
  - Parallel compute with batch writes (higher risk, limited applicability)
- Target areas with highest impact: Post Migration Scripts (226 min) and Product Migration Scripts (223 min)

**Key Constraints:**
- PostgreSQL table contention limits parallelization options
- Functions writing to `res_partner` (6 functions) must run sequentially
- Product attribute scripts (8 scripts) must run sequentially due to shared tables
- Only functions operating on isolated tables can safely run in parallel

**Recommended Parallel Execution Windows:**
| Window | Channels | Description |
|--------|----------|-------------|
| Window 2 | 3 parallel | Isolated tables (scrap, purchase, account_payment) + sale_order domain + account domain |
| Window 5 | 4 parallel | US/EU stock operations + US/EU RMA migration |

**Quick Wins (Highest Impact, Lowest Risk):**
1. Remove inner loop commits in `script_3()`, `script_4()`, `script_5()` - potential 60-90 minute savings
2. Batch commits in `recompute_tax_id_on_contacts()` - potential 25-30 minute savings
3. Pre-build payment method mapping in `payment_method_update()` - potential 20-30 minute savings
4. Prefetch RMA data before `migrate_helpdesk_rma_to_ticket()` loop - potential 15-25 minute savings
5. Replace row-by-row INSERT/UPDATE with bulk SQL operations - potential 20-30 minute savings

---

## Overview

This document provides a comprehensive analysis of the `osi_ol_decryption` Odoo module, which handles database decryption following an Odoo version migration (v13 to v17), and the subsequent post-release data migration tasks.

The module is triggered via a `post_init_hook` that executes decryption functions on module installation. Additional migration scripts are available as server action methods that can be called manually or through scheduled actions.

---

## Table of Contents

- [Executive Summary](#executive-summary)

1. [Decryption Process](#1-decryption-process)
   - [1.1 Character Field Decryption](#11-character-field-decryption)
   - [1.2 Numeric Field Decryption](#12-numeric-field-decryption)
   - [1.3 JSON Field Decryption](#13-json-field-decryption)
   - [1.4 Secondary Decryption Pass](#14-secondary-decryption-pass)
   - [1.5 Targeted Field Decryption](#15-targeted-field-decryption)
2. [Post-Release Migration](#2-post-release-migration)
   - [2.1 Module Cleanup and Installation](#21-module-cleanup-and-installation)
   - [2.2 Account and Financial Data Migration](#22-account-and-financial-data-migration)
   - [2.3 Product and Attribute Migration](#23-product-and-attribute-migration)
   - [2.4 Stock and Inventory Migration](#24-stock-and-inventory-migration)
   - [2.5 Sales and CRM Migration](#25-sales-and-crm-migration)
   - [2.6 Manufacturing (MRP) Migration](#26-manufacturing-mrp-migration)
   - [2.7 Helpdesk and RMA Migration](#27-helpdesk-and-rma-migration)
   - [2.8 Partner and Contact Migration](#28-partner-and-contact-migration)
   - [2.9 System Configuration and Settings](#29-system-configuration-and-settings)
   - [2.10 Data Cleanup and Validation](#210-data-cleanup-and-validation)
   - [2.11 Computed Field Recomputation](#211-computed-field-recomputation)
3. [Performance Optimization Analysis](#3-performance-optimization-analysis)
   - [3.1 Key Performance Issues Identified](#31-key-performance-issues-identified)
   - [3.2 Parallelization Opportunities](#32-parallelization-opportunities)
   - [3.3 Function-Specific Optimization Recommendations](#33-function-specific-optimization-recommendations)
   - [3.4 Proposed Optimized Execution Plan](#34-proposed-optimized-execution-plan)
     - [3.4.1 Channel Execution Matrix](#341-channel-execution-matrix)
     - [3.4.2 Execution Summary by Window](#342-execution-summary-by-window)
     - [3.4.3 Visual Timeline](#343-visual-timeline)
   - [3.5 Time Analysis](#35-time-analysis)
   - [3.6 Detailed Optimization Opportunities](#36-detailed-optimization-opportunities)
     - [3.6.1 Commit Pattern Analysis](#361-commit-pattern-analysis)
     - [3.6.2 Row-by-Row Operations](#362-row-by-row-operations-should-be-bulk)
     - [3.6.3 Repeated Database Queries in Loops](#363-repeated-database-queries-in-loops)
     - [3.6.4 ORM vs. SQL Opportunities](#364-orm-vs-sql-opportunities)
     - [3.6.5 Specific Function Optimizations](#365-specific-function-optimizations)
     - [3.6.6 Quick Wins Summary](#366-quick-wins-summary-minimal-code-changes-high-impact)
   - [3.7 PostgreSQL Lock Considerations](#37-postgresql-lock-considerations)
   - [3.8 Advanced: Parallel Compute with Batch Writes (Higher Risk)](#38-advanced-parallel-compute-with-batch-writes-higher-risk)
   - [3.9 Final Time Estimates](#39-final-time-estimates)

---

## 1. Decryption Process

The decryption process is the first critical step after database migration. The source database was encrypted using PGP symmetric encryption (pgcrypto extension), and this module decrypts the data to restore it to its original form.

### 1.1 Character Field Decryption

**Function:** `decrypt_char_field()` (ir_server_action.py, lines 12-261)

**Purpose:** Decrypts all character/text fields that were encrypted during the v13 operation.

**Steps:**

1. **Read Decryption Key:** Reads the decryption key from `/home/odoo/decryption.txt`

2. **Enable pgcrypto Extension:** Ensures PostgreSQL pgcrypto extension is available:
   ```sql
   CREATE EXTENSION IF NOT EXISTS pgcrypto;
   ```

3. **Identify Target Columns:** Queries the database schema to find all character-type columns:
   - Data types: `character varying`, `character`, `text`, `"char"`, `name`
   - Excludes: `ir%` tables (system tables), `mail%` tables, `report%` tables
   - Excludes selection fields
   - Only includes columns with maximum length > 64 or NULL
   - Excluded tables: `res_config_settings`, `res_lang`, `account_invoice_extract_words`, `mrp_bom_line`, `stock_lot`, `stock_move_line`, `stock_move`, `account_move_line`, `webhook_broadcast_date`

4. **Excluded Columns:** Specific columns excluded from decryption:
   - `project_task_burndown_chart_report.date_group_by`
   - `res_partner.contact_address_complete`
   - `account_move.sequence_prefix`, `account_move.invoice_partner_display_name`
   - `stock_move.reporting_extended_name`, `reporting_name`, `next_serial`, `origin_system`
   - `account_bank_statement.name`

5. **Batch Processing:** Processes records in batches of 100,000 (10,000 for `project_task`)

6. **Decryption Logic:**
   - Identifies encrypted data by prefix `\xc30`
   - Skips corrupted data containing `<br>`, `<br/>`, `...`, or `@`
   - Strips `<p>` and `</p>` tags before processing
   - Uses `pgp_sym_decrypt()` function with the key

7. **Update Records:** Executes UPDATE statements with decrypted values:
   ```sql
   UPDATE table SET column = pgp_sym_decrypt('encrypted_data', 'KEY') WHERE id = X;
   ```

8. **Commit Strategy:** Commits every 100,000 records per table

### 1.2 Numeric Field Decryption

**Function:** `decrypt_number_field()` (ir_server_action.py, lines 262-412)

**Purpose:** Decrypts numeric fields that were obfuscated by multiplying by 5.

**Note:** This function is currently commented out in the post_init_hook.

**Steps:**

1. **Identify Target Columns:** Finds columns with data types `double precision` or `numeric`

2. **Excluded Tables:** `uom_uom`, `crm_lead`, `account_invoice_extract_words`

3. **Special Handling:** Only the `sales_price` column from `dyn_saleorderlines` table

4. **Check Decryption Status:** Queries `is_decimal_encryption` flag in `ir_model` to skip already-decrypted tables

5. **Decryption Logic:** Divides all numeric values by 5:
   ```python
   col_data / 5
   ```

6. **Mark Complete:** Updates `is_decimal_encryption` to false after processing

### 1.3 JSON Field Decryption

**Function:** `decrypt_json_field()` (ir_server_action.py, lines 414-631)

**Purpose:** Decrypts JSONB fields containing encrypted text in the `en_US` locale key.

**Steps:**

1. **Read Decryption Key:** Same as character fields

2. **Identify Target Columns:** Finds JSONB columns meeting criteria:
   - Non-transient models only
   - Excludes: `ir%`, `mail%`, `report%` tables
   - Excludes: `res_config_settings`, `res_country_group`, `res_lang`, `knowledge_article`, `stock_rule`
   - Excludes columns starting with `analytic%`

3. **Decryption Logic:**
   - Extracts `en_US` value from JSON
   - Checks for encrypted prefix `\xc30`
   - Decrypts and rebuilds JSON structure:
   ```sql
   UPDATE table SET column = json_build_object('en_US', pgp_sym_decrypt('encrypted', 'KEY'))
   ```

### 1.4 Secondary Decryption Pass

**Function:** `decrypt_char_field(all_data=True)` (called from post_init_hook)

**Purpose:** Second pass to catch any remaining encrypted data that may have been missed.

**Steps:**

1. **Scan for Remaining Encrypted Data:** Uses `get_non_decrpted_data()` function (lines 1619-1693)

2. **Pattern Matching:** Searches for `\xc30` pattern in all character columns

3. **Process Remaining Records:** Decrypts any records still containing encrypted data

### 1.5 Targeted Field Decryption

**Functions:** Various cleanup functions for specific fields

#### 1.5.1 Internal Notes Decryption
**Function:** `update_internal_notes()` (lines 1568-1586)

- Targets: `repair.order.internal_notes` field
- Uses regex pattern: `\\xc30[0-9a-f]+`
- Decrypts matched patterns inline

#### 1.5.2 Account Move Line Name Decryption
**Function:** `update_acount_move_name()` (lines 1588-1617)

- Targets: `account.move.line.name` and `account.move.invoice_partner_display_name`
- Handles special currency symbol encoding
- Updates partner display names from partner records

#### 1.5.3 Check Amount in Words
**Function:** `update_check_amount_in_words()` (lines 1559-1566)

- Recomputes `check_amount_in_words` for payments with encrypted data

---

## 2. Post-Release Migration

The post-release migration handles data transformations, schema updates, and business logic migrations necessary after the Odoo version upgrade.

### 2.1 Module Cleanup and Installation

#### 2.1.1 Uninstall Old Modules
**Function:** `uninstall_old_module()` (lines 2291-2576)

**Purpose:** Removes v13 custom modules (ls_* modules) that are incompatible with v17.

**Modules Uninstalled:** Over 180 modules including:
- `ls_account_*` - Legacy accounting modules
- `ls_delivery_*` - Legacy delivery/shipping modules
- `ls_graphql_*` - Legacy API modules
- `ls_mrp_*` - Legacy manufacturing modules
- `ls_product_*` - Legacy product modules
- `ls_sale_*` - Legacy sales modules
- `ls_stock_*` - Legacy inventory modules
- `osi_encryption` - Original encryption module

**Steps:**
1. Search for ir.model.data records from these modules
2. Delete associated views, menus, rules, crons, fields, access rights
3. Disable triggers during deletion
4. Mark modules for removal

#### 2.1.2 Install New Modules
**Function:** `install_new_module()` (lines 2579-2827)

**Purpose:** Installs v17-compatible replacement modules.

**Modules Installed:** Over 150 modules including:
- Standard Odoo Enterprise modules (account_accountant, helpdesk, mrp, etc.)
- OCA modules (base_tier_validation, partner_identification, etc.)
- OnLogic custom modules (ol_* modules)
- Localization modules (l10n_de_reports, l10n_nl_intrastat, etc.)

### 2.2 Account and Financial Data Migration

#### 2.2.1 Chart of Accounts Setup
**Function:** `set_localizations()` (lines 2234-2289)

**Chart Templates by Company:**
| Company ID | Template |
|------------|----------|
| 1, 3, 4, 5, 7, 8, 11 | `generic_coa` (US) |
| 2, 10 | `nl` (Netherlands) |
| 6 | `tw` (Taiwan) |
| 9 | `de_skr04` (Germany) |
| 12 | `my` (Malaysia) |

#### 2.2.2 Account Updates from Excel
**Function:** `update_accounts_from_excel()` (lines 1313-1489)

**Data Source:** `data/Odoo_17_GL_Remap.xlsx`

**Steps:**
1. Reads Excel file with account mapping
2. For each account: updates code, name, type, tags, reconcile flag
3. Creates new accounts if they don't exist
4. Uses direct SQL for performance

#### 2.2.3 Delete Obsolete Accounts
**Function:** `delete_account()` (lines 1284-1310)

**Data Source:** `data/account_delete.xlsx`

- Removes accounts marked for deletion (except Cash and Bank)

#### 2.2.4 Product Category Account Setup
**Function:** `update_product_category_account()` (lines 1184-1282)

**For US Company:**
- Income Account: `41100-02`
- Expense Account: `51105-02`
- Stock Input Account: `21040.02`
- Stock Output Account: `11765-02`
- Stock Valuation Account: `11720.02`

**For EU Company:**
- Income Account: `41100-03`
- Expense Account: `51105-03`
- Stock Input Account: `21040.04`
- Stock Output Account: `11750-03`
- Stock Valuation Account: `11720.04`

#### 2.2.5 Analytic Account Migration
**Function:** `update_cost_center_distribution()` (lines 652-687)

**Steps:**
1. Clears existing analytic account references
2. Imports new analytic plans from `data/account.analytic.plan.csv`
3. Imports new analytic accounts from `data/account.analytic.account.csv`
4. Maps old cost center IDs to new analytic account IDs
5. Updates journal items with new analytic distribution

**Cost Center Mapping:**
| Old ID | New Code |
|--------|----------|
| 1 | 11000 |
| 2 | 12000 |
| 3 | 13000 |
| ... | ... |

#### 2.2.6 Journal Configuration
**Updates include:**
- Deactivating duplicate vendor bill journals
- Setting payment accounts on outbound/inbound methods
- Configuring suspense accounts
- Setting up SEPA Direct Debit (EU company)

#### 2.2.7 Payment Method Migration
**Function:** `payment_method_update()` (lines 1041-1148)

**Legacy to New Mapping:**
| Legacy ID | Name |
|-----------|------|
| 1, 6 | Paypal |
| 8 | Stripe |
| 2 | Bank Transfer |
| 3 | Zero Payment |
| 4 | Manual |
| 5 | Check |
| 9, 16 | Credit Card |
| 10 | Net Terms -> Payment Terms |
| 11 | iDEAL |
| 12 | Bancontact |
| 13 | GiroPay |
| 14 | Sofort |
| 15 | Maestro |

#### 2.2.8 Supplier Invoice Number Migration
**Function:** `update_supplier_invoice_number()` (lines 1756-1794)

- Migrates `supplier_invoice_number` field to `ref` field
- Handles duplicates by appending move ID

### 2.3 Product and Attribute Migration

#### 2.3.1 Attribute Cleanup and Deduplication
**Function:** `script_1()` (ir_server_action_2.py, lines 10-85)

**Steps:**
1. Drop unique constraint on product_attribute_value
2. Clean attribute names (remove tabs, double quotes, trim whitespace)
3. Clean attribute value names similarly
4. Identify distinct attributes by name
5. Deactivate duplicate attributes
6. Deactivate duplicate attribute values
7. Update attribute values to point to active attributes

#### 2.3.2 Merge Attribute Values
**Function:** `script_2()` (ir_server_action_2.py, lines 87-185)

**Steps:**
1. Update ProductTemplateAttributeLine to use active attributes
2. Update ProductTemplateAttributeValue to use active attributes
3. Recompute products for affected attributes

#### 2.3.3 Update Product Templates
**Function:** `script_3()` (ir_server_action_2.py, lines 188-375)

**Steps:**
1. Process all configurable products in batches of 100
2. Set `used_in_sale_description = true` on attribute lines
3. Handle inactive PTAVs by activating appropriate ones
4. Deduplicate PTAVs with same name
5. Update product variant combinations

#### 2.3.4 Sync Attribute Values in Variants
**Function:** `script_4()` (ir_server_action_2.py, lines 377-496)

**Steps:**
1. Remove orphan config step lines
2. Update PTAVs with wrong attribute IDs
3. Handle active/inactive value mismatches
4. Update quantity-related attribute data

#### 2.3.5 Update Quantity Attributes
**Function:** `script_5()` (ir_server_action_2.py, lines 498-607)

**Steps:**
1. Restore quantity requirements from v13 data
2. Create missing `attribute_value_qty` records
3. Handle "None" values with quantity requirements

#### 2.3.6 Product Category Migration
**Function:** `update_product_category()` (lines 1967-2032)

**Mappings:**
- "Product Management, Expansion" -> Category: Expansion
- "Computers, Panel PCs" -> Category: Computers
- "Cases, Computers" -> Category: Cases
- NULL pim_category -> "All products"

#### 2.3.7 Lifecycle Status Migration
**Function:** `script_8()` (ir_server_action_2.py, lines 770-984)

**Status Mappings:**
| Old Status | New Status |
|------------|------------|
| coming_soon, in_development | draft |
| available | active |
| preorder | pre_order |
| end_of_life | end |
| NULL | new |

#### 2.3.8 Remove "None" Values
**Function:** `removing_none_values()` (ir_server_action_2.py, lines 985-1033)

- Removes "None" attribute values from product templates
- Cleans up related M2M relations
- Deactivates corresponding PTAVs

#### 2.3.9 Product State Migration
**Function:** `set_product_candidates()` (lines 2167-2232)

**Steps:**
1. Map old state IDs to new ones
2. Set candidate flags (bom, manufacture, purchase, sale, ship)
3. Set approval flags based on product state
4. Disable purchase for phantom kit products

#### 2.3.10 Country of Origin Migration
- Reads from `temp_ir_property_v13_vp` table
- Updates `product_template.country_of_origin`

#### 2.3.11 Product Tax Code Migration
**Function:** `update_product_tax_code()` (lines 1796-1812)

- Maps `tax_code_id` from v13 ir.property to product templates

### 2.4 Stock and Inventory Migration

#### 2.4.1 Warehouse Location Restructuring
**Function:** `set_warehouse_locations()` (lines 955-1038)

**Steps:**
1. Move locations from "Physical Locations" to appropriate warehouse parents (WH/EU)
2. Rename "Warehouse" to "Stock" for both companies
3. Exclude specific locations (Amazon, Out To Supplier, Taiwan Warehouse, Tradeshows, TYC Tong Yu)

#### 2.4.2 Create OnLogic Locations and Routes
**Function:** `create_onlogic_locations_and_route()` (lines 770-953)

**New Locations:**
- US: WH/Stock/Primary, WH/Overstock
- EU: EU/Stock/Primary, EU/Overstock

**New Routes:**
- "Overstock Replenishment" with "Pull from Overstock" rules

**Data Source:** `data/US_and_EU_Stock_Locations.xlsx`

#### 2.4.3 Stock Transfer
**Function:** `tranfer_stock()` (lines 485-565)

- Creates internal transfers to move stock to correct locations
- Uses loc_row, loc_rack, loc_case from v13 properties to determine destination

#### 2.4.4 Stock Inventory Migration
**Function:** `update_stock_inventory()` (ir_server_action_2.py, lines 1679-1768)

**Pre-requisite Tables:**
- `temp_stock_inventory_vp13`
- `temp_product_product_stock_inventory_rel_vp13`
- `temp_stock_inventory_stock_location_rel_vp13`
- `temp_stock_move_vp13`

**Steps:**
1. Insert inventory records with mapped states
2. Link products and locations
3. Associate stock moves with inventory adjustments

#### 2.4.5 Putaway Rule Creation
**Function:** `create_stock_putway_rule()` (lines 2089-2164)

**Data Source:** `data/stock.location.csv`

- Creates putaway rules based on product location properties

### 2.5 Sales and CRM Migration

#### 2.5.1 Sale Order Substate Migration
**Function:** `update_saleorder_substate()` (lines 718-729)

**Mappings:**
| Old detailed_state | New Substate |
|-------------------|--------------|
| done_partial, done | Complete |
| review | Legacy Order Review |
| sale | Waiting |
| in_production, invoiced, invoiced_partial, ship_hold, ship_ready | In Production |

#### 2.5.2 Sales Order Inspection Migration
**Function:** `update_inspections()` (lines 446-482)

- Maps legacy workflow hold checks to new inspection system
- Check ID 55, 69 -> Finance Manual Exception
- Check ID 63 -> Do Not Build
- Check ID 72 -> Do Not Ship

#### 2.5.3 Payment Provider Updates
**Function:** `update_payment_provide()` (lines 138-154)

- Unlinks Stripe from Paypal payment method
- Links Stripe to correct providers

### 2.6 Manufacturing (MRP) Migration

#### 2.6.1 Generate Scaffolding BOMs
**Function:** `script_6()` (ir_server_action_2.py, lines 610-738)

**Steps:**
1. Archive invalid BOMs (inactive products, TA BOMs, empty BOMs)
2. Create scaffolding BOMs for all configurable products
3. Create BOM lines from attribute values with linked products
4. Create configuration sets for BOM line configuration

#### 2.6.2 Add Classification to BOM Lines
**Function:** `script_7()` (ir_server_action_2.py, lines 741-767)

- Adds `classification_id` to scaffolding BOM lines based on attribute classification

#### 2.6.3 Update Phantom BOMs
**Function:** `update_phantoms_bom_data()` (ir_server_action_2.py, lines 1519-1642)

**Steps:**
1. Normalize company assignments on phantom BOMs
2. Deduplicate equivalent phantom BOMs
3. Ensure all companies point to master BOM
4. Archive unused phantom BOMs

#### 2.6.4 BOM Operations Setup
**Function:** Part of `script_8()` (ir_server_action_2.py)

- Sequences: Build=10, Test=20, Box=30
- Creates operations on BOMs without them

#### 2.6.5 Split Manufacturing Orders
**Function:** `split_mo()` (lines 567-600)

- Splits MOs with quantity > 1 and state = confirmed
- Links MOs to sale order lines

#### 2.6.6 Update Workcenters
**Function:** `update_workcenter_mo()` (ir_server_action_2.py, lines 1644-1676)

- Creates workcenter operations on scaffolding BOMs
- Workcenters: Test, Build, Box

### 2.7 Helpdesk and RMA Migration

#### 2.7.1 Migrate Helpdesk RMA to Tickets
**Function:** `migrate_helpdesk_rma_to_ticket()` (lines 157-444)

**Stage Mappings:**
| Old State | New Stage |
|-----------|-----------|
| new | RMA Requested |
| accepted | RMA Accepted |
| in_progress | RMA In Progress |
| resolved | RMA Resolved |
| cancelled | RMA Cancelled |

**Steps:**
1. Update sequence configurations
2. Create helpdesk tickets from RMA records
3. Link repair orders to tickets
4. Create repair orders from RMA lines
5. Link stock pickings and moves to repair orders

#### 2.7.2 Scrap Reason Migration
**Function:** `mig_scrap_reasons()` (lines 1152-1181)

- Creates scrap reason codes from failure_reason table
- Maps stock scraps to new reason codes
- Location mapping: US=116 (WH/SRMA Staging), EU=117 (EU/SRMA Staging)

### 2.8 Partner and Contact Migration

#### 2.8.1 Timezone Correction
**Function:** `set_timezones()` (lines 603-622)

**Mappings:**
| Old Timezone | New Timezone |
|-------------|--------------|
| US/Eastern | America/New_York |
| US/Central | America/Chicago |
| US/Mountain | America/Denver |
| US/Pacific | America/Los_Angeles |

#### 2.8.2 Tax ID Propagation
**Function:** `recompute_tax_id_on_contacts()` (lines 690-715)

- Copies VAT numbers from parent/commercial partner to contacts

#### 2.8.3 Complete Address Computation
**Function:** `update_compute_complete_address()` (lines 1695-1741)

- Batch updates `contact_address_complete` for all partners
- Migrates `default_supplier_contact` to M2M relation

#### 2.8.4 PO Contact Migration
**Function:** `update_po_contact_ids()` (lines 1743-1754)

- Migrates `contact_id` to M2M relation on purchase orders

#### 2.8.5 Partner Merge
**Function:** `merge_partner_data()` (base_partner_merge.py, lines 97-154)

- Merges duplicate partners based on `rollup_customer_id`
- Handles batch processing for large partner sets

#### 2.8.6 AR/AP/Followup Contact Flags
**Function:** `update_ar_ap_followup_contacts()` (ir_server_action_2.py, lines 1491-1517)

- Migrates AR, AP, and Followup boolean flags from v13

#### 2.8.7 Credit Limit Migration
**Function:** `update_credit_limit_data()` (ir_server_action_2.py, lines 1770-1840)

**Steps:**
1. Update `partner_rollup_id` from v13 data
2. Create credit limit properties from v13 ir.property
3. Recompute outstanding receivables and balances

#### 2.8.8 Payment Preference Migration
- Creates ir.property records for payment_preference field

### 2.9 System Configuration and Settings

#### 2.9.1 Default General Settings
**Function:** `update_default_general_settings()` (lines 1491-1523)

**Settings per Company:**
- Internal Bank Transfer Account: accounts starting with `11060`
- Clear payment debit/credit accounts
- Clear suspense/deferred accounts
- Set documents spreadsheet folder

#### 2.9.2 Followup Status Update
**Function:** `update_followup_status()` (lines 18-66)

- Deletes obsolete followup lines and templates
- Updates partner followup status based on overdue invoices

#### 2.9.3 Archive Journal Automation
**Function:** `create_archive_journal_automation()` (lines 67-134)

- Creates automated action to archive "Vendor Bills" journal with code "LF" for company 2

#### 2.9.4 SEPA Direct Debit Configuration
**Function:** `configure_account_sepa_direct_debit()` (lines 732-768)

- Enables SEPA Direct Debit for EU company
- Creates Rabobank bank record
- Links bank account to Wire Transfer journal

### 2.10 Data Cleanup and Validation

#### 2.10.1 Fix Invalid Check Numbers
**Function:** `fix_invalid_check_numbers()` (lines 1926-1965)

- Sets check_number to 0 for payments with non-numeric check numbers
- Adds chatter message documenting the change

#### 2.10.2 Drop Temporary Tables
**Function:** `drop_temp_tables()` (ir_server_action_2.py, lines 1842-1860)

**Tables Dropped:**
- `temp_ir_property_v13_vp`
- `temp_product_temp_v13_vp`
- `temp_product_template_res_company_rel_v13_vp`
- `temp_product_template_attribute_value_v13_vp`
- `temp_ir_property_inbound_shipping_method`
- `temp_ir_property`
- `temp_res_users`
- `temp_product_attribute_value_v13`
- `temp_stock_inventory_vp13`
- `temp_product_product_stock_inventory_rel_vp13`
- `temp_stock_inventory_stock_location_rel_vp13`
- `temp_stock_move_vp13`
- `temp_ir_property_row_rack_case`
- `temp_res_partner_vp`

### 2.11 Computed Field Recomputation

#### 2.11.1 Partner Computed Fields
**Function:** `run_all()` (ir_server_action_3.py)

**Queued Recomputations:**
- `_compute_customer_deposit_balance`
- `_compute_open_so_balance`
- `_compute_outstanding_receivable`
- `_compute_net_terms_allowed`
- `_compute_check_hot_ar`

#### 2.11.2 Sale Order Line Computed Fields
- `_compute_bo_qty`
- `_compute_purchase_price`
- `_compute_uigd_qty`
- `_compute_bo_value`
- `_compute_last_date_delivered`
- `_compute_last_bill_date`

#### 2.11.3 Sale Order Computed Fields
- `_compute_current_estimate_ship_date`
- `_compute_uigd_value`
- `_compute_bo_value`
- `_compute_last_date_delivered`
- `_compute_last_bill_date`
- `_compute_uninvoiced_balance`

#### 2.11.4 Stock Picking Computed Fields
- `_compute_total_sales_price`
- `_compute_main_error`
- `_compute_credit_hold`

#### 2.11.5 MRP Production Computed Fields
- `_compute_credit_hold`

#### 2.11.6 Account Move Computed Fields
- `_compute_intrastat_country_id`
- `_compute_sale_type_id`
- `_compute_po_line_price_difference`

#### 2.11.7 Account Move Line Computed Fields
- `_compute_po_line_price_difference`

#### 2.11.8 Product Computed Fields
**Function:** `update_total_cost()` (lines 2059-2087)
- Creates price reviews and computes `approved_total_cost`
- Computes product volume from dimensions

---

## Data Files Reference

| File | Purpose |
|------|---------|
| `data/account_delete.xlsx` | Accounts to be deleted |
| `data/account.analytic.account.csv` | New analytic accounts |
| `data/account.analytic.plan.csv` | New analytic plans |
| `data/Odoo_17_GL_Remap.xlsx` | Account mapping for migration |
| `data/stock.location.csv` | Stock locations to import |
| `data/US_and_EU_Stock_Locations.xlsx` | Location hierarchy configuration |

---

## Pre-Migration SQL Requirements

Before running the migration, several temporary tables must be created by exporting data from the v13 database:

```sql
-- From v13 database:
CREATE TABLE temp_ir_property_v13_vp AS SELECT * FROM ir_property;
CREATE TABLE temp_product_temp_v13_vp AS SELECT * FROM product_template;
CREATE TABLE temp_product_template_res_company_rel_v13_VP AS SELECT * FROM product_template_res_company_rel;
CREATE TABLE temp_product_template_attribute_value_V13_VP AS SELECT * FROM product_template_attribute_value;
CREATE TABLE temp_helpdesk_rma_line AS SELECT * FROM helpdesk_rma_line;
CREATE TABLE temp_support_repair_order AS SELECT * FROM support_repair_order;
CREATE TABLE temp_sale_workflow_hold AS SELECT * FROM sale_workflow_hold;
CREATE TABLE temp_sale_workflow_check AS SELECT * FROM sale_workflow_check;
CREATE TABLE temp_account_move AS SELECT * FROM account_move;
CREATE TABLE temp_product_attribute_value_v13 AS SELECT * FROM product_attribute_value;
CREATE TABLE temp_res_partner_contact_type_v13 AS SELECT * FROM res_partner_contact_type;
CREATE TABLE temp_res_partner_vp AS SELECT id, terms_partner_id FROM res_partner WHERE terms_partner_id IS NOT NULL;
CREATE TABLE temp_stock_inventory_vp13 AS SELECT * FROM stock_inventory;
CREATE TABLE temp_product_product_stock_inventory_rel_vp13 AS SELECT * FROM product_product_stock_inventory_rel;
CREATE TABLE temp_stock_inventory_stock_location_rel_vp13 AS SELECT * FROM stock_inventory_stock_location_rel;
CREATE TABLE temp_stock_move_vp13 AS SELECT * FROM stock_move WHERE inventory_id IS NOT NULL;
```

---

## Execution Order

### Phase 1: Decryption (Automatic via post_init_hook)
1. `decrypt_char_field()` - First pass
2. `decrypt_json_field()`
3. `decrypt_char_field(all_data=True)` - Second pass

### Phase 2: Module Management
1. `uninstall_old_module()`
2. `install_new_module()`

### Phase 3: Core Data Migration
1. `set_localizations()`
2. `update_accounts_from_excel()`
3. `delete_account()`
4. `update_product_category_account()`
5. `update_cost_center_distribution()`
6. `payment_method_update()`

### Phase 4: Product Migration
1. `script_1()` - Attribute cleanup
2. `script_2()` - Attribute merge
3. `script_3()` - Template updates
4. `script_4()` - Variant sync
5. `script_5()` - Quantity attributes
6. `script_6()` - Scaffolding BOMs
7. `script_7()` - BOM classification
8. `script_8()` - Lifecycle and misc

### Phase 5: Operational Data
1. `migrate_helpdesk_rma_to_ticket()`
2. `set_warehouse_locations()`
3. `create_onlogic_locations_and_route()`
4. `update_saleorder_substate()`
5. `update_inspections()`
6. `mig_scrap_reasons()`

### Phase 6: Partner and Contact Data
1. `set_timezones()`
2. `recompute_tax_id_on_contacts()`
3. `update_compute_complete_address()`
4. `merge_partner_data()`
5. `update_credit_limit_data()`

### Phase 7: Cleanup and Validation
1. `update_acount_move_name()` - Final decryption cleanup
2. `update_internal_notes()`
3. `fix_invalid_check_numbers()`
4. `run_all()` - Computed field recomputation
5. `drop_temp_tables()`
6. `unistall_module()` - Remove this module

---

## 3. Performance Optimization Analysis

This section analyzes the current implementation to identify opportunities for reducing the ~14.2 hour runtime (850 minutes) through parallelization and code streamlining.

### 3.1 Key Performance Issues Identified

#### 3.1.1 Excessive Database Commits

**Current State:** The codebase contains **180 commit statements** across the migration scripts.

**Critical Problem Areas:**

| Function | Issue | Commits Inside Loops |
|----------|-------|---------------------|
| `script_4()` | Commits after nearly every individual UPDATE | ~12+ commits per product template |
| `script_3()` | Commits after each DELETE/INSERT pair | ~6 commits per attribute line |
| `script_5()` | Commits after each attribute_value_qty creation | ~3 commits per PTAV |
| `migrate_helpdesk_rma_to_ticket()` | Commits during repair order creation | Per RMA line |
| `payment_method_update()` | No batch commits | Individual updates per record |

**Impact:** Each commit forces a disk sync and transaction boundary, adding ~10-50ms overhead per commit. With thousands of products and attribute lines, this accumulates to hours of unnecessary overhead.

**Recommendation:** Batch commits to once per 1,000-10,000 records or once per batch iteration, not per individual operation.

#### 3.1.2 Row-by-Row Processing Instead of Bulk Operations

**Current State:** The codebase contains **226 for-loops**, many executing single-record operations.

**Worst Offenders:**

| Function | Pattern | Records Affected |
|----------|---------|-----------------|
| `script_1()` lines 67-80 | Individual UPDATE per attribute value | All attribute values |
| `script_4()` lines 406-478 | Individual UPDATE per PTAV | Thousands of PTAVs |
| `payment_method_update()` lines 1077-1148 | SELECT + UPDATE per sale order | All sale orders with payment methods |
| `recompute_tax_id_on_contacts()` lines 698-715 | Individual UPDATE per contact | All contacts |
| `update_supplier_invoice_number()` lines 1756-1794 | Individual UPDATE per invoice | All vendor invoices |

**Only 4 uses of `executemany()`** in the entire codebase (all in script_2), despite 48 `.create()` calls and 78 `.write()` calls that could benefit from batching.

**Recommendation:** Replace row-by-row processing with:
- `executemany()` for parameterized batch INSERT/UPDATE
- Bulk SQL with `UPDATE ... FROM` or `INSERT ... SELECT` patterns
- ORM `create()` with list of dicts for batch record creation

#### 3.1.3 Redundant Database Queries Inside Loops

**Examples:**

| Function | Issue |
|----------|-------|
| `script_4()` line 407 | `self.env["product.attribute.value"].search()` called per value inside loop |
| `payment_method_update()` lines 1080, 1106, 1132 | Separate SELECT for each sale_order_payment_method lookup |
| `script_5()` line 517 | v13 data SELECT executed per attribute line instead of prefetched |
| `migrate_helpdesk_rma_to_ticket()` lines 213-226 | Multiple SELECTs per RMA record |

**Recommendation:** Prefetch all required data into dictionaries before loops, then lookup from memory.

#### 3.1.4 ORM Operations Where SQL Would Be Faster

**Examples:**

| Function | Current | Better Approach |
|----------|---------|-----------------|
| `script_4()` lines 436, 439, 444 | `inactive_value_active_ptav.ptav_active = False` (triggers ORM) | Direct SQL UPDATE |
| `update_total_cost()` | Creates price_review records via ORM | Bulk INSERT with SQL |
| `script_5()` lines 541-548 | `attribute_value_qty_ids.create()` per qty value | Batch creation |
| `script_6()` lines 683-728 | Individual ORM creates for BOM, BOM lines, config sets | Bulk SQL INSERT |

---

### 3.2 Parallelization Opportunities

**Table Contention Constraints:** Parallelization must account for PostgreSQL table contention. Running multiple processes that UPDATE the same table simultaneously will cause:
- Row-level lock waits (serialization delays)
- Potential deadlocks if transactions acquire locks in different orders
- Transaction serialization failures requiring retry logic

#### 3.2.1 Table Access Matrix - Conflict Analysis

| Function | Primary Table(s) Written | Conflict Group |
|----------|-------------------------|----------------|
| `set_timezones()` | res_partner (tz) | **PARTNER** |
| `recompute_tax_id_on_contacts()` | res_partner (vat) | **PARTNER** |
| `update_compute_complete_address()` | res_partner (contact_address_complete) | **PARTNER** |
| `update_ar_ap_followup_contacts()` | res_partner (ar, ap, followup) | **PARTNER** |
| `update_credit_limit_data()` | res_partner (partner_rollup_id), ir_property | **PARTNER** |
| `merge_partner_data()` | res_partner (heavy - deletes/merges) | **PARTNER** |
| `update_saleorder_substate()` | sale_order (substate_id) | **SALE** |
| `update_inspections()` | sale_order_sale_order_inspection_rel | **SALE-REL** |
| `payment_method_update()` | sale_order, account_move, payment_transaction | **SALE + ACCOUNT** |
| `update_supplier_invoice_number()` | account_move (ref) | **ACCOUNT** |
| `fix_invalid_check_numbers()` | account_payment (check_number) | **PAYMENT** |
| `mig_scrap_reasons()` | scrap_reason_code, stock_scrap | **SCRAP** |
| `update_po_contact_ids()` | purchase_order_res_partner_rel | **PURCHASE** |
| `update_shipping_methods()` | product_template (carrier_multiplier_id) | **PRODUCT** |
| `update_followup_status()` | account_move_line (followup_line_id) | **ACCOUNT-LINE** |

#### 3.2.2 Parallel Groups

**Serial Group: res_partner**
These functions all write to `res_partner` and must run sequentially:
```
set_timezones()
    ↓
recompute_tax_id_on_contacts()
    ↓
update_compute_complete_address()
    ↓
update_ar_ap_followup_contacts()
    ↓
update_credit_limit_data()
    ↓
merge_partner_data()  [must be last - destructive merges]
```

**SERIAL GROUP: sale_order domain**
```
update_saleorder_substate()
    ↓
payment_method_update() [sale_order portion]
```
Note: `update_inspections()` writes to a junction table, not sale_order itself, so it could technically run in parallel with substate update, but the `ON CONFLICT DO NOTHING` clause provides natural protection.

**TRULY PARALLEL GROUP - Isolated Tables:**
These functions write to completely independent tables and CAN safely run in parallel:

| Function | Table | Safe to Parallel |
|----------|-------|------------------|
| `mig_scrap_reasons()` | scrap_reason_code, stock_scrap | YES |
| `update_po_contact_ids()` | purchase_order_res_partner_rel | YES |
| `fix_invalid_check_numbers()` | account_payment | YES |
| `update_shipping_methods()` | product_template (carrier_multiplier_id) | YES* |

*Schedule `update_shipping_methods()` after product scripts complete to avoid conflicts on product_template.

**CONDITIONALLY PARALLEL:**
These can run in parallel with specific groups:

| Function | Can Run With | Cannot Run With |
|----------|--------------|-----------------|
| `update_supplier_invoice_number()` | Partner group, Scrap group | payment_method_update() |
| `update_followup_status()` | Scrap group, Purchase group | Partner group (reads partners) |
| `update_inspections()` | Partner group, Scrap group | update_saleorder_substate() (same SO IDs) |

#### 3.2.3 Company-Based Parallelization

Splitting by company_id can work IF the tables have proper company_id filtering in WHERE clauses. However, PostgreSQL still acquires table-level locks for certain operations (DDL, some constraints).

**Safe to Split by Company:**
| Function | Company Split Safe | Notes |
|----------|-------------------|-------|
| `create_onlogic_locations_and_route()` | YES | stock_location.company_id filtered |
| `mig_scrap_reasons()` | YES | Already iterates per company |
| `update_cost_center_distribution()` | YES | account_move_line filtered by company |
| `update_product_category_account()` | YES | Uses with_company() context |

**Not Safe to Split by Company:**
| Function | Reason |
|----------|--------|
| `merge_partner_data()` | Partners may have cross-company relationships |
| `set_timezones()` | No company_id filter - updates all matching tz |
| `payment_method_update()` | No company filtering in queries |

#### 3.2.4 Product Template Scripts - Batch Parallelization Risk

**The product attribute scripts (3-5) process the SAME tables:**
- product_template_attribute_line
- product_template_attribute_value
- product_attribute_value
- product_variant_combination

**Risk of Batch Parallelization:**
If you split product template IDs into ranges (e.g., IDs 1-10000 to Worker A, 10001-20000 to Worker B), you may still get conflicts because:
1. Attribute values are SHARED across templates
2. Scripts update `product_attribute_value.active` and `product_attribute_value.attribute_id` globally
3. The M2M relation table `product_attribute_value_product_template_attribute_line_rel` can have concurrent inserts

**Recommendation:** Do NOT parallelize scripts 3-5 by template ID batches. The shared attribute data creates cross-batch dependencies.

**Script 6 (BOM creation)** is safer to parallelize because each BOM is independent, but the `mrp_bom_line_configuration_set` table is shared and could cause conflicts on the config_set_map lookups.

#### 3.2.2 Functions with Sequential Dependencies

**Strict Sequential Chain - Product Attributes:**
```
script_1() → script_2() → script_3() → script_4() → script_5() → script_6() → script_7() → script_8()
```
Each script depends on data state established by the previous script.

**Strict Sequential Chain - Module Management:**
```
uninstall_old_module() → install_new_module()
```
Cannot install new modules while old conflicting modules exist.

**Strict Sequential Chain - Accounting Setup:**
```
set_localizations() → update_accounts_from_excel() → delete_account() → update_product_category_account()
```
Chart templates must be set before accounts can be updated.

---

### 3.3 Function-Specific Optimization Recommendations

#### 3.3.1 `script_4()` - CRITICAL (Estimated 30-60 min runtime)

**Current Issues:**
- Commits after every single database operation (~12 commits per template)
- Individual SQL UPDATE per PTAV (line 417-454)
- Individual SQL UPDATE per attribute_value_qty (line 465-478)
- ORM `.search()` inside innermost loop (line 407)

**Optimizations:**
1. **Batch Commits:** Move commit to end of template batch (line 493 exists but inner commits negate it)
2. **Collect Updates:** Build lists of `(id, value)` tuples, then execute single UPDATE with CASE/WHEN or `executemany`
3. **Prefetch Data:** Load all product_attribute_values into a name-keyed dictionary before processing
4. **Remove Inner Commits:** Delete all `cr.commit()` calls inside the product_template loop (lines 394, 412, 422, 433, 437, 440, 445, 454, 470, 478, 490)

**Estimated Savings:** 60-70% of function runtime

#### 3.3.2 `payment_method_update()` - HIGH IMPACT

**Current Issues:**
- Three separate processing loops (sale_order, account_move, payment_transaction)
- Individual SELECT + UPDATE per record
- Repeated `new_payment_data.filtered()` calls per record

**Optimizations:**
1. **Pre-build Mapping:** Create `{old_method_id: new_payment_method_id}` dictionary once
2. **Single Bulk UPDATE:** Replace loops with:
   ```sql
   UPDATE sale_order SET sale_payment_method_id = mapping.new_id
   FROM (VALUES (old1, new1), (old2, new2), ...) AS mapping(old_id, new_id)
   JOIN sale_order_payment_method sopm ON sopm.id = sale_order.payment_method_id
   WHERE mapping.old_id = COALESCE(sopm.sub_method_id, sopm.method_id)
   ```
3. **Parallelize:** Run the three record type updates (sale_order, account_move, payment_transaction) in parallel

**Estimated Savings:** 80-90% of function runtime

#### 3.3.3 `script_6()` - HIGH IMPACT (BOM Creation)

**Current Issues:**
- Individual BOM creation via ORM (line 683)
- Individual BOM line creation via ORM (line 722-728)
- Individual config set creation (line 709)
- `_compute_available_config_components()` called per BOM (line 692)

**Optimizations:**
1. **Batch BOM Creation:** Collect all BOM dicts, create in single `MrpBom.create([list])` call per batch
2. **Batch Config Sets:** Pre-create all needed config sets before BOM loop
3. **SQL for BOM Lines:** Use `INSERT INTO mrp_bom_line ... SELECT ...` for bulk creation
4. **Defer Compute:** Set flag to skip compute during creation, run once at end

**Estimated Savings:** 50-60% of function runtime

#### 3.3.4 `migrate_helpdesk_rma_to_ticket()` - MODERATE IMPACT

**Current Issues:**
- Commits every 10,000 records but creates records individually
- Multiple SQL queries per RMA (lines 213-226)
- Individual repair_order creation inside loop

**Optimizations:**
1. **Prefetch All Data:** Load `temp_helpdesk_rma_line`, `temp_support_repair_order` into dictionaries
2. **Batch Ticket Creation:** Collect ticket dicts, create in batches of 1000
3. **Batch UPDATE:** Collect repair_order updates, execute as single UPDATE with CASE/WHEN

**Estimated Savings:** 40-50% of function runtime

#### 3.3.5 `update_compute_complete_address()` - ALREADY OPTIMIZED

This function is a **good example** of proper batch SQL:
- Uses CTE with UPDATE ... FROM pattern
- Batch size of 50,000
- Single commit per batch

**One Remaining Issue:** Lines 1737-1741 do row-by-row INSERT for `partner_supplier_contact_rel`:
```python
for data in datas:
    self._cr.execute("insert into partner_supplier_contact_rel ...")
```

**Optimization:** Replace with single `INSERT INTO ... SELECT`:
```sql
INSERT INTO partner_supplier_contact_rel (partner_id, contact_id)
SELECT id, default_supplier_contact FROM res_partner 
WHERE default_supplier_contact IS NOT NULL
```

#### 3.3.6 `setting_default_val()` - RECENTLY IMPROVED

The function now has batch processing (BATCH_SIZE = 1000) but still has individual property lookups inside the loop.

**Remaining Issue:** The `AttributeValue.browse(value_id)` and existence check per row could be optimized by prefetching all value_ids validity.

---

### 3.4 Proposed Optimized Execution Plan

#### Phase 1: Pre-Migration Data Preparation
Run before migration begins - no dependencies:
- Create all temp tables in v13
- Export to v17 database

#### Phase 2: Decryption (Sequential - Cannot Parallelize)
Must run first, cannot be parallelized due to data dependencies:
1. `decrypt_char_field()`
2. `decrypt_json_field()`
3. `decrypt_char_field(all_data=True)`

#### Phase 3: Module Management (Sequential)
1. `uninstall_old_module()`
2. `install_new_module()`

#### Phase 4: Core Setup
```
set_localizations()
    ↓
update_accounts_from_excel()
    ↓
delete_account()
    ↓
update_product_category_account()  [Can split US/EU - different company_id filters]
    ↓
update_cost_center_distribution()  [Can split by company - different account_move_line rows]
```

#### Phase 5: Product Migration (Sequential - Shared Tables)
Scripts 1-8 share product_attribute, product_attribute_value, and product_template_attribute_* tables. They must run sequentially.
```
script_1() → script_2() → script_3() → script_4() → script_5() → script_6() → script_7() → script_8()
```
**Do NOT parallelize by template ID batches** - attribute values are shared across templates.

After scripts complete:
```
update_shipping_methods()  [Now safe - no other product_template writes]
```

#### Phase 6: Parallel Stream A - Isolated Tables
These write to completely separate tables and can run in parallel:
```
┌─ mig_scrap_reasons()           [scrap_reason_code, stock_scrap]
├─ update_po_contact_ids()       [purchase_order_res_partner_rel]
├─ fix_invalid_check_numbers()   [account_payment]
└─ update_stock_inventory()      [stock_inventory, stock_move_line]
```

#### Phase 7: Parallel Stream B - Sale Order Domain (Sequential Within)
```
update_saleorder_substate()      [sale_order.substate_id]
    ↓
update_inspections()             [sale_order_sale_order_inspection_rel]
```
Note: These can run IN PARALLEL with Stream A (different tables).

#### Phase 8: Parallel Stream C - Account Domain
```
update_supplier_invoice_number() [account_move.ref]
    ↓
update_followup_status()         [account_move_line.followup_line_id]
```
Can run in parallel with Streams A and B. Do not run with payment_method_update().

After Stream C completes:
```
payment_method_update()          [sale_order, account_move, payment_transaction - touches multiple domains]
```

#### Phase 9: Partner Data (Sequential - Same Table)
All these functions write to res_partner. They must run one at a time:
```
set_timezones()
    ↓
recompute_tax_id_on_contacts()
    ↓
update_compute_complete_address()
    ↓
update_ar_ap_followup_contacts()
    ↓
update_credit_limit_data()
    ↓
merge_partner_data()  [MUST BE LAST - merges/deletes partners]
```

#### Phase 10: Location and Stock
```
set_warehouse_locations()
    ↓
create_onlogic_locations_and_route()  [CAN split US/EU - company_id filtered]
    ↓
tranfer_stock()
    ↓
create_stock_putway_rule()
```

#### Phase 11: Helpdesk/RMA Migration
```
migrate_helpdesk_rma_to_ticket()  [CAN split by company_id - different ticket/repair records]
```

#### Phase 12: Computed Fields (Queue-Based - Inherently Parallel)
`run_all()` already uses `with_delay()` for queue_job parallel processing.
The queue workers will naturally serialize access to the same records.

#### Phase 13: Cleanup
```
drop_temp_tables() → unistall_module()
```

---

### 3.4.1 Channel Execution Matrix

This matrix shows exactly which operations to run, in which channel, and in what order. Channels with the same "Parallel Window" number can run simultaneously.

| Parallel Window | Channel | Step | Function | Table(s) Affected | Wait For |
|-----------------|---------|------|----------|-------------------|----------|
| **WINDOW 0** | MAIN | 1 | `decrypt_char_field()` | ALL encrypted tables | - |
| | MAIN | 2 | `decrypt_json_field()` | ALL json tables | Step 1 |
| | MAIN | 3 | `decrypt_char_field(all_data=True)` | ALL encrypted tables | Step 2 |
| | MAIN | 4 | `uninstall_old_module()` | ir_module_module | Step 3 |
| | MAIN | 5 | `install_new_module()` | ir_module_module | Step 4 |
| | MAIN | 6 | `set_localizations()` | res_company | Step 5 |
| | MAIN | 7 | `update_accounts_from_excel()` | account_account | Step 6 |
| | MAIN | 8 | `delete_account()` | account_account | Step 7 |
| | MAIN | 9 | `update_product_category_account()` | product_category | Step 8 |
| | MAIN | 10 | `update_cost_center_distribution()` | account_move_line | Step 9 |
| **WINDOW 1** | PRODUCT | 1 | `script_1()` | product_attribute | Window 0 |
| | PRODUCT | 2 | `script_2()` | product_attribute_value | Prod Step 1 |
| | PRODUCT | 3 | `script_3()` | product_template_attribute_* | Prod Step 2 |
| | PRODUCT | 4 | `script_4()` | product_template_attribute_* | Prod Step 3 |
| | PRODUCT | 5 | `script_5()` | product_template_attribute_* | Prod Step 4 |
| | PRODUCT | 6 | `script_6()` | mrp_bom, mrp_bom_line | Prod Step 5 |
| | PRODUCT | 7 | `script_7()` | mrp_bom (phantom) | Prod Step 6 |
| | PRODUCT | 8 | `script_8()` | mrp_workcenter | Prod Step 7 |
| | PRODUCT | 9 | `update_shipping_methods()` | product_template | Prod Step 8 |
| **WINDOW 2** | CHANNEL-A | 1 | `mig_scrap_reasons()` | scrap_reason_code, stock_scrap | Window 1 |
| | CHANNEL-A | 2 | `update_po_contact_ids()` | purchase_order_res_partner_rel | Window 1 |
| | CHANNEL-A | 3 | `fix_invalid_check_numbers()` | account_payment | Window 1 |
| | CHANNEL-A | 4 | `update_stock_inventory()` | stock_inventory, stock_move_line | Window 1 |
| **WINDOW 2** | CHANNEL-B | 1 | `update_saleorder_substate()` | sale_order | Window 1 |
| | CHANNEL-B | 2 | `update_inspections()` | sale_order_inspection_rel | B Step 1 |
| **WINDOW 2** | CHANNEL-C | 1 | `update_supplier_invoice_number()` | account_move | Window 1 |
| | CHANNEL-C | 2 | `update_followup_status()` | account_move_line | C Step 1 |
| **WINDOW 3** | MAIN | 1 | `payment_method_update()` | sale_order, account_move, payment_transaction | Window 2 ALL |
| **WINDOW 4** | PARTNER | 1 | `set_timezones()` | res_partner | Window 3 |
| | PARTNER | 2 | `recompute_tax_id_on_contacts()` | res_partner | Partner Step 1 |
| | PARTNER | 3 | `update_compute_complete_address()` | res_partner | Partner Step 2 |
| | PARTNER | 4 | `update_ar_ap_followup_contacts()` | res_partner | Partner Step 3 |
| | PARTNER | 5 | `update_credit_limit_data()` | res_partner, ir_property | Partner Step 4 |
| | PARTNER | 6 | `merge_partner_data()` | res_partner (destructive) | Partner Step 5 |
| **WINDOW 5** | STOCK-US | 1 | `set_warehouse_locations()` | stock_warehouse (US) | Window 4 |
| | STOCK-US | 2 | `create_onlogic_locations_and_route()` [US] | stock_location (company=1) | US Step 1 |
| | STOCK-US | 3 | `tranfer_stock()` [US] | stock_move, stock_quant | US Step 2 |
| | STOCK-US | 4 | `create_stock_putway_rule()` [US] | stock_putaway_rule | US Step 3 |
| **WINDOW 5** | STOCK-EU | 1 | `set_warehouse_locations()` | stock_warehouse (EU) | Window 4 |
| | STOCK-EU | 2 | `create_onlogic_locations_and_route()` [EU] | stock_location (company=2) | EU Step 1 |
| | STOCK-EU | 3 | `tranfer_stock()` [EU] | stock_move, stock_quant | EU Step 2 |
| | STOCK-EU | 4 | `create_stock_putway_rule()` [EU] | stock_putaway_rule | EU Step 3 |
| **WINDOW 5** | RMA-US | 1 | `migrate_helpdesk_rma_to_ticket()` [US] | helpdesk_ticket, repair_order | Window 4 |
| **WINDOW 5** | RMA-EU | 1 | `migrate_helpdesk_rma_to_ticket()` [EU] | helpdesk_ticket, repair_order | Window 4 |
| **WINDOW 6** | QUEUE | 1 | `run_all()` | Various (queue_job managed) | Window 5 |
| **WINDOW 7** | CLEANUP | 1 | `drop_temp_tables()` | temp_* tables | Window 6 |
| | CLEANUP | 2 | `unistall_module()` | ir_module_module | Cleanup Step 1 |

---

### 3.4.2 Execution Summary by Window

**Window 0 - Sequential Bootstrap (est. 60-75 min)**
- Single channel, must complete before anything else
- Decryption, module management, core account setup

**Window 1 - Product Migration (est. 90-120 min)**
- Single channel (PRODUCT), sequential scripts 1-8
- Cannot parallelize due to shared attribute tables

**Window 2 - Triple Parallel Channels (est. 15-25 min)**
- CHANNEL-A: 4 functions hitting isolated tables (run all simultaneously within channel)
- CHANNEL-B: 2 functions on sale_order domain (sequential within channel)
- CHANNEL-C: 2 functions on account domain (sequential within channel)
- **All three channels run AT THE SAME TIME**

**Window 3 - Cross-Domain Payment (est. 20-30 min)**
- Single function that touches multiple domains
- Must wait for Window 2 to avoid conflicts with sale_order and account_move

**Window 4 - Partner Sequential (est. 30-45 min)**
- Single channel, 6 functions all writing to res_partner
- Sequential execution required - no parallelization possible

**Window 5 - Location/RMA by Company (est. 20-30 min)**
- Up to 4 parallel channels: STOCK-US, STOCK-EU, RMA-US, RMA-EU
- Company filtering ensures no row conflicts

**Window 6 - Computed Fields (est. 30-60 min)**
- Queue job workers handle parallelization internally

**Window 7 - Cleanup (est. 5-10 min)**
- Drop temp tables and uninstall migration module

---

### 3.4.3 Visual Timeline

```
TIME →
═══════════════════════════════════════════════════════════════════════════════
WINDOW 0: MAIN CHANNEL (Sequential)
│ decrypt_char ─► decrypt_json ─► decrypt_all ─► uninstall ─► install ─► ...
═══════════════════════════════════════════════════════════════════════════════
WINDOW 1: PRODUCT CHANNEL (Sequential)
│ script_1 ─► script_2 ─► script_3 ─► script_4 ─► script_5 ─► script_6 ─► script_7 ─► script_8 ─► shipping
═══════════════════════════════════════════════════════════════════════════════
WINDOW 2: PARALLEL CHANNELS (Run A, B, C simultaneously)
│
│ CHANNEL-A: ██████████████████████████████████████████████████████████████████
│            mig_scrap ║ update_po ║ fix_checks ║ stock_inv  (all 4 parallel)
│
│ CHANNEL-B: ████████████████████████████
│            substate ─────► inspections
│
│ CHANNEL-C: ████████████████████████████████████
│            supplier_inv ─────► followup
│
═══════════════════════════════════════════════════════════════════════════════
WINDOW 3: CROSS-DOMAIN (must wait for Window 2)
│ payment_method_update
═══════════════════════════════════════════════════════════════════════════════
WINDOW 4: PARTNER CHANNEL (Sequential - all write res_partner)
│ timezones ─► tax_id ─► complete_addr ─► ar_ap ─► credit_limit ─► merge
═══════════════════════════════════════════════════════════════════════════════
WINDOW 5: COMPANY-SPLIT CHANNELS (US and EU run in parallel)
│
│ STOCK-US: ████████████████████████████████████████
│           warehouse ─► locations ─► transfer ─► putaway
│
│ STOCK-EU: ████████████████████████████████████████
│           warehouse ─► locations ─► transfer ─► putaway
│
│ RMA-US:   ██████████████████████████
│           helpdesk_rma_to_ticket
│
│ RMA-EU:   ██████████████████████████
│           helpdesk_rma_to_ticket
│
═══════════════════════════════════════════════════════════════════════════════
WINDOW 6: QUEUE WORKERS (internal parallelization)
│ run_all() with with_delay()
═══════════════════════════════════════════════════════════════════════════════
WINDOW 7: CLEANUP
│ drop_temp_tables ─► uninstall_module
═══════════════════════════════════════════════════════════════════════════════
```

---

### 3.5 Time Analysis

**Actual Measured Timings:**

| Phase | Actual (min) | Optimization Potential | Notes |
|-------|--------------|------------------------|-------|
| Decryption | 148 | Low | Already batch-optimized |
| Uninstall Old Module | 9 | None | Fixed overhead |
| Module Installations | 114 | None | Odoo core process |
| After Decryption | 18 | Low | Minor cleanup tasks |
| Post Migration Scripts | 226 | High | Batch commits, SQL optimization |
| Product Migration Scripts | 223 | Medium | Sequential - shared tables |
| MO, RMA, Other Scripts | 112 | Medium | Company-split parallelization possible |
| **Total** | **850** | | **~14.2 hours** |

**Key Constraint:** Table contention limits parallelization opportunities. See Section 3.2.1 for the table access matrix.

**Safe Parallelization Groups:**

| Parallel Group | Tables | Potential Savings |
|----------------|--------|-------------------|
| mig_scrap_reasons + update_po_contact_ids + fix_invalid_check_numbers | scrap_reason_code, purchase_order_res_partner_rel, account_payment | 10-15 min |
| Company-split for locations/RMA | Filtered by company_id | 5-10 min |
| Streams A/B/C (Phase 6-8 in execution plan) | Isolated tables | 15-20 min |

---

### 3.6 Detailed Optimization Opportunities

#### 3.6.1 Commit Pattern Analysis

Total commit calls found across all files: **180**

| File | Commit Count | Severity |
|------|--------------|----------|
| ir_server_action_2.py | 64 | HIGH |
| ir_server_action_1.py | 24 | MEDIUM |
| ir_server_action_2_old.py | 81 | HIGH (legacy) |
| ir_server_action.py | 9 | LOW |

**Functions with excessive inner-loop commits:**

| Function | Commits in Loop | Lines | Impact |
|----------|-----------------|-------|--------|
| `script_3()` | ~8 per template | 205, 247, 255, 267, 305, 308, 324, 346, 349 | HIGH |
| `script_4()` | ~11 per template | 394, 412, 422, 433, 437, 440, 445, 454, 470, 478, 490 | HIGH |
| `script_5()` | ~7 per template | 534, 549, 555, 568, 585, 601, 604 | HIGH |
| `recompute_tax_id_on_contacts()` | 1 per contact | 715 | HIGH |
| `migrate_helpdesk_rma_to_ticket()` | 1 per 10k records | 266, 442, 444 | MEDIUM |

#### 3.6.2 Row-by-Row Operations (Should be Bulk)

| Function | Pattern | Lines | Optimization |
|----------|---------|-------|--------------|
| `update_po_contact_ids()` | Row-by-row INSERT | 1751-1754 | Use `INSERT INTO...SELECT` |
| `update_compute_complete_address()` | Row-by-row INSERT for rel table | 1737-1741 | Use `INSERT INTO...SELECT` |
| `update_inspections()` | Row-by-row INSERT | 455-482 | Use `executemany()` or `INSERT...SELECT` |
| `update_supplier_invoice_number()` | Row-by-row UPDATE | 1792-1794 | Use UPDATE with CASE/WHEN or temp table JOIN |
| `update_ar_ap_followup_contacts()` | Row-by-row UPDATE | 1506-1512 | Use `UPDATE...FROM` with JOIN |
| `mig_scrap_reasons()` | Individual ORM create | 1165-1169 | Use batch `create([list])` |

#### 3.6.3 Repeated Database Queries in Loops

| Function | Issue | Lines | Optimization |
|----------|-------|-------|--------------|
| `migrate_helpdesk_rma_to_ticket()` | 3-5 SQL queries per RMA | 213-226, 291-360 | Prefetch all data into dicts before loop |
| `payment_method_update()` | Individual SELECT per sale_order/move/transaction | 1080-1148 | Pre-join data with single query |
| `script_5()` | `search()` inside nested loops | 598-599 | Build lookup dict before processing |
| `script_6()` | `search()` for attribute lines per template | 694 | Use SQL with JOIN or prefetch |
| `update_phantoms_bom_data()` | `with_company()` in nested loop | 1607-1636 | Process all companies at once with SQL |

#### 3.6.4 ORM vs. SQL Opportunities

| Function | Current Approach | Better Approach | Impact |
|----------|------------------|-----------------|--------|
| `mig_scrap_reasons()` | Individual `create()` | Batch `create([list])` | MEDIUM |
| `script_6()` | Individual BOM creation | Batch BOM creation | HIGH |
| `update_product_category_account()` | Loop with `write()` | Single UPDATE with CASE | MEDIUM |
| `update_followup_status()` | ORM `write()` per partner | Bulk UPDATE via SQL | MEDIUM |
| `update_phantoms_bom_data()` | `with_company()` per company | Single SQL update | HIGH |

#### 3.6.5 Specific Function Optimizations

**`payment_method_update()` (lines 1030-1148) - Estimated 20-30 min**
- Current: 3 separate loops (sale_order, account_move, payment_transaction)
- Each loop: SELECT per record + conditional logic + UPDATE per record
- Optimization: Pre-build mapping dict, use single UPDATE with CASE/WHEN:
```sql
UPDATE sale_order 
SET sale_payment_method_id = CASE 
    WHEN payment_method_id IN (SELECT id FROM sale_order_payment_method WHERE sub_method_id = 10) THEN <payment_terms_id>
    WHEN payment_method_id IN (SELECT id FROM sale_order_payment_method WHERE sub_method_id IN (9, 16)) THEN <card_id>
    ...
END
WHERE payment_method_id IS NOT NULL;
```

**`migrate_helpdesk_rma_to_ticket()` (lines 157-444) - Estimated 30-45 min**
- Current: For each RMA, executes 3-6 SQL queries and creates records individually
- Optimization: 
  1. Prefetch all `temp_helpdesk_rma_line` into dict keyed by rma_id
  2. Prefetch all `temp_support_repair_order` into dict keyed by rma_line_id
  3. Batch ticket creation with `Ticket.create([list])`
  4. Batch repair_order updates with single UPDATE

**`script_3()`, `script_4()`, `script_5()` - Combined estimated 60-90 min**
- Current: Commits after nearly every database operation
- Optimization: 
  1. Remove ALL inner-loop commits
  2. Commit only at batch boundaries (every 100-500 templates)
  3. Use `executemany()` for bulk updates
  4. Pre-load attribute lookups into memory

---

### 3.6.6 Quick Wins Summary (Minimal Code Changes, High Impact)

| Priority | Change | Impact | Risk |
|----------|--------|--------|------|
| 1 | Remove inner loop commits in script_3/4/5 | 60-90 min | LOW |
| 2 | Batch commits in recompute_tax_id_on_contacts() | 25-30 min | LOW |
| 3 | Pre-build payment method mapping dict | 20-30 min | LOW |
| 4 | Prefetch RMA data before migrate_helpdesk_rma_to_ticket() loop | 15-25 min | MEDIUM |
| 5 | Replace row-by-row INSERTs with INSERT...SELECT | 10-15 min | LOW |
| 6 | Replace row-by-row UPDATEs with UPDATE...FROM JOIN | 10-15 min | LOW |
| 7 | Increase batch sizes (script_3/4: 100→300, script_5: 10→50) | 10-15 min | MEDIUM |
| 8 | Batch ORM creates in mig_scrap_reasons() | 5-10 min | LOW |

**Total Potential Savings from Code Optimizations: 155-230 minutes (2.5-4 hours)**

---

### 3.7 PostgreSQL Lock Considerations

#### Row-Level vs. Table-Level Locks
- **UPDATE with WHERE clause:** Acquires ROW EXCLUSIVE lock on specific rows
- **Multiple UPDATEs to same table, different rows:** Generally safe, but heavy write load can cause checkpoint pressure
- **Multiple UPDATEs to same rows:** WILL serialize - second transaction waits for first to commit
- **Bulk operations (DELETE, TRUNCATE):** Can escalate to table-level locks

#### Deadlock Risk Scenarios
```
Transaction A: UPDATE res_partner SET tz = 'X' WHERE id = 1;
Transaction A: UPDATE res_partner SET vat = 'Y' WHERE id = 2;  -- waiting

Transaction B: UPDATE res_partner SET vat = 'Z' WHERE id = 2;
Transaction B: UPDATE res_partner SET tz = 'W' WHERE id = 1;  -- DEADLOCK
```

**Prevention:** When functions operate on the same table, ensure they either:
1. Run sequentially (safest)
2. Process mutually exclusive row sets (e.g., company_id filtering with guaranteed no overlap)
3. Acquire locks in consistent order (complex to implement)

#### Index Contention
Heavy concurrent writes can also cause B-tree index page splits and contention. Tables with many indexes (like res_partner with ~20+ indexes) are particularly vulnerable.

#### Recommendations for Production
- Set `statement_timeout` to detect stalled queries
- Monitor `pg_stat_activity` for lock waits during migration
- Consider `SET LOCAL lock_timeout = '30s'` in long-running functions to fail fast on contention
- Transaction isolation level should remain READ COMMITTED (default)

---

### 3.8 Advanced: Parallel Compute with Batch Writes (Higher Risk)

This section describes an advanced optimization pattern: parallelizing the computation phase of loops while keeping writes sequential and batched. This approach carries higher risk due to Odoo ORM thread safety concerns and increased code complexity.

#### 3.8.1 Pattern Overview

**Current Pattern (Sequential):**
```python
for record in records:
    computed_value = expensive_computation(record)  # SLOW
    cr.execute("UPDATE ... SET x = %s WHERE id = %s", (computed_value, record.id))
    cr.commit()  # SLOW
```

**Optimized Pattern (Parallel Compute + Batch Write):**
```python
from concurrent.futures import ThreadPoolExecutor

def compute_only(record_data):
    # Pure computation - no ORM, no DB writes
    return (record_data['id'], expensive_computation(record_data))

# Phase 1: Parallel compute (no DB access)
with ThreadPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(compute_only, record_data_list))

# Phase 2: Sequential batch write
cr.executemany("UPDATE ... SET x = %s WHERE id = %s", results)
cr.commit()
```

#### 3.8.2 Function-by-Function Analysis

##### `payment_method_update()` - GOOD CANDIDATE

**Current Code Analysis (lines 1041-1148):**
```python
# Current: 3 loops, each with per-record SQL SELECT and UPDATE
for sale in sale_order_data:
    cr.execute("select id,sub_method_id,method_id from sale_order_payment_method where id = %s", (sale[1],))
    data = cr.dictfetchone()
    name = payment_methods.get(data.get('sub_method_id') or data.get('method_id'))
    # ... name mapping logic ...
    payment = new_payment_data.filtered(lambda l: l.name == name)  # ORM filtered()
    cr.execute("update sale_order set sale_payment_method_id = %s where id = %s", (payment.id, sale[0]))
```

**Bottlenecks Identified:**
1. SQL SELECT per record to get method details (could be JOIN)
2. ORM `filtered()` call per record (could be pre-built dict)
3. SQL UPDATE per record (could be `executemany`)

**Parallelization Feasibility: HIGH**
- Compute phase is almost pure Python (dict lookups, string comparisons)
- `filtered()` can be replaced with pre-built dict
- All data can be prefetched with single JOIN query

**Proposed Approach:**
```python
# Phase 1: Prefetch all data with JOIN
cr.execute("""
    SELECT so.id, sopm.method_id, sopm.sub_method_id
    FROM sale_order so
    JOIN sale_order_payment_method sopm ON so.payment_method_id = sopm.id
    WHERE so.payment_method_id IS NOT NULL
""")
sale_data = cr.fetchall()

# Pre-build name-to-id mapping (replaces filtered() calls)
name_to_payment_id = {pm.name: pm.id for pm in new_payment_data}

# Phase 2: Parallel compute (pure Python)
def compute_payment(row):
    sale_id, method_id, sub_method_id = row
    name = payment_methods.get(sub_method_id) if sub_method_id else payment_methods.get(method_id)
    if name == 'Net Terms': name = 'Payment Terms'
    elif name in ('Credit Card', 'Credit Card Prepayment'): name = 'Card'
    new_id = name_to_payment_id.get(name)
    return (new_id, sale_id) if new_id else None

with ThreadPoolExecutor(max_workers=4) as executor:
    updates = [r for r in executor.map(compute_payment, sale_data) if r]

# Phase 3: Batch write
cr.executemany("UPDATE sale_order SET sale_payment_method_id = %s WHERE id = %s", updates)
cr.commit()
```

**Estimated Savings:** 15-20 minutes | **Risk:** LOW

---

##### `update_supplier_invoice_number()` - NOT PARALLELIZABLE

**Current Code Analysis (lines 1756-1794):**
```python
duplicate_supplier_numbers = set()
for move in move_ids:
    supplier_invoice_number = move.get("supplier_invoice_number")
    is_duplicate = supplier_invoice_number in duplicate_supplier_numbers  # Sequential dependency!
    duplicate_supplier_numbers.add(supplier_invoice_number)
    # ... build new_ref based on is_duplicate ...
    cr.execute("UPDATE account_move SET ref = %s WHERE id = %s", (new_ref, move_id))
```

**Parallelization Feasibility: NOT POSSIBLE**
- The duplicate detection requires checking if a value exists in a set that is being built during iteration
- Each iteration depends on the results of ALL previous iterations
- This is inherently sequential logic

**Better Optimization:** Use `executemany()` for batch writes, but computation must remain sequential.

---

##### `recompute_tax_id_on_contacts()` - COMPLEX CANDIDATE

**Current Code Analysis (lines 690-715):**
```python
contacts = Partner.search([('is_company', '=', False), ('active', '=', True)])
for contact in contacts:
    parent = contact.parent_id  # ORM field access
    while parent and not parent.parent_id:  # Parent chain traversal
        parent = parent.parent_id
    if parent and parent.vat:
        tax_id_to_set = parent.vat
    if not tax_id_to_set:
        commercial_entity = contact.commercial_partner_id  # ORM field access
        if commercial_entity and commercial_entity.vat:
            tax_id_to_set = commercial_entity.vat
    if tax_id_to_set and contact.vat != tax_id_to_set:
        cr.execute("update res_partner set vat = %s where id = %s", (tax_id_to_set, contact.id))
        cr.commit()
```

**Bottlenecks Identified:**
1. ORM field access (`contact.parent_id`, `contact.commercial_partner_id`) inside loop
2. While loop traverses parent chain (could be multiple levels)
3. Commit after EACH update

**Parallelization Feasibility: MEDIUM**
- Requires prefetching ALL parent relationships (recursive CTE or multiple JOINs)
- Parent chain traversal logic is complex to convert to pure SQL
- Can be done but requires significant refactoring

**Proposed Approach:**
```python
# Phase 1: Prefetch all needed data with recursive CTE
cr.execute("""
    WITH RECURSIVE parent_chain AS (
        SELECT id, parent_id, commercial_partner_id, vat, 0 as depth
        FROM res_partner
        WHERE is_company = false AND active = true
        
        UNION ALL
        
        SELECT c.id, p.parent_id, c.commercial_partner_id, 
               COALESCE(p.vat, c.vat) as vat, c.depth + 1
        FROM parent_chain c
        JOIN res_partner p ON c.parent_id = p.id
        WHERE c.depth < 10  -- Safety limit
    ),
    final_vat AS (
        SELECT DISTINCT ON (id) id, vat
        FROM parent_chain
        WHERE vat IS NOT NULL
        ORDER BY id, depth DESC
    )
    SELECT c.id, c.vat as current_vat, 
           COALESCE(f.vat, cp.vat) as new_vat
    FROM res_partner c
    LEFT JOIN final_vat f ON c.id = f.id
    LEFT JOIN res_partner cp ON c.commercial_partner_id = cp.id
    WHERE c.is_company = false AND c.active = true
""")
contact_data = cr.fetchall()

# Phase 2: Parallel compute (pure Python comparison)
def compute_vat(row):
    contact_id, current_vat, new_vat = row
    if new_vat and new_vat != current_vat:
        return (new_vat, contact_id)
    return None

with ThreadPoolExecutor(max_workers=4) as executor:
    updates = [r for r in executor.map(compute_vat, contact_data) if r]

# Phase 3: Batch write
cr.executemany("UPDATE res_partner SET vat = %s WHERE id = %s", updates)
cr.commit()
```

**Estimated Savings:** 15-20 minutes | **Risk:** MEDIUM (recursive CTE complexity)

---

##### `update_followup_status()` - NOT PARALLELIZABLE

**Current Code Analysis (lines 18-65):**
```python
for partner in partners.filtered(lambda p: p.followup_status in [...]):
    aml_lines = partner.unreconciled_aml_ids.filtered(lambda aml:
        aml.company_id == company
        and aml.account_id.account_type == 'asset_receivable'
        # ... more ORM field access ...
    )
    overdue_days = [(today - aml.date_maturity).days for aml in aml_lines]
    # ... followup line matching ...
    aml_lines.write({'followup_line_id': followup_line.id})
```

**Parallelization Feasibility: NOT POSSIBLE**
- Heavy ORM dependencies: `partner.unreconciled_aml_ids` is a computed/related field
- Multiple ORM `filtered()` calls with complex lambda expressions
- `aml.company_id`, `aml.account_id.account_type`, `aml.move_id.move_type` are all ORM field accesses
- Would require completely rewriting to use raw SQL, losing ORM benefits

---

##### `migrate_helpdesk_rma_to_ticket()` - NOT PARALLELIZABLE

**Current Code Analysis (lines 157-444):**
```python
for rma in rma_data_ids:
    cr.execute("select id from temp_helpdesk_rma_line where rma_id = %s", (rma.get("id"),))
    # ... more queries ...
    ticket_id = Ticket.create(vals)  # ORM create returns ID needed for next operations
    if historical_repair_order_ids:
        cr.execute("update repair_order set ticket_id = %s where id in %s", (ticket_id.id, ...))
    else:
        repair_id = repair_obj.create(repair)  # Depends on ticket_id
        # ... more operations depending on repair_id ...
```

**Parallelization Feasibility: NOT POSSIBLE**
- Strong sequential dependencies: ticket_id is needed for repair_order creation
- repair_id is needed for stock_move updates
- ORM `create()` operations cannot be parallelized
- The `get_stage()` function calls `self.env.ref()` which is not thread-safe

---

##### `script_3()`, `script_4()`, `script_5()` - NOT PARALLELIZABLE

**Current Code Analysis (script_3, lines 188-375):**
```python
for product_template in batch_products:
    for line in product_template.attribute_line_ids:  # ORM field
        value_ids = line.product_template_value_ids.filtered(lambda v: v.ptav_active)  # ORM filtered
        for name, duplicates in grouped_values.items():
            active_value_id = self.env["product.attribute.value"].search([...])  # ORM search inside loop!
            active_ptav = self.env["product.template.attribute.value"].search([...])  # Another search!
            active_ptav.write({"ptav_active": True})  # ORM write
```

**Parallelization Feasibility: NOT POSSIBLE**
- Nearly every operation is ORM-dependent
- `search()` calls inside nested loops
- `filtered()` with lambda expressions
- `write()` operations scattered throughout
- Complex attribute matching logic that depends on ORM relationships
- Would require complete rewrite to raw SQL, losing data integrity benefits

---

#### 3.8.3 Summary: Actual Parallelization Candidates

| Function | Parallelizable | Reason |
|----------|----------------|--------|
| `payment_method_update()` | **YES** | Compute is pure dict lookups after prefetch |
| `recompute_tax_id_on_contacts()` | **PARTIAL** | Requires complex recursive CTE, then pure Python |
| `update_supplier_invoice_number()` | **NO** | Sequential duplicate detection dependency |
| `update_followup_status()` | **NO** | Heavy ORM dependencies throughout |
| `migrate_helpdesk_rma_to_ticket()` | **NO** | Sequential ticket_id/repair_id dependencies |
| `script_3()` | **NO** | ORM search/filtered/write throughout |
| `script_4()` | **NO** | ORM search/filtered/write throughout |
| `script_5()` | **NO** | ORM search/filtered/write throughout |

#### 3.8.4 Realistic Savings Estimate

| Function | Current Time | Optimized Time | Savings | Risk |
|----------|--------------|----------------|---------|------|
| `payment_method_update()` | 20-30 min | 5-10 min | 15-20 min | LOW |
| `recompute_tax_id_on_contacts()` | 25-30 min | 10-15 min | 10-15 min | MEDIUM |

**Realistic Additional Savings from Parallel Compute: 25-35 minutes**

Note: This is significantly lower than the initial estimate of 60-80 minutes because most functions have ORM or sequential dependencies that prevent parallelization.

#### 3.8.5 Implementation Risks

| Risk | Description | Mitigation |
|------|-------------|------------|
| ORM Thread Safety | Odoo ORM is NOT thread-safe | Use only raw SQL or plain Python in workers |
| Cursor Sharing | Database cursors cannot be shared | Compute without DB access |
| Environment Isolation | `self.env` is not thread-safe | Pass only primitive data to workers |
| Recursive CTE Complexity | Parent chain queries are complex | Test thoroughly, add depth limits |

#### 3.8.6 Recommendation

1. **Implement** parallel compute for `payment_method_update()` - low risk, good savings
2. **Consider** `recompute_tax_id_on_contacts()` only if the recursive CTE approach is validated
3. **Do not attempt** parallelization for RMA migration, followup status, or product scripts - the refactoring effort exceeds the potential benefit

---

### 3.9 Final Time Estimates

This section consolidates all optimization opportunities identified in this document to provide realistic time savings estimates.

#### 3.9.1 Current Baseline (Actual Measured)

| Phase | Current (min) | Current (hrs) |
|-------|---------------|---------------|
| Decryption | 148 | 2.5 |
| Uninstall Old Module | 9 | 0.2 |
| Module Installations | 114 | 1.9 |
| After Decryption | 18 | 0.3 |
| Post Migration Scripts | 226 | 3.8 |
| Product Migration Scripts | 223 | 3.7 |
| MO, RMA, Other Scripts | 112 | 1.9 |
| **TOTAL** | **850** | **14.2** |

#### 3.9.2 Safe Optimizations (Low Risk)

These optimizations involve straightforward code changes with minimal risk of introducing bugs.

| Optimization | Affected Phase | Savings (min) | Risk |
|--------------|----------------|---------------|------|
| Remove inner loop commits in script_3() | Product Migration | 20-30 | LOW |
| Remove inner loop commits in script_4() | Product Migration | 25-35 | LOW |
| Remove inner loop commits in script_5() | Product Migration | 15-25 | LOW |
| Batch commits in recompute_tax_id_on_contacts() | Post Migration | 25-30 | LOW |
| Pre-build payment method mapping dict | Post Migration | 20-30 | LOW |
| Replace row-by-row INSERTs with INSERT...SELECT | Post Migration | 10-15 | LOW |
| Replace row-by-row UPDATEs with UPDATE...FROM | Post Migration | 10-15 | LOW |
| Batch ORM creates in mig_scrap_reasons() | MO, RMA, Other | 5-10 | LOW |
| Increase batch sizes (script_3/4: 100→300) | Product Migration | 5-10 | LOW |
| Run isolated table functions in parallel (Window 2) | Post Migration | 15-20 | LOW |
| **SUBTOTAL - Safe Optimizations** | | **150-220** | |

#### 3.9.3 Medium Risk Optimizations

These require more careful implementation and testing.

| Optimization | Affected Phase | Savings (min) | Risk |
|--------------|----------------|---------------|------|
| Prefetch RMA data before loop | MO, RMA, Other | 15-25 | MEDIUM |
| Increase script_5 batch size (10→50) | Product Migration | 5-10 | MEDIUM |
| Company-split for locations/RMA (Window 5) | MO, RMA, Other | 5-10 | MEDIUM |
| **SUBTOTAL - Medium Risk** | | **25-45** | |

#### 3.9.4 Higher Risk Optimizations

These involve significant refactoring and carry higher implementation risk.

| Optimization | Affected Phase | Savings (min) | Risk |
|--------------|----------------|---------------|------|
| Parallel compute + batch write for payment_method_update() | Post Migration | 15-20 | HIGH |
| Recursive CTE + parallel compute for recompute_tax_id | Post Migration | 10-15 | HIGH |
| **SUBTOTAL - Higher Risk** | | **25-35** | |

#### 3.9.5 Optimizations NOT Recommended

These were evaluated but determined to be not viable or not worth the effort.

| Optimization | Reason Not Recommended |
|--------------|------------------------|
| Parallelize script_3/4/5 by template batches | ORM dependencies throughout, shared attribute tables |
| Parallelize update_supplier_invoice_number() | Sequential duplicate detection logic |
| Parallelize update_followup_status() | Heavy ORM field access dependencies |
| Parallelize migrate_helpdesk_rma_to_ticket() | Sequential ticket_id/repair_id creation chain |
| Parallelize res_partner functions | All 6 functions write to same table |

#### 3.9.6 Final Estimates by Scenario

**Scenario A: Safe Optimizations Only**

| Phase | Current | Savings | Optimized | Notes |
|-------|---------|---------|-----------|-------|
| Decryption | 148 | 0 | 148 | Already optimized |
| Uninstall Old Module | 9 | 0 | 9 | Fixed overhead |
| Module Installations | 114 | 0 | 114 | Odoo core process |
| After Decryption | 18 | 0 | 18 | Minor tasks |
| Post Migration Scripts | 226 | 80-110 | 116-146 | Commit batching, bulk SQL |
| Product Migration Scripts | 223 | 65-100 | 123-158 | Remove inner commits |
| MO, RMA, Other Scripts | 112 | 5-10 | 102-107 | Batch ORM creates |
| **TOTAL** | **850** | **150-220** | **630-700** | |
| **Hours** | **14.2** | **2.5-3.7** | **10.5-11.7** | |

**Scenario B: Safe + Medium Risk Optimizations**

| Phase | Current | Savings | Optimized | Notes |
|-------|---------|---------|-----------|-------|
| Decryption | 148 | 0 | 148 | Already optimized |
| Uninstall Old Module | 9 | 0 | 9 | Fixed overhead |
| Module Installations | 114 | 0 | 114 | Odoo core process |
| After Decryption | 18 | 0 | 18 | Minor tasks |
| Post Migration Scripts | 226 | 80-110 | 116-146 | Commit batching, bulk SQL |
| Product Migration Scripts | 223 | 70-110 | 113-153 | Remove commits + batch sizes |
| MO, RMA, Other Scripts | 112 | 25-45 | 67-87 | RMA prefetch + company split |
| **TOTAL** | **850** | **175-265** | **585-675** | |
| **Hours** | **14.2** | **2.9-4.4** | **9.8-11.3** | |

**Scenario C: All Optimizations (Including Higher Risk)**

| Phase | Current | Savings | Optimized | Notes |
|-------|---------|---------|-----------|-------|
| Decryption | 148 | 0 | 148 | Already optimized |
| Uninstall Old Module | 9 | 0 | 9 | Fixed overhead |
| Module Installations | 114 | 0 | 114 | Odoo core process |
| After Decryption | 18 | 0 | 18 | Minor tasks |
| Post Migration Scripts | 226 | 105-145 | 81-121 | + parallel compute |
| Product Migration Scripts | 223 | 70-110 | 113-153 | Remove commits + batch sizes |
| MO, RMA, Other Scripts | 112 | 25-45 | 67-87 | RMA prefetch + company split |
| **TOTAL** | **850** | **200-300** | **550-650** | |
| **Hours** | **14.2** | **3.3-5.0** | **9.2-10.8** | |

#### 3.9.7 Summary

| Scenario | Total Savings | Final Runtime | Reduction |
|----------|---------------|---------------|-----------|
| Current (No Changes) | 0 | 14.2 hours | 0% |
| **A: Safe Only** | 150-220 min | 10.5-11.7 hours | **18-26%** |
| **B: Safe + Medium** | 175-265 min | 9.8-11.3 hours | **20-31%** |
| **C: All Optimizations** | 200-300 min | 9.2-10.8 hours | **24-35%** |

#### 3.9.8 Recommended Implementation Order

**Phase 1 - Quick Wins (~100 min savings)**
1. Remove inner loop commits in script_3/4/5
2. Batch commits in recompute_tax_id_on_contacts()
3. Pre-build payment method mapping dict

**Phase 2 - Bulk Operations (~40 min savings)**
4. Replace row-by-row INSERTs with INSERT...SELECT
5. Replace row-by-row UPDATEs with UPDATE...FROM
6. Batch ORM creates in mig_scrap_reasons()

**Phase 3 - Parallelization (~20 min savings)**
7. Run isolated table functions in parallel (Window 2)
8. Increase batch sizes for script_3/4/5

**Phase 4 - Medium Risk (~30 min savings)**
9. Prefetch RMA data before migrate_helpdesk_rma_to_ticket()
10. Company-split parallelization for locations/RMA

**Phase 5 - Higher Risk (Optional, ~30 min savings)**
11. Parallel compute for payment_method_update()
12. Recursive CTE approach for recompute_tax_id_on_contacts()

---

## Copyright

Copyright (C) 2024 - Open Source Integrators
License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

Documentation compiled by Artic Tern LLC
