import frappe
from sebco_customization.sebco_customization.custom_methods.boya_payments import BoyaPayments

@frappe.whitelist(allow_guest=True)
def boya_payments_api(*args, **kwargs):
    # hardcode user to administrator
    frappe.session.user = 'Administrator'
   
    # get request details from kwargs
    boya_payment = BoyaPayments(kwargs)
    boya_payment.process_expense_notification()

