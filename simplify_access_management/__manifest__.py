# -*- coding: utf-8 -*-
#################################################################################
# Author      : Terabits Technolab (<www.terabits.xyz>)
# Copyright(c): 2023-25
# All Rights Reserved.
#
# This module is copyright property of the author mentioned above.
# You can't redistribute/reshare/recreate it for any purpose.
#
#################################################################################

{
    'name': 'Simplify Access Management',
    'version': '17.0.9.9.21',
    'sequence': 5,
    'author': 'Terabits Technolab',
    'license': 'OPL-1',
    'category': 'Services',
    'website': 'https://www.terabits.xyz/apps/17.0/simplify_access_management',
    'summary': """All In One Access Management App for setting the correct access rights for fields, models, menus, views for any module and for any user.
        All in one access management App,
        Easier then Record rules setup,
        Centralize access rules,
        User wise access rules,
        Show only what is needed for users,
        Access rules setup,
        Easy access rights setup, Hide Any Menu, Any Field, Any Report, Any Button,
        Easy To Configure,
        Access group management,
        Access organizational structure,
        Odoo user rights,
        User security roles,
        readonly whole system,
        Access Rights Manager,
        Advanced Users Access,
        Advanced Users Access Rights,
        Advanced Users Access Rights Manager,
        Access Manager Ninja,
        
        Main Features:-
        Hide fields,
        Hide Buttons,
        Hide Tabs,
        Hide views,
        Hide Contacts,
        Hide Menus,
        Hide submenus,
        Hide sub-menus,
        Hide reports,
        Hide actions,
        Hide server actions,
        Hide import,
        Hide delete,
        Hide Export,
        Hide archive,
        Hide Tree view, 
        Hide Form view, 
        Hide Kanban view, 
        Hide Calendar view, 
        Hide Pivot,
        Hide Graph view,
        Hide Apps,
        Hide object buttons,
        Hide action buttons,
        Hide smart buttons,
        Readonly Any Field,
        read only user,
        readonly user,
        Hide create,
        Hide duplicate,
        Readonly Field,
        Invisible Field,
        Hide Chatter,
        Invisible Chatter,
        Hide group by,
        Hide filter,
        Hide filters,
        Chatter Hide,
        Control every fields,
        Control every views,
        Control every buttons,
        Control every actions,
        Restrict/Read-Only Apps,
        Restrict/Read-Only Fields,
        Restrict/Read-Only Export,
        Restrict/Read-Only  Archive,
        Restrict/Read-Only Actions,
        Restrict/Read-Only Views,
        Restrict/Read-Only Reports,
        Restrict Delete items,
        Restrict Apps,
        Restrict Fields,
        Restrict Export,
        Restrict  Archive,
        Restrict Actions,
        Restrict Views,
        Restrict Reports,
        Restrict Delete items,
        user access,
        advance user,
        model access rights,
        sales access rights,sales user permissions,dashboard ninja
        inventery access rights, timesheet access rights,
        accounting access rights, accounting user permission,
        invoicing access rights,
        purchase access rights ,
        crm access rights ,
        all in one access rights manager
        access manager
        Sales access
        Sale access
        Invoicing access
        Invoice access
        CRM access
        Inventory access
        Accounting access
        Purchase access
        Project access
        Manufacturing access
        Email Marketing access
        Timesheets access
        Expenses access
        Documents access
        Time Off access
        Recruitment access
        Employees access
        Knowledge access
        Maintenance access
        Helpdesk access
        Subscriptions access
        Quality access
        Quality control access
        Contacts access
        Rental access
        Calendar access
        Field Service access
        Social Marketing access
        Appraisals access
        Fleet access
        Approvals access
        Consolidation access
        Appointments access
        Surveys access
        Repairs access
        Referral access
        Attendances access
        Management access
        Shipping access
        VOIP access
        Payroll access
        Jobs access
        Lunch access
        Fleet access
        Multi Company supported.
        """,

    'description': """
        All In One Access Management App for setting the correct access rights for fields, models, menus, views for any module and for any user.
        Configuring correct access rights in Odoo is quite technical for someone who has little experience with the system and can get messy if you are not sure what you are doing. This module helps you avoid all this complexity by providing you with a user friendly interface from where you can define access to specific objects in one place such as -

        Model/App access (Reports, Actions, Views, Readonly, Create, Write, Delete, Export, Archive etc.)
        Fields access (Invisible, Readonly fields for any model/app)
        Menu access(Hide any menu/submenu for any model/app for selected users)
        Views Access (Hide any view such as Tree view, Form view, Kanban view, Calendar view, Pivot & Graph view, etc)
        Hide Tabs and buttons
        Or, make any user Readonly
        Also the app allows you to create user-wise access management so that you can add/remove users to and from any group(s) in batch and with much ease.
        If you want to hide unwanted menu, sub-menu,fields,button(smart button and regular button), report action for any users, then you can use this app.
        
        All in one access management App,
        Easier then Record rules setup,
        Centralize access rules,
        User wise access rules,
        Show only what is needed for users,
        Access rules setup,
        Easy access rights setup, Hide Any Menu, Any Field, Any Report, Any Button,
        Easy To Configure,
        
        
        
        
        Main Features:-
        Hide fields,
        Hide Buttons,
        Hide Tabs,
        Hide views,
        Hide Contacts,
        Hide Menus,
        Hide submenus,
        Hide sub-menus,
        Hide reports,
        Hide actions,
        Hide server actions,
        Hide import,
        Hide delete,
        Hide archive,
        Hide Tree view, 
        Hide Form view, 
        Hide Kanban view, 
        Hide Calendar view, 
        Hide Pivot,
        Hide Graph view,
        Hide Apps,
        Hide object buttons,
        Hide action buttons,
        Hide smart buttons,
        Readonly Any Field,
        read only user,
        readonly user,
        Hide create,
        Hide duplicate,
        Control every fields,
        Control every views,
        Control every buttons,
        Control every actions,
        user access,
        advance user,
        model access rights,
        sales access rights,sales user permissions,
        inventery access rights, timesheet access rights,
        accounting access rights, accounting user permission,
        invoicing access rights,
        purchase access rights ,
        crm access rights ,
        all in one access rights manager
        Delight POS theme | Advance POS Theme | point of sale theme | Theme POS | Odoo POS theme
        Point of sale split bill | Point of sale split order | POS split bill | POS split invoices
	
    """,
    "images": ["static/description/banner.gif"],
    "price": "292.97",
    "currency": "USD",
    'data': [
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        'data/view_data.xml',
        'views/access_management_view.xml',
        'views/res_users_view.xml',
        'views/store_model_nodes_view.xml',
    ],
    'assets': {
        'web.assets_backend': [
            '/simplify_access_management/static/src/js/action_menus.js',
            '/simplify_access_management/static/src/js/hide_chatter.js',
            '/simplify_access_management/static/src/js/cog_menu.js',
            '/simplify_access_management/static/src/js/form_controller.js',
            '/simplify_access_management/static/src/js/pivot_grp_menu.js',
            '/simplify_access_management/static/src/js/pivot_renderer.js',
            '/simplify_access_management/static/src/js/model_field_selector.js',
            '/simplify_access_management/static/src/js/search_bar_menu.js',
        ],

    },
    'depends': ['base','mail','web','advanced_web_domain_widget'],
    'post_init_hook': 'post_install_action_dup_hook',
    'application': True,
    'installable': True,
    'auto_install': False,
    'live_test_url': 'https://www.terabits.xyz/request_demo?source=index&version=17&app=simplify_access_management',
}
