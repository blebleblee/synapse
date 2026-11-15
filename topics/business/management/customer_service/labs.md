# Operational Verification Labs: Customer Service

## Objective & Operational Lab Setup

This lab sequence develops the analytical and operational skills a customer service manager needs to diagnose performance, model trade-offs, and design recovery protocols that hold under real-world pressure. The three exercises move from baseline audit construction through parameter sensitivity analysis to stress-test simulation and failure recovery. Each exercise uses tools native to business operations: spreadsheet models, structured interview rubrics, statistical significance testing, and cohort-based retention analysis. No exercise is conceptual alone. Every one produces a working artifact you can apply to a live service operation.

Customer service is frequently treated as a cost center to be minimized rather than a revenue-protection and expansion mechanism. That framing is expensive. Net Revenue Retention, the metric that determines whether a SaaS or subscription business compounds or decays, is as much a function of service execution as of product quality. A customer who receives a resolution in one contact on the first attempt churns at a materially lower rate than one who escalates or re-contacts. The labs here are designed to make that causal chain measurable and actionable.

**Analytical Environment Setup**

You need a spreadsheet application capable of array formulas and pivot analysis (Microsoft Excel or Google Sheets both work), a dataset of at least 90 days of resolved service tickets (a minimum of 500 records is statistically sufficient for the significance tests in Exercise 2), and access to your CRM or helpdesk export (Zendesk, Salesforce Service Cloud, Freshdesk, or equivalent). If you are running this lab in a training context without live data, the synthetic dataset specification at the end of this section produces a fully valid substitute.

Each ticket record must carry the following fields before you begin: `ticket_id`, `open_timestamp`, `close_timestamp`, `channel` (phone / email / chat / self-service), `agent_id`, `contact_reason_tier1` (billing / technical / account / fulfillment / policy), `contact_reason_tier2` (sub-category), `resolution_status` (resolved / escalated / abandoned), `csat_score` (1–5 integer, nullable), `first_contact_resolution` (boolean), `handle_time_seconds`, `customer_segment` (enterprise / mid-market / SMB / consumer), `customer_tenure_months`, and
