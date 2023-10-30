from odoo import models

FISCAL_REGIMES_MAPPING = {
    "Régimen General de Ley Personas Morales": "601",
    "Régimen de Sueldos y Salarios e Ingresos Asimilados a Salarios": "605",
    "Régimen de los demás ingresos": "608",
    "Régimen de Ingresos por Dividendos (socios y accionistas)": "611",
    "Régimen de las Personas Físicas con Actividades Empresariales y Profesionales": "612",
    "Régimen de los ingresos por intereses": "614",
    "Régimen de Incorporación Fiscal": "621",
    "Régimen de las Actividades Empresariales "
    "con ingresos a través de Plataformas Tecnológicas": "625",
    "Régimen de las Actividades Empresariales "
    "con ingresos a través de Plataformas Tecnológicas.": "625",
    "Régimen Simplificado de Confianza": "626",
}


class ImportCSF(models.TransientModel):
    _inherit = "import.csf"

    def prepare_res_partner_values(self, text):
        vals = super().prepare_res_partner_values(text)
        split_data = text.split("\n")
        fiscal_regime = ""
        for index, _line in enumerate(split_data):
            if split_data[index].strip() in FISCAL_REGIMES_MAPPING.keys():
                fiscal_regime = split_data[index].strip()
                fiscal_regime = FISCAL_REGIMES_MAPPING[fiscal_regime]
        vals.update(
            {
                "l10n_mx_edi_fiscal_regime": fiscal_regime,
            }
        )
        return vals
