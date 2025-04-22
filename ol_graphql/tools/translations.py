# Retrieves the translated values of a field for a record


def get_translated_field_values(odoo_record, field, translation_key="value"):
    """
    Get the translated values of the field as an array
    """

    # Get all active Languages
    active_langue_data = odoo_record.env["res.lang"].get_installed()
    languages = [x[0] for x in active_langue_data]

    translations = []

    if hasattr(odoo_record, field):
        for lang in languages:
            translation = {
                "locale": lang,
            }
            translation[translation_key] = getattr(
                odoo_record.with_context(lang=lang), field
            )
            translations.append(translation)
    return translations
