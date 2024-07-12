Even if this module does not provide views to display some model's
Attributes, it provides however a Technical menu in *Settings \>
Technical \> Database Structure \> Attributes* to **create new
Attributes**.

An Attribute is related to both an Attribute Group and an Attribute Set
:

- The **Attribute Set** is related to the *"model's category"*, i.e. all
  the model's instances which will display the same Attributes.

- The **Attribute Group** is related to the *"attribute's category"*.
  All the attributes from the same Attribute Set and Attribute Group
  will be displayed under the same field's Group in the model's view.

  > 🔎 In order to create a custom Attribute many2one or many2many
  > related to **other Odoo model**, you need to activate the Technical
  > Setting **"Advanced Attribute Set settings"**
  > (`group_advanced_attribute_set`).

------------------------------------------------------------------------

If you want to create a module displaying some specific model's
Attributes :

1.  Your model must **\_inherit the mixin**
    `"attribute.set.owner.mixin"`
2.  You need to **add a placeholder**
    `<separator name="attributes_placeholder" />` at the desired
    location in the model's form view.
3.  Finally, **add a context** `{"include_native_attribute": True}` on
    the action leading to this form view if the model's view needs to
    display attributes related to native fields together with the other
    "custom" attributes.
