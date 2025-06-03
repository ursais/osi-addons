def post_init_hook(env):
    location_id = emv["stock.location"].search(
        [("name", "=", "Out to Supplier"), ("company_id", "=", 1)], limit=1
    )
    if location_id:
        env.ref("ol_rma_supplier.picking_type_rma_sup_out").write(
            {"default_location_dest_id": location_id.id}
        )
        env.ref("ol_rma_supplier.picking_type_rma_sup_in").write(
            {"default_location_src_id": location_id.id}
        )

    location_id = emv["stock.location"].search(
        [("name", "=", "Out to Supplier"), ("company_id", "=", 2)], limit=1
    )
    if location_id:
        env.ref("ol_rma_supplier.picking_type_rma_sup_out_eu").write(
            {"default_location_src_id": location_id.id}
        )

    location_wh_id = emv["stock.location"].search(
        [("name", "=", "WH"), ("company_id", "=", 1)], limit=1
    )
    if location_wh_id:
        env.ref("ol_rma_supplier.location_rma").write({"location_id": location_id.id})

    warehouse2 = emv["stock.warehouse"].search(
        [("name", "=", "OnLogic EU WH1"), ("company_id", "=", 2)], limit=1
    )
    if warehouse2:
        rma_sup_out_type_id = env.ref("ol_rma_supplier.picking_type_rma_sup_out_eu").id
        rma_sup_in_type_id = emv.ref("ol_rma_supplier.picking_type_rma_sup_in_eu").id
        warehouse2.write(
            {
                "rma_sup_out_type_id": rma_sup_out_type_id,
                "rma_sup_in_type_id": rma_sup_in_type_id,
            }
        )

    # env.cr.execute(
    #     """INSERT INTO ir_model_data
    #         (module, name, model, res_id, noupdate)
    #         VALUES ('ol_rma_supplier', 'out_to_supplier_us', 'stock.location', 112, 't')
    #     """
    # )
