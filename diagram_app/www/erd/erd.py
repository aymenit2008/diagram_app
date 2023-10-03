import frappe
import frappe.utils
from frappe import _
from frappe.query_builder import Order
from frappe.query_builder.custom import ConstantColumn
from pypika import functions as fn
from pypika import CustomFunction


@frappe.whitelist(allow_guest=True)
def get_erd(doc_type, doc_name, status):
    frappe.msgprint("doc_type: " + doc_type + " doc_name: " + doc_name)
    if doc_type == "Workflow":
        return get_workflow(doc_name, status)
    elif doc_type == "Diagram Doc DA":
        return get_diagram(doc_name)


@frappe.whitelist(allow_guest=True)
def get_doc_name(doc_type):
    list_all = frappe.get_all(doc_type, fields=['name'])
    html_str = " "
    for l in list_all:
        html_str += "<option value='" + l.name + "'>" + l.name + "</option>"
    html_str += ""
    return html_str

@frappe.whitelist(allow_guest=True)
def get_status(doc_name):
    workflow_status = frappe.qb.DocType("Workflow Document State")
    subq = (
        frappe.qb.from_(workflow_status)
        .select(workflow_status.state)
        .where(workflow_status.parent == doc_name)
    )
    query = ( frappe.qb.from_("Workflow State").select("name").where(frappe.qb.Field("name").isin(subq)))
    list_all = query.run(as_dict=True)
    html_str = "<option value=''>all</option>"
    for l in list_all:
        html_str += "<option value='" + l.name + "'>" + l.name + "</option>"
    html_str += ""
    return html_str

def get_workflow_status(doc_name):

    workflow_status = frappe.qb.DocType("Workflow Document State")
    replace = CustomFunction('REPLACE', ['column_name', 'text to find', 'text to replace with'])
    subq = (
        frappe.qb.from_(workflow_status)
        .select(workflow_status.idx,replace(workflow_status.state, ' ', '_').as_('state'))
        .where(workflow_status.parent == doc_name).orderby(workflow_status.idx, order=Order.asc)
    ).run(as_dict=True)
    return subq



def get_workflow(doc_name,status):
    status_list = get_workflow_status(doc_name)
    t_doctype = frappe.qb.DocType("Workflow Transition")
    replace = CustomFunction('REPLACE', ['column_name', 'text to find', 'text to replace with'])
    query = (frappe.qb.from_(t_doctype)
             .select(
        replace(t_doctype.state, ' ', '_').as_('state'), replace(t_doctype.next_state, ' ', '_').as_('next_state'),
        t_doctype.action.as_('action'), t_doctype.allowed.as_('allowed'))
             .where(t_doctype.parent == doc_name).orderby(t_doctype.idx, order=Order.asc))
    if status != "":
        query = query.where(t_doctype.state == status)

    # frappe.msgprint(str(query))
    list_all = query.run(as_dict=True)

    # get unique state and next_state from list_all
    state_list = list(set([dt.state for dt in list_all])) + list(set([dt.next_state for dt in list_all]))
    # frappe.throw(str(state_list))




    a_str = "sequenceDiagram" + "\n"
    for l in status_list:
        # check if state is in list_all
        if l.state in state_list:
            a_str += "participant " + l.state + "\n"

    for l in list_all:
        a_str += l.state + " ->> " + l.next_state + ": " + l.action + " ( " +l.allowed + " )\n"

    return a_str


def get_diagram(doc_name):
    diagram_doc = frappe.get_doc("Diagram Doc DA", doc_name)
    doctype_list = []
    # add doctype to list from child table diagram_doc.diagram_doc_details
    doctype_list = list(set([dt.doc_type for dt in diagram_doc.diagram_doc_details]))
    t_doctype = frappe.qb.DocType("DocField")
    replace = CustomFunction('REPLACE', ['column_name', 'text to find', 'text to replace with'])
    query = (frappe.qb.from_(t_doctype)
             .select(
        replace(t_doctype.parent, ' ', '-').as_('parent'), replace(t_doctype.options, ' ', '-').as_('options'),
        t_doctype.fieldtype.as_('fieldtype'), t_doctype.fieldname.as_('fieldname'), t_doctype.label.as_('label'),
        t_doctype.reqd.as_('reqd'))
             .where(t_doctype.fieldtype.isin(['Link', 'Table'])
                    & t_doctype.parent.isin(doctype_list) & t_doctype.options.isin(doctype_list) & (
                            t_doctype.parent != t_doctype.options)))
    # frappe.msgprint(str(query))
    list_all = query.run(as_dict=True)
    a_str = "erDiagram" + "\n"
    for l in list_all:
        # a_str += l.d_syntics + "\n"
        syn_reqd = "||"
        if not l.reqd:
            syn_reqd = "|o"
        if l.fieldtype == 'Table':
            a_str += l.parent + " " + syn_reqd + "--|{ " + l.options + " : is" + "\n"
        else:
            a_str += l.parent + " }|--" + syn_reqd + " " + l.options + " : is" + "\n"

    for dt in diagram_doc.diagram_doc_details:
        if dt.show_fields:
            a_str += get_doctype_fields(dt)

    return a_str


def get_doctype_fields(doctype):
    fields = frappe.get_meta(doctype.doc_type).fields
    # frappe.msgprint(str(fields))
    # replace space in doctype name with '-'
    doctype_new = doctype.doc_type.replace(' ', '-')
    table_str = doctype_new + "{\n"

    for d in fields:
        if doctype.only_reqd:
            if d.reqd and d.fieldtype not in ["Link", "Table"] and d.label:
                # replace space in field type with '-'
                d.fieldtype = d.fieldtype.replace(' ', '-')
                # put label in double quotes
                a_label = '"' + d.label + '"'
                table_str += d.fieldtype + "  " + d.fieldname + " " + a_label + "\n"
        else:
            if d.fieldtype not in ["Link", "Table"] and d.label:
                # replace space in field type with '-'
                d.fieldtype = d.fieldtype.replace(' ', '-')
                # put label in double quotes
                a_label = '"' + d.label + '"'
                table_str += d.fieldtype + "  " + d.fieldname + " " + a_label + "\n"
    table_str += "}\n"
    return table_str
