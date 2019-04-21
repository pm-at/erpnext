# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _

def execute(filters=None):
	columns = get_columns()
	data = get_data()
	return columns, data

def get_columns():
	columns = [
		{
			"label": _("Material Request Date"),
			"fieldname": "material_request_date",
			"fieldtype": "Date",
			"width": 140
		},
		{
			"label": _("Cost Center"),
			"options": "Cost Center",
			"fieldname": "cost_center",
			"fieldtype": "Link",
			"width": 140
		},
		{
			"label": _("Project"),
			"options": "Project",
			"fieldname": "project",
			"fieldtype": "Link",
			"width": 140
		},
		{
			"label": _("Requesting Site"),
			"options": "Warehouse",
			"fieldname": "requesting_site",
			"fieldtype": "Link",
			"width": 140
		},
		{
			"label": _("Requestor"),
			"options": "Employee",
			"fieldname": "requestor",
			"fieldtype": "Link",
			"width": 140
		},
		{
			"label": _("Material Request No"),
			"options": "Material Request",
			"fieldname": "material_request_no",
			"fieldtype": "Link",
			"width": 140
		},
		{
			"label": _("Budget Code"),
			"options": "Budget",
			"fieldname": "budget_code",
			"fieldtype": "Link",
			"width": 140
		},
		{
			"label": _("Description"),
			"fieldname": "description",
			"fieldtype": "Data",
			"width": 200
		},
		{
			"label": _("Quantity"),
			"fieldname": "quantity",
			"fieldtype": "Int",
			"width": 140
		},
		{
			"label": _("Unit of Measure"),
			"options": "UOM",
			"fieldname": "unit_of_measurement",
			"fieldtype": "Link",
			"width": 140
		},
		{
			"label": _("Status"),
			"fieldname": "status",
			"fieldtype": "data",
			"width": 140
		},
		{
			"label": _("Purchase Order Date"),
			"fieldname": "purchase_order_date",
			"fieldtype": "Date",
			"width": 140
		},
		{
			"label": _("Purchase Order"),
			"options": "Purchase Order",
			"fieldname": "purchase_order",
			"fieldtype": "Link",
			"width": 140
		},
		{
			"label": _("Supplier"),
			"options": "Supplier",
			"fieldname": "supplier",
			"fieldtype": "Link",
			"width": 140
		},
		{
			"label": _("Estimated Cost"),
			"fieldname": "estimated_cost",
			"fieldtype": "Float",
			"width": 140
		},
		{
			"label": _("Actual Cost"),
			"fieldname": "actual_cost",
			"fieldtype": "Float",
			"width": 140
		},
		{
			"label": _("Purchase Order Amount"),
			"fieldname": "purchase_order_amt",
			"fieldtype": "Float",
			"width": 140
		},
		{
			"label": _("Purchase Order Amount(Company Currency)"),
			"fieldname": "purchase_order_amt_usd",
			"fieldtype": "Float",
			"width": 140
		},
		{
			"label": _("Expected Delivery Date"),
			"fieldname": "expected_delivery_date",
			"fieldtype": "Date",
			"width": 140
		},
		{
			"label": _("Actual Delivery Date"),
			"fieldname": "actual_delivery_date",
			"fieldtype": "Date",
			"width": 140
		},
	]
	return columns

def get_data():
	purchase_order_entry = frappe.db.sql("""
		SELECT
			po_item.name,
			po_item.parent,
			po_item.cost_center,
			po_item.project,
			po_item.warehouse,
			po_item.material_request,
			po_item.material_request_item,
			po_item.description,
			po_item.stock_uom,
			po_item.qty,
			po_item.amount,
			po_item.base_amount,
			po_item.schedule_date,
			po.transaction_date,
			po.supplier,
			po.status,
			po.owner
		FROM `tabPurchase Order` po, `tabPurchase Order Item` po_item
		WHERE
			po.docstatus = 1
			AND po.name = po_item.parent
			AND po.status not in  ("Closed","Completed","Cancelled")
		GROUP BY
			po.name,po_item.item_code
		""", as_dict=1)

	mr_details = frappe.db.sql("""
		SELECT
			mr.transaction_date,
			mr_item.name,
			mr_item.parent,
			mr_item.amount
		FROM `tabMaterial Request` mr, `tabMaterial Request Item` mr_item
		WHERE
			per_ordered > 0
			AND mr.name = mr_item.parent
			AND mr.docstatus = 1
		""", as_dict=1)

	pi_records = frappe._dict(frappe.db.sql("""
		SELECT
			po_detail,
			base_amount
		FROM `tabPurchase Invoice Item`
		WHERE
			docstatus=1
			AND po_detail IS NOT NULL
		"""))

	pr_records = frappe._dict(frappe.db.sql("""
		SELECT
			pr_item.purchase_order_item,
			pr.posting_date
		FROM `tabPurchase Receipt` pr, `tabPurchase Receipt Item` pr_item
		WHERE
			pr.docstatus=1
			AND pr.name=pr_item.parent
			AND pr_item.purchase_order_item IS NOT NULL
		"""))


	mr_records = {}
	for record in mr_details:
		mr_records.setdefault(record.name, []).append(frappe._dict(record))

	procurement_record=[]
	for po in purchase_order_entry:
		# fetch material records linked to the purchase order item
		mr_record = mr_records.get(po.material_request_item, [{}])[0]

		procurement_detail = {
			"material_request_date": mr_record.get('transaction_date', ''),
			"cost_center": po.cost_center,
			"project": po.project,
			"requesting_site": po.warehouse,
			"requestor": po.owner,
			"material_request_no": po.material_request,
			"description": po.description,
			"quantity": po.qty,
			"unit_of_measurement": po.stock_uom,
			"status": po.status,
			"purchase_order_date": po.transaction_date,
			"purchase_order": po.parent,
			"supplier": po.supplier,
			"estimated_cost": mr_record.get('amount'),
			"actual_cost": pi_records.get(po.name, ''),
			"purchase_order_amt": po.amount,
			"purchase_order_amt_in_company_currency": po.base_amount,
			"expected_delivery_date": po.schedule_date,
			"actual_delivery_date": pr_records.get(po.name, {})
		}
		procurement_record.append(procurement_detail)
	return procurement_record