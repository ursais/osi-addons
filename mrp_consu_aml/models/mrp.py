# Copyright (C) 2023 Open Source Integrators
# Copyright (C) 2023 Serpent Consulting Services Pvt. Ltd.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import _, models
from odoo.exceptions import UserError


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    def run_consu_aml(self):
        pc_array = self.env[
            "report.mrp_account_enterprise.mrp_cost_structure"
        ].get_lines(self)
        if self._context.get("from_unbuild"):
            je = self.env["account.move"].search(
                [
                    ("ref", "ilike", self._context.get("unbuild_name")),
                    ("state", "=", "posted"),
                ],
                limit=1,
                order="id desc",
            )
            move_line_ids = je.mapped("line_ids")
        else:
            je = self.env["account.move"].search(
                [("ref", "ilike", self.name), ("state", "=", "posted")],
                limit=1,
                order="id",
            )
            move_line_ids = je.mapped("line_ids").filtered(
                lambda x: x["osi_is_consu"]
            )
        if not je:
            return False
        # sum(x["total_cost"] for x in pc_array)
        to_make = []
        if len(pc_array) >= 1:
            pc_array = pc_array[0]
        else:
            return False
        for pc in pc_array["raw_material_moves"]:
            product = pc["product_id"]
            if product["type"] == "consu":
                if self._context.get("from_unbuild"):
                    mo_qty = pc_array.get("mo_qty")
                    tot_cmp_qty = pc.get("qty")
                    tot_unbuild_qty = 0
                    single_cmp_cost = tot_cmp_qty and pc.get("cost") / tot_cmp_qty or 0
                    if mo_qty:
                        tot_unbuild_qty = (
                            self._context.get("unbuild_qty") * tot_cmp_qty
                        ) / mo_qty
                    unbuild_cmp_cost = tot_unbuild_qty * single_cmp_cost
                    cost = unbuild_cmp_cost
                else:
                    cost = pc["cost"]
                found = False
                for line in move_line_ids:
                    if self._context.get("from_unbuild"):
                        if (
                            product["id"] == line["product_id"]["id"]
                            and cost != line["debit"]
                            and not line["credit"]
                        ):
                            line["debit"] = cost
                            found = True
                            break
                    else:
                        if (
                            product["id"] == line["product_id"]["id"]
                            and cost != line["credit"]
                            and not line["debit"]
                        ):
                            line["credit"] = cost
                            found = True
                            break
                if not found:
                    if product.property_account_expense_id.id:
                        account_id = product.property_account_expense_id.id
                    elif product.categ_id.property_account_expense_categ_id.id:
                        account_id = (
                            product.categ_id.property_account_expense_categ_id.id
                        )
                    else:
                        raise UserError(
                            _("Missing account for product %s") % product["name"]
                        )
                    if self._context.get("from_unbuild"):
                        to_make.append(
                            {
                                "account_id": account_id,
                                "debit": cost,
                                "product_id": product["id"],
                                "move_id": je.id,
                                "osi_is_consu": True,
                                "company_id": self.company_id.id,
                                "name": self._context.get("unbuild_name")
                                + " - "
                                + product["name"],
                            }
                        )
                    else:
                        to_make.append(
                            {
                                "account_id": account_id,
                                "credit": cost,
                                "product_id": product["id"],
                                "move_id": je.id,
                                "osi_is_consu": True,
                                "company_id": self.company_id.id,
                                "name": self.name + " - " + product["name"],
                            }
                        )
                if self._context.get("from_unbuild"):
                    if self.production_location_id.valuation_out_account_id:
                        account = (
                            self.production_location_id.valuation_out_account_id.id
                        )
                    else:
                        account = (
                            product.categ_id.property_stock_account_output_categ_id.id
                        )
                    to_make.append(
                        {
                            "account_id": account,
                            "credit": cost,
                            "product_id": product["id"],
                            "move_id": je.id,
                            "osi_is_consu": True,
                            "company_id": self.company_id.id,
                            "name": self._context.get("unbuild_name")
                            + " - "
                            + product["name"],
                        }
                    )
                else:
                    out_line = move_line_ids.filtered(
                        lambda x: x["debit"] and x["product_id"]["id"] == product["id"]
                    )
                    if len(out_line):
                        out_line.write({"debit": cost / len(out_line)})
                    else:
                        if self.production_location_id.valuation_out_account_id:
                            account = (
                                self.production_location_id.valuation_out_account_id.id
                            )
                        else:
                            account = (
                                product.categ_id.property_stock_account_output_categ_id.id
                            )
                        to_make.append(
                            {
                                "account_id": account,
                                "debit": cost,
                                "product_id": product["id"],
                                "move_id": je.id,
                                "osi_is_consu": True,
                                "company_id": self.company_id.id,
                                "name": self.name + " - " + product["name"],
                            }
                        )
        je.button_draft()
        self.env["account.move.line"].with_context(check_move_validity=False).create(
            to_make
        )
        je.action_post()
        return False

    def button_mark_done(self):
        res = super(MrpProduction, self).button_mark_done()
        self.run_consu_aml()
        return res
