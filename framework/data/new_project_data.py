from pathlib import Path

# Build paths from this file's location (framework/data) so they work from any working directory.
framework_dir = Path(__file__).resolve().parent.parent
file_path_t3 = framework_dir / 'test_attachment' / 't3_spec.docx'
file_path_comp_1 = framework_dir / 'test_attachment' / 'comp_1.xlsx'
requirement_overview = {
    'project_title':'NPR Smoke Test 02',
    'Please provide a summary of the project':'Test Project Summary',
    'Which Directorate / Department does this relate to?':'Test Department',
    'Which service within the Directorate / Department does this requirement relate to?':'Test Service',
    'Category':'Construction, Design and Engineering',
    'Subcategory':'Costing and Estimation Services'
}
project_details_data = {
    'publication_date':'01/12/2026 04:30 AM',
    'clarification_deadline':'02/12/2026 04:30 AM',
    'submission_deadline':'03/12/2026 04:30 AM',
    'project_start_date':'04/12/2026 04:30 AM',
    'project_end_date':'05/12/2026 04:30 AM',
    'covid_19':'No',
    'itt_approval':'No',
    'cost_of_project':'500000.25',
    'budget_code':'Test Budget Code',
    'sub_code':'Test Sub Code',
    't3_specification_path':file_path_t3

}
compliance_test_data = {
    'file_path':file_path_comp_1
}

select_framework = {
    'framework':'NEPRO 3'
}

# Expected values on the Summary page (Summary labels differ from the form question text).
# They match the answers given by fill_project_stakeholder() and fill_procurement_route().
project_stakeholders_summary = {
    'Requirement Owner Name':'Sawan - Project Owner Test',   # label was 'Owner Name' before the 08-10-2026 app update
    'Additional Stakeholders':['Sawan - Additional Stakeholder 01 Test (sawan.hukm+ash01@bloom.services)'],
    'Project Approval Required':'Yes',
    'Project Pre Approval':'No',
    'Approver Name':'Sawan - Project Approver Test',
    'Payment Approver Name':'Sawan - Budget Approver Test'
}
procurement_route_summary = {
    'Preferred Procurement Process':'Mini Competition',
    'Number Of Suppliers':'3',
    'Specific Suppliers':'Yes',
    'Company Name':['Bloom Test Supplier 01'],
    'Supplier Shortlist Approval Required':'Yes',
    'Region':['Belfast'],
    'Technical Accreditation':'Test Technical Accreditations',
    'Size of Supplier':['Medium'],
    'Security (inc data security)':['Cloud Security Alliances Cloud Controls Matrix (CCM)'],
    'Security Clearance':['Baseline Personnel Security Standard (BPSS)'],
    'Industry Standards':['BES6001'],
    'DBS':['Standard']
}

# Matches the answers given by fill_complaince_milestone(); attachments and the insurance summary are built in the test.
compliance_summary = {
    'Insurance Levels Apply':'No',
    'Public Liability':'£10.25',
    'Professional Indemnity':'£11.25',
    'Employer Liability':'£12.25',
    'Other Insurance Required':'Yes',
    'Other Insurance Details':'Test Other Insurance',
    'Special Clause Required':'Yes',
    'Outside IR35':'Yes',
    'Social Value Standards':'Yes',
    'Social Value Details':'Test Social Value',
    'Nda Required':'Yes',
    'Nda Successful Supplier':'No',
    'Collateral Warranty Required':'No',
    'Commercial Model':'Milestones',
    'Payment Schedule':'Milestones',
    'Accept Expenses':'No',
    'Best And Final Offer':'No',
    'External Funding':'No',
    'Share Budget':'Yes - show budget',
    'Commercial Evaluator':'Bloom',
    'Preferred Evaluation Methodology':'Price & Quality (MEAT)',
    'Supplier resumes required':'No',
    'Incumbent provider available':'No',
    'Case study consent':'No'
}

submit_request_data = {
    # Each submission test creates its own draft: '<prefix> <ddmmyyyyHHMMSS>'
    'project_title_prefix':'Automation NPR Approval',
    'success_message':'Submission completed and elevate project created successfully.',
    # Project Approval Required = Yes (fill_project_stakeholder) -> the request waits for the buyer approver.
    'status_after_submit':'Buyer Approver'
}

project_detail_draft = {
    'current_status':'In Draft',
    'milestone':'New Project Draft',
    'task_name':'Submit Project Request',
    'task_status':'On Hold'
}