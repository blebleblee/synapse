# Lesson 2: ERP Core Modules

## 1. First-Principles Intuition & Invariants

The fundamental insight behind SAP's design philosophy is that a modern enterprise is not a collection of independent departments but a single integrated information machine. Every business event — a purchase order raised by procurement, a goods receipt confirmed at a warehouse dock, an invoice matched in accounts payable — is not merely an operational act. It is simultaneously a financial event, a cost allocation event, a demand signal, and a compliance record. SAP's core module architecture was engineered to enforce that unity. When you understand this invariant at the level of mechanism rather than metaphor, you understand why SAP works the way it does and why shortcuts that break integration cause failures that surface far from their origin.

The original R/2 mainframe architecture, and its successor R/3 released in 1992, organized enterprise functions into functional modules that share a common database layer. This was not an obvious design choice at the time. The dominant paradigm of the 1980s was best-of-breed: buy the best accounts payable application, the best inventory system, the best payroll engine, and connect them via batch file transfers. SAP's founders, Hasso Plattner and Dietmar Hopp among others, observed that the latency and inconsistency of batch integration created a class of problems that no amount of tuning could fix. The balance sheet could not reflect the actual state of inventory because the inventory system had not yet posted its nightly batch. The controlling team could not see actuals against budget in real time because the financial accounting close had not yet propagated. SAP's answer was a shared persistent data layer with synchronous posting: when a goods receipt is confirmed in Materials Management, the financial document in Financial Accounting is created in the same database transaction, not in a subsequent batch run. This architectural invariant — the synchronous integration post — is the bedrock on which everything else is built.

This design creates a second invariant that every practitioner must internalize: master data is singular and authoritative. A material master record in SAP is not a procurement record or a warehouse record or an accounting record. It is the single record of a material's identity, and each functional module reads views from that single record. The accounting team reads the accounting view to find the valuation class. The warehouse team reads the warehouse management view to find storage type and bin layout rules. The sales team reads the sales organization view to find the delivering plant and item category group. All these views coexist in one record under one material number. If that number is wrong, every downstream function that depends on it inherits the error simultaneously. This is why master data governance in SAP environments is not an IT housekeeping concern. It is a business control.

The third invariant governs the relationship between Financial Accounting and Controlling. SAP distinguishes between external accounting — the balance sheet and income statement as reported to shareholders, regulators, and tax authorities — and internal accounting, which is the management view of cost and profitability by cost center, profit center, internal order, or product. These two views are related but not identical, and SAP manages their reconciliation through a framework called the reconciliation ledger in older releases and the Universal Journal in S/4HANA. In classic R/3 and ECC, FI posted to general ledger accounts and CO posted to cost objects, and a periodic reconciliation run was required to align them. In S/4HANA, every business transaction writes a single line item in the ACDOCA table that carries both the GL account dimension and the controlling object dimension simultaneously, eliminating the reconciliation step. Understanding which architecture your system is running on determines which reporting tools are valid and which reconciliation procedures are necessary.

## 2. Core Architecture & Mechanics

### Financial Accounting (FI): The Ledger Engine

Financial Accounting in SAP is organized around the company code, which is the smallest legal entity capable of producing a complete set of legally required financial statements. A single SAP client — the highest-level organizational unit, essentially a database partition — can contain dozens of company codes representing subsidiaries across different jurisdictions. Each company code is assigned a chart of accounts, a fiscal year variant, and a currency configuration. The chart of accounts defines the GL account numbers available to all company codes that share it, but each company code maintains its own account determination and posting rules.

The document principle is FI's foundational mechanical rule: every posting in Financial Accounting creates a document with a unique document number within a combination of company code, fiscal year, and document type. Documents are immutable after posting. You cannot delete a posted FI document; you can only reverse it, which creates an equal and opposite document. This immutability is not a limitation but a deliberate audit control. The document header carries the posting date, document date, document type, and reference fields. Each line item carries the GL account, debit or credit indicator, amount in document currency, amount in company code currency, amount in group currency if configured, and a text field for description. In S/4HANA, every line item in every FI document is a row in ACDOCA, the Universal Journal entry table, with additional columns for the profit center, segment, cost center, and functional area that bring the controlling dimension into the same record.

The account determination framework is where FI connects to operational modules. When a goods receipt is posted in MM, SAP does not ask the user which GL account to debit and credit. It executes a rules engine called the Material Ledger / Account Determination, specifically the transaction OBYC configuration, which maps a combination of transaction key (such as BSX for inventory postings, WRX for GR/IR clearing, PRD for price differences) to a GL account based on the valuation class of the material and the chart of accounts. This means the finance team configures the rules once, and every subsequent operational posting uses those rules automatically without requiring human intervention for account coding. The same logic applies in SD via the condition technique and revenue account determination, where a combination of account assignment group on the customer master, account assignment group on the material master, and the chart of accounts maps to a revenue GL account in transaction VKOA.

```
FI Document Structure (Classic ECC)

BKPF (Document Header)
├── BUKRS  Company Code
├── BELNR  Document Number
├── GJAHR  Fiscal Year
├── BLART  Document Type
├── BLDAT  Document Date
├── BUDAT  Posting Date
└── WAERS  Currency Key

BSEG (Document Line Item)
├── BUZEI  Line Item Number
├── HKONT  G/L Account
├── SHKZG  Debit/Credit Indicator
├── DMBTR  Amount in Local Currency
├── WRBTR  Amount in Document Currency
├── KOSTL  Cost Center (CO Integration)
├── AUFNR  Internal Order (CO Integration)
└── PRCTR  Profit Center (EC-PCA Integration)

S/4HANA Universal Journal (ACDOCA - replaces above)
├── RLDNR  Ledger
├── RBUKRS Company Code
├── GJAHR  Fiscal Year
├── BELNR  Accounting Document Number
├── DOCLN  Document Line
├── RACCT  Account Number
├── DRCRK  Debit/Credit Indicator
├── HSL    Amount in Object Currency
├── KSL    Amount in Global Currency
├── RCNTR  Cost Center
├── PRCTR  Profit Center
├── SEGMENT Segment
└── RBUSA  Business Area
```

The accounts payable and accounts receivable sub-ledgers operate as reconciliation sub-ledgers to the GL. Every vendor invoice posted in FI-AP simultaneously updates the vendor account in the sub-ledger and the reconciliation account in the GL. This double-write architecture means that the sum of open items in the vendor sub-ledger always equals the balance of the AP reconciliation account in the GL — provided no one has posted directly to the reconciliation account, which SAP prevents by default through the field status configuration that marks reconciliation accounts as recon-account-managed and therefore blocked for direct manual posting.

### Controlling (CO): The Profitability Engine

If FI answers the question "what is our financial position according to external accounting standards," CO answers the question "how did we spend our money and where did we make it?" These are related but structurally different inquiries, and SAP's CO module is architecturally distinct from FI even though the two are tightly integrated.

The CO area is the central organizational unit of Controlling. One or more company codes are assigned to a CO area, and all cost objects within that CO area share the same operative chart of accounts and the same controlling version. A controlling version defines whether you are looking at plan data, actual data, or a specific simulation version, which matters enormously for budget-to-actual analysis.

Cost Center Accounting (CO-CCA) is the most basic CO function. A cost center represents an organizational unit responsible for costs: a manufacturing department, an IT team, a finance shared service team. Costs are posted to cost centers either directly (a purchase order for department supplies posted with a cost center account assignment) or indirectly through assessments and distributions. An assessment cycle takes the total costs accumulated on a sender cost center and allocates them to receiver cost centers or other CO objects based on a defined statistical key figure — headcount, square footage, CPU consumption, or any quantity you configure. A distribution cycle, by contrast, allocates the original cost elements (GL accounts) rather than posting everything under a single assessment cost element. The distinction matters for profitability reporting: distribution preserves the original cost structure for downstream analysis; assessment consolidates it.

Internal orders in CO-OPA serve as short-lived cost collectors for projects, campaigns, or capital expenditures that do not warrant a full Work Breakdown Structure in PS (Project System). An internal order accumulates actual costs, can carry a budget with availability control set to warning or error on overrun, and is settled periodically to a cost center, an asset under construction, or a PA segment. The settlement rule, stored on the order itself, defines the receivers and their percentage or equivalence number allocations.

Profitability Analysis (CO-PA) is where CO delivers management P&L. SAP supports two CO-PA types: account-based and costing-based. Account-based CO-PA stores profitability data in GL accounts and reconciles precisely with FI — in S/4HANA, it is the only type written to ACDOCA and is effectively the default. Costing-based CO-PA uses value fields instead of GL accounts, allows real-time accruals for planned costs like freight or rebates that have not yet been invoiced, and historically provided faster, more flexible margin analysis at the cost of a reconciliation gap with FI. Many enterprises running ECC operated both types simultaneously and reconciled them periodically. In S/4HANA, SAP's recommended path is account-based CO-PA.

```
CO Object Hierarchy & Cost Flow

                    ┌─────────────────┐
                    │   CO Area        │
                    │  (Controlling   │
                    │   Umbrella)     │
                    └────────┬────────┘
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
   ┌──────┴──────┐   ┌───────┴──────┐   ┌──────┴──────┐
   │  Cost Center│   │Internal Order│   │  WBS Element│
   │  (CCA)      │   │  (OPA)       │   │  (PS)       │
   └──────┬──────┘   └──────┬───────┘   └──────┬──────┘
          │                 │                   │
          │   Assessment/   │   Settlement      │   Settlement
          │   Distribution  │                   │
          └────────────┬────┴───────────────────┘
                       │
              ┌────────┴────────┐
              │  CO-PA Segment  │
              │ (Product/Region/│
              │  Customer)      │
              └─────────────────┘
```

Product costing (CO-PC) calculates the standard cost of a manufactured or assembled product by exploding its bill of materials through the routing operations on the work centers, applying activity rates per operation, and summing material costs at standard prices. The result is the standard cost estimate, which is marked and released to the material master as the standard price field. Every subsequent goods movement of that material uses this standard price, and any difference between the actual purchase price and the standard is posted as a price variance to a price difference GL account. Manufacturing orders accumulate actual costs against their standard, and at period end the variance is calculated by category — price variance, quantity variance, lot size variance, resource-usage variance — and settled to CO-PA, closing the loop between operational manufacturing and management profitability reporting.

### Materials Management (MM): The Procurement and Inventory Engine

Materials Management governs the external procurement of goods and services and the internal management of inventory. Its organizational architecture starts with the client and company code from FI, adds the plant (a physical facility capable of producing, storing, or transferring materials), and subdivides the plant into storage locations for inventory management and into purchasing organizations for procurement authority.

The procurement cycle in MM follows a canonical document chain: purchase requisition to purchase order to goods receipt to invoice receipt. Each step creates a document, and each document is linked to its predecessor through reference fields that enable the three-way match — the foundational control that ensures you only pay for what you ordered and what you received.

A purchase order line item carries quantity, net price, delivery date, plant, storage location, account assignment (cost center, internal order, or asset for non-stock items), and a link to an info record or contract that provides the agreed price. When the warehouse confirms a goods receipt against the purchase order using MIGO, SAP creates a material document recording the quantity and storage location movement, and simultaneously creates an FI document that debits the inventory account (or the consumption account for non-stock items) and credits the GR/IR clearing account. The GR/IR (Goods Receipt / Invoice Receipt) clearing account is a liability account that represents obligations recognized but not yet invoiced — a critical accrual account for month-end close accuracy.

When the vendor invoice arrives and the accounts payable team posts it via MIRO, SAP debits the GR/IR clearing account and credits the vendor sub-ledger. If the invoice price matches the purchase order price within tolerance, the GR/IR clears cleanly. If there is a discrepancy, SAP posts a price difference to the variance account if the material is managed at standard price, or adjusts the moving average price if the material is on moving average. The tolerance check in MIRO is configured via transaction OMR6, where you define percentage and absolute tolerances for price variances, quantity variances, and delivery cost variances. Violations above tolerance block the invoice for payment pending manual review.

```
MM Procurement Document Chain & FI Integration

Purchase Requisition (PR)
      │  (converted by buyer)
      ▼
Purchase Order (PO) ──── ME21N
      │
      │ Vendor delivers goods
      ▼
Goods Receipt (GR) ───── MIGO
      │
      ├─── Material Document (stock increase)
      │       Qty: +100 EA, Storage Loc: 0001
      │
      └─── FI Document (automatic)
              Dr: Inventory / GR BSX     1,000
              Cr: GR/IR Clearing WRX     1,000
      │
      │ Vendor sends invoice
      ▼
Invoice Verification (IV) ── MIRO
      │
      └─── FI Document (automatic)
              Dr: GR/IR Clearing WRX     1,000
              Dr: Tax Input (VST)           80
              Cr: Vendor (AP Sub-ledger) 1,080
```

Inventory management in MM tracks stock at three levels of granularity: plant level, storage location level, and in Warehouse Management (WM) or Extended Warehouse Management (EWM), down to the bin level. Stock types add a further dimension: unrestricted-use stock is available for manufacturing or sales; quality inspection stock is blocked pending quality disposition; blocked stock is unavailable for use but still owned. Movement types are the atomic codes that drive every inventory transaction. Movement type 101 is a goods receipt against a purchase order. Movement type 261 is a goods issue to a production order. Movement type 601 is a goods issue to a customer delivery. Each movement type carries a configuration entry in OMJJ that defines which account determination keys to use, whether the movement requires a reference document, and how the quantity and value update behaves. Practitioners who know movement type configuration can trace any inventory discrepancy to its transactional source.

### Sales and Distribution (SD): The Revenue Engine

SD governs the entire order-to-cash process, from customer inquiry through delivery, billing, and cash application. Its organizational structure maps commercial selling authority onto the physical supply chain. The sales organization is the top-level SD unit, representing a legal selling entity. It is divided into distribution channels (direct sales, retail, e-commerce) and further into divisions (product lines). The combination of sales organization, distribution channel, and division is called a sales area, and every SD master record — the customer master sales area view, the material master sales organization view, the pricing condition records — is maintained at the sales area level.

The SD document chain mirrors the MM chain in its logic: sales inquiry leads to quotation leads to sales order leads to delivery leads to goods issue leads to billing document. Each step is a discrete document linked by reference. The sales order is the central document, carrying customer details, requested delivery dates, materials and quantities, pricing, and shipping instructions. Pricing in SD is driven by the condition technique, one of SAP's most powerful and most misunderstood configuration frameworks. A pricing procedure defines the sequence of condition types — PR00 for base price, K004 for material discount, K005 for customer-material discount, MWST for tax — and the calculation rules (whether a condition is a percentage step-down, a fixed amount, or an accrual). Condition records for each condition type are maintained in VK11 and stored in KONP/KONV tables, keyed by the condition type's access sequence, which defines which combination of fields to search — customer number plus material, customer hierarchy node plus material group, or any other configuration the business requires.

Delivery processing creates the physical shipment instructions and is the trigger for the inventory movement. When an outbound delivery is created from a sales order and the picking and packing steps are completed, the goods issue posting (movement type 601) reduces unrestricted stock, creates a material document, and creates the FI document that debits cost of goods sold and credits the inventory account. This goods issue posting is also the revenue recognition trigger in simple scenarios: the billing document can only be created after goods issue, ensuring that revenue is not invoiced before ownership has transferred.

The billing document, created via VF01 or the billing due list in VF04, generates the customer invoice and creates the FI posting that debits the accounts receivable sub-ledger and credits the revenue GL account via the account determination in VKOA. The billing document also transfers the actual revenue and cost data to CO-PA, completing the profitability loop from sales order through delivery through financial close.

### Production Planning (PP): The Manufacturing Engine

PP governs the planning and execution of production, connecting sales demand signals to manufacturing capacity and material requirements. Its master data foundation is the Bill of Materials (BOM) and the Routing. The BOM defines the material components and quantities required to produce one unit of a finished or semi-finished good. The Routing defines the sequence of operations, the work center where each operation runs, and the standard values for setup time, machine time, and labor time. Together, the BOM and Routing feed the standard cost estimate in CO-PC, the material requirements calculation in MRP, and the production order confirmation in shop floor execution.

Material Requirements Planning (MRP) is the planning engine at PP's core. MRP runs either at the plant level for all materials or selectively for a material-plant combination. It reads the demand picture — sales orders, planned independent requirements from the demand plan, dependent requirements from higher-level production orders — and nets it against existing stock and open receipts. Where a shortage exists within the replenishment lead time, MRP creates a planned order for in-house production or a purchase requisition for external procurement. The MRP parameters on the material master — MRP type (consumption-based versus deterministic MRP versus MPS), lot sizing procedure, safety stock, planned delivery time, in-house production time — are the control parameters that govern how MRP behaves for each material. Getting these parameters wrong creates either stock-outs or excess inventory, and the practitioners who tune MRP parameters are doing the equivalent of calibrating a production control system.

A production order in PP is the execution document that authorizes manufacturing. It carries the BOM explosion (components with required quantities and issue storage locations), the routing operations, the scheduled start and finish dates calculated by backward scheduling from the required delivery date, and the costing data populated from the standard cost estimate. As the order is executed, actual component consumption is confirmed via goods issues (movement type 261), and actual labor and machine time is confirmed via operation confirmations (CO11N). These actuals accumulate on the production order cost collector, and at period end, the variance between the order's actual costs and its standard cost is calculated and settled to CO-PA through a CO settlement run (transaction CO88 for collective processing).

### Human Capital Management (HCM): The Workforce Engine

HCM manages the entire employee lifecycle from organizational structure through hiring, payroll, time management, and benefits administration. Its foundational master data structure is the infotype, a time-delimited data record that stores a specific category of employee information. Infotype 0001 stores organizational assignment — employee group, employee subgroup, personnel area, personnel subarea, organizational unit, position. Infotype 0007 stores planned working time — work schedule rule, full-time or part-time indicator. Infotype 0008 stores basic pay — pay scale type, pay scale area, pay grade, pay step, and wage type amounts. Every piece of employee data in HCM lives in an infotype record with a valid-from and valid-to date, creating a complete temporal history of every change to every employee record.

The payroll engine reads infotype data as of the payroll period end date and executes a schema — a sequence of payroll functions called in a defined order — to calculate gross pay, deductions, taxes, and net pay. The schema is a programming construct defined in transaction PE01, and each function in the schema processes wage types through a series of internal tables (IT, OT, RT for results table). The results of payroll execution are stored in payroll cluster tables and feed both the financial posting to FI (via symbolic account assignment that maps wage types to GL accounts) and the HR reporting for headcount, cost distribution, and statutory reporting.

Organizational Management (OM) in HCM maintains the enterprise's reporting hierarchy as an object-oriented model. Organizational units, positions, and jobs are objects connected by relationships. An organizational unit has positions within it (relationship A003). A position is described by a job (relationship A007). A person holds a position (relationship A008). This object-relationship model is not merely administrative. It is the structure that drives workflow routing in SAP (approval requests route to the manager of the initiating employee's organizational unit), security role inheritance in some authorization concepts, and headcount reporting in CO through cost center assignment on infotype 0001.

## 3. High-Performance Optimization & Failure Modes

### Integration Failure: The Unreconciled GR/IR Account

One of the most common and costly failure modes in live SAP environments is a GR/IR clearing account that accumulates old, uncleared items over time until the balance becomes materially misleading on the balance sheet. The root cause is almost always a process gap: goods receipts are posted for purchase orders that are subsequently cancelled or changed, leaving a debit on the GR/IR account with no corresponding invoice receipt to clear it. Alternatively, vendor invoices are posted before goods receipts — particularly common in service-related procurement — leaving credits that have no matching debit to close against.

The practitioner fix requires both a system-side and a process-side response. On the system side, the transaction MR11 (Maintain GR/IR Clearing Account) is the SAP-standard tool for clearing GR/IR items where the difference between the goods receipt quantity and the invoice receipt quantity will not be corrected. MR11 creates a clearing document that closes the open item and posts the residual to either a purchase account or a price difference account depending on configuration. On the process side, a weekly GR/IR aging report — built on table EKBE joined to BSIK/BSAK for the invoice posting side — should flag any item older than 30 days for buyer review. Items older than 90 days almost always represent abandoned transactions and should be cleared immediately. Allowing them to age into annual report periods creates an audit finding and potentially a restatement risk if the amounts are material.

### MRP Master Data Decay and Phantom Demand

MRP's reliability is entirely dependent on the accuracy of the master data it consumes. Lead times on material masters that have not been updated since implementation, phantom components in BOMs that reflect a product design several generations old, safety stock levels set to arbitrary round numbers rather than statistically derived quantities — all of these cause MRP to generate either vastly over-optimistic procurement proposals (driving stock-outs when actual lead times are longer than planned) or massive overstock proposals (driving working capital inflation when safety stock buffers are set without demand variability analysis).

A mature MRP parameter review cycle addresses this systematically. For procurement lead time accuracy, the buyer team should run a report on EKBE for the previous twelve months, calculate the actual time elapsed between purchase order creation and goods receipt confirmation for each vendor-material combination, and compare it to the planned delivery time on the material master. Where the actual exceeds the planned by more than twenty percent, the material master should be updated. For safety stock, the statistically defensible formula is the product of the z-score for the target service level, the standard deviation of daily demand over the review period, and the square root of the replenishment lead time in days. Setting safety stock to the output of this formula rather than a buyer's intuition typically reduces both stock-out frequency and average inventory value simultaneously.

BOM explosion accuracy in PP is especially critical because a BOM error propagates through every planned production order and every standard cost estimate that references it. A missing component causes a shortage exception during production that halts the shop floor. A quantity error of even a few percent compounds into a material variance that distorts CO-PA profitability reporting for the product line. The practice of engineering change management with controlled BOM versioning and explicit validity dates — using SAP's Engineering Change Management (ECM) functionality or at minimum the BOM alternative and usage controls — is not overhead. It is the control that keeps production costing and manufacturing execution synchronized with the actual product design.

### Authorization and Segregation of Duties in FI/MM Integration

SAP's authorization concept uses authorization objects and profiles to control which transactions a user can execute and on which organizational objects. In the FI/MM integration context, the most consequential segregation of duties (SoD) risk is the ability of a single user to create a vendor master record (FK01), create a purchase order (ME21N), and post the vendor payment (F-53). A user with all three authorizations can create a fraudulent vendor, raise a purchase order to that vendor, and release the payment — the classic payment fraud scenario that SAP's authorization concept is specifically designed to prevent through role separation.

GRC (Governance, Risk, and Compliance) tooling — either SAP GRC Access Control or a third-party alternative — automates the detection of SoD conflicts by evaluating user role assignments against a ruleset that defines which transaction combinations represent conflicts. But the more important practitioner discipline is preventive: designing roles at the authorization object level rather than assigning SAP's delivered composite roles, which are intentionally broad for demonstration purposes and almost always contain SoD violations when assigned to real users. The standard to work from is the authorization object level for each transaction's most sensitive fields: BUKRS (company code) and BKPF-BLART (document type) in FI, EKORG (purchasing organization) and EKGRP (purchasing group) in MM, and VKORG (sales organization) in SD. Roles built with field-level specificity on these objects protect the organization's control environment without restricting legitimate access.

### HANA Performance: Table Partitioning and Index Strategy in S/4HANA

Transitioning from ECC on a traditional RDBMS to S/4HANA on HANA eliminates many performance problems that practitioners spent years working around — the totals tables like FAGLFLEXT and GLT0 that existed only to serve balance and totals queries are deprecated because HANA can aggregate ACDOCA on the fly. However, HANA introduces its own performance discipline. The ACDOCA table in a mature production system holds hundreds of millions of rows. Queries that do not use the table's partitioning key — RCLNT (client), RLDNR (ledger), RBUKRS (company code), GJAHR (fiscal year) — force full partition scans that drive memory and CPU consumption.

Custom ABAP reports and BW extractors written without awareness of ACDOCA's partitioning strategy are the primary source of performance regressions after S/4HANA migration. The discipline of always including RCLNT, RLDNR, RBUKRS, and GJAHR as the leading fields in any WHERE clause against ACDOCA, and testing custom code with the SQL Performance Tuning Worklist in transaction ST05, eliminates the majority of these issues before they reach production. The SAP HANA Studio and HANA cockpit provide column store analyzer tools that show the compression ratio, memory footprint, and merge delta statistics for any column store table — practitioners who run these checks monthly on ACDOCA, MATDOC (the material document table in S/4HANA), and VBAK/VBAP (sales document header and line) catch fragmentation before it degrades end-user response times.

### Period-End Close Sequence and Dependency Ordering

The month-end close in an integrated SAP environment is a dependency graph, not a checklist. FI postings cannot be finalized until MM is closed for the period, because goods receipts posted after the FI close would land in the wrong period. CO variances cannot be settled to CO-PA until all production order confirmations are complete and all activity price revaluations have been executed. The billing document transfer to accounting cannot reflect accurate revenue until SD billing is complete. Any step performed out of order creates entries in a period that is supposed to be locked, requiring reversal and reposting that extends the close timeline.

A reliable close sequence for a manufacturing enterprise on SAP runs in this dependency order: first, complete all operational transactions (final goods receipts, final goods issues, final production confirmations) by the operational cut-off time. Second, run MM period close (MMPV) to shift the MM posting period forward, preventing further goods movements in the closing period. Third, run the ML (Material Ledger) actual costing cockpit if the material ledger is active, which calculates actual costs and revalues inventory at actual prices. Fourth, run CO activity price revaluation (CON2) to revalue production order confirmations at actual activity rates rather than plan rates. Fifth, calculate and settle production order variances (CO88). Sixth, run CO-PA assessment cycles and distribution cycles. Seventh, run FI-GL closing activities including accrual postings, depreciation runs (AFAB), and foreign currency revaluation (FAGL_FC_VAL). Eighth, run financial statement version reporting for preliminary review. Ninth, lock the FI posting period (OB52) for the closed period. Any organization that runs these steps in a different order, or that runs MM period close after FI period close, is creating reconciliation problems that will compound from month to month until the accumulated errors require an extraordinary correction posting.

The practitioners who internalize SAP's module integration not as a feature catalog but as a system of invariant relationships — synchronous posting, singular master data, the universal journal as the single record of financial truth — are the ones who build controls that hold under production stress and close books that auditors can rely on without reservation.
