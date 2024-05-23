# pylint: disable=pointless-statement
{
    'name': 'Tariffs on Products',
    'summary': 'Store and sync tariff field on products.',
    'description': """
        Some products have tariffs applied to them. We need to be able to sync those values and
        use them when creating quote workups.
        """,
    'author': 'OnLogic',
    'website': 'https://www.onlogic.com',
    'onlogic': True,
    'category': 'Products',
    'version': '17.0.0.1.0',
    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'product'
    ],
    # always loaded
    'data': ['views/product.xml'],
}
