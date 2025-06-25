# Migrations Directory (linked from `ls_addons13` root)

This directory contains queries and code to be run before and/or after a module is upgraded. It is used by the
core code in odoo13/odoo/module/migration.py.

## Information

* Odoo server version is pulled from odoo13/odoo/release.py.  It is currently `13.0`
* Module version is pulled from the `__manifest__.py` file in the module. The current version is stored in
  the `ir_module_module` table under the `latest_version` column.  This stored version includes the Odoo server
  version.  So a module with `1.3` in its manifest is stored as `13.0.1.3` in the table.

**WARNING**: Odoo does not enforce any constraits on versioning.  If you change the version from `1.3` to `1.0`, it
will store the new version in the database.  If you later change `1.0` to `1.3`, it will run the migrations for
any versions between `1.0` and `1.3` again.


## Directory structure

This directory must follow a certain structure.  Each subdirectory must be a version number in one of 3 formats:

1. Full version, including Odoo code version.  For example: `13.0.1.0`
2. Module version, with just 2 numbers.  For example: `1.0`
3. Special case of `0.0.0`


In the first two cases, the code inside will be run if the new module version is greater than or equal to the
version of the directory.  It will not run code for directories with older versions than the installed version.
For example:
  - Manifest version: `1.3`
  - Database version: `1.0`
  - Directories that will have their code files run:
    - `migrations/1.2`
    - `migrations/13.0.1.2`
    - `migrations/1.3`
    - `migrations/13.0.1.3`
  - Directories that will be ignored:
    - `migrations/0.9`
    - `migrations/13.0.0.3`
    - `migrations/1.4`
    - `migrations/13.0.12.3`


In the special third case, the code inside `migrations/0.0.0` will always be run when the version changes,
regardless of the module versions in the database or manifest.


All other directories will be ignored.


## Code files

Within each directory, Odoo will look for 3 types of files.  Each which will be run at a different time during
the upgrade process.

1. `pre-SOMETHING_DESCRIPTIVE.py`
   - This file is run before upgrading the module
   - If this is in a `0.0.0` directory, it is run before all other `pre-...` files for that module
2. `post-SOMTHING_DESCRIPTIVE.py`
   - This file is run after upgrading the module
   - If this is in a `0.0.0` directory, it is run after all other `post-...` files for that module

3. `end-SOMETHING_DESCRIPTIVE.py`
   - This file is run after all modules have been upgraded
   - If this is in a `0.0.0` directory, it is run last at the end of the upgrade process


All other files are ignored.  It is wise to add a README.md to each directory for reviewers and for historical
tracking of changes.


Each code file must be a python file that contains a function with this signature:

```
def migrate(cr, installed_version):
```

This is what Odoo calls, but you can add other functionality such as logging or getting an Odoo Environment.

## Examples:

* Run a query:

    ```
    import logging
    _logger = logging.getLogger(__name__)

    def migrate(cr, installed_version):
        _logger.info(f'Updating rows')

        update_query = """
          UPDATE table_a
          SET field_b = 'NEW VAL'
          WHERE field_b = 'OLD VAL'
          RETURNING id, field_b;
        """

        cr.execute(update_query)
        rows = cr.fetchall()
        _logger.info(f'updated rows: {rows}')
    ```

* Run a function:

    ```
    import logging

    import odoo.api

    _logger = logging.getLogger(__name__)

    def get_stuff():
        # NOTE: be careful when using the SUPERUSER_ID! Use the appropriate user when doing this
        env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})

        foos = env['example.model'].search([('thing', '=', 'bar')])
        return foos.action_do_thing()


    def migrate(cr, installed_version):
        _logger.info(f'Doing thing!')
        res = get_stuff()
        _logger.info(f'Results: {res}')
    ```

* Install a new module (usually in an `end-...py` file in `ls_base`):

    ```
    import logging

    import odoo.api

    _logger = logging.getLogger(__name__)


    def migrate(cr, installed_version):
        env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
        new_mod = env['ir.module.module'].search([('name', '=', MODULE NAME)])
        res = new_mod.button_immediate_install()
        _logger.info(f'Res from installing: {res}')
    ```
