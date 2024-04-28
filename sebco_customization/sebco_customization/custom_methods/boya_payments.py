import frappe, json
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

    def retry_process_expense_notification(self):
        '''
        This is the main methods that calls all the other class methods to handle an
        expense notification from Boya
        '''
        # Run the retry transaction method
        transaction_details = self.retry_get_or_create_boya_expense()
        if not transaction_details['status']:
            return transaction_details
        
        # Create journal entry if the retrial was successful
        self.create_journal_entry()
        return { 'status': True }

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
        # new_expense_doc.complete_request_data = self.expense_details
        new_expense_doc.complete_request_data_json = self.expense_details
        new_expense_doc.save()
        frappe.db.commit()

        # add all the details from Boya
        new_expense_doc.id = self.get_values(['_id'])
        new_expense_doc.transaction_ref = self.get_values(['transaction_ref'])
        new_expense_doc.provider_ref = self.get_values(['provider_ref'])
        new_expense_doc.amount = self.get_values(['amount'])
        new_expense_doc.fees = self.get_values(['fees'])
        new_expense_doc.transaction_date = self.get_values(['transaction_date'])
        new_expense_doc.charge = self.get_values(['charge'])
        new_expense_doc.original_currency = self.get_values(['original_currency'])
        # new_expense_doc.original_amount = self.expense_details['original_amount']
        new_expense_doc.employee_id = self.get_values(['employee_id'])
        new_expense_doc.person = self.get_values(['person'])
        new_expense_doc.merchant_category_code = self.get_values(['MerchantCategoryCode'])
        new_expense_doc.fx_rate = self.get_values(['fx_rate'])
        new_expense_doc.card_vcn = self.get_values(['card_vcn'])
        new_expense_doc.reciever = self.get_values(['receiver'])
        new_expense_doc.account_no = self.get_values(['accno'])
        new_expense_doc.payment_type = self.get_values(['payment_type'])
        new_expense_doc.channel = self.get_values(['channel'])

        # handle sub category as  table
        new_expense_doc.subcategory = self.expense_details['subcategory']
        new_expense_doc.subcategory_id = self.get_values(['subcategory','_id'])
        new_expense_doc.group_id = self.get_values(['subcategory','group_id'])
        new_expense_doc.category = self.get_values(['subcategory','category'])
        new_expense_doc.sub_category_status = self.get_values(['subcategory','status'])
        new_expense_doc.code = self.get_values(['subcategory','code'])
        new_expense_doc.name1 = self.get_values(['subcategory','name'])
        new_expense_doc.description = self.get_values(['subcategory','description'])
        new_expense_doc.mapping_id = self.get_values(['subcategory','mapping_id'])
        new_expense_doc.created_at_subcategory = self.get_values(['subcategory','createdAt'])
        new_expense_doc.__v = self.get_values(['subcategory','__v'])
        new_expense_doc.updated_at_subcategory = self.get_values(['subcategory','updatedAt'])

        # handle team as a table
        # new_expense_doc.team = self.expense_details['team']

        new_expense_doc.currency = self.get_values(['currency'])

        # handle tag as a list/ table
        # new_expense_doc.tag = self.expense_details['tag']

        new_expense_doc.notes = self.get_values(['notes'])

        # Add attachements here
        if self.get_values(['attachments']) and len(self.get_values(['attachments'])):
            for attachement in self.get_values(['attachments']):
                new_expense_doc.append("attachments", {
					"attachment_url":attachement,
				})

        new_expense_doc.payment_status = self.get_values(['payment_status'])
        new_expense_doc.boya_status = self.get_values(['status'])

        # Add reviews here
        reviews = self.get_values(['reviews'])
        if reviews and len(reviews):
            for review in reviews:
                new_expense_doc.append("reviews", {
					"person": review['person'],
                    "reviewed_on": review['reviewed_on'],
                    "notes": review['notes'],
                    "status": review['status']
				})

        new_expense_doc.exported = self.get_values(['exported'])
        new_expense_doc.sync_successful = self.get_values(['sync_successful'])
        # new_expense_doc.external_sync_id = self.expense_details['external_sync_id']
        # new_expense_doc.sync_error = self.expense_details['sync_error']
        new_expense_doc.vendor = self.get_values(['vendor'])

        # Add complete request data log here
        # new_expense_doc.complete_request_data = str(self.expense_details)

        # add project abbreviations
        sub_category_code = self.get_values(['subcategory','code'])
        project_abbreviation = None
        if sub_category_code:
            try:
                project_abbreviation = sub_category_code[:-7]
            except:
                pass
        new_expense_doc.project_abbreviation = project_abbreviation
        
        # save new expense
        new_expense_doc.save()
        frappe.db.commit()

        # set class expense_doc
        self.expense_doc = new_expense_doc

    def retry_get_or_create_boya_expense(self):
        '''
        Methods that attempts to retry processing of the expense
        '''
        # define expense_doc as self.expense_doc 
        expense_doc = self.expense_doc

        # Can only retry transaction whose statuses are are Pending, Draft or Failed
        retry_statuses = ['Pending', 'Draft', 'Failed']
        if self.expense_doc.status not in retry_statuses:
            return { "status": False, 
                    "error": "This action is only allowed for Pending, Draft and Failed Expenses"}

        # Check that the transaction is not marked as aborted
        if self.abort_transaction:
            return { "status": False, 
                    "error": "An error occured please contact support"}
        
        # check that the expense details were defined
        if not self.expense_details:
            return { "status": False, "error": "This Expense is blank"}
        
        # add all the details from Boya
        expense_doc.id = self.get_only_nil_values(expense_doc.id,['_id'])
        expense_doc.transaction_ref = self.get_only_nil_values(expense_doc.transaction_ref,['transaction_ref'])
        expense_doc.provider_ref = self.get_only_nil_values(expense_doc.provider_ref,['provider_ref'])
        expense_doc.amount = self.get_only_nil_values(expense_doc.amount,['amount'])
        expense_doc.fees = self.get_only_nil_values(expense_doc.amount,['fees'])
        expense_doc.transaction_date = self.get_values(['transaction_date'])
        expense_doc.charge = self.get_only_nil_values(expense_doc.charge,['charge'])
        expense_doc.original_currency = self.get_only_nil_values(expense_doc.original_currency,['original_currency'])
        # new_expense_doc.original_amount = self.expense_details['original_amount']
        expense_doc.employee_id = self.get_only_nil_values(expense_doc.employee_id,['employee_id'])
        expense_doc.person = self.get_only_nil_values(expense_doc.person,['person'])
        expense_doc.merchant_category_code = self.get_only_nil_values(expense_doc.merchant_category_code,['MerchantCategoryCode'])
        expense_doc.fx_rate = self.get_only_nil_values(expense_doc.fx_rate,['fx_rate'])
        expense_doc.card_vcn = self.get_only_nil_values(expense_doc.card_vcn,['card_vcn'])
        expense_doc.reciever = self.get_only_nil_values(expense_doc.reciever,['receiver']) 
        expense_doc.account_no = self.get_only_nil_values(expense_doc.account_no,['accno'])
        expense_doc.payment_type = self.get_only_nil_values(expense_doc.payment_type,['payment_type'])
        expense_doc.channel = self.get_only_nil_values(expense_doc.channel,['channel'])

        # handle sub category as table
        expense_doc.subcategory = self.expense_details['subcategory']
        expense_doc.subcategory_id = self.get_only_nil_values(expense_doc.subcategory_id,['subcategory','_id'])
        expense_doc.group_id = self.get_only_nil_values(expense_doc.group_id,['subcategory','group_id'])
        expense_doc.category = self.get_only_nil_values(expense_doc.category,['subcategory','category'])
        expense_doc.sub_category_status = self.get_only_nil_values(expense_doc.sub_category_status,['subcategory','status'])
        expense_doc.code = self.get_only_nil_values(expense_doc.code,['subcategory','code'])
        expense_doc.name1 = self.get_only_nil_values(expense_doc.name1,['subcategory','name'])
        expense_doc.description = self.get_only_nil_values(expense_doc.description,['subcategory','description'])
        expense_doc.mapping_id = self.get_only_nil_values(expense_doc.mapping_id,['subcategory','mapping_id'])
        expense_doc.created_at_subcategory = self.get_only_nil_values(expense_doc.created_at_subcategory,['subcategory','createdAt'])
        # expense_doc.__v = self.get_only_nil_values(expense_doc.__v,['subcategory','__v'])
        # expense_doc.updated_at_subcategory = self.get_only_nil_values(expense_doc.updated_at_subcategory,['subcategory','updatedAt'])

        # handle team as a table
        # expense_doc.team = self.expense_details['team']
        self.currency = self.get_only_nil_values(expense_doc.currency,['currency'])

        # handle tag as a list/ table
        # new_expense_doc.tag = self.expense_details['tag']

        expense_doc.notes = self.get_only_nil_values(expense_doc.notes,['notes'])

        # Add attachements here
        if self.get_values(['attachments']) and len(self.get_values(['attachments'])):
            for attachement in self.get_values(['attachments']):
                expense_doc.append("attachments", {
					"attachment_url":attachement,
				})

        expense_doc.payment_status = self.get_only_nil_values(expense_doc.payment_status,['payment_status'])
        expense_doc.boya_status = self.get_only_nil_values(expense_doc.boya_status,['status'])

        # Add reviews here
        reviews = self.get_values(['reviews'])
        if reviews and len(reviews):
            for review in reviews:
                expense_doc.append("reviews", {
					"person": review['person'],
                    "reviewed_on": review['reviewed_on'],
                    "notes": review['notes'],
                    "status": review['status']
				})

        expense_doc.exported = self.get_only_nil_values(expense_doc.exported,['exported'])
        expense_doc.sync_successful = self.get_only_nil_values(expense_doc.sync_successful,['sync_successful'])
        # new_expense_doc.external_sync_id = self.expense_details['external_sync_id']
        # new_expense_doc.sync_error = self.expense_details['sync_error']
        expense_doc.vendor = self.get_only_nil_values(expense_doc.vendor,['vendor'])

        # Add complete request data log here
        # new_expense_doc.complete_request_data = str(self.expense_details)

        # add project abbreviations
        sub_category_code = self.get_only_nil_values(expense_doc.code,['subcategory','code'])
        project_abbreviation = None
        if sub_category_code:
            try:
                project_abbreviation = sub_category_code[:-7]
            except:
                pass
        if not expense_doc.project_abbreviation:
            expense_doc.project_abbreviation = project_abbreviation
        
        # save new expense
        expense_doc.save()
        frappe.db.commit()

        # set class expense_doc
        if not self.expense_doc:
            self.expense_doc = expense_doc

        return { 'status': True }

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
        
        # Get Boya Settings details
        sebco_settings = frappe.get_single('Sebco Settings')
        boya_account = sebco_settings.boya_expense_account
        default_cost_center = sebco_settings.default_cost_center
        default_company = sebco_settings.default_company
        related_party_accounts = sebco_settings.boya_expense_company_account

        # company and cost center of project owner
        associated_company, associated_cost_center,project_name, self.defined_project = None, None, None, None 
        # get project associated with expense
        project_list = frappe.get_list('Project', fields=['name','company','cost_center'], filters={
            'project_abbreviation': self.expense_doc.project_abbreviation
        })

        if len(project_list):
            # get company associated with project
            associated_company = project_list[0]['company']
            associated_cost_center = project_list[0]['cost_center'] 
            project_name = project_list[0]['name']

            # check all the required values are defined
            if not associated_company:
                # add a error log to boya expense
                self.expense_doc.append('activity_logs_table',
                    {
                        'activity': 'Creating Journal Entry',
                        'status': 'Failed',
                        'description': 'The associated company in related project is not defined'
                    }
                )
                self.expense_doc.status = 'Failed'
                self.expense_doc.save()
                frappe.db.commit()
            
            if not associated_cost_center:
                # add a error log to boya expense
                self.expense_doc.append('activity_logs_table',
                    {
                        'activity': 'Creating Journal Entry',
                        'status': 'Failed',
                        'description': 'The associated cost center in related project is not defined'
                    }
                )
                self.expense_doc.status = 'Failed'
                self.expense_doc.save()
                frappe.db.commit()

            if not project_name:
                # add a error log to boya expense
                self.expense_doc.append('activity_logs_table',
                    {
                        'activity': 'Creating Journal Entry',
                        'status': 'Failed',
                        'description': 'The associated project_name in related project is not defined'
                    }
                )
                self.expense_doc.status = 'Failed'
                self.expense_doc.save()
                frappe.db.commit()

            if not associated_company or not associated_cost_center:
                # define project as part of self
                self.defined_project = project_name
                # create one journal entry within the main company in sebco settings
                self.create_journal_with_default_settings(default_company,boya_account,default_cost_center)
                return
        else:
            # create one journal entry within the main company in sebco settings
            self.create_journal_with_default_settings(default_company,boya_account,default_cost_center)
            return
    
        # At this point the project, company and cost centers are defined
        filtered_list = list(filter(lambda x: x.company == associated_company, related_party_accounts))
        company_related_party_acc = None
        if len(filtered_list):
            company_related_party_acc = filtered_list[0].expense_account
            related_party_within_company = filtered_list[0].related_party_account__within_company
        else:
            # define project as part of self
            self.defined_project = project_name
            # create one journal entry within the main company in sebco settings
            self.create_journal_with_default_settings(default_company,boya_account,default_cost_center)
            return
        
        # define supplier expense account here or return
        if not self.define_supplier_expense_acc(): 
            doc_status = "Failed",
            activity = "Getting supplier expense account"
            status = "Failed"
            description = "The supplier expense account is not defined"
            self.add_error_logs(doc_status,activity,status,description)
            return
        
        # get supplier account name in default company
        supplier_acc_details = self.get_account_name(self.supplier_expense_acc_no, default_company)
        if not supplier_acc_details['status']:
            doc_status = "Failed",
            activity = "Getting supplier account name"
            status = "Failed"
            description = "The supplier account name is not defined"
            self.add_error_logs(doc_status,activity,status,description)
            return

        supplier_acc_name = supplier_acc_details['account_name']
        amount = self.expense_doc.charge
        if associated_company  == default_company:
            # create journal entry with default setting and add correct project
            self.create_actual_journal_entry(amount,default_company,supplier_acc_name,boya_account,default_cost_center,'Bank Entry',project_name)
            return
        
        # At this point any expense that gets here need have two journal entries one to cather 
        # for double entry within the company of the project and another to cater for related 
        # related_party_accounts i.e session blue paying for another company

        # get supplier account name in host company
        supplier_acc_details = self.get_account_name(self.supplier_expense_acc_no, associated_company)
        if not supplier_acc_details['status']:
            doc_status = "Failed",
            activity = "Getting supplier account name"
            status = "Failed"
            description = "The supplier account name is not defined"
            self.add_error_logs(doc_status,activity,status,description)
            return
        supplier_acc_name = supplier_acc_details['account_name']

        # first entry in the default company
        self.create_actual_journal_entry(amount,default_company,company_related_party_acc,boya_account,default_cost_center,'Inter Company Journal Entry',project_name)

        # create the second entry within the host company (company whose payment are being made)
        self.create_actual_journal_entry(amount,associated_company,supplier_acc_name,related_party_within_company,associated_cost_center,'Inter Company Journal Entry',project_name)
        
    def notification_received(self):
        '''
        Method that sends a callback notification back to Boya that the 
        notification was recieved successfully
        '''
        pass

    def define_supplier_expense_acc(self):
        '''
        Method used to define the correct supplier expense account
        '''
        try:
            # Sebco accounts from are given in the following format
            # <Project Identifiers - varying number of letters><seven digits - actual account number>
            if self.expense_doc.code:
                supplier_expense_acc_no = self.expense_doc.code
            else:
                supplier_expense_acc_no = self.expense_details['subcategory']['code']

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
                return False
            
            self.supplier_expense_acc_no = supplier_expense_acc_no[:4] + '/' + supplier_expense_acc_no[4:]
            return True
        except:
            return False

    def create_actual_journal_entry(self,amount,company,debit_acc,credit_acc,cost_center,entry_type,project=None):
        '''
        Method that creates and save jounal entry based on given parameters
        '''
        try:
            # Create a new journal entry
            new_journal_entry = frappe.new_doc('Journal Entry')
            new_journal_entry.voucher_type = entry_type
            new_journal_entry.company = company

            # Ensure that the posting transaction_date is defined
            transaction_date = self.expense_details['transaction_date'].split('T')[0]
            if not transaction_date:
                self.expense_doc.append('activity_logs_table',
                    {
                        'activity': 'Creating journal entry',
                        'status': 'Failed',
                        'description': 'The transaction date is not defined'
                    }
                )
                self.expense_doc.status = 'Faiuled'
                self.expense_doc.save()
                frappe.db.commit()
                return
            
            new_journal_entry.posting_date = transaction_date
            new_journal_entry.cheque_no = self.expense_details['provider_ref'],
            new_journal_entry.cheque_date = transaction_date
            new_journal_entry.bill_no = self.expense_details['transaction_ref']

            # Do one journal entry affecting the the main company only
            new_journal_entry.append('accounts', {
                'account': debit_acc,
                'debit_in_account_currency': amount,
                'credit_in_account_currency': 0.0,
                'cost_center': cost_center,
                'project': project
            })
            new_journal_entry.append('accounts', {
                'account': credit_acc,
                'debit_in_account_currency': 0.0,
                'credit_in_account_currency': amount,
                'cost_center': cost_center,
                'project': project
            })

            # add description
            new_journal_entry.user_remark = self.expense_details['notes']
            
            # Add all the required details for the journal entry
            new_journal_entry.save()

            # submit the journal entry
            new_journal_entry.submit()

            self.expense_doc.append('activity_logs_table',
                {
                    'activity': 'Creating journal entry',
                    'status': 'Successful',
                    'description': 'Journal entry created successfully'
                }
            )
            self.expense_doc.status = 'Complete'
            self.expense_doc.linked_journal_entry = new_journal_entry.name
            self.expense_doc.save()
            frappe.db.commit()

            return True
        except Exception as err:
            # one of the failures gotten from this is when the budget is exceeded we should add functionality to take care of this or instead do not stop actual transaction but rather on material request. Use just a warning instead
            self.expense_doc.append('activity_logs_table',
                {
                    'activity': 'Creating journal entry',
                    'status': 'Failed',
                    'description': 'An error occured while creating Journal entry: check the following details: accounts, budget amount'
                }
            )
            self.expense_doc.status = 'Failed'
            self.expense_doc.save()
            frappe.db.commit()

            # Abort transaction
            self.abort_transaction = True
            return False

    def get_account_name(self,account_number, company):
        '''
        Get the correct account name based on the account number and the company
        '''
        account_list = frappe.get_list('Account', 
            fields=['name'], filters={
            'account_number': account_number,
            'company': company,
        })

        if not len(account_list):
            # add a error log to boya expense
            self.expense_doc.append('activity_logs_table',
                {
                    'activity': 'Getting Expense Account',
                    'status': 'Failed',
                    'description': 'The account number: {} does not exist.'.format(account_number)
                }
            )
            self.expense_doc.status = 'Failed'
            self.expense_doc.save()
            frappe.db.commit()

            # Abort transaction
            self.abort_transaction = True
            return {'status': False}

        supplier_expense_acc_name = account_list[0]['name']
        return {'status': True, 'account_name': supplier_expense_acc_name}

    def create_journal_with_default_settings(self,default_company,boya_account,default_cost_center):
        '''
        Method that runs the creation of journal entry using the default settings i.e
        session blue settings
        '''
        # define supplier expense account here or return
        if not self.define_supplier_expense_acc(): 
            doc_status = "Failed",
            activity = "Getting supplier expense account"
            status = "Failed"
            description = "The supplier expense account is not defined"
            self.add_error_logs(doc_status,activity,status,description)
            return

        # get supplier account name
        supplier_acc_details = self.get_account_name(self.supplier_expense_acc_no, default_company)
        if not supplier_acc_details['status']:
            doc_status = "Failed",
            activity = "Getting supplier account details"
            status = "Failed"
            description = "The supplier account details are not defined"
            self.add_error_logs(doc_status,activity,status,description)
            return
    
        # the project is not defined hence place the expense under main company 
        amount = self.expense_details['charge']
        debit_acc = supplier_acc_details['account_name']
        # create one journal entry
        creation_status = self.create_actual_journal_entry(amount,default_company,debit_acc,boya_account,default_cost_center,'Bank Entry',self.defined_project)

    def get_values(self,keys):
        # define current_dict as expense details from Boya API
        current_dict = self.expense_details

        # Traverse through each key in the list
        for key in keys:
            try:
                if key in current_dict:
                    current_dict = current_dict[key]
                else:
                    return ''  
            except:
                return ''
                    
        return current_dict

    def get_only_nil_values(self,current_value,keys):
        '''
        Method that will retunr the current values of the field in the doc or get its values from request
        if its values if nil
        '''
        if current_value:
            return current_value
        else:
            return self.get_values(keys)
    
    def add_error_logs(self,document_status,activity,status,description):
        '''
        Method that is used to add logs to the expense docuemnt
        '''
        # add a error log to boya expense
        self.expense_doc.append('activity_logs_table',
            {
                'activity': activity,
                'status': status,
                'description': description
            }
        )
        self.expense_doc.status = "Failed"
        self.expense_doc.save()
        frappe.db.commit()
    
@frappe.whitelist()
def retry_processing(filters=None):
    '''
    Method that is used to retry the processing of a Boya expenses already in the database
    '''
    filters = json.loads(filters)
    doc_name, doc = filters['name'], None
    try:
        doc = frappe.get_doc('Boya Expense', doc_name)
    except:
        pass

    # Check if the document is defined
    if not doc:
        return { 'status': False, 'error': 'Failed to retry document processing. Pleas try again' }
    
    # Check if the expense details are defined
    if not doc.complete_request_data_json or doc.complete_request_data_json == '':
        error = 'Boya expense is blank, please contact support for assistance'
        return { 'status': False, 'error': error }
    
    # get request details from kwargs
    expense_details = json.loads(doc.complete_request_data_json)
    boya_payment = BoyaPayments(expense_details)
    boya_payment.expense_doc = doc
    process_details = boya_payment.retry_process_expense_notification()
    try:
        if not process_details['status']:
            return  { 'status': process_details['status'],
             'error': process_details['error'] }
    except:
        return  { 'status': False,
             'error': 'Error occured while retrying transaction check the details and try again'}
    
    # If everything works return success message
    return  { 'status': True, 'message': 'Successfully retried transaction' }





    
