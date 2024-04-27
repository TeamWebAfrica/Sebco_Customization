// Copyright (c) 2023, Kipngetich Ngeno and contributors
// For license information, please see license.txt

frappe.ui.form.on('Boya Expense', {
	refresh: function(frm) {

		// Add more action buttons
		frm.add_custom_button(__('Retry Processing'), function(){
			frappe.call({
				method: "sebco_customization.sebco_customization.custom_methods.boya_payments.retry_processing",
				args: 	{
						doctype: "Boya Expense",
						filters: {
							name: frm.doc.name
						},
				fields:["name"]
				},
				callback: function(response) {	
					// check if the status is successful else throw error
					if(!response.message.status){
						frappe.throw(response.message.error)
					}else{
						frappe.msgprint(response.message.message);
					}
				}
			})

		}, __("More Actions"));

	}
});
