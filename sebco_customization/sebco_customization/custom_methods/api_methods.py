import frappe

@frappe.whitelist(allow_guest=True)
def boya_payments_api(*args, **kwargs):
    print('Boya payment recieved .......................................')
   
    # get request details from kwargs
    print(kwargs)
    