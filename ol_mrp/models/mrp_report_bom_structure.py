# Import Odoo libs
from odoo import api, models
from datetime import datetime


class ReportBomStructure(models.AbstractModel):
    """
    Inherit BoM Structure Report to fix phantom kit availability aggregation.

    This fix ensures that phantom kits show the worst-case (latest) expected date
    among their components when components are fully reserved.
    """

    _inherit = "report.mrp.report_bom_structure"

    @api.model
    def _get_report_data(self, bom_id=False, searchQty=1, searchVariant=False):
        """
        Override _get_report_data to fix phantom kit availability aggregation.

        After getting the standard report data, this method processes phantom kits
        to ensure they show the worst-case (latest) expected date from their components.

        Args:
            bom_id: BoM ID
            searchQty: Quantity to search for
            searchVariant: Search variant flag

        Returns:
            dict: Report data with corrected availability for phantom kits
        """
        # Call parent method to get standard report data
        res = super()._get_report_data(
            bom_id=bom_id,
            searchQty=searchQty,
            searchVariant=searchVariant
        )

        # Skip processing if we're in a nested call (prevent infinite recursion)
        if self._context.get('skip_phantom_kit_processing'):
            return res

        if not res or not res.get('lines'):
            return res

        # Get components from the report data
        lines = res.get('lines', {})
        components = lines.get('components', [])

        # Process all phantom kits in components recursively
        self._process_phantom_kits_in_components(components)

        return res

    def _process_phantom_kits_in_components(self, components):
        """
        Recursively process components to fix nested phantom kits.

        Args:
            components: List of component dictionaries
        """
        if not components:
            return

        for component in components:
            # Check if this component is a phantom kit
            # Phantom kits have type='phantom' and may have nested components
            if component.get('type') == 'phantom':
                # Get nested components for this phantom kit
                # Nested components might be in 'components' field or we need to get them
                nested_components = component.get('components', [])
                
                # If nested components are not directly available, try to get them from the BOM
                if not nested_components and component.get('bom_id'):
                    # Get the BOM data for this phantom kit with context flag to prevent recursion
                    nested_bom_data = self.with_context(skip_phantom_kit_processing=True)._get_report_data(
                        bom_id=component.get('bom_id'),
                        searchQty=component.get('quantity', 1),
                        searchVariant=False
                    )
                    if nested_bom_data and nested_bom_data.get('lines'):
                        nested_components = nested_bom_data.get('lines', {}).get('components', [])

                # Update phantom kit availability based on nested components
                if nested_components:
                    self._update_phantom_kit_availability(component, nested_components)
                    # Recursively process nested phantom kits
                    self._process_phantom_kits_in_components(nested_components)

    def _update_phantom_kit_availability(self, bom_line, components):
        """
        Update phantom kit availability based on worst-case component dates.

        Args:
            bom_line: Dictionary containing the BOM line data for the phantom kit
            components: List of component dictionaries
        """
        if not components:
            return

        # Find the worst-case (latest) expected date from all components
        worst_expected_date = None
        worst_availability_date = None
        has_reserved_component = False

        for component in components:
            # Check for expected date in component data
            # The date might be in different fields depending on Odoo version
            component_expected_date = (
                component.get('expected_date') or
                component.get('availability_date') or
                component.get('expected_delivery_date')
            )
            component_availability_state = component.get('availability_state', '')

            # Track if any component is fully reserved or has expected date
            if component_availability_state == 'expected' or component_expected_date:
                has_reserved_component = True

            # Convert string dates to datetime objects for comparison
            if component_expected_date:
                date_obj = self._parse_date(component_expected_date)
                if date_obj:
                    if worst_expected_date is None or date_obj > worst_expected_date:
                        worst_expected_date = date_obj

            # Also check availability_date separately
            component_availability_date = component.get('availability_date')
            if component_availability_date and component_availability_date != component_expected_date:
                date_obj = self._parse_date(component_availability_date)
                if date_obj:
                    if worst_availability_date is None or date_obj > worst_availability_date:
                        worst_availability_date = date_obj

        # Update phantom kit availability based on worst-case component dates
        if worst_expected_date or worst_availability_date:
            # Use the latest of the two dates
            final_date = worst_expected_date
            if worst_availability_date and (not worst_expected_date or worst_availability_date > worst_expected_date):
                final_date = worst_availability_date

            # Convert datetime back to string format if needed
            if final_date:
                if isinstance(final_date, datetime):
                    date_str = final_date.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    date_str = str(final_date)

                # Update the BOM line data with worst-case availability
                bom_line['expected_date'] = date_str
                bom_line['availability_date'] = date_str

                # Update availability state if component is reserved
                if has_reserved_component:
                    bom_line['availability_state'] = 'expected'
                    # Update availability display to show expected date
                    if 'availability_display' in bom_line:
                        bom_line['availability_display'] = date_str
                elif bom_line.get('availability_state') == 'available':
                    # If worst case shows a date, it's not immediately available
                    bom_line['availability_state'] = 'expected'

    def _parse_date(self, date_value):
        """
        Parse a date value into a datetime object.

        Args:
            date_value: Date value (string, datetime, or date object)

        Returns:
            datetime: Parsed datetime object or None
        """
        if not date_value:
            return None

        if isinstance(date_value, datetime):
            return date_value
        elif hasattr(date_value, 'date'):
            # Date object
            return datetime.combine(date_value, datetime.min.time())

        if isinstance(date_value, str):
            # Try different date formats
            formats = [
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d %H:%M:%S.%f',
                '%Y-%m-%d',
                '%m/%d/%Y %H:%M:%S',
                '%m/%d/%Y',
            ]
            for fmt in formats:
                try:
                    return datetime.strptime(date_value, fmt)
                except ValueError:
                    continue

        return None
