// Copyright (c) 2024, Kipngetich Ngeno and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Weekly Casual Wages Report"] = {
	"filters": [
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"reqd": 1,
			"default": frappe.datetime.add_days(frappe.datetime.get_today(), -6)
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"reqd": 1,
			"default": frappe.datetime.get_today()
		},
		{
			"fieldname": "project",
			"label": __("Project"),
			"fieldtype": "Link",
			"options": "Project",
			"reqd": 0
		},
		{
			"fieldname": "casual_worker_name",
			"label": __("Casual Worker"),
			"fieldtype": "Link",
			"options": "Casual Worker",
			"reqd": 0
		},
		{
			"fieldname": "based_on",
			"label": __("Based On"),
			"fieldtype": "Select",
			"options": ["Casual Worker", "Project"],
			"default": "Casual Worker"
		}
	],
	
	// Reload button to refresh report
	onload: function(report) {
		report.page.add_inner_button(__("Reload Report"), function() {
			report.refresh();
		});
	},

	// Summary to show total wage for easy viewing
	get_report_summary: function(report) {
		let total = 0;
		report.data.forEach(row => {
			if (row.cumulative_total_wage) {
				total += row.cumulative_total_wage;
			}
		});
		return [
			{
				label: __("Total Wage (KES)"),
				value: total,
				indicator: 'Green'
			}
		];
	}
};
