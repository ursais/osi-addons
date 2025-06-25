# ol_company_demo

Demo/Dev module specifically intended to be a sandbox for exploration and discovery around company rules and sudo

## Running it as a unit test

Note for future devs: this is before we built any unit test suite for Odoo 17, so it may be outdated. The point is, this module only depends on "base", so it is "clean" of any outside interference as we only install the base module and this one. 

The output currently isn't great (no coverage %) but check the logs and as long as there aren't any errors, that means none have failed.

How to run unit tests:

1) In odoo.env, change PGDATABASE to a database that doesn't yet exist. 

2) Run the following command to create a new database with just base and this module installed:

        time docker compose run odoo odoo --stop-after-init --addons-path=$ODOO_ADDONS_PATH -i ol_company_demo

3) Run this command to execute unit tests

        time docker compose run --remove-orphans odoo odoo --stop-after-init --addons-path=$ODOO_ADDONS_PATH -u ol_company_demo --test-enable



## Interesting discoveries

**How does su = True invalidate record rules?**

There seems to be two places where this flag is literally evaluated:

1. The "check" method here is a fairly low level method that is called in various areas in core Odoo, and contains a check for self.env.su

    _An example to look at to help understand is the "get_bindings" function in odoo/addons/base/models/ir_actions.py_

        odoo/addons/base/models/ir_model.py

        class IrModelAccess(models.Model):
        ...
            @api.model
            def check(self, model, mode='read', raise_exception=True):
                if self.env.su:
                    # User root have all accesses
                    return True

                assert isinstance(model, str), 'Not a model name: %s' % (model,)

                if model not in self.env:
                    _logger.error('Missing model %s', model)

                has_access = model in self._get_allowed_models(mode)
                if not has_access and raise_exception:
                    raise self._make_access_error(model, mode) from None
                return has_access

2. The "_get_rules" method retrieves the ir_rule ids that are: 
    - for a given model
    - for the given mode (_MODES = ['read', 'write', 'create', 'unlink'])
    - either global or are associated with the groups that the self.env.user is in

    self.env.su bypasses all of this

    _This also gets used in a few areas in core Odoo, but I think the key one to look at for more information is in "\_compute_domain" also on the IrRule class._

        odoo/addons/base/models/ir_rule.py

        class IrRule(models.Model):
        ...
            def _get_rules(self, model_name, mode='read'):
                """ Returns all the rules matching the model for the mode for the
                current user.
                """
                if mode not in self._MODES:
                    raise ValueError('Invalid mode: %r' % (mode,))

                if self.env.su:
                    return self.browse(())

                sql = SQL("""
                    SELECT r.id FROM ir_rule r
                    JOIN ir_model m ON (r.model_id=m.id)
                    WHERE m.model = %s AND r.active AND r.perm_%s
                        AND (r.global OR r.id IN (
                            SELECT rule_group_id FROM rule_group_rel rg
                            WHERE rg.group_id IN %s
                        ))
                    ORDER BY r.id
                """, model_name, SQL(mode), tuple(self.env.user._get_group_ids()) or (None,))
                return self.browse(v for v, in self.env.execute_query(sql))


**Why does root user instantly make su = True**

1. In odoo/__init__.py:

        # ----------------------------------------------------------
        # Shortcuts
        # ----------------------------------------------------------
        # The hard-coded super-user id (a.k.a. administrator, or root user).
        SUPERUSER_ID = 1

2. In odoo/api.py:

        class Environment(Mapping):
        ...
            def __new__(cls, cr, uid, context, su=False, uid_origin=None):
                assert isinstance(cr, BaseCursor)
                if uid == SUPERUSER_ID:
                    su = True
