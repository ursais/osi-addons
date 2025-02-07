# Import Python libs
from collections import defaultdict
import logging

# Import Odoo libs
from odoo import api, models
from odoo.exceptions import UserError
from odoo.addons.ol_production_automation.models.build_profile import BuildProfile

_logger = logging.getLogger(__name__)


class MrpBom(models.Model):
    """
    Traveler related functionality
    """

    _inherit = "mrp.bom"

    # COLUMNS #####
    # END #########

    @api.model
    def convert_to_check_array(self, assembly_checks, tuple_length=3):
        """
        Returns an array of 3-tuples created from the given assembly_checks
        For example:
        assembly_checks = [1,2,3,4,5,6,7]
        returns [(1,2,3),(4,5,6),(7)]
        """
        check_array = []

        # Loop through in TUPLE_LENGTH increments
        for idx in range(0, len(assembly_checks), tuple_length):
            cur_tuple = assembly_checks[idx : idx + tuple_length]

            check_array.append(tuple(cur_tuple))

        return check_array

    def _get_key_traveler_recs(self):
        """
        Return a dictionary of key objects
        """
        return {
            "custom_work_sku": self.env["product.product"].search(
                [("default_code", "=", "SV-CUWorkInst")]
            ),
            "custom_bios_sku": self.env["product.product"].search(
                [("default_code", "=", "SV-CustomBIOS")]
            ),
            "boxing_stage": self.env["mrp.assembly.stage"].search(
                [("name", "=", "Boxing")]
            ),
            "bios_classification_stage": self.env["product.attribute.classification"]
            .search([("name", "=", "BIOS")])
            .stage_id,
            "os_classification_stage": self.env["product.attribute.classification"]
            .search([("name", "=", "Operating System")])
            .stage_id,
            # 'install_os_task_type': self.env['mrp.automation.task.type'].search(
            #     [('name', '=', 'install_os')]
            # ),
            "custom_work_stage": self.env.ref("ol_mrp_traveler.custom_work_stage"),
            "standard_work_stage": self.env.ref("ol_mrp_traveler.standard_work_stage"),
        }

    def get_traveler_info(self, partner_id=None):
        """
        Returns a dictionary to be used in the construction of the traveler
        dict is in the format:
        mrp.assembly_stage() -> 'lines' -> mrp.bom.line(),
                                'additional_checks' -> list of tuples of mrp.assembly.check()
                                'next_checks' -> mrp.assembly.check()
        The work instructions stage gets an additional key:
                             -> 'documentation' -> url of documentation location if it is set
        There could be a label in the stage or a bios name
                             -> 'label' -> mrp.label.template()
                             -> 'bios' -> str
        """
        self.ensure_one()
        check_obj = self.env["mrp.assembly.check"]

        # important records
        key_recs = self._get_key_traveler_recs()
        if not partner_id:
            partner_id = self.env["res.partner"]

        # initialize the dictionary.  We need all of these things if any of them are present
        traveler_dict = defaultdict(
            lambda: {
                "lines": self.env["mrp.bom.line"],
                "output_checks": self.env["mrp.assembly.check"],
                "input_checks": self.env["mrp.assembly.check"],
            }
        )

        # Get a list of products (incl system) and options for this bom
        # system product and all bom line products
        bom_lines_products = self.bom_line_ids.product_id
        product_ids = self.product_id | bom_lines_products

        # any products in phantom kit bom lines (or original kits for exploded boms)
        product_ids |= bom_lines_products.get_components_of_phantom_kits()
        product_ids |= (
            self.bom_line_ids.original_phantom_bom_id.phantom_product_variant_id
        )

        def add_traveler_line(dict, stage, key, data, append=False):
            if append:
                dict[stage][key] |= data
            else:
                dict[stage][key] = data
            dict[stage]["stage_name"] = stage.name
            return dict

        # Check if we have a custom work SKU in the products (SV-CUWorkInst)
        # If yes add the `CUSTOM WORK INSTRUCTIONS` Assembly Work Stage
        # And documentation key with a link to the related google doc
        if key_recs["custom_work_sku"] in product_ids:
            # has custom work
            traveler_dict = add_traveler_line(
                dict=traveler_dict,
                stage=key_recs["custom_work_stage"],
                key="documentation",
                data=self.product_id.work_documentation_url,
            )
        else:
            # has standard work
            docs = product_ids.filtered(lambda r: r.work_documentation_url)
            if len(docs) > 1:
                # TODO: deal with more than one documentation in a better way
                _logger.error(
                    "Found more than one documentation URL"
                    " on system: {}".format(self.product_id.default_code)
                )

            traveler_dict = add_traveler_line(
                dict=traveler_dict,
                stage=key_recs["standard_work_stage"],
                key="documentation",
                data=(docs and docs[0].work_documentation_url),
            )

        # determine bios name
        if self.product_id.bios_name:
            bios_name = self.product_id.bios_name
        elif key_recs["custom_bios_sku"] in product_ids:
            # custom BIOS in BoM but nothing set on system product
            bios_name = "NO CUSTOM BIOS FOUND"
        else:
            # no bios set on the system, so use whatever else we can find
            bios_name = ", ".join(
                [
                    bios_name
                    for bios_name in product_ids.mapped("bios_name")
                    if bios_name
                ]
            )

        traveler_dict = add_traveler_line(
            dict=traveler_dict,
            stage=key_recs["bios_classification_stage"],
            key="bios_name",
            data=bios_name,
        )

        # determine the labeling template
        label_type = ""
        try:
            template_id = self.pick_label_template_id(partner_id)
            label_type = template_id.name
        except UserError as warning:
            # Unable to determine the labelling strategy, so put the warning in instead
            # exceptions.Warning.args is a tuple: (TITLE, MESSAGE)
            label_type = warning.args[1]
        traveler_dict = add_traveler_line(
            dict=traveler_dict,
            stage=key_recs["boxing_stage"],
            key="label_type",
            data=label_type,
        )

        # Determine the OS image name
        install_os_task_type = self.env["mrp.automation.task.type"].search(
            [("name", "=", "install_os")]
        )
        install_tasks = [
            task
            for task in self.get_all_tasks()
            if task["task_type"] == install_os_task_type.name
        ]
        picked_task, _ = BuildProfile.pick_appropriate_os_install_task(install_tasks)
        if picked_task:
            os_line = picked_task["image_name"]
        else:
            os_line = "No OS"

        traveler_dict = add_traveler_line(
            dict=traveler_dict,
            stage=key_recs["os_classification_stage"],
            key="image_name",
            data=os_line,
        )

        # sort the bom lines based on their assembly stage
        for line in self.bom_line_ids:
            traveler_dict = add_traveler_line(
                dict=traveler_dict,
                stage=line.assembly_stage_id,
                key="lines",
                data=line,
                append=True,
            )

        # force default values for stages that are always shown
        for stage in self.env["mrp.assembly.stage"].search(
            [("show_when_empty", "=", True)]
        ):
            traveler_dict[stage]["stage_name"] = stage.name

        # build the final dictionary mapping
        for stage, val in traveler_dict.items():
            # sort the lines by classification
            val["lines"].sorted(lambda r: r.classification_id)

            all_checks = check_obj.get_all_checks(
                stage,
                traveler_dict[stage]["lines"].mapped("classification_id"),
                val["lines"].mapped("product_id")
                | val["lines"].mapped(
                    "original_phantom_bom_id.phantom_product_variant_id"
                ),
                product_ids,
            )

            # filter out any repair only checks
            all_checks = all_checks.filtered(lambda r: r.assembly_check is True)

            # filter out next step QA
            val["input_checks"] = all_checks.filtered(
                lambda r: r.type == "input" or r.type == "both"
            )

            # add notes
            val["notes"] = all_checks.filtered(lambda r: r.type == "note")

            # additional_checks sorted into tuple list
            output_checks = all_checks.filtered(
                lambda r: r.type == "output" or r.type == "both"
            )

            val["output_checks"] = self.convert_to_check_array(output_checks)

        # can't sort a dict, so convert to tuple array,
        # then sort by stage sequence
        stages = [(k, v) for k, v in traveler_dict.items() if k.show_on_traveler]

        return sorted(stages, key=lambda x: x[0].sequence)
