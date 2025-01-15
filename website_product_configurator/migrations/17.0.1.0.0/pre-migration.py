def migrate(cr, version):
    # Query to check if the specific key exists in the 'ir_config_parameter' table.
    cr.execute(
        """SELECT id, value key FROM ir_config_parameter
        WHERE key = 'product_configurator.default_configuration_step_website_view_id'"""
    )
    record = cr.fetchone()

    if record:
        update_query = """
            UPDATE ir_config_parameter
            SET value = (
                SELECT id FROM ir_ui_view WHERE key = '%s'
            )
            WHERE id = %s
        """
        cr.execute(update_query % (record[1], record[0]))  # pylint: disable=E8103
