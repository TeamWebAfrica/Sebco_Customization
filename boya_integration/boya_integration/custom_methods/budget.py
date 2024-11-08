import frappe

def before_save(doc, method=None):
    '''
    Extend method of the budget doctype that runs before the doctype is saved
    '''
    # Calculate the correct budget total
    correct_total_budget_amounts(doc)

def correct_total_budget_amounts(doc):
    total_budget = 0
    for account in doc.accounts:
        total_budget += account.budget_amount
    
    if total_budget != doc.total_budget2 or total_budget != doc.total_budget:
        doc.total_budget2 = total_budget
        doc.total_budget = total_budget
