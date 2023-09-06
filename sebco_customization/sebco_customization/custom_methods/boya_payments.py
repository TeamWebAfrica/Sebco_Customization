import frappe

class BoyaPayments:
    '''
    Class that handles all things related to the Boya expense doctype functionality
    '''
    def __init__(self, expense_details):
        self.expense_details = expense_details

    def process_expense_notification(self):
        '''
        This is the main methods that calls all the other class methods to handle an
        expense notification from Boya
        '''
        self.get_or_create_boya_expense()

    def get_or_create_boya_expense(self):
        '''
        Method that checks if the given Boya expense already exists 
        in the database and if not creates one
        '''
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
        new_expense_doc.subcategory = self.expense_details['subcategory']

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
        # Create a new journal entry
        new_journal_entry = frappe.new_doc('Journal Entry')
        
        #Add all the required details for the journal entry

    def notification_received(self):
        '''
        Method that sends a callback notification back to Boya that the 
        notification was recieved successfully
        '''
        pass
