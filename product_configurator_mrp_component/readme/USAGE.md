- When the parent product is configured, the system will look for the
  first BoM for that product and cycle through the configurable
  components.
- If a product variant doesn't exist for the configurable component then
  one will be created with the matching values in the config wizard.
- The parent product BoM will then be modified with a new bom line(s)
  and configuration set(s) for the new configurable component variants.
- The new parent product variant will be created if one doesn't exist
  and it's BoM will contain the new configurable components lines.
