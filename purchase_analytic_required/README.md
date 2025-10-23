# Purchase Analytic Required

This module extends the `purchase_analytic` module to enforce analytic account requirements on purchase orders based on the account's analytic policy settings.

## Problem Solved

When Purchase Order 1532 (or any purchase order) is validated, it may fail with an error about missing analytic accounts. This happens when:

1. The product's expense account has an analytic policy set to "Always" or "Posted moves"
2. The purchase order lines don't have analytic distribution assigned
3. The `account_analytic_required` module enforces this requirement at the account move line level

## Solution

This module provides:

1. **Validation at Purchase Order Level**: Checks analytic requirements before confirming purchase orders
2. **Validation at Purchase Order Line Level**: Validates analytic distribution when creating/updating lines
3. **Improved UI**: Makes analytic distribution fields more prominent and required
4. **Clear Error Messages**: Provides detailed information about which products/accounts need analytic distribution

## Features

- Validates analytic distribution requirements before purchase order confirmation
- Validates analytic distribution requirements when creating/updating purchase order lines
- Makes analytic distribution fields required in the UI when needed
- Provides clear error messages indicating which products need analytic distribution
- Supports all analytic policy types: Optional, Always, Posted moves, Never
- Inherits from existing `purchase_analytic` module without modifying core Odoo

## Installation

This module automatically installs when both `purchase_analytic` and `account_analytic_required` modules are installed.

## Usage

1. Set up analytic accounts and plans
2. Configure account analytic policies in Accounting > Configuration > Chart of Accounts
3. Create purchase orders with products that have expense accounts requiring analytic distribution
4. The system will now validate and enforce analytic distribution requirements

## Technical Details

- Inherits from `purchase.order` and `purchase.order_line` models
- Overrides `button_confirm()` and `_prepare_invoice()` methods
- Adds `@api.constrains` validation on purchase order lines
- Extends XML views to make analytic fields more prominent
- Includes comprehensive test coverage

## Dependencies

- `purchase_analytic`
- `account_analytic_required`
- `purchase`
- `analytic`
