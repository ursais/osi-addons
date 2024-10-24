# Import Python Libs
from collections import namedtuple


ActionTuple = namedtuple(
    "Action",
    [
        # Specific odoo recordset or empty recordset
        "odoo_record",
        # The function we need to call
        "function",
        # Key value arguments for the function
        "function_kwargs",
        # UUID of the record we want to run the function on
        # this should match the UUID of the `odoo_record` if one was provided
        "uuid",
        # The Odoo `res.company` we should use to run the given function
        "company",
        # Flag to mark if this action was is for the `main mutation record``
        "main_mutation_record_action",
        # Allows us to link any record to the `main mutation record`
        "main_mutation_record_relationship_field_name",
    ],
)


class OdooMutationData:
    """
    OdooMutationData data represents two things.
    1. All of the decoded data that we received via the message directly for the record that we need to create / update / delete.
    2. List of function we need to call once the main crud functions finished. These function can range from updating the main mutation record, create related record, or run addition function at the end.

    The promise of this class is also two fold:
        - Store all of the mutation/decoding result in a nice clean structured way
        - Push the computation heavy processes to the queue.job so we don't have to run them immediately.
    """

    def __init__(self, env, uuid):
        self.env = env
        self.mutation_record_uuid = uuid
        self.actions = []

    def add_value_to_action(
        self,
        odoo_record,
        function,
        values,
        uuid,
        company=False,
        main_mutation_record_action=False,
    ):
        """
        Add decoded values to an Action for a specific record (identified by the odoo_record, or UUID).
        If the Action for the given record/function/company doesn't exist we create a new one and add the values to that.
        """
        # Use the given company, or default back to the environments company
        company = company or self.env.company

        # Use the given uuid, or default back to the odoo record's uuid if it has such a field defined
        uuid = uuid or odoo_record.uuid if hasattr(odoo_record, "uuid") else False

        # Try to find an existing action
        action = self.get_action(
            odoo_record=odoo_record, function=function, uuid=uuid, company=company
        )

        if action:
            # Update the existing action
            action.function_kwargs.update(values)
        else:
            self.add_action(
                odoo_record=odoo_record,
                function=function,
                function_kwargs=values,
                uuid=uuid,
                company=company,
                main_mutation_record_action=main_mutation_record_action,
            )

    def add_action(
        self,
        odoo_record,
        function,
        function_kwargs,
        uuid,
        company=False,
        main_mutation_record_action=False,
        main_mutation_record_relationship_field_name=False,
    ):
        """
        Wrapper function to make it easier to interact with this class
        """
        # Use the given company, or default back to the environments company
        company = company or self.env.company

        # Use the given uuid, or default back to the odoo record's uuid if it has such a field defined
        uuid = uuid or odoo_record.uuid if hasattr(odoo_record, "uuid") else False

        # Create a new action
        self.actions.append(
            ActionTuple(
                odoo_record=odoo_record,
                function=function,
                function_kwargs=function_kwargs,
                uuid=uuid,
                company=company,
                main_mutation_record_action=main_mutation_record_action,
                main_mutation_record_relationship_field_name=main_mutation_record_relationship_field_name,
            )
        )

    def get_action(self, odoo_record, uuid, function, company):
        if not uuid and not odoo_record:
            # If both the `odoo_record` and `UUID` is missing we can't find a specific action
            return False

        for action in self.actions:

            if (
                action.odoo_record == odoo_record
                and action.uuid == uuid
                and action.company == company
                and action.function == function
            ):
                # If all of the above is matching we can be sure we found the action we need
                return action

        return False

    def sort_actions(self):
        """
        Sort the actions by making sure the order of operations/company are correct
        for the main mutation record
        We can append the rest of the function to the end
        """

        sorted_actions = []
        # Find the company that is not the current environment company
        other_company = (
            self.env["res.company"]
            .get_all()
            .filtered(lambda c: c.id != self.env.company.id)
        )
        # Sorted list of companies
        # We need to do this so the main data is processed first
        companies = [self.env.company, other_company]

        for operation in ["create", "update", "delete"]:
            for company in companies:
                action = self.get_action(
                    odoo_record=False,
                    uuid=self.mutation_record_uuid,
                    function=operation,
                    company=company,
                )
                if action:
                    sorted_actions.append(action)
                    self.actions = [a for a in self.actions if a != action]
        self.actions = sorted_actions + self.actions

    def print(self):
        # Make sure actions are in the correct order
        print("")
        print("All current mutation actions:")
        ####################
        #  Pretty printer  #
        ####################
        import pprint

        for action in self.actions:
            print("")
            print(f"Odoo Record: {action.odoo_record}")
            print(f"Function: {action.function}")
            print("Function Kwargs:")
            pprint.pprint(action.function_kwargs)
            print(f"UUID: {action.uuid}")
            print(f"Company: {action.company}")
            print(f"Main Record: {action.main_mutation_record_action}")
            print(
                f"Main Record relation field: {action.main_mutation_record_relationship_field_name}"
            )
            print("-" * 20)

    def apply(self):
        """
        Convert the named tuple actions into dictionaries.
        We need to do this as named tuples can't be serialized correctly,
        which means the queue.job() processing would mess up our data.
        """
        self.sort_actions()

        action_dictionaries = []
        for action in self.actions:
            action_dictionaries.append(dict(action._asdict()))
        return action_dictionaries
