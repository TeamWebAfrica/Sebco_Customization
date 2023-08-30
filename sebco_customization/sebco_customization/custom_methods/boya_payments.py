import frappe

class BoyaPayments:
    '''
    Class that handles all things related to the Boya expense doctype functionality
    '''

    def __init__(self,transaction_id):
        self.transaction_id = transaction_id

    def get_or_create_boya_expense(self,transaction_id):
        '''
        Method that checks if the given Boya expense already exists 
        in the database and if not creates one
        '''
        boya_expense_doc = frappe.get_doc('BoyaExpense',transaction_id)

        # return if the boya expense record is not found
        if not boya_expense_doc:
            return
        
    def notification_received(self):
        '''
        Method that sends a callback notification back to Boya that the 
        notification was recieved successfully
        '''
        pass

