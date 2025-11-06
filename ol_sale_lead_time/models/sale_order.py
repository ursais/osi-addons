# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta
from collections import defaultdict
import logging

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    """Extend sale order with ESD calculation functionality."""
    _inherit = 'sale.order'

    estimated_ship_date = fields.Date(
        string='Estimated Ship Date',
        readonly=True,
        help='Calculated maximum ship date across all lines'
    )

    last_esd_calculation = fields.Datetime(
        string='Last ESD Calculation',
        readonly=True,
        help='Timestamp of last calculation'
    )

    esd_calculation_status = fields.Selection(
        [
            ('success', 'Success'),
            ('warning', 'Warning'),
            ('error', 'Error'),
        ],
        string='ESD Calculation Status',
        readonly=True,
        default='success',
        help='Status of the last ESD calculation'
    )

    rush_order = fields.Boolean(
        string='Rush Order',
        default=False,
        help='Indicates if this is a rush order with expedited lead times'
    )

    def action_calculate_esd(self):
        """Manual trigger for ESD calculation."""
        self.ensure_one()
        try:
            self._calculate_esd()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('ESD Calculation'),
                    'message': _('Estimated Ship Date calculated successfully.'),
                    'type': 'success',
                    'sticky': False,
                }
            }
        except Exception as e:
            _logger.error('ESD calculation error: %s', str(e))
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('ESD Calculation Error'),
                    'message': _('Error calculating ESD: %s') % str(e),
                    'type': 'danger',
                    'sticky': True,
                }
            }

    def _calculate_esd(self):
        """
        Main ESD calculation method implementing the 3-step algorithm.

        STEP 1: Build Component List
        STEP 2: Find Availability Date for Each Component
        STEP 3: Calculate Lead Time per SO Line
        """
        self.ensure_one()
        start_time = datetime.now()

        # Get configuration parameters
        config = self.env['ir.config_parameter'].sudo()
        max_bom_depth = int(config.get_param('ol_sale_lead_time.max_bom_depth', '5'))
        timeout_seconds = int(config.get_param('ol_sale_lead_time.calculation_timeout', '30'))

        warnings = []
        status = 'success'

        try:
            # STEP 1: Build Component List
            component_requirements = self._build_component_list(max_bom_depth)

            # STEP 2: Find Availability Date for Each Component
            component_availability = self._find_component_availability_dates(
                component_requirements, warnings
            )

            # STEP 3: Calculate Lead Time per SO Line
            self._calculate_line_lead_times(
                component_requirements, component_availability, warnings
            )

            # Set overall ESD as max of all line available dates
            max_date = False
            for line in self.order_line:
                if line.available_date:
                    if not max_date or line.available_date > max_date:
                        max_date = line.available_date

            self.estimated_ship_date = max_date

            if warnings:
                status = 'warning'

            # Check timeout
            elapsed = (datetime.now() - start_time).total_seconds()
            if elapsed > timeout_seconds:
                warnings.append(_('Calculation took %s seconds, exceeded recommended timeout') % int(elapsed))
                status = 'warning'

        except Exception as e:
            _logger.error('ESD calculation failed: %s', str(e))
            status = 'error'
            raise

        finally:
            # Update calculation metadata
            self.write({
                'last_esd_calculation': fields.Datetime.now(),
                'esd_calculation_status': status,
            })

    def _build_component_list(self, max_depth):
        """
        STEP 1: Build Component List

        Expand all BoMs recursively and calculate total component quantities
        needed across all SO lines.

        Args:
            max_depth: Maximum BoM nesting depth to prevent infinite loops

        Returns:
            dict: {component_id: total_quantity_required}
        """
        component_requirements = defaultdict(float)
        processed_products = set()

        for line in self.order_line:
            if not line.product_id:
                continue

            line_components = self._expand_bom_recursive(
                line.product_id,
                line.product_uom_qty,
                max_depth,
                processed_products,
                depth=0
            )

            # Aggregate component quantities
            for component_id, qty in line_components.items():
                component_requirements[component_id] += qty

        return dict(component_requirements)

    def _expand_bom_recursive(self, product, quantity, max_depth, processed_products, depth=0):
        """
        Recursively expand BoM to get all components.

        Args:
            product: product.product record
            quantity: Quantity needed of this product
            max_depth: Maximum nesting depth
            processed_products: Set of already processed products (for cycle detection)
            depth: Current depth level

        Returns:
            dict: {component_id: quantity_needed}
        """
        components = defaultdict(float)

        # Prevent infinite loops
        if depth >= max_depth:
            _logger.warning(
                'Max BoM depth reached for product %s (depth: %s)',
                product.display_name, depth
            )
            return components

        # Check for circular references
        if product.id in processed_products:
            _logger.warning(
                'Circular BoM reference detected for product %s',
                product.display_name
            )
            return components

        processed_products.add(product.id)

        # Find BoM for this product (check both normal and phantom types)
        bom = self.env['mrp.bom']._bom_find(
            product=product,
            company_id=self.company_id.id,
            bom_type='normal'
        )[product]

        if not bom:
            # Also check for phantom/kit BoM
            bom = self.env['mrp.bom']._bom_find(
                product=product,
                company_id=self.company_id.id,
                bom_type='phantom'
            )[product]

        if not bom:
            # No BoM - this is a leaf component
            components[product.id] += quantity
            processed_products.remove(product.id)
            return components

        # Expand BoM components (works for both normal and phantom types)
        for bom_line in bom.bom_line_ids:
            component_qty = quantity * bom_line.product_qty / bom.product_qty
            sub_components = self._expand_bom_recursive(
                bom_line.product_id,
                component_qty,
                max_depth,
                processed_products,
                depth + 1
            )
            for comp_id, comp_qty in sub_components.items():
                components[comp_id] += comp_qty

        processed_products.remove(product.id)
        return components

    def _find_component_availability_dates(self, component_requirements, warnings):
        """
        STEP 2: Find Availability Date for Each Component

        For each component, find the earliest date where sufficient stock
        will be available using forecast data, or fall back to vendor lead times.

        Args:
            component_requirements: dict {component_id: quantity_required}
            warnings: list to append warnings to

        Returns:
            dict: {component_id: availability_date}
        """
        component_availability = {}
        today = fields.Date.today()
        config = self.env['ir.config_parameter'].sudo()
        no_po_lead_time = int(config.get_param('ol_sale_lead_time.no_po_lead_time', '999'))

        warehouse = self.warehouse_id or self.env['stock.warehouse'].search([], limit=1)

        for component_id, qty_required in component_requirements.items():
            component = self.env['product.product'].browse(component_id)
            availability_date = None

            # Try to find availability from forecast
            try:
                availability_date = self._find_forecast_availability_date(
                    component, qty_required, warehouse
                )
            except Exception as e:
                _logger.warning('Error checking forecast for %s: %s', component.display_name, str(e))
                warnings.append(_('Could not check forecast for %s') % component.display_name)

            # If not found in forecast, use vendor lead time
            if not availability_date:
                lead_time = self._get_component_lead_time(component, no_po_lead_time)
                availability_date = today + timedelta(days=lead_time)
                if lead_time == no_po_lead_time:
                    warnings.append(
                        _('No vendor pricelist found for %s, using default lead time')
                        % component.display_name
                    )

            component_availability[component_id] = availability_date

        return component_availability

    def _find_forecast_availability_date(self, product, qty_required, warehouse):
        """
        Find earliest date where virtual_available >= qty_required.

        Uses Odoo's stock forecast functionality by checking virtual_available
        at different dates through stock moves.

        Args:
            product: product.product record
            qty_required: Required quantity
            warehouse: stock.warehouse record

        Returns:
            date or None: Earliest availability date, or None if not found
        """
        today = fields.Date.today()
        max_lookahead_days = 365  # Look up to 1 year ahead
        end_date = today + timedelta(days=max_lookahead_days)

        # Check current virtual available
        product_warehouse = product.with_context(warehouse=warehouse.id)
        virtual_available = product_warehouse.virtual_available

        if virtual_available >= qty_required:
            return today

        # Build a forecast by checking stock moves day by day
        # Get all relevant stock moves
        location = warehouse.lot_stock_id

        # Get incoming moves (supplier receipts, internal transfers in)
        incoming_moves = self.env['stock.move'].search([
            ('product_id', '=', product.id),
            ('state', 'in', ['waiting', 'confirmed', 'assigned', 'partially_available']),
            ('location_dest_id', '=', location.id),
            ('date', '>=', fields.Datetime.to_datetime(today)),
            ('date', '<=', fields.Datetime.to_datetime(end_date)),
        ], order='date')

        # Get outgoing moves (sales, internal transfers out)
        outgoing_moves = self.env['stock.move'].search([
            ('product_id', '=', product.id),
            ('state', 'in', ['waiting', 'confirmed', 'assigned', 'partially_available']),
            ('location_id', '=', location.id),
            ('date', '>=', fields.Datetime.to_datetime(today)),
            ('date', '<=', fields.Datetime.to_datetime(end_date)),
        ], order='date')

        # Build a dictionary of net changes by date
        daily_changes = defaultdict(float)
        for move in incoming_moves:
            move_date = fields.Datetime.to_datetime(move.date).date() if move.date else None
            if move_date:
                daily_changes[move_date] += move.product_uom_qty
            daily_changes[move_date] += move.product_uom_qty

        for move in outgoing_moves:
            move_date = fields.Datetime.to_datetime(move.date).date() if move.date else None
            if move_date:
                daily_changes[move_date] -= move.product_uom_qty
            daily_changes[move_date] -= move.product_uom_qty

        # Calculate running quantity day by day
        running_qty = virtual_available
        check_date = today

        # Sort dates
        sorted_dates = sorted(daily_changes.keys())

        for date in sorted_dates:
            # Update running quantity up to this date
            while check_date < date:
                if running_qty >= qty_required:
                    return check_date
                check_date += timedelta(days=1)

            # Apply change for this date
            running_qty += daily_changes[date]
            if running_qty >= qty_required:
                return date

        # Check remaining days up to max lookahead
        while check_date <= end_date:
            if running_qty >= qty_required:
                return check_date
            check_date += timedelta(days=1)

        return None

    def _get_component_lead_time(self, component, default_lead_time):
        """
        Get lead time for a component from vendor pricelist or use default.

        Args:
            component: product.product record
            default_lead_time: Default lead time if no vendor found

        Returns:
            int: Lead time in days
        """
        # Find vendor pricelist (first in sequence)
        supplier_info = self.env['product.supplierinfo'].search([
            ('product_id', '=', component.id),
            ('company_id', 'in', [False, self.company_id.id]),
        ], order='sequence', limit=1)

        if supplier_info and supplier_info.delay:
            return int(supplier_info.delay)

        return default_lead_time

    def _calculate_line_lead_times(self, component_requirements, component_availability, warnings):
        """
        STEP 3: Calculate Lead Time per SO Line

        For each SO line, find the maximum component availability date,
        add manufacturing buffers if applicable, and set customer_lead.

        Args:
            component_requirements: dict {component_id: quantity_required}
            component_availability: dict {component_id: availability_date}
            warnings: list to append warnings to
        """
        today = fields.Date.today()
        config = self.env['ir.config_parameter'].sudo()
        default_mfg_lead_time = int(config.get_param('ol_sale_lead_time.default_mfg_lead_time', '5'))
        rush_order_lead_time = int(config.get_param('ol_sale_lead_time.rush_order_lead_time', '2'))
        mfg_security_lead_time = int(config.get_param('ol_sale_lead_time.mfg_security_lead_time', '1'))

        for line in self.order_line:
            if not line.product_id:
                continue

            # Get components for this line
            line_components = self._get_line_components(line)

            # Find max component availability date
            max_component_date = None
            bottleneck_component = None

            for component_id in line_components:
                if component_id in component_availability:
                    comp_date = component_availability[component_id]
                    if not max_component_date or comp_date > max_component_date:
                        max_component_date = comp_date
                        bottleneck_component = component_id

            if not max_component_date:
                # No components found, use product's own lead time
                lead_time = self._get_component_lead_time(
                    line.product_id,
                    int(config.get_param('ol_sale_lead_time.no_po_lead_time', '999'))
                )
                max_component_date = today + timedelta(days=lead_time)

            # Calculate base lead days
            base_lead_days = (max_component_date - today).days

            # Add manufacturing buffer if applicable
            buffer_days = 0
            bom = self.env['mrp.bom']._bom_find(
                product=line.product_id,
                company_id=self.company_id.id,
                bom_type='normal'
            )[line.product_id]

            if bom and bom.type == 'normal':  # Manufacture this product
                if self.rush_order:
                    buffer_days = rush_order_lead_time + mfg_security_lead_time
                else:
                    buffer_days = default_mfg_lead_time + mfg_security_lead_time

            # Calculate final customer lead
            customer_lead = base_lead_days + buffer_days

            # Update line
            line.write({
                'customer_lead': customer_lead,
                'bottleneck_component_id': bottleneck_component,
            })

    def _get_line_components(self, line):
        """
        Get list of component IDs for a sale order line.

        Args:
            line: sale.order.line record

        Returns:
            set: Set of component product IDs
        """
        components = set()
        processed = set()
        max_depth = int(
            self.env['ir.config_parameter'].sudo().get_param(
                'ol_sale_lead_time.max_bom_depth', '5'
            )
        )

        line_components = self._expand_bom_recursive(
            line.product_id,
            line.product_uom_qty,
            max_depth,
            processed,
            depth=0
        )

        return set(line_components.keys())

    def action_confirm(self):
        """Override action_confirm to automatically recalculate ESD."""
        result = super().action_confirm()
        for order in self:
            try:
                order._calculate_esd()
            except Exception as e:
                _logger.warning('ESD calculation failed on order confirmation: %s', str(e))
        return result
