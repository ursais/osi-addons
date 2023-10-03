import logging

from odoo import models

_logger = logging.getLogger(__name__)

try:
    pass
except ImportError as err:
    _logger.debug(err)

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
    "Régimen Simplificado de Confianza": "626",
}


class ImportCSF(models.TransientModel):
    _inherit = "import.csf"

    def prepare_res_partner_values(self, text):
        vals = super().prepare_res_partner_values(text)
        split_data = text.split("\n")
        fiscal_regime = ""
        for index, line in enumerate(split_data):
            if "Regímenes" in line:
                fiscal_regime += split_data[index + 2].strip()
                if fiscal_regime == "Régimen":
                    fiscal_regime = split_data[index + 3].strip()
                fiscal_regime = FISCAL_REGIMES_MAPPING[fiscal_regime]
        return vals.update(
            {
                "l10n_mx_edi_fiscal_regime": fiscal_regime,
            }
        )
