# pylint: disable=pointless-statement
{
    "name": "OnLogic Exception handling",
    "summary": "Add group for python access to exception rules.",
    "description": """
        Adding the Group for Adding a Python code in Base Exception.
        """,
    "author": "OnLogic",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "category": "Tools",
    "version": "17.0.0.1.0",
    # any module necessary for this one to work correctly
    "depends": [
        "base_exception",
    ],
    # always loaded
    "data": [
        "security/base_exception_security.xml",
        "views/exception_rule_view.xml",
    ],
}
