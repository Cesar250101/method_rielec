# -*- coding: utf-8 -*-
{
    'name': "method_rielec",

    'summary': """
        Localización Rielec""",

    'description': """
        Localización Rielec
    """,

    'author': "Method ERP",
    'website': "https://www.method.cl",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','account','sale','purchase','point_of_sale','l10n_cl_dte_point_of_sale','bi_pos_backend_workflow','pos_user_restrict'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'data/cron.xml',
        'wizard/select_products_wizard_view.xml',
        'views/sale_views.xml',        
        'views/journal.xml',
        'wizard/pos_make_payment.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}