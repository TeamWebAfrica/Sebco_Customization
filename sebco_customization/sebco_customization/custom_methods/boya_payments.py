import frappe
from datetime import datetime

class BoyaPayments:
    '''
    Class that handles all things related to the Boya expense doctype functionality
    '''
    def __init__(self, expense_details):
        self.expense_details = expense_details
        self.abort_transaction = False

    def process_expense_notification(self):
        '''
        This is the main methods that calls all the other class methods to handle an
        expense notification from Boya
        '''
        self.get_or_create_boya_expense()
        self.create_journal_entry()

    def get_or_create_boya_expense(self):
        '''
        Method that checks if the given Boya expense already exists 
        in the database and if not creates one
        '''
        if self.abort_transaction:
            return 

        boya_expense_list = frappe.get_list('Boya Expense', fields=['name'], filters={
            'transaction_ref': self.expense_details['transaction_ref']
        })

        self.expense_doc = None
        if len(boya_expense_list): 
            expense_name = boya_expense_list[0]['name']
            self.expense_doc = frappe.get_doc('Boya Expense',expense_name)
        
        # return if the boya expense record is found
        if self.expense_doc:
            return
        
        # create a new expense
        new_expense_doc = frappe.new_doc('Boya Expense')
        # add all the details from Boya
        new_expense_doc.id = self.expense_details['_id']
        new_expense_doc.transaction_ref = self.expense_details['transaction_ref']
        new_expense_doc.provider_ref = self.expense_details['provider_ref']
        new_expense_doc.amount = self.expense_details['amount']
        new_expense_doc.fees = self.expense_details['fees']
        new_expense_doc.charge = self.expense_details['charge']
        new_expense_doc.original_currency = self.expense_details['original_currency']
        # new_expense_doc.original_amount = self.expense_details['original_amount']
        new_expense_doc.employee_id = self.expense_details['employee_id']
        new_expense_doc.person = self.expense_details['person']
        new_expense_doc.merchant_category_code = self.expense_details['MerchantCategoryCode']
        new_expense_doc.fx_rate = self.expense_details['fx_rate']
        new_expense_doc.card_vcn = self.expense_details['card_vcn']
        new_expense_doc.reciever = self.expense_details['receiver']
        new_expense_doc.account_no = self.expense_details['accno']
        new_expense_doc.payment_type = self.expense_details['payment_type']
        new_expense_doc.channel = self.expense_details['channel']

        # handle sub category as  table
        # new_expense_doc.subcategory = self.expense_details['subcategory']
        new_expense_doc.subcategory_id = self.expense_details['subcategory']['_id']
        new_expense_doc.group_id = self.expense_details['subcategory']['group_id']
        new_expense_doc.category = self.expense_details['subcategory']['category']
        new_expense_doc.sub_category_status = self.expense_details['subcategory']['status']
        new_expense_doc.code = self.expense_details['subcategory']['code']
        new_expense_doc.name1 = self.expense_details['subcategory']['name']
        new_expense_doc.description = self.expense_details['subcategory']['description']
        new_expense_doc.mapping_id = self.expense_details['subcategory']['mapping_id']
        new_expense_doc.created_at_subcategory = self.expense_details['subcategory']['createdAt']
        new_expense_doc.__v = self.expense_details['subcategory']['__v']
        new_expense_doc.updated_at_subcategory = self.expense_details['subcategory']['updatedAt']


        # handle team as a table
        # new_expense_doc.team = self.expense_details['team']

        new_expense_doc.currency = self.expense_details['currency']

        # handle tag as a list/ table
        # new_expense_doc.tag = self.expense_details['tag']

        new_expense_doc.notes = self.expense_details['notes']

        # Add attachements here
        if self.expense_details['attachments'] and len(self.expense_details['attachments']):
            for attachement in self.expense_details['attachments']:
                new_expense_doc.append("attachments", {
					"attachment_url":attachement,
				})

        new_expense_doc.payment_status = self.expense_details['payment_status']
        new_expense_doc.boya_status = self.expense_details['status']

        # Add reviews here
        if self.expense_details['reviews'] and len(self.expense_details['reviews']):
            for review in self.expense_details['reviews']:
                new_expense_doc.append("reviews", {
					"person": review['person'],
                    "reviewed_on": review['reviewed_on'],
                    "notes": review['notes'],
                    "status": review['status']
				})

        new_expense_doc.exported = self.expense_details['exported']
        new_expense_doc.sync_successful = self.expense_details['sync_successful']
        # new_expense_doc.external_sync_id = self.expense_details['external_sync_id']
        # new_expense_doc.sync_error = self.expense_details['sync_error']
        new_expense_doc.vendor = self.expense_details['vendor']

        # Add complete request data log here
        new_expense_doc.complete_request_data = str(self.expense_details)

        # add project abbreviations
        new_expense_doc.project_abbreviation = self.expense_details['subcategory']['code'][:-7]
        
        # save new expense
        new_expense_doc.save()
        frappe.db.commit()

        # set class expense_doc
        self.expense_doc = new_expense_doc

    def create_journal_entry(self):
        '''
        Method that creates a jounal entry based on a notifaction recieved from 
        Boya
        '''
        if self.expense_doc.status == 'Complete':
            self.expense_doc.append('activity_logs_table',
            {
                'activity': 'Posting Journal Entry',
                'status': 'Failed',
                'description': 'This transaction has already been completed (Double Posting from Boya)'
            }
            )
            self.expense_doc.save()
            frappe.db.commit()
            return
        
        # Mark transaction expense as pending
        self.expense_doc.status = 'Pending'
        # add an initialization log to boya expense
        self.expense_doc.append('activity_logs_table',
            {
                'activity': 'Posting Journal Entry',
                'status': 'Success',
                'description': 'Linking to Journal entry process started'
            }
        )
        self.expense_doc.save()
        frappe.db.commit()

        if self.abort_transaction:
            self.expense_doc.append('activity_logs_table',
                {
                    'activity': 'Posting Journal Entry',
                    'status': 'Failed',
                    'description': 'Transaction aborted'
                }
            )
            self.expense_doc.status = 'Failed'
            self.expense_doc.save()
            frappe.db.commit()
            return 
        
        # check for duplicate transaction
        if self.expense_doc.linked_journal_entry:
            
            # add a error log to boya expense
            self.expense_doc.append('activity_logs_table',
                {
                    'activity': 'Checking Journal Entry',
                    'status': 'Failed',
                    'description': 'This expense transaction is already linked to a Journal Entry: {}.'.format(self.expense_doc.linked_journal_entry)
                }
            )
            self.expense_doc.status = 'Failed'
            self.expense_doc.save()
            frappe.db.commit()

            # Abort transaction
            self.abort_transaction = True
            return
        
        # get project associated with expense
        project_list = frappe.get_list('Project', fields=['name','company','cost_center'], filters={
            'project_abbreviation': self.expense_doc.project_abbreviation
        })

        associated_company, associated_cost_center = None, None # company and cost center of project owner
        if len(project_list):
            # get company associated with project
            associated_company = project_list[0]['company']
            associated_cost_center = project_list[0]['cost_center']    

        # get account details
        sebco_settings = frappe.get_single('Sebco Settings')
        company_expense_accounts = sebco_settings.boya_expense_company_account
        boya_expense_acc_name, boya_fees_acc_name = None, None
        if associated_company:
            filtered_list = list(filter(lambda x: x.company == associated_company, company_expense_accounts))
            if len(filtered_list):
                boya_expense_acc_name = filtered_list[0].expense_account
                boya_fees_acc_name = filtered_list[0].bank_charges_account
        else:
            associated_company = sebco_settings.main_company

        if not boya_expense_acc_name:
            boya_expense_acc_name = sebco_settings.boya_expense_account
        if not boya_fees_acc_name:
            boya_fees_acc_name = sebco_settings.bank_charges

        supplier_expense_acc_no = self.expense_details['subcategory']['code']
        if not boya_expense_acc_name or not boya_fees_acc_name:
            # add a error log to boya expense
            self.expense_doc.append('activity_logs_table',
                {
                    'activity': 'Fetching Expense/Bank Charges',
                    'status': 'Failed',
                    'description': 'Error occuring fetching expense account in Sebco Settings'
                }
            )
            self.expense_doc.status = 'Failed'
            self.expense_doc.save()
            frappe.db.commit()

            # Abort transaction
            self.abort_transaction = True
            return

        # Sebco accounts from are given in the following format
        # <Project Identifiers - varying number of letters><seven digits - actual account number>
        supplier_expense_acc_no = supplier_expense_acc_no[-7:]
        if len(supplier_expense_acc_no) != 7:
            # add a error log to boya expense
            self.expense_doc.append('activity_logs_table',
                {
                    'activity': 'Checking Account Validity',
                    'status': 'Failed',
                    'description': 'Every account should be made of 7 digits apart from project identifiers'.format(supplier_expense_acc_no)
                }
            )
            self.expense_doc.status = 'Failed'
            self.expense_doc.save()
            frappe.db.commit()

            # Abort transaction
            self.abort_transaction = True
            return
        
        supplier_expense_acc_no = supplier_expense_acc_no[:4] + '/' + supplier_expense_acc_no[4:]

        account_list = frappe.get_list('Account', 
            fields=['name'], filters={
            'account_number': supplier_expense_acc_no,
            'company': associated_company,
        })

        if not len(account_list):
            # add a error log to boya expense
            self.expense_doc.append('activity_logs_table',
                {
                    'activity': 'Getting Expense Account',
                    'status': 'Failed',
                    'description': 'The account number: {} does not exist.'.format(supplier_expense_acc_no)
                }
            )
            self.expense_doc.status = 'Failed'
            self.expense_doc.save()
            frappe.db.commit()

            # Abort transaction
            self.abort_transaction = True
            return    

        supplier_expense_acc_name = account_list[0]['name']
        transaction_date = self.expense_details['transaction_date'].split('T')[0]
        # Create a new journal entry
        new_journal_entry = frappe.new_doc('Journal Entry')
        new_journal_entry.voucher_type = 'Bank Entry'
        new_journal_entry.posting_date = transaction_date
        new_journal_entry.cheque_no = self.expense_details['provider_ref'],
        new_journal_entry.cheque_date = transaction_date
        new_journal_entry.bill_no = self.expense_details['transaction_ref']
        if associated_company and associated_cost_center:
            new_journal_entry.company = associated_company

            # credit account
            new_journal_entry.append('accounts', {
                'account': boya_expense_acc_name,
                'debit_in_account_currency': 0,
                'credit_in_account_currency': self.expense_details['charge'],
                'cost_center': associated_cost_center
            })
            # debit account (Amount)
            new_journal_entry.append('accounts', {
                'account': supplier_expense_acc_name,
                'debit_in_account_currency': self.expense_details['amount'],
                'credit_in_account_currency': 0,
                'cost_center': associated_cost_center
            })
            # debit account (Charge/Fees)
            new_journal_entry.append('accounts', {
                'account': boya_fees_acc_name,
                'debit_in_account_currency': self.expense_details['fees'],
                'credit_in_account_currency': 0,
                'cost_center': associated_cost_center
            })
        else:
            # credit account
            new_journal_entry.append('accounts', {
                'account': boya_expense_acc_name,
                'debit_in_account_currency': 0,
                'credit_in_account_currency': self.expense_details['charge']
            })
            # debit account (Amount)
            new_journal_entry.append('accounts', {
                'account': supplier_expense_acc_name,
                'debit_in_account_currency': self.expense_details['amount'],
                'credit_in_account_currency': 0
            })
            # debit account (Charge/Fees)
            new_journal_entry.append('accounts', {
                'account': boya_fees_acc_name,
                'debit_in_account_currency': self.expense_details['fees'],
                'credit_in_account_currency': 0
            })

        # add description
        new_journal_entry.user_remark = self.expense_details['notes']
        
        # Add all the required details for the journal entry
        new_journal_entry.save()

        # submit the journal entry
        new_journal_entry.submit()

        # add success log to boya expense
        self.expense_doc.append('activity_logs_table',
            {
                'activity': 'Posting Expense to Journal Entry',
                'status': 'Success',
                'description': f'Successfully posted to Journal Entry: {new_journal_entry.name}'
            }
        )
        self.expense_doc.save()
        frappe.db.commit()

        # update the status of expense
        self.expense_doc.status = 'Complete'
        self.expense_doc.linked_journal_entry = new_journal_entry.name
        self.expense_doc.save()
        frappe.db.commit()

    def notification_received(self):
        '''
        Method that sends a callback notification back to Boya that the 
        notification was recieved successfully
        '''
        pass
