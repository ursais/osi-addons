import odoo.tests.common as common
import time


class TestAccountMove(common.TransactionCase):

    def setUp(self):
        super(TestAccountMove, self).setUp()

        self.company = self.env.ref('base.main_company')

        self.due_to_due_from_journal_main_company =\
            self.env['account.journal'].create(
                {'name': 'Test Due To/Due From', 'type': 'general',
                 'code': 'DUE',
                 'currency_id': self.company.currency_id.id,
                 'company_id': self.company.id})

        user_type_current_liabilities = self.env.ref(
            'account.data_account_type_current_liabilities')

        self.account_due_to_main_company = self.env['account.account'].create({
            'code': 'Test 101404',
            'name': 'Test Due To Account',
            'user_type_id': user_type_current_liabilities.id,
            'company_id': self.company.id
        })

        self.account_payroll_clearing_main_company =\
            self.env['account.account'].create({
                'code': 'Test 212410',
                'name': 'Test Payroll Clearing',
                'user_type_id': user_type_current_liabilities.id,
                'company_id': self.company.id
            })

        user_type_current_assets = self.env.ref(
            'account.data_account_type_current_assets')

        self.account_due_from_main_company =\
            self.env['account.account'].create({
                'code': 'Test 100020',
                'name': 'Test Due From Account',
                'user_type_id': user_type_current_assets.id,
                'company_id': self.company.id
            })

        user_type_current_expenses = self.env.ref(
            'account.data_account_type_expenses')

        self.account_salary_expense_main_company =\
            self.env['account.account'].create({
                'code': 'Test 212400',
                'name': 'Test Salary Expenses',
                'user_type_id': user_type_current_expenses.id,
                'company_id': self.company.id,
                'reconcile': True
            })

        self.account_invoice_main_company =\
            self.env['account.account'].create({
                'code': 'Invoice 062320',
                'name': 'Test Invoices',
                'user_type_id': user_type_current_expenses.id,
                'company_id': self.company.id,
                'reconcile': True
            })

        self.company.due_fromto_payment_journal_id =\
            self.due_to_due_from_journal_main_company
        self.company.due_from_account_id = self.account_due_from_main_company
        self.company.due_to_account_id = self.account_due_to_main_company

        self.partner_company_one = self.env["res.partner"].sudo().create({
            "name": "Test Company One"
        })
        self.company_one = self.env["res.company"].sudo().create({
            "name": "Test Company One",
            "partner_id": self.partner_company_one.id,
            "parent_id": self.company.id
        })

        self.due_to_due_from_journal_company_one =\
            self.env['account.journal'].sudo().create(
                {'name': 'Test Due To/Due From', 'type': 'general',
                 'code': 'DUE',
                 'currency_id': self.company.currency_id.id,
                 'company_id': self.company_one.id})

        self.account_due_to_company_one =\
            self.env['account.account'].sudo().create({
                'code': 'Test 101404',
                'name': 'Test Due To Account',
                'user_type_id': user_type_current_liabilities.id,
                'company_id': self.company_one.id
            })

        self.account_due_from_company_one =\
            self.env['account.account'].sudo().create({
                'code': 'Test 100020',
                'name': 'Test Due From Account',
                'user_type_id': user_type_current_assets.id,
                'company_id': self.company_one.id
            })

        self.account_invoice_company_one =\
            self.env['account.account'].create({
                'code': 'Invoice 062320',
                'name': 'Test Invoices',
                'user_type_id': user_type_current_expenses.id,
                'company_id': self.company_one.id,
                'reconcile': True
            })

        self.company_one.due_fromto_payment_journal_id =\
            self.due_to_due_from_journal_company_one
        self.company_one.due_from_account_id =\
            self.account_due_from_company_one
        self.company_one.due_to_account_id = self.account_due_to_company_one

        self.account_salary_expense_company_one =\
            self.env['account.account'].sudo().create({
                'code': 'Test 212400',
                'name': 'Test Salary Expenses',
                'user_type_id': user_type_current_expenses.id,
                'company_id': self.company_one.id,
                'reconcile': True
            })

        self.partner_company_two = self.env["res.partner"].sudo().create({
            "name": "Test Company Two"
        })
        self.company_two = self.env["res.company"].sudo().create({
            "name": "Test Company Two",
            "partner_id": self.partner_company_two.id,
            "parent_id": self.company.id
        })

        self.due_to_due_from_journal_company_two =\
            self.env['account.journal'].sudo().create(
                {'name': 'Test Due To/Due From', 'type': 'general',
                 'code': 'DUE',
                 'currency_id': self.company.currency_id.id,
                 'company_id': self.company_two.id})

        self.account_due_to_company_two =\
            self.env['account.account'].sudo().create({
                'code': 'Test 101404',
                'name': 'Test Due To Account',
                'user_type_id': user_type_current_liabilities.id,
                'company_id': self.company_two.id
            })

        self.account_due_from_company_two =\
            self.env['account.account'].sudo().create({
                'code': 'Test 100020',
                'name': 'Test Due From Account',
                'user_type_id': user_type_current_assets.id,
                'company_id': self.company_two.id
            })

        self.account_salary_expense_company_two =\
            self.env['account.account'].sudo().create({
                'code': 'Test 212400',
                'name': 'Test Salary Expenses',
                'user_type_id': user_type_current_expenses.id,
                'company_id': self.company_two.id,
                'reconcile': True
            })

        self.company_two.due_fromto_payment_journal_id =\
            self.due_to_due_from_journal_company_two
        self.company_two.due_from_account_id =\
            self.account_due_from_company_two
        self.company_two.due_to_account_id = self.account_due_to_company_two

        self.employee_A = self.env["res.partner"].create({
            'name': 'Employee A'
        })

        self.employee_B = self.env["res.partner"].create({
            'name': 'Employee B'
        })

        self.employee_C = self.env["res.partner"].create({
            'name': 'Employee C'
        })

        employee_group = self.env.ref('base.group_user')
        employee_invoice_group = self.env.ref('account.group_account_invoice')

        self.account_user = self.env["res.users"].\
            with_context({'no_reset_password': True}).create(dict(
                name="Adviser",
                company_id=self.company.id,
                login="fm",
                email="accountmanager@yourcompany.com",
                groups_id=[
                    (6, 0, [employee_group.id, employee_invoice_group.id])]
            ))
        self.seg_one_a = self.env['analytic.segment.one'].create({
            'name': "Test One Alpha",
            'code': '1A'
        })
        self.seg_one_b = self.env['analytic.segment.one'].create({
            'name': "Test One Beta",
            'code': '1B'
        })
        self.seg_one_c = self.env['analytic.segment.one'].create({
            'name': "Test One Charlie",
            'code': '1C'
        })
        self.seg_two_a = self.env['analytic.segment.two'].create({
            'name': "Test Two Alpha",
            'code': '2A'
        })
        self.seg_two_b = self.env['analytic.segment.two'].create({
            'name': "Test Two Beta",
            'code': '2B'
        })
        self.seg_two_c = self.env['analytic.segment.two'].create({
            'name': "Test Two Charlie",
            'code': '2C'
        })

    def test_account_move_segments(self):

        self.journalrec = self.env['account.journal'].sudo(
            self.account_user.id).search([('type', '=', 'general')])[0]

        payroll_move = self.env["account.move"].\
            sudo(self.account_user.id).create({
                'journal_id': self.journalrec.id,
                'company_id': self.company.id,
                'line_ids': [(0, 0, {
                    'account_id': self.account_salary_expense_main_company.id,
                    'partner_id': self.employee_B.id,
                    'debit': 1000
                }), (0, 0, {
                    'account_id': self.account_salary_expense_main_company.id,
                    'partner_id': self.employee_A.id,
                    'debit': 500
                }), (0, 0, {
                    'account_id': self.account_salary_expense_main_company.id,
                    'partner_id': self.employee_C.id,
                    'debit': 500,
                    'transfer_to_company_id': self.company_two.id,
                    'analytic_segment_one_id': self.seg_one_a.id,
                    'analytic_segment_two_id': self.seg_two_a.id
                }), (0, 0, {
                    'account_id': self.account_salary_expense_main_company.id,
                    'partner_id': self.employee_B.id,
                    'debit': 600,
                    'transfer_to_company_id': self.company_one.id,
                    'analytic_segment_one_id': self.seg_one_b.id,
                    'analytic_segment_two_id': self.seg_two_b.id
                }), (0, 0, {
                    'account_id': self.account_salary_expense_main_company.id,
                    'partner_id': self.employee_A.id,
                    'debit': 400,
                    'transfer_to_company_id': self.company_one.id,
                    'analytic_segment_one_id': self.seg_one_c.id,
                    'analytic_segment_two_id': self.seg_two_c.id

                }), (0, 0, {
                    'account_id':
                    self.account_payroll_clearing_main_company.id,
                    'credit': 3000,
                })
                ]
            })

        payroll_move.post()

        company_one_move = self.env['account.move'].sudo(self.account_user.id).\
            search([('journal_id', '=',
                     self.due_to_due_from_journal_company_one.id),
                    ('company_id', '=', self.company_one.id)])


        self.assertEqual(company_one_move.line_ids[0].analytic_segment_one_id.id,
                         company_one_move.line_ids[1].analytic_segment_one_id.id,
                         self.seg_one_b.id)

        self.assertEqual(company_one_move.line_ids[2].analytic_segment_one_id.id,
                         company_one_move.line_ids[3].analytic_segment_one_id.id,
                         self.seg_one_c.id)
        
        self.assertEqual(company_one_move.line_ids[0].analytic_segment_two_id.id,
                         company_one_move.line_ids[1].analytic_segment_two_id.id,
                         self.seg_two_b.id)

        self.assertEqual(company_one_move.line_ids[2].analytic_segment_two_id.id,
                         company_one_move.line_ids[3].analytic_segment_two_id.id,
                         self.seg_two_c.id)

        company_two_move =\
            self.env['account.move'].sudo(self.account_user.id).\
                search([('journal_id', '=',
                         self.due_to_due_from_journal_company_two.id),
                       ('company_id', '=', self.company_two.id)])

        self.assertEqual(company_two_move.line_ids[0].analytic_segment_one_id.id,
                         company_two_move.line_ids[1].analytic_segment_one_id.id,
                         self.seg_one_a.id)

        self.assertEqual(company_two_move.line_ids[0].analytic_segment_two_id.id,
                         company_two_move.line_ids[1].analytic_segment_two_id.id,
                         self.seg_two_a.id)

    def test_distribution_segments(self):
        """ Returns an open invoice """
        invoice_id = self.env['account.invoice'].create({
            'partner_id': self.env.ref("base.res_partner_2").id,
            'currency_id': self.env.ref('base.USD').id,
            'name': 'Test Distribution Segments',
            'account_id': self.account_invoice_main_company.id,
            'type': 'in_invoice',
            'date_invoice': time.strftime('%Y') + '-06-26',
        })
        invoice_line_id = self.env['account.invoice.line'].create({
            'product_id': self.env.ref("product.product_product_4").id,
            'quantity': 1,
            'price_unit': 100.00,
            'invoice_id': invoice_id.id,
            'name': 'something',
            'account_id': self.account_invoice_main_company.id,
            'analytic_segment_one_id': self.seg_one_a.id,
            'analytic_segment_two_id': self.seg_two_a.id
        })
        self.env['account.invoice.line.distribution'].create({
            'percent': 50.00,
            'amount': 50.00,
            'company_id': self.company_one.id,
            'invoice_line_id': invoice_line_id.id
        })
        invoice_line_id._onchange_distribution_ids_percent()
        invoice_id.action_invoice_open()

        self.due_to = self.env['account.move'].sudo().search([
            ('company_id', '=', self.company_one.id),
            ('ref', 'like', invoice_id.number)])

        self.assertEqual(self.due_to.line_ids[0].analytic_segment_one_id.id,
                         self.due_to.line_ids[1].analytic_segment_one_id.id,
                         self.seg_one_a.id)

        self.assertEqual(self.due_to.line_ids[0].analytic_segment_two_id.id,
                         self.due_to.line_ids[1].analytic_segment_two_id.id,
                         self.seg_two_a.id)

        self.due_from = self.env['account.move'].search([
            ('ref', 'like', invoice_id.number),
            ('journal_id', '=', self.due_to_due_from_journal_main_company.id)
        ])

        self.assertEqual(self.due_from.line_ids[0].analytic_segment_one_id.id,
                         self.due_from.line_ids[1].analytic_segment_one_id.id,
                         self.seg_one_a.id)

        self.assertEqual(self.due_from.line_ids[0].analytic_segment_two_id.id,
                         self.due_from.line_ids[1].analytic_segment_two_id.id,
                         self.seg_two_a.id)
