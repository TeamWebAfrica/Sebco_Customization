# Copyright (c) 2024, Kipngetich Ngeno and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import getdate, add_days

def execute(filters=None):
    if not filters:
        filters = {}

    # Retrieve filter values
    from_date = getdate(filters.get('from_date'))
    to_date = getdate(filters.get('to_date'))
    project = filters.get('project', None)
    casual_worker_name = filters.get('casual_worker_name', None)
    based_on = filters.get('based_on', 'Casual Worker')  # Default to "Casual Worker"

    # Calculate the number of days between from_date and to_date, inclusive
    date_diff = (to_date - from_date).days + 1

    # Generate columns based on "based_on" filter and exact dates within the range
    columns = get_columns(from_date, date_diff, based_on)

    # SQL dynamic grouping based on "based_on" filter
    group_by_clause = "clw.project, clw.project_name" if based_on == "Project" else "cld.casual_worker_name, clw.project, clw.project_name"

    # SQL conditions for each day in date range, using the exact date for each column
    date_conditions = ', '.join([
        f"SUM(CASE WHEN DATE(clw.date) = DATE_ADD(%(from_date)s, INTERVAL {i} DAY) THEN cld.total_wage ELSE 0 END) AS day_{i + 1}"
        for i in range(date_diff)
    ])

    # Define cumulative wage condition
    cumulative_condition = "SUM(cld.total_wage) AS cumulative_total_wage"

    # Execute the query to fetch data
    data = frappe.db.sql(f"""
        SELECT 
            { 'clw.project,' if based_on == 'Project' else 'cld.casual_worker_name, clw.project,' }
            clw.project_name,
            {date_conditions},
            {cumulative_condition}
        FROM
            `tabCasual Labour Wages` AS clw
        JOIN
            `tabCasual Labour Details` AS cld ON clw.name = cld.parent
        WHERE
            clw.date BETWEEN %(from_date)s AND %(to_date)s
            AND (%(project)s IS NULL OR clw.project = %(project)s)
            AND (%(casual_worker_name)s IS NULL OR cld.casual_worker_name = %(casual_worker_name)s)
        GROUP BY
            {group_by_clause}
    """, {'from_date': from_date, 'to_date': to_date, 'project': project, 'casual_worker_name': casual_worker_name}, as_dict=True)

    return columns, data

def get_columns(from_date, date_diff, based_on):
    columns = []
    if based_on == 'Project':
        columns.extend([
            {
                "label": "<b>" + _("Project") + "</b>",
                "fieldname": "project",
                "fieldtype": "Data",
                "width": 100
            },
            {
                "label": "<b>" + _("Project Name") + "</b>",
                "fieldname": "project_name",
                "fieldtype": "Data",
                "width": 200
            }
        ])
    else:
        columns.extend([
            {
                "label": "<b>" + _("Casual Worker") + "</b>",
                "fieldname": "casual_worker_name",
                "fieldtype": "Data",
                "width": 150
            },
            {
                "label": "<b>" + _("Project") + "</b>",
                "fieldname": "project",
                "fieldtype": "Data",
                "width": 100
            },
            {
                "label": "<b>" + _("Project Name") + "</b>",
                "fieldname": "project_name",
                "fieldtype": "Data",
                "width": 200
            }
        ])

    # Add columns for each day in the date range with the exact date in "day month year" format
    for day in range(date_diff):
        day_date = add_days(from_date, day)
        formatted_date = day_date.strftime('%d-%m-%Y')
        columns.append({
            "label": f"<b>{formatted_date}</b>",
            "fieldname": f"day_{day + 1}",
            "fieldtype": "Currency",
            "width": 150
        })

    # Append a column for the total wage
    columns.append({
        "label": "<b>" + _("Total Wage (KES)") + "</b>",
        "fieldname": "cumulative_total_wage",
        "fieldtype": "Currency",
        "width": 150
    })

    return columns
