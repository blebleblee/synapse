# Lesson 1: Equity Instruments, Ownership Rights, Capital Structure

## 1. First-Principles Intuition & Invariants

Equity is not, at its root, a financial abstraction. It is a legal claim — a residual ownership interest in the assets and future cash flows of a business enterprise after all prior creditor obligations have been satisfied. When you hold a share of common stock, you hold a fractional, undivided interest in everything the corporation owns and everything it will earn, subordinated to every other class of claimant in the capital structure. That subordination is not a quirk of contract — it is the definitional feature of equity, the characteristic that makes it simultaneously the riskiest and most potentially rewarding position in any capital stack.

Understanding equity from first principles requires grasping the corporate form itself. A corporation is a legal person distinct from its founders, employees, and shareholders. It can own property, enter contracts, sue, and be sued. Shareholders do not own the corporation's assets directly; they own shares in the corporation, which in turn owns the assets. This distinction has enormous practical consequences. A shareholder cannot walk into a company's warehouse and claim a desk. What the shareholder owns is a bundle of contingent rights: the right to vote on certain governance matters, the right to receive dividends if and when the board declares them, and the right to receive a pro-rata distribution of whatever net value remains after all liabilities are extinguished in a liquidation. This bundle of contingent rights — not any direct claim on physical property — is the legal substance of a share.

The residual nature of equity creates an asymmetric payoff structure that defines modern capital markets. A bondholder who lends $100 million at 6% has a contractual claim on $6 million per year and the return of principal at maturity, regardless of how well or poorly the business performs above its debt service obligations. The equity holder, by contrast, has no guaranteed return and no guaranteed principal recovery. If the business earns $5 million above its obligations, the equity holder receives proportionally. If it earns $500 million, the equity holder receives proportionally. If it earns nothing, the equity holder receives nothing. And if it enters bankruptcy with liabilities exceeding assets, the equity holder receives nothing at all while creditors absorb the loss. This unlimited upside combined with total downside wipeout — the equity residual claim — is precisely what investors are pricing when they buy stock. It is why equity investors demand higher expected returns than debt investors, and why that equity risk premium has historically averaged between 4% and 6% above the risk-free rate in U.S. markets.

The capital structure of a corporation is the full set of claims against the enterprise, ordered by priority. Senior secured debt sits at the top, backed by specific collateral pledges. Unsecured senior notes follow. Subordinated or mezzanine debt sits below that, accepting higher default risk in exchange for a higher coupon or equity-linked features like warrants. Preferred stock occupies the boundary between debt and equity — it carries a specified dividend rate and liquidation preference that rank above common equity, while still sitting below all debt in bankruptcy. Common stock occupies the very bottom, the last in line, the truest residual claimant. This ordering is not merely analytical; it is legally enforceable in U.S. courts under state corporate law (Delaware General Corporation Law being the dominant framework) and under the absolute priority rule codified in the U.S. Bankruptcy Code.

The critical invariant every practitioner must internalize is this: **enterprise value is a pie, and capital structure determines how that pie is divided and in what order.** Enterprise value (EV) equals the total market value of all claims on the firm — debt, preferred, common equity, and any other instruments. When EV rises or falls, all classes of claimants are affected, but the magnitude and sequence of impact flows through the priority stack. Debt holders are insulated until the EV falls below their claim. Preferred holders are insulated until EV falls below their liquidation preference. Common equity holders absorb every unit of EV volatility without any floor. This mechanical reality shapes how every class of investor prices risk, structures deal terms, and negotiates governance rights.

---

## 2. Core Architecture & Mechanics

### Common Stock: The Residual Engine

Common stock is the foundational equity instrument. Its economic rights are strictly residual: common shareholders receive dividends only after preferred dividends are paid, and they receive liquidation proceeds only after all debt and preferred claims are satisfied. Its governance rights are primary: in most standard corporate structures, only common stockholders vote to elect the board of directors, approve fundamental transactions (mergers, asset sales, charter amendments), and ratify auditor appointments.

The voting mechanism itself has a specific architecture. Each share of common stock typically carries one vote per share. At an annual general meeting (AGM) or special meeting, votes are cast by proxy — shareholders submit voting instructions to a registered agent (typically a transfer agent like Computershare or Broadridge), and those instructions are tabulated and reported to the company. Institutional shareholders controlling large positions coordinate with proxy advisory firms such as Institutional Shareholder Services (ISS) and Glass Lewis, whose voting recommendations function in practice as de facto governance standards for a significant portion of the institutional investor base. A shareholder proposal requires majority approval among shares present and voting for ordinary resolutions; charter amendments and fundamental transactions require supermajority votes (typically two-thirds) in most jurisdictions.

The economic mechanics of common stock are expressed in per-share terms, and the core mathematical relationship practitioners must keep always live is the **earnings per share (EPS)** and **price-to-earnings (P/E)** framework:

$$\text{EPS} = \frac{\text{Net Income} - \text{Preferred Dividends}}{\text{Weighted Average Diluted Shares Outstanding}}$$

$$\text{Intrinsic Value (DDM)} = \frac{D_1}{r - g}$$

where $D_1$ is the expected dividend per share in the next period, $r$ is the required return on equity, and $g$ is the perpetual dividend growth rate. The DDM is analytically clean but practically limited to mature dividend-paying firms. For high-growth companies that reinvest all earnings, practitioners apply a DCF on free cash flow to equity (FCFE), or more commonly, a discounted unlevered free cash flow model at the enterprise level, then subtract net debt to arrive at equity value.

### Preferred Stock: Contractual Priority Within Equity

Preferred stock is not a monolithic instrument. It is a category containing several mechanically distinct variants, each with different economic implications for common shareholders. The key variants are:

**Participating preferred** holds a liquidation preference equal to the original investment (often 1× or 2× invested capital) and then participates pro-rata with common shareholders in any remaining proceeds as if converted to common. This structure is heavily founder-dilutive in exit scenarios above the preference threshold because preferred holders effectively double-dip. Suppose a company raises $20 million from Series A investors at a $60 million post-money valuation, with Series A receiving 1× participating preferred. At a $100 million exit:

The Series A investors receive their $20 million liquidation preference first, leaving $80 million. Then all remaining proceeds are distributed pro-rata across common and as-converted preferred. If Series A owns 33% of fully diluted shares, they receive an additional $26.4 million, for total proceeds of $46.4 million — a 2.32× return on a 1.67× exit multiple, extracted at the expense of common shareholders.

**Non-participating preferred** (also called "straight preferred") forces the preferred holder to choose between taking the liquidation preference *or* converting to common and sharing pro-rata — but not both. This creates a conversion trigger: preferred holders convert when their pro-rata share of proceeds exceeds their liquidation preference. The break-even conversion point is:

$$\text{Conversion Threshold} = \frac{\text{Liquidation Preference}}{\text{Preferred Ownership \%}}$$

For a Series A with $20 million preference and 33% ownership, conversion is rational when the total exit value exceeds approximately $60.6 million. Below that threshold, they take the preference. Above it, they convert and share.

**Cumulative preferred dividends** accumulate as an accrued liability even if the board never declares payment. Non-cumulative dividends are simply forgone if not declared. In practice, nearly all venture-stage and growth-equity preferred stock includes cumulative dividends at a nominal rate (commonly 6–8% per annum), which compound against the liquidation preference and can materially reduce common shareholders' proceeds in a delayed exit scenario. If a company raises $10 million in cumulative 8% preferred and exits five years later without having paid dividends, the accrued dividend balance is $4.69 million (using compound rather than simple accumulation), increasing the effective liquidation preference to $14.69 million before common shareholders see a dollar.

### The Liquidation Waterfall: Modeling Priority Flows

The liquidation waterfall is the definitive mechanism by which proceeds from a company sale or liquidation are distributed across all capital structure claimants. Every M&A practitioner and equity analyst must be able to construct and stress-test this model from scratch. The waterfall has the following canonical structure:

```
Total Enterprise Proceeds (Sale Price or Liquidation Value)
         │
         ▼
[1] Senior Secured Debt Repayment
    (Term Loans, Revolving Credit Facility — full principal + accrued interest)
         │
         ▼
[2] Unsecured Senior Notes / Subordinated Debt
    (Full principal + accrued interest, in priority order)
         │
         ▼
[3] Preferred Stock Liquidation Preferences
    (Series C → Series B → Series A, in reverse seniority order)
    + Accrued Cumulative Dividends (if applicable)
         │
         ▼
[4] Participating Preferred Participation Rights
    (Pro-rata with common, only if participating structure)
         │
         ▼
[5] Common Stock (Residual)
    (Pro-rata among all common holders, including converted preferred)
```

A complete worked model for a hypothetical SaaS company acquisition at $150 million illustrates the mechanics fully. Assume the company has $30 million in senior secured term debt (6% coupon, accrued interest $900K), $15 million in Series A preferred (1× non-participating, cumulative 8%, accrued dividends of $3.6M over three years), and $20 million in Series B preferred (1.5× non-participating, 8% cumulative, accrued dividends of $3.2M over two years). The fully diluted cap table is 10 million common shares, 2 million Series A shares (25% as-converted), and 1.5 million Series B shares (20% as-converted), for 13.5 million fully diluted shares.

Working through the waterfall from $150 million in proceeds:

After retiring $30.9 million in senior debt (principal plus accrued interest), $119.1 million remains. Series B holds a 1.5× liquidation preference on $20 million, or $30 million, plus $3.2 million in accrued dividends, totaling $33.2 million. Series B's conversion break-even is $33.2M / 20% = $166 million. Since the remaining $119.1 million is below that threshold, Series B takes its preference, leaving $85.9 million. Series A holds a 1× preference on $15 million, plus $3.6 million in accrued dividends, totaling $18.6 million. Series A's conversion break-even is $18.6M / 25% = $74.4 million. Since $85.9 million exceeds that threshold, Series A converts and takes its pro-rata share: 25% × $85.9 million = $21.5 million, which exceeds the $18.6 million preference, confirming conversion is rational. Common holders receive the remaining 75% × $85.9 million = $64.4 million, divided among 10 million common shares at $6.44 per share.

This model must be rebuilt for every transaction scenario with varying exit proceeds to identify at what sale price each class of preferred converts, and what the per-share common proceeds look like across a range of outcomes. This sensitivity analysis is the foundation of a shareholder value analysis (SVA) table — an essential deliverable in any M&A negotiation involving a venture-backed company.

### Dual-Class Share Structures: Governance Architecture

Dual-class share structures emerged as a mechanism for founders and controlling shareholders to retain voting control while accessing public market capital. The architecture is straightforward in concept: the company designates two (or more) classes of common stock with different voting rights per share. Class A shares, typically sold to the public, carry one vote per share or a fractional vote. Class B shares, retained by founders or insiders, carry a multiple — commonly 10 votes per share, though ratios as high as 20× exist (Alphabet, Meta, Snap, and Lyft all use variants of this structure).

The economic ownership and the voting control these structures create become radically decoupled over time. Mark Zuckerberg controls Meta with roughly 13% of economic ownership but over 57% of voting power through Class B share concentration. This decoupling has significant pricing implications: equity research analysts frequently apply a "governance discount" to dual-class structures, reflecting the risk that minority shareholders cannot discipline management through the proxy mechanism if management destroys value. Empirically, this discount has been estimated in academic literature at 5–10% of share price relative to single-class peers, though it compresses during periods of strong operational performance.

Governance advocates at institutions like CalPERS and the Council of Institutional Investors have pushed index providers to respond. MSCI, S&P Dow Jones, and FTSE Russell each adopted policies between 2017 and 2019 restricting or excluding newly public dual-class companies from major indices, reducing automatic index-driven institutional demand for such stocks. The result for practitioners is a real cost of capital consideration: dual-class structures may be appropriate for founder-driven businesses where long-term strategic vision is a genuine competitive differentiator, but they carry tangible index exclusion risks and institutional ownership limitations that suppress demand and elevate the cost of equity financing.

The legal architecture of dual-class structures is typically codified in the certificate of incorporation (or amended and restated certificate filed with the Delaware Secretary of State). Critically, most structures include **sunset provisions** — automatic conversion triggers that collapse Class B to Class A upon specific events: the death or departure of the founder, a transfer of shares outside the founder's immediate family or approved estate vehicles, or a time-based sunset (commonly seven to ten years post-IPO). These sunset provisions are increasingly demanded by institutional investors and proxy advisory firms as a condition of their support for the IPO governance structure, and their inclusion has become market standard for companies seeking broad institutional demand in the IPO book-build.

### Dilution Mathematics: The Mechanics of Ownership Erosion

Dilution is the reduction in an existing shareholder's percentage ownership caused by the issuance of additional shares. It is one of the most practically important calculations any equity analyst or company operator must execute with precision. There are two distinct forms: **economic dilution**, which occurs when new shares are issued at a price below fair value (causing existing shareholders to lose value, not just percentage), and **percentage dilution**, which occurs whenever new shares are issued at any price (reducing pro-rata ownership even if done at fair value).

The basic dilution formula is:

$$\text{Post-Dilution Ownership \%} = \frac{\text{Existing Shares}}{\text{Existing Shares} + \text{New Shares Issued}}$$

But this understates real-world complexity. The fully diluted share count for any cap table analysis must include all issued and outstanding common shares, all issued and outstanding preferred shares on an as-converted basis, all outstanding stock options (both vested and unvested), all outstanding warrants, all restricted stock units (RSUs), and all shares reserved for future issuance under the equity incentive pool. The treasury stock method (TSM) governs the dilution calculation for in-the-money options and warrants in EPS calculations: the proceeds from hypothetical exercise are assumed to repurchase shares at the current market price, netting against the gross new shares.

$$\text{TSM Diluted Shares from Options} = \text{Options Outstanding} - \frac{\text{Options Outstanding} \times \text{Strike Price}}{\text{Current Market Price}}$$

For a company with 1 million stock options outstanding at a $10 strike price and a current market price of $25, the TSM calculates: 1,000,000 − (1,000,000 × $10 / $25) = 1,000,000 − 400,000 = 600,000 net dilutive shares added to the diluted share count.

Anti-dilution provisions in preferred stock term sheets protect preferred investors from dilution in down rounds (new financing rounds at a lower valuation than the previous round). The two dominant mechanisms are **broad-based weighted average anti-dilution** and the more aggressive **full ratchet anti-dilution**. Under full ratchet, the conversion price of existing preferred shares is adjusted downward to match the new round price in full, as if the preferred investors had always paid the lower price. This can devastate common shareholders in a down round. Under broad-based weighted average anti-dilution, the adjustment is moderated by the volume of new shares issued relative to the total fully diluted share count, producing a less punitive conversion price adjustment:

$$\text{New Conversion Price} = \text{Old Conversion Price} \times \frac{(\text{Shares Outstanding Before} + \text{Shares Issuable at Old Price})}{(\text{Shares Outstanding Before} + \text{Actual New Shares Issued})}$$

If a company with 10 million fully diluted shares and a $5.00 Series A conversion price raises a Series B at $2.00, issuing 2 million new shares, the weighted average new conversion price for Series A is: $5.00 × (10M + 4M) / (10M + 2M) = $5.00 × 14/12 = $5.83... wait — the formula adjusts *downward* toward the new price, not upward. Recalibrating: the numerator is shares that would have been issued at the old price, the denominator includes the actual new shares. Using the NVCA-standard formula:

$$\text{CP}_\text{new} = \text{CP}_\text{old} \times \frac{A + B}{A + C}$$

where $A$ is shares outstanding pre-financing, $B$ is the number of shares that would have been issued at the old conversion price for the same aggregate consideration, and $C$ is the actual number of new shares issued. For a $4 million Series B raise at $2.00/share (issuing 2 million shares): $B$ = $4M / $5.00 = 800,000 hypothetical shares. So the new conversion price is $5.00 × (10M + 800K) / (10M + 2M) = $5.00 × 10.8/12 = $4.50. This $4.50 conversion price increases the number of common shares into which Series A preferred converts, diluting common holders without fully ratcheting Series A investors down to the new round price.

---

## 3. High-Performance Optimization & Failure Modes

### Cap Table Hygiene and Scenario Modeling

The single most common operational failure in equity management is an imprecise, unreconciled cap table. For private companies, the cap table is the definitive legal record of ownership, and errors in it — missing warrant grants, unstated option pool reserves, incorrectly recorded conversion prices — become catastrophic when a liquidity event occurs and the disbursement calculations surface inconsistencies. For public companies and their analysts, the diluted share count errors in financial models propagate directly into EPS, P/E multiples, and per-share DCF valuations, compounding across every output.

Best practice for cap table management requires maintaining a single system of record (Carta and Pulley are the dominant platforms for private companies) with every security issuance, transfer, repurchase, and conversion event recorded in real time and reconciled against the company's Delaware corporate ledger. Every new financing round should trigger a full waterfall model rebuild under at least three exit scenarios: a base case at approximately 2× the current post-money valuation, a downside case at 0.75× current post-money, and an upside case at 5× current post-money. This three-scenario waterfall is the minimum diligence a board should demand before approving any new financing round, because it makes explicit the trade-offs between liquidation preference stack, anti-dilution provisions, and common shareholder value across the realistic range of outcomes.

### Voting Mechanics and Governance Risk

Governance failures in dual-class structures typically manifest in one of two ways: board entrenchment leading to capital allocation decisions that destroy value for minority shareholders, or sunset provisions that lapse without enforcement due to ambiguous triggering language. Both failure modes are preventable at the structuring stage. Practitioners advising on IPO governance structures should ensure that sunset provisions specify exact triggering conditions with no room for interpretive dispute, that automatic conversion mechanics are confirmed with the transfer agent and registrar before the S-1 is filed, and that the economic and voting ownership split is disclosed with sufficient detail that institutional investors can model the governance risk explicitly.

For public equity analysts, dual-class structure risk manifests in the discount applied to the governance-adjusted valuation. A common practitioner heuristic is to model the controlled company at a 5–10% EV discount to a single-class peer trading at the same EV/EBITDA or EV/Revenue multiple, then adjust upward or downward based on founder track record, capital allocation history, and the proximity of any sunset trigger. This is not a precise science, but it is a necessary discipline: ignoring dual-class governance in a valuation creates systematic overestimation of the equity's risk-adjusted intrinsic value.

### Dilution Failure Modes in Down Rounds

The most financially destructive equity mechanics scenario for common shareholders — particularly employees and early-stage common holders — is the interaction of full-ratchet anti-dilution provisions, pay-to-play clauses, and accumulated preferred liquidation preferences in a down-round financing. This trifecta can reduce common shareholders to economic irrelevance even in a modestly successful exit. Consider a company that raised $50 million in Series C at a $200 million post-money valuation with 1× participating preferred and full-ratchet anti-dilution protection, then raises a down-round Series D at a $50 million post-money valuation. Under full ratchet, Series C's conversion price resets to the Series D price, increasing the as-converted common share equivalent of Series C preferred by 4× (since the price dropped by 75%). If Series C originally represented 25% of fully diluted shares, it now represents something approaching 60–70% on an as-converted basis, before even accounting for the new Series D issuance. Common holders who thought they owned 40% of the company may find themselves holding 10–12% — and that residual claim still sits behind the full Series C and Series D liquidation preferences in any exit.

The practitioner mitigation for this scenario is not primarily quantitative; it is contractual. Negotiating broad-based weighted average anti-dilution rather than full ratchet, capping participation rights at a 2× multiple before the preference is relinquished, and including carve-outs from the preference stack for management incentive pools are the three most consequential terms in any preferred stock financing. These negotiations happen in the term sheet, not in the definitive documents — by the time lawyers are drafting the certificate of designation, all material economic terms are locked. Founders and equity plan participants who allow full-ratchet anti-dilution into a term sheet without modeling its down-round consequences are making a decision that can cost them millions in realized proceeds at exit.

### Price Per Share vs. Per-Unit Economic Reality

A subtle but persistent failure mode in equity analysis is confusing share price with per-unit economic value. High nominal share prices (Berkshire Hathaway Class A trades above $600,000 per share) and low nominal share prices (penny stocks, post-reverse-split companies) carry no information about the size of the underlying enterprise or the quality of the equity claim. What matters is the product of price per share and fully diluted share count — the equity market capitalization — and its relationship to underlying earnings, free cash flow, or asset value. An analyst who filters for stocks by share price, or who interprets a stock split as increasing shareholder value, has confused a unit of measurement for the substance being measured.

Similarly, rights offerings, stock dividends, and bonus issues affect the share count without affecting enterprise value. The share price adjusts proportionally, leaving each existing shareholder's economic position unchanged. The practitioner test is always to compare pre- and post-event *market capitalization*, not share price, before concluding that any event created or destroyed shareholder value. Genuine value creation in equity is measured by EV growth net of capital invested — the organic compounding of the residual claim over time, which is the most fundamental expression of what equity ownership means in the first place.
