import frappe, requests 
from boya_integration.boya_integration.custom_methods.boya_payments import BoyaPayments

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

def pull_and_reconcile_payments():
    base_url = "https://api.boyahq.com/v1"
    uri = "/expenses?fromdate=2024-11-01&limit=50&page=1&todate=2024-11-03"
    url = base_url + uri
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "x-api-key": "5MnuowJTqo2BXscBx1hpkbEq8gjbj1A2m8wsN1ob"
    }

    response = requests.get(url,headers=headers)
    return response

