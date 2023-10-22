// Copyright (c) 2023, Kipngetich Ngeno and contributors
// For license information, please see license.txt

frappe.ui.form.on('Sebco Settings', {
	refresh: function(frm) {

		// filter accounts to show non group accounts
		cur_frm.set_query("expense_account", "boya_expense_company_account", function(doc, cdt, cdn) {
			let row = locals[cdt][cdn]
			return {
				filters: {
					is_group: 0,
					// company: row.company
				}
			};
		});

		// filter accounts to show non group accounts
		cur_frm.set_query("bank_charges_account", "boya_expense_company_account", function(doc, cdt, cdn) {
			let row = locals[cdt][cdn]
			return {
				filters: {
					is_group: 0,
					// company: row.company
				}
			};
		});

		// filter main expense accout
		cur_frm.set_query("boya_expense_account", function() {
			return {
				"filters": {
					is_group: 0,
				}
			}
		});

		// filter main bank charges account
		cur_frm.set_query("bank_charges", function() {
			return {
				"filters": {
					is_group: 0,
				}
			}
		});

	}
});
