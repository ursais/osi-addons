# Enable Webhook for new Odoo Model
1. Create new separate file under `ol_webhooks/models/{model_name}.py`
2. Inherit from the `webhook.mixin` this makes sure that Webhook Events can be created for related CRUD events
    ```
    class SaleOrder(models.Model):
        """
        Add webhook compatibility to Sale Orders
        """

        _name = 'sale.order'
        _inherit = ['sale.order', 'webhook.mixin']
    ```
    - If special logic is needed you can extend or override any of the methods defined in `webhook_mixin.py` in your new file
        - `_create_filter, _update_filter, _delete_filter, basic_filter` 
3. Create new separate data under `ol_webhooks/data/{model_name}.xml`
    - In this files create `webhook.event` records for each CRUD event you want to be able to use in Webhooks
    Ex.: `
    <record id="sale_order_create" model="webhook.event">
      <field name="model_id" search="[('model', '=', 'sale.order')]" />
      <field name="model_name">sale.order</field>
      <field name="operation">create</field>
    </record>
    `
- After this users can create `webhook` records via the Odoo UI.
    - Each webhook has to have a URL, Secret, and Client field set.
- If the client you want to use doesn't exist you need to create a new `api.client` record for it.
    - In this case make sure you also add a Google Secret Manager entry `CLIENTNAME_ODOO_API_KEY`.
        ex. `HUBSPOT_ODOO_API_KEY`
    - This key will be used and sent via request headers `X-Odoo-Api-Signature` field
