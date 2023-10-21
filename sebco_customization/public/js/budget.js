frappe.ui.form.on('Budget Account', {
    budget_amount: function(frm, cdt, cdn) {
        // When total budget in accounts is updated, recalculate total budget amount
        calculateTotalBudget(frm);
    }
});

function calculateTotalBudget(frm) {
    var total_budget = 0;
    frm.doc.accounts.forEach(function(row) {
        total_budget += (row.budget_amount || 0);
    });
    frm.set_value('total_budget', total_budget);
    frm.set_value('total_budget2', total_budget);
}
