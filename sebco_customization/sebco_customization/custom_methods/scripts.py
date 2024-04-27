import frappe, ast,json

def add_str_to_json_in_boya_expense(status):
    '''
    Function that gets data that is currently in string formats in the complete_request_data and adds it to the 
    complete_request_data_json field as json data
    '''
    list_of_expenses = frappe.get_list("Boya Expense",
        fields=["name"],
        filters = { 'status': status},
    )

    for expense in list_of_expenses:
        try:
            print("{}....................................................".format(expense['name']))
            expense_doc = frappe.get_doc("Boya Expense", expense['name'])
            str_data = expense_doc.complete_request_data
            converted_str_data = str_data.replace("'",'"')
            dictionary_data = ast.literal_eval(converted_str_data)
            expense_doc.complete_request_data_json = dictionary_data
            expense_doc.save()
            frappe.db.commit()
            print('End......................................................')
        except:
            print("An error occurred")

