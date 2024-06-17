# ol_base #

## External Link Button Override ##

In this module is a solution to override the core functionality of the external link button.

To find an example of this button:
 - create a new quotation
 - set a customer or address
 - click on the button to the right of the field *while in edit mode*

To extend this functionality, override the method `modify_external_link_behavior`, defined in ol_base/models/models.py, in your desired module.

<br>

### modify_external_link_behavior ###
___
The purpose of this function is to provide odoo with enough information to open the correct view. This solution was introduced with `ls_customer` to open views for fields in different models.

To override this function successfully, it needs to return a `res_id`, `model`, and `view_id` in a dictionary with those fields as keys, eg:
```
    destination = {
        'res_id': your_target_record_id,
        'model': your_target_model_name,
        'view_id': your_target_view_id
    }
```
This dictionary will be used by odoo javascript to display the correct view. The benefit of using this solution is it allows for flexibility in what model to display your record data, and you are not locked into the model of the field in question.

An example of this function being overridden can be found here:
`ls_customer/models/res_partner.py`
