# -*- coding: utf-8 -*-
"""
Domain In-List Operator Implementation

Adds 'in_list' operator support for Odoo domains, enabling users to paste
multi-line values from Excel/Google Sheets or comma-separated lists.
"""

import logging
from typing import List, Any, Tuple

from odoo.osv import expression

_logger = logging.getLogger(__name__)

SUPPORTED_FIELD_TYPES = ['char', 'text', 'integer', 'float']


def parse_multiline_input(input_value: str) -> List[str]:
    """
    Parse input with multiple separator support.
    
    Supports: newlines, spaces, commas, semicolons, pipes
    Handles Excel/Google Sheets paste formats
    """
    if not input_value or not isinstance(input_value, str):
        return []
    
    values = []
    for line in input_value.split('\n'):
        line = line.strip()
        if not line:
            continue
            
        # Check for separators in priority order
        if ',' in line:
            values.extend(v.strip() for v in line.split(',') if v.strip())
        elif ';' in line:
            values.extend(v.strip() for v in line.split(';') if v.strip())
        elif '|' in line:
            values.extend(v.strip() for v in line.split('|') if v.strip())
        elif ' ' in line and len(line.split()) > 1:
            values.extend(v.strip() for v in line.split() if v.strip())
        else:
            values.append(line)
    
    return [v for v in values if v]


def process_values_by_type(values: List[str], field_type: str) -> Tuple[List[Any], str]:
    """Convert and validate values based on field type."""
    if not values:
        return [], None
    
    processed = []
    for value in values:
        try:
            if field_type == 'integer':
                processed.append(int(value))
            elif field_type == 'float':
                processed.append(float(value))
            else:
                processed.append(value)
        except ValueError:
            return [], f"Invalid {field_type} value: '{value}'"
    
    return list(dict.fromkeys(processed)), None


def setup_in_list_operator():
    """Initialize the in_list operator by patching Odoo's expression system."""
    expression.TERM_OPERATORS = expression.TERM_OPERATORS + ('in_list',)
    expression.TERM_OPERATORS_NEGATION = {
        **expression.TERM_OPERATORS_NEGATION,
        'in_list': 'not in',
    }

    from odoo.osv.expression import expression as expr_class
    original_init = expr_class.__init__

    def patched_init(self, domain, model, alias=None, query=None):
        """Process in_list operators before normal expression handling."""
        processed_domain = []
        
        for item in domain or []:
            if isinstance(item, (list, tuple)) and len(item) == 3:
                field, operator, value = item
                
                if operator == 'in_list':
                    field_type = 'char'
                    try:
                        if hasattr(model, '_fields') and field in model._fields:
                            field_type = model._fields[field].type
                            if field_type not in SUPPORTED_FIELD_TYPES:
                                processed_domain.append(item)
                                continue
                    except Exception as e:
                        _logger.debug(f"Could not determine field type for {field}: {e}")
                    
                    # Process input value
                    if isinstance(value, list):
                        raw_values = [str(v) for v in value]
                    elif isinstance(value, str):
                        raw_values = parse_multiline_input(value)
                    else:
                        raw_values = [str(value)] if value is not None else []
                    
                    processed_values, error = process_values_by_type(raw_values, field_type)
                    
                    if error:
                        _logger.warning(f"in_list validation error for '{field}': {error}")
                        processed_values = []
                    
                    processed_domain.append((field, 'in', processed_values))
                else:
                    processed_domain.append(item)
            else:
                processed_domain.append(item)
        
        return original_init(self, processed_domain, model, alias, query)

    expr_class.__init__ = patched_init


# Initialize the operator
setup_in_list_operator()