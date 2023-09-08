import frappe
from sebco_customization.sebco_customization.custom_methods.boya_payments import BoyaPayments

frappe.utils.logger.set_log_level("DEBUG")
logger = frappe.logger("boya_webhook", allow_site=True, file_count=50)

@frappe.whitelist(allow_guest=True)
def boya_payments_api(*args, **kwargs):
    logger.info('==========================================================================================================================')
    logger.info(f"Boya Webhook Request: \n args: {args} , \n kwargs: {kwargs}")
    # hardcode user to administrator
    frappe.session.user = 'Administrator'
   
    # get request details from kwargs
    boya_payment = BoyaPayments(kwargs)
    boya_payment.process_expense_notification()

