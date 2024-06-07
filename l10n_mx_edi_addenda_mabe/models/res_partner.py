from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    mabe_plant_code = fields.Selection(
        selection=[
            ("D026", "Mabe Internacional"),
            ("D121", "CDR SAN LUIS POTOSI"),
            ("D128", "EXPORTACION CEAM"),
            ("D161", "CDR AF SAN LUIS POTOSI"),
            ("D165", "CDR TLAQUEPAQUE"),
            ("A002", "MABE SA CENTRAL"),
            ("A003", "TI"),
            ("A004", "CSC FINANZAS"),
            ("A006", "CORPORATIVO TYP"),
            ("T102", "ADR MEXICO DF"),
            ("T103", "MODULO MEXICO METRO NORTE"),
            ("T104", "MODULO ACAPULCO"),
            ("T105", "MODULO PUEBLA"),
            ("T106", "MODULO MEXICO METRO ORIENTE"),
            ("T107", "MODULO QUERETARO"),
            ("T108", "MODULO VERACRUZ"),
            ("T109", "MODULO MERIDA"),
            ("T110", "MODULO VILLAHERMOSA"),
            ("T111", "MODULO CANCUN"),
            ("T112", "ADR MONTERREY"),
            ("T113", "MODULO MONTERREY"),
            ("T114", "MODULO CD JUAREZ"),
            ("T115", "MODULO CHIHUAHUA"),
            ("T116", "MODULO TORREON"),
            ("T117", "MODULO MEXICO METRO SUR"),
            ("T118", "MODULO TAMPICO"),
            ("T119", "MODULO MONTERREY SUR"),
            ("T120", "MODULO REYNOSA"),
            ("T121", "MODULO MATAMOROS"),
            ("T122", "MODULO CD VICTORIA"),
            ("T123", "MODULO PIEDRAS NEGRAS"),
            ("T124", "ADR GUADALAJARA"),
            ("T125", "MODULO GUADALAJARA"),
            ("T126", "MODULO AGUASCALIENTES"),
            ("T127", "MODULO SAN LUIS POTOSI"),
            ("T128", "MODULO MEXICALLI"),
            ("T129", "MODULO TIJUANA"),
            ("T130", "MODULO HERMOSILLO"),
            ("T131", "MODULO LEON"),
            ("T132", "MODULO CULIACAN"),
            ("T133", "MODULO LOS MOCHIS"),
            ("T134", "MODULO LA PAZ"),
            ("T135", "Corporativo Serviplus"),
            ("T136", "ADR SAN LUIS POTOSI"),
        ]
    )
