{
    'name': 'Sale order discount approval',
    'version': '20.0.1.0.0',
    'category': 'Sales/Sales',
    'summary': 'Tiered approval workflow for sales orders with high discounts',
    'author': 'Luis Calero',
    'website': 'https://github.com/naul-sketches/odoo-custom-addons',
    'maintainer': 'Luis Calero',
    'license': 'LGPL-3',
    'depends': [
        'sale',
    ],
    'data': [
        'views/sale_order_views.xml',
    ],
    'demo': [
        'demo/sale_order_demo.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
