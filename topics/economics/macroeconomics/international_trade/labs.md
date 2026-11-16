# Operational Verification Labs: International Trade

## Objective & Operational Lab Setup

These operational verification labs establish hands-on mastery of international trade analysis through empirical data manipulation, gravity model estimation, and trade policy simulation. You will work directly with real-world bilateral trade flows, tariff schedules, and exchange rate time series to quantify comparative advantage, measure trade elasticities, and evaluate the welfare impacts of protectionist interventions. The lab environment replicates the analytical workflow of trade economists at central banks, ministries of finance, and international organizations like the WTO and IMF.

International trade theory rests on Ricardo's principle of comparative advantage: nations gain from specialization even when one country holds absolute advantage in all goods. The Heckscher-Ohlin framework extends this insight by linking trade patterns to relative factor endowments—capital-abundant countries export capital-intensive goods, while labor-abundant nations export labor-intensive products. Modern gravity models formalize the empirical regularity that bilateral trade flows increase with economic mass (GDP) and decrease with geographic distance, capturing both supply-side production capacity and demand-side market size. These labs operationalize all three frameworks through data estimation, not abstract derivation.

Your analytical environment requires Python 3.9+ with pandas, numpy, statsmodels, and matplotlib libraries for econometric estimation and visualization. You will also use Excel or LibreOffice Calc for constructing revealed comparative advantage (RCA) indices and effective rate of protection (ERP) calculations. Data sources include the UN Comtrade database for bilateral trade flows at HS6 product classification, CEPII's GeoDist dataset for bilateral distance and contiguity variables, Penn World Tables for real GDP and exchange rate series, and TRAINS/WITS for tariff line data. Install the Python environment with `pip install pandas numpy statsmodels matplotlib seaborn scipy`. Download the CEPII gravity dataset from `http://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=8` and extract `dist_cepii.csv` to your working directory. For Comtrade data, register at `https://comtradeplus.un.org/` and use the bulk download API to retrieve annual bilateral trade matrices.

The operational protocol follows a three-stage diagnostic pipeline. First, you compute Balassa's revealed comparative advantage indices across product categories to identify a country's export specialization pattern and verify Ricardian predictions. Second, you estimate a structural gravity equation using Poisson pseudo-maximum likelihood (PPML) to quantify distance elasticity, border effects, and trade agreement impacts while controlling for multilateral resistance terms through fixed effects. Third, you simulate tariff shocks using partial equilibrium elasticity methods to calculate deadweight loss triangles, terms-of-trade effects, and real income changes for importing and exporting nations. Each exercise builds operational muscle memory for the empirical techniques that underpin trade policy evaluation in professional macroeconomic practice.

## Exercise 1: Foundational Practical Implementation

### Exercise 1.1: Revealed Comparative Advantage Calculation and Ricardian Verification

This exercise establishes the foundational measurement of comparative advantage through Balassa's RCA index, which compares a country's export share in a particular product category to the world's export share in that category. An RCA greater than unity indicates revealed comparative advantage; values below unity signal comparative disadvantage. You will compute RCA indices for the United States across two-digit SITC product categories, identify sectors of specialization, and cross-validate against factor endowment predictions from Heckscher-Ohlin theory.

Begin by downloading US bilateral export data from UN Comtrade for the most recent available year. Navigate to the Comtrade bulk download portal and select "Annual" frequency, "Exports" trade flow, "United States" as reporter, "World" as partner, and "SITC Rev. 3" classification at the two-digit level. Download the CSV file and save it as `us_exports_sitc2.csv` in your working directory. The file contains columns for `Reporter`, `Partner`, `Year`, `Commodity Code`, `Commodity`, and `Trade Value (US$)`.

Open a new Python script named `rca_analysis.py` and begin by loading the trade data and aggregating across all partner countries to compute total US exports by product category:

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Load US export data
df = pd.read_csv('us_exports_sitc2.csv')

# Aggregate US exports by SITC 2-digit code
us_exports = df.groupby('Commodity Code')['Trade Value (US$)'].sum().reset_index()
us_exports.columns = ['sitc2', 'us_export_value']

# Calculate total US exports across all products
total_us_exports = us_exports['us_export_value'].sum()
us_exports['us_share'] = us_exports['us_export_value'] / total_us_exports

print("US Export Distribution:")
print(us_exports.head(10))
```

Next, download world export data for the same year to compute the denominator of the RCA formula. Return to Comtrade and select "World" as reporter, "World" as partner, and the same SITC Rev. 3 two-digit classification. Download as `world_exports_sitc2.csv`. Load this data and compute world export shares by product:

```python
# Load world export data
world_df = pd.read_csv('world_exports_sitc2.csv')

# Aggregate world exports by SITC 2-digit code
world_exports = world_df.groupby('Commodity Code')['Trade Value (US$)'].sum().reset_index()
world_exports.columns = ['sitc2', 'world_export_value']

# Calculate total world exports
total_world_exports = world_exports['world_export_value'].sum()
world_exports['world_share'] = world_exports['world_export_value'] / total_world_exports

print("\nWorld Export Distribution:")
print(world_exports.head(10))
```

Merge the US and world datasets on the SITC product code and compute the Balassa RCA index as the ratio of US share to world share:

```python
# Merge US and world export data
rca_data = us_exports.merge(world_exports, on='sitc2', how='inner')

# Calculate Balassa RCA index
rca_data['rca'] = rca_data['us_share'] / rca_data['world_share']

# Sort by RCA in descending order
rca_data = rca_data.sort_values('rca', ascending=False)

print("\nTop 10 US RCA Sectors:")
print(rca_data[['sitc2', 'rca']].head(10))

print("\nBottom 10 US RCA Sectors:")
print(rca_data[['sitc2', 'rca']].tail(10))
```

The RCA index directly operationalizes Ricardo's comparative advantage principle. Products with RCA > 1 represent sectors where the United States exhibits stronger export specialization relative to the world average, indicating lower opportunity cost in production. High RCA values typically appear in capital-intensive and skill-intensive sectors (aerospace, machinery, pharmaceuticals, business services) consistent with US factor endowments—abundant physical and human capital relative to labor. Low RCA values concentrate in labor-intensive manufacturing (textiles, apparel, footwear) where countries with lower wage rates hold comparative advantage.

To validate these patterns against factor intensity predictions, manually annotate each SITC two-digit category with factor intensity classifications based on established trade literature. Create a reference mapping file `sitc2_factor_intensity.csv` with columns `sitc2`, `factor_type` (capital_intensive, skill_intensive, labor_intensive, resource_intensive), and `description`. Load this mapping and merge with your RCA results:

```python
# Load factor intensity classifications
factor_map = pd.read_csv('sitc2_factor_intensity.csv')
rca_data = rca_data.merge(factor_map, on='sitc2', how='left')

# Calculate mean RCA by factor type
mean_rca_by_factor = rca_data.groupby('factor_type')['rca'].mean().sort_values(ascending=False)

print("\nMean RCA by Factor Intensity:")
print(mean_rca_by_factor)

# Visualize RCA distribution by factor type
plt.figure(figsize=(12, 6))
sns.boxplot(data=rca_data, x='factor_type', y='rca', order=mean_rca_by_factor.index)
plt.axhline(y=1.0, color='r', linestyle='--', label='RCA = 1 (Neutral)')
plt.ylabel('Revealed Comparative Advantage Index')
plt.xlabel('Factor Intensity Category')
plt.title('US RCA Distribution by Factor Intensity (Heckscher-Ohlin Validation)')
plt.legend()
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('us_rca_factor_intensity.png', dpi=300)
plt.close()
```

The empirical pattern should confirm that US mean RCA indices rank highest in capital-intensive and skill-intensive categories, lowest in labor-intensive categories, validating the Heckscher-Ohlin prediction that countries export goods that intensively use their abundant factors. This operational verification grounds trade theory in measurable export patterns rather than abstract production possibility frontiers.

Now extend the analysis to compute the normalized revealed comparative advantage (NRCA) index, which transforms RCA into a symmetric metric bounded between -1 and +1 for easier cross-country comparison:

```python
# Calculate normalized RCA
rca_data['nrca'] = (rca_data['rca'] - 1) / (rca_data['rca'] + 1)

print("\nTop 10 US NRCA Sectors:")
print(rca_data[['sitc2', 'description', 'rca', 'nrca']].head(10))

# Export full results to CSV
rca_data.to_csv('us_rca_analysis_results.csv', index=False)
print("\nFull RCA analysis exported to us_rca_analysis_results.csv")
```

The NRCA transformation facilitates regression analysis and time-series tracking of comparative advantage evolution. Values near +1 indicate strong comparative advantage, values near 0 indicate neutrality, and values near -1 indicate strong comparative disadvantage.

### Exercise 1.2: Gravity Model Estimation with Multilateral Resistance

The gravity equation stands as the workhorse empirical model of international trade, explaining bilateral trade flows through an analogy to Newtonian physics: trade between two countries increases with their economic masses (GDPs) and decreases with the distance between them. The structural gravity framework, formalized by Anderson and van Wincoop (2003), introduces multilateral resistance terms that capture each country's remoteness from all trading partners. Proper estimation requires controlling for these inward and outward multilateral resistance terms through exporter and importer fixed effects, while addressing the prevalence of zero trade flows through Poisson pseudo-maximum likelihood (PPML) rather than log-linearized OLS.

Begin by downloading the CEPII gravity dataset, which provides pre-computed bilateral distance measures, contiguity indicators, common language variables, and colonial relationship flags. Visit `http://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele.asp?id=8` and download the GeoDist dataset in CSV format, saving as `dist_cepii.csv`. This file contains `iso_o` (origin country), `iso_d` (destination country), `dist` (population-weighted distance in kilometers), `contig` (contiguity dummy), `comlang_off` (common official language), and `colony` (colonial relationship).

Next, obtain bilateral trade flow data from UN Comtrade. Download total merchandise trade (all SITC categories aggregated) for a cross-section year (2019 recommended for pre-pandemic patterns) with all reporter-partner pairs. Save as `bilateral_trade_2019.csv` with columns `reporter_iso`, `partner_iso`, and `trade_value_usd`.

Download GDP data from the World Bank World Development Indicators or Penn World Tables. You need current USD GDP for all countries in your trade dataset for the same year. Save as `gdp_2019.csv` with columns `iso3`, `gdp_usd`.

Create a new Python script `gravity_estimation.py` and begin data preparation:

```python
import pandas as pd
import numpy as np
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.iolib.summary2 import summary_col
import matplotlib.pyplot as plt

# Load datasets
gravity = pd.read_csv('dist_cepii.csv')
trade = pd.read_csv('bilateral_trade_2019.csv')
gdp = pd.read_csv('gdp_2019.csv')

# Rename columns for consistency
trade.columns = ['iso_o', 'iso_d', 'trade_value']
gdp.columns = ['iso3', 'gdp']

# Merge GDP data for origin and destination
trade = trade.merge(gdp.rename(columns={'iso3': 'iso_o', 'gdp': 'gdp_o'}), 
                    on='iso_o', how='left')
trade = trade.merge(gdp.rename(columns={'iso3': 'iso_d', 'gdp': 'gdp_d'}), 
                    on='iso_d', how='left')

# Merge with gravity variables
full_data = trade.merge(gravity[['iso_o', 'iso_d', 'dist', 'contig', 
                                  'comlang_off', 'colony']], 
                        on=['iso_o', 'iso_d'], how='left')

# Drop missing observations
full_data = full_data.dropna()

# Create log-transformed variables for traditional gravity
full_data['ln_trade'] = np.log(full_data['trade_value'] + 1)
full_data['ln_dist'] = np.log(full_data['dist'])
full_data['ln_gdp_o'] = np.log(full_data['gdp_o'])
full_data['ln_gdp_d'] = np.log(full_data['gdp_d'])

print(f"Sample size: {len(full_data)} country pairs")
print(f"Zero trade flows: {(full_data['trade_value'] == 0).sum()} observations")
print("\nSummary Statistics:")
print(full_data[['trade_value', 'dist', 'gdp_o', 'gdp_d']].describe())
```

The traditional approach estimates gravity via OLS on log-linearized variables, but this method suffers from two critical failures. First, log-transformation drops zero trade flows, which comprise 40-50% of observations in typical bilateral datasets and are economically meaningful (high trade costs preventing any exchange). Second, Jensen's inequality implies that $E[\ln Y] \neq \ln E[Y]$, creating bias in elasticity estimates when the error term is heteroskedastic—which bilateral trade residuals always are.

Estimate the naive OLS gravity model to document these problems:

```python
# Naive OLS gravity estimation (log-linearized)
ols_formula = 'ln_trade ~ ln_gdp_o + ln_gdp_d + ln_dist + contig + comlang_off + colony'
ols_model = smf.ols(ols_formula, data=full_data[full_data['trade_value'] > 0]).fit()

print("\nNaive OLS Gravity Estimation:")
print(ols_model.summary())
```

The OLS distance elasticity typically emerges around -1.0 to -1.2, implying that doubling distance reduces trade by approximately 50-60%. However, this estimate conflates true trade cost effects with sample selection bias from dropping zero flows.

Now implement the theoretically consistent PPML estimator, which handles zeros naturally and provides unbiased elasticity estimates under heteroskedasticity. The PPML specification models trade value in levels (not logs) using a Poisson likelihood function, while including exporter and importer fixed effects to absorb multilateral resistance terms:

```python
# PPML gravity estimation with fixed effects
ppml_formula = 'trade_value ~ ln_dist + contig + comlang_off + colony + C(iso_o) + C(iso_d) - 1'

# Estimate PPML using GLM with Poisson family
ppml_model = smf.glm(ppml_formula, 
                     data=full_data,
                     family=sm.families.Poisson()).fit(cov_type='HC0')

print("\nPPML Gravity Estimation with Fixed Effects:")
print(ppml_model.summary())

# Extract key elasticities
dist_elasticity = ppml_model.params['ln_dist']
contig_effect = np.exp(ppml_model.params['contig']) - 1
comlang_effect = np.exp(ppml_model.params['comlang_off']) - 1
colony_effect = np.exp(ppml_model.params['colony']) - 1

print(f"\nKey Trade Elasticities:")
print(f"Distance elasticity: {dist_elasticity:.3f}")
print(f"Contiguity effect: {contig_effect:.1%} increase in trade")
print(f"Common language effect: {comlang_effect:.1%} increase in trade")
print(f"Colonial relationship effect: {colony_effect:.1%} increase in trade")
```

The PPML distance elasticity typically falls between -0.8 and -1.1, more negative than OLS because it properly accounts for zero flows representing prohibitively high trade costs. The exponentiated coefficients on dummy variables give proportional trade effects: contiguity typically raises trade by 30-50%, common official language by 40-70%, and colonial relationships by 80-150%. These magnitudes quantify the border effect puzzle—national borders impose implicit trade costs equivalent to thousands of kilometers of distance.

The fixed effects $\alpha_i$ (exporter) and $\beta_j$ (importer) absorbed by the categorical variables represent structural outward and inward multilateral resistance indices. Countries with high outward multilateral resistance are remote from major markets; countries with high inward multilateral resistance face high average trade barriers. Extract and visualize these fixed effects:

```python
# Extract fixed effects as measures of multilateral resistance
fe_params = ppml_model.params
exporter_fe = {k.replace('C(iso_o)[', '').replace(']', ''): v 
               for k, v in fe_params.items() if 'iso_o' in k}
importer_fe = {k.replace('C(iso_d)[', '').replace(']', ''): v 
               for k, v in fe_params.items() if 'iso_d' in k}

# Convert to DataFrames
exp_fe_df = pd.DataFrame(list(exporter_fe.items()), 
                         columns=['country', 'exporter_fe']).sort_values('exporter_fe', ascending=False)
imp_fe_df = pd.DataFrame(list(importer_fe.items()), 
                         columns=['country', 'importer_fe']).sort_values('importer_fe', ascending=False)

print("\nTop 10 Exporter Fixed Effects (Lowest Outward Multilateral Resistance):")
print(exp_fe_df.head(10))

print("\nTop 10 Importer Fixed Effects (Lowest Inward Multilateral Resistance):")
print(imp_fe_df.head(10))

# Export fixed effects
exp_fe_df.to_csv('exporter_fixed_effects.csv', index=False)
imp_fe_df.to_csv('importer_fixed_effects.csv', index=False)
```

High exporter fixed effects indicate countries positioned near large markets with low average trade barriers—typically Western European nations like Germany, Netherlands, and Belgium. High importer fixed effects reflect strong import demand and low tariff barriers—generally large developed economies like the United States, China, and Japan.

Compare PPML and OLS coefficient estimates directly to quantify the bias from ignoring zeros and heteroskedasticity:

```python
# Estimate PPML without fixed effects for direct comparison to OLS
ppml_no_fe_formula = 'trade_value ~ ln_gdp_o + ln_gdp_d + ln_dist + contig + comlang_off + colony'
ppml_no_fe = smf.glm(ppml_no_fe_formula,
                     data=full_data,
                     family=sm.families.Poisson()).fit(cov_type='HC0')

# Create comparison table
comparison = pd.DataFrame({
    'OLS (log)': ols_model.params[['ln_gdp_o', 'ln_gdp_d', 'ln_dist', 'contig', 'comlang_off', 'colony']],
    'PPML (no FE)': ppml_no_fe.params[['ln_gdp_o', 'ln_gdp_d', 'ln_dist', 'contig', 'comlang_off', 'colony']],
    'PPML (with FE)': ppml_model.params[['ln_dist', 'contig', 'comlang_off', 'colony']]
})

print("\nEstimator Comparison:")
print(comparison)
```

The PPML specification with fixed effects represents best practice for gravity estimation. The distance elasticity serves as the key parameter for simulating trade policy counterfactuals: a 10% increase in trade costs (tariffs, transport costs, regulatory barriers) reduces trade volume by approximately $|\beta_{dist}| \times 10\%$, typically 8-11%. This elasticity anchors all subsequent welfare calculations.

### Exercise 1.3: Effective Rate of Protection and Tariff Escalation Analysis

Nominal tariff rates misrepresent the true protective effect on domestic value-added when imported intermediate inputs also face tariffs. The effective rate of protection (ERP) measures the percentage increase in domestic value-added per unit output enabled by the tariff structure, accounting for both output tariffs (which protect) and input tariffs (which penalize domestic producers). Tariff escalation—the pattern of rising tariff rates as goods move from raw materials to intermediate inputs to final products—amplifies effective protection on downstream manufacturing, creating incentives for developing countries to remain trapped in primary commodity exports.

The ERP formula quantifies this distortion:

$$\text{ERP}_j = \frac{t_j - \sum_i a_{ij} t_i}{1 - \sum_i a_{ij}}$$

where $t_j$ represents the nominal tariff on final good $j$, $a_{ij}$ denotes the technical coefficient (value of input $i$ per unit value of output $j$ at free trade prices), and $t_i$ gives the tariff on input $i$. The denominator $1 - \sum_i a_{ij}$ represents the value-added coefficient—domestic value-added as a share of gross output. When $\text{ERP}_j > t_j$, tariff escalation grants more protection to domestic value-added than the nominal tariff suggests. When $\text{ERP}_j < t_j$, input tariffs erode protection. Negative ERP values indicate that input tariffs harm domestic producers more than output tariffs help them.

Download tariff schedule data from the WITS (World Integrated Trade Solution) database at `https://wits.worldbank.org/`. Select a country (United States recommended), year 2019, "Simple Average" tariff type, and "HS 6-digit" product classification. Export the tariff data as `us_tariff_schedule_2019.csv` with columns `hs6`, `product_description`, and `tariff_rate` (in percentage points).

Download an input-output table for the same country from the OECD ICIO database or national statistical agency. The US Bureau of Economic Analysis provides detailed Use tables showing intermediate input requirements by industry. For this exercise, use a simplified concordance mapping HS6 products to IO sectors. Create `io_coefficients.csv` with columns `output_hs6`, `input_hs6`, and `technical_coefficient` (input value per dollar of output).

Create a new Python script `effective_protection.py`:

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Load tariff schedule
tariffs = pd.read_csv('us_tariff_schedule_2019.csv')
tariffs.columns = ['hs6', 'description', 'tariff_rate']
tariffs['tariff_rate'] = tariffs['tariff_rate'] / 100  # Convert to decimal

# Load input-output technical coefficients
io_table = pd.read_csv('io_coefficients.csv')
io_table.columns = ['output_hs6', 'input_hs6', 'tech_coef']

print(f"Tariff lines: {len(tariffs)}")
print(f"IO relationships: {len(io_table)}")
print("\nTariff rate distribution:")
print(tariffs['tariff_rate'].describe())
```

Compute the effective rate of protection for each output product by summing weighted input tariffs and applying the ERP formula:

```python
# Merge input tariffs into IO table
io_with_tariffs = io_table.merge(
    tariffs[['hs6', 'tariff_rate']].rename(columns={'hs6': 'input_hs6', 'tariff_rate': 'input_tariff'}),
    on='input_hs6',
    how='left'
).fillna({'input_tariff': 0})

# Calculate weighted input tariff for each output
input_tariff_sum = io_with_tariffs.groupby('output_hs6').apply(
    lambda x: (x['tech_coef'] * x['input_tariff']).sum()
).reset_index(name='weighted_input_tariff')

# Calculate value-added coefficient (1 - sum of technical coefficients)
va_coef = io_table.groupby('output_hs6')['tech_coef'].sum().reset_index(name='input_coef_sum')
va_coef['va_coefficient'] = 1 - va_coef['input_coef_sum']

# Merge output tariffs
erp_data = tariffs[['hs6', 'description', 'tariff_rate']].rename(columns={'hs6': 'output_hs6', 'tariff_rate': 'output_tariff'})
erp_data = erp_data.merge(input_tariff_sum, on='output_hs6', how='left').fillna({'weighted_input_tariff': 0})
erp_data = erp_data.merge(va_coef, on='output_hs6', how='left')

# Calculate ERP
erp_data['erp'] = (erp_data['output_tariff'] - erp_data['weighted_input_tariff']) / erp_data['va_coefficient']
erp_data['erp_percentage'] = erp_data['erp'] * 100

# Calculate tariff escalation indicator
erp_data['escalation'] = erp_data['erp'] - erp_data['output_tariff']

print("\nEffective Rate of Protection Summary:")
print(erp_data[['output_tariff', 'erp', 'escalation']].describe())

print("\nProducts with Highest ERP:")
print(erp_data.nlargest(10, 'erp')[['output_hs6', 'description', 'output_tariff', 'erp_percentage']])

print("\nProducts with Negative ERP (Anti-Protection):")
print(erp_data.nsmallest(10, 'erp')[['output_hs6', 'description', 'output_tariff', 'erp_percentage']])
```

Products exhibiting high ERP relative to nominal tariffs reveal tariff escalation: raw materials enter duty-free or at low rates, while finished goods face higher tariffs, magnifying protection on domestic processing activities. Negative ERP values occur when input tariffs exceed output tariffs, penalizing domestic producers who compete against duty-free imports of final goods while paying tariffs on imported components.

Visualize the relationship between nominal tariffs and effective protection to identify escalation patterns:

```python
# Scatter plot: Nominal vs Effective Protection
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Panel A: ERP vs Nominal Tariff
axes[0].scatter(erp_data['output_tariff'] * 100, erp_data['erp_percentage'], 
                alpha=0.5, s=20)
axes[0].plot([0, erp_data['output_tariff'].max() * 100], 
             [0, erp_data['output_tariff'].max() * 100], 
             'r--', label='ERP = Nominal (No Escalation)')
axes[0].axhline(y=0, color='k', linestyle='-', linewidth=0.5)
axes[0].set_xlabel('Nominal Tariff Rate (%)')
axes[0].set_ylabel('Effective Rate of Protection (%)')
axes[0].set_title('Tariff Escalation: ERP vs Nominal Tariff')
axes[0].legend()
axes[0].grid(True, alpha=0.3)

# Panel B: Distribution of Escalation Margin
axes[1].hist(erp_data['escalation'] * 100, bins=50, edgecolor='black', alpha=0.7)
axes[1].axvline(x=0, color='r', linestyle='--', label='No Escalation')
axes[1].set_xlabel('Escalation Margin: ERP - Nominal Tariff (percentage points)')
axes[1].set_ylabel('Frequency')
axes[1].set_title('Distribution of Tariff Escalation')
axes[1].legend()
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('tariff_escalation_analysis.png', dpi=300)
plt.close()

# Export full ERP results
erp_data.to_csv('effective_protection_rates.csv', index=False)
print("\nERP analysis exported to effective_protection_rates.csv")
```

Points above the 45-degree line indicate tariff escalation (ERP exceeds nominal tariff); points below indicate anti-protection (input tariffs erode output protection). The escalation margin histogram reveals the distribution of distortions: a right-skewed distribution with positive median confirms systematic escalation favoring downstream manufacturing.

Aggregate ERP by broad product categories (raw materials, intermediate goods, final consumer goods) to quantify escalation across the production chain:

```python
# Create product stage classifications
# First digit of HS code roughly indicates processing stage
erp_data['hs2'] = erp_data['output_hs6'].astype(str).str[:2]

# Define stage mapping (simplified classification)
raw_materials = [str(i).zfill(2) for i in range(1, 15)]  # Chapters 1-14
intermediates = [str(i).zfill(2) for i in range(15, 50)]  # Chapters 15-49
final_goods = [str(i).zfill(2) for i in range(50, 100)]  # Chapters 50-99

def classify_stage(hs2):
    if hs2 in raw_materials:
        return 'Raw Materials'
    elif hs2 in intermediates:
        return 'Intermediate Goods'
    else:
        return 'Final Goods'

erp_data['product_stage'] = erp_data['hs2'].apply(classify_stage)

# Calculate mean tariffs and ERP by stage
stage_summary = erp_data.groupby('product_stage').agg({
    'output_tariff': 'mean',
    'erp': 'mean',
    'escalation': 'mean'
}).reset_index()

stage_summary['output_tariff_pct'] = stage_summary['output_tariff'] * 100
stage_summary['erp_pct'] = stage_summary['erp'] * 100
stage_summary['escalation_pct'] = stage_summary['escalation'] * 100

print("\nTariff Escalation by Product Stage:")
print(stage_summary[['product_stage', 'output_tariff_pct', 'erp_pct', 'escalation_pct']])

# Visualize escalation across production chain
fig, ax = plt.subplots(figsize=(10, 6))
x = np.arange(len(stage_summary))
width = 0.35

bars1 = ax.bar(x - width/2, stage_summary['output_tariff_pct'], width, 
               label='Nominal Tariff', alpha=0.8)
bars2 = ax.bar(x + width/2, stage_summary['erp_pct'], width, 
               label='Effective Rate of Protection', alpha=0.8)

ax.set_xlabel('Production Stage')
ax.set_ylabel('Tariff Rate (%)')
ax.set_title('Tariff Escalation Across Production Chain')
ax.set_xticks(x)
ax.set_xticklabels(stage_summary['product_stage'])
ax.legend()
ax.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('tariff_escalation_by_stage.png', dpi=300)
plt.close()
```

The systematic rise in ERP from raw materials through intermediates to final goods confirms tariff escalation, which protects domestic manufacturing value-added more than nominal tariffs suggest. This structure discourages developing-country industrialization by penalizing domestic processing of commodities while allowing duty-free import of raw materials by developed-country manufacturers. The welfare cost includes both static deadweight loss from resource misallocation and dynamic efficiency loss from blocking comparative advantage evolution.

## Exercise 2: Parameter Variation & Empirical Analysis

### Exercise 2.1: Trade Elasticity Sensitivity and Welfare Cost Simulation

The elasticity of trade with respect to trade costs—measured as the distance coefficient in gravity estimation or calibrated from tariff-trade correlations—determines the magnitude of welfare losses from protectionist policies. A higher elasticity (more negative distance coefficient) implies greater substitutability between domestic and foreign goods, meaning tariffs induce larger trade volume reductions and smaller terms-of-trade gains for the imposing country. This exercise operationalizes elasticity variation through Monte Carlo simulation of tariff shocks, computing deadweight loss triangles and real income changes under different elasticity assumptions.

Begin with the partial equilibrium welfare analysis framework for a small country imposing an import tariff. The deadweight loss (DWL) from a tariff $t$ on imports equals:

$$\text{DWL} = \frac{1}{2} t^2 M \left( \epsilon_s^* + |\epsilon_d| \right)$$

where $M$ represents initial import volume, $\epsilon_s^*$ denotes foreign export supply elasticity, and $\epsilon_d$ gives domestic import demand elasticity. For a small country facing perfectly elastic world supply ($\epsilon_s^* \to \infty$), the formula simplifies to $\text{DWL} = \frac{1}{2} t^2 M |\epsilon_d|$. The import demand elasticity $\epsilon_d$ relates directly to the trade cost elasticity from gravity estimation: $\epsilon_d \approx \beta_{dist}$, the distance coefficient.

Create a new Python script `tariff_welfare_simulation.py` and define the welfare calculation functions:

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

# Welfare analysis parameters
np.random.seed(42)

# Base scenario parameters
initial_imports = 500e9  # $500 billion initial imports
tariff_rates = np.linspace(0, 0.25, 50)  # Tariff range from 0% to 25%

# Elasticity parameter distributions (based on gravity literature)
elasticity_mean = -1.0
elasticity_std = 0.15

# Foreign supply elasticity scenarios
supply_elasticity_small_country = 999  # Approximates infinity (perfectly elastic)
supply_elasticity_large_country = 5.0  # Large country faces upward-sloping supply

def calculate_dwl(tariff, imports, demand_elasticity, supply_elasticity):
    """
    Calculate deadweight loss from tariff imposition.
    
    Parameters:
    -----------
    tariff : float
        Ad valorem tariff rate (e.g., 0.25 for 25%)
    imports : float
        Initial import value in dollars
    demand_elasticity : float
        Import demand elasticity (negative)
    supply_elasticity : float
        Foreign export supply elasticity (positive)
    
    Returns:
    --------
    dwl : float
        Deadweight loss in dollars
    """
    elasticity_sum = supply_elasticity + abs(demand_elasticity)
    dwl = 0.5 * (tariff ** 2) * imports * elasticity_sum
    return dwl

def calculate_terms_of_trade_gain(tariff, imports, supply_elasticity):
    """
    Calculate terms-of-trade gain for large country imposing tariff.
    Large country tariff reduces world price, improving terms of trade.
    
    TOT gain = t * M * (1 / (1 + supply_elasticity / |demand_elasticity|))
    
    For simplicity, approximate as: t * M * (supply_elasticity / (supply_elasticity + |demand_elasticity|))
    """
    # This is positive for large country, zero for small country
    if supply_elasticity > 100:  # Small country approximation
        return 0
    else:
        # Simplified TOT effect (world price reduction)
        price_reduction_share = 1 / (1 + supply_elasticity)
        tot_gain = tariff * imports * price_reduction_share
        return tot_gain

def calculate_net_welfare_change(tariff, imports, demand_elasticity, supply_elasticity):
    """
    Net welfare change = TOT gain - DWL - Production/Consumption distortions
    """
    dwl = calculate_dwl(tariff, imports, demand_elasticity, supply_elasticity)
    tot_gain = calculate_terms_of_trade_gain(tariff, imports, supply_elasticity)
    net_welfare = tot_gain - dwl
    return net_welfare, dwl, tot_gain

# Compute base case (small country scenario)
print("SMALL COUNTRY TARIFF ANALYSIS")
print("=" * 60)

base_elasticity = -1.0
dwl_base = []
for t in tariff_rates:
    dwl = calculate_dwl(t, initial_imports, base_elasticity, supply_elasticity_small_country)
    dwl_base.append(dwl)

dwl_base = np.array(dwl_base)

print(f"\nBase elasticity: {base_elasticity}")
print(f"Initial imports: ${initial_imports/1e9:.0f} billion")
print(f"\nDeadweight Loss at Selected Tariff Rates:")
for i, t in enumerate([0.05, 0.10, 0.15, 0.20, 0.25]):
    idx = np.argmin(np.abs(tariff_rates - t))
    print(f"  {t*100:.0f}% tariff: ${dwl_base[idx]/1e9:.2f} billion ({dwl_base[idx]/initial_imports*100:.2f}% of imports)")
```

This establishes baseline deadweight losses under the standard assumption of a small country facing infinitely elastic world supply. A 10% tariff generates DWL of approximately 0.5% of import value when the demand elasticity equals -1.0; a 25% tariff produces DWL around 3.1% of imports. These losses increase quadratically with the tariff rate due to the $t^2$ term.

Now conduct sensitivity analysis across the range of empirically plausible demand elasticities:

```python
# Elasticity sensitivity analysis
elasticity_range = np.linspace(-1.5, -0.5, 6)
dwl_by_elasticity = {}

print("\n\nELASTICITY SENSITIVITY ANALYSIS")
print("=" * 60)

for elast in elasticity_range:
    dwl_series = []
    for t in tariff_rates:
        dwl = calculate_dwl(t, initial_imports, elast, supply_elasticity_small_country)
        dwl_series.append(dwl)
    dwl_by_elasticity[elast] = np.array(dwl_series)
    
    # Report DWL at 10% and 20% tariffs
    idx_10 = np.argmin(np.abs(tariff_rates - 0.10))
    idx_20 = np.argmin(np.abs(tariff_rates - 0.20))
    print(f"\nElasticity = {elast:.2f}:")
    print(f"  DWL at 10% tariff: ${dwl_series[idx_10]/1e9:.2f} billion")
    print(f"  DWL at 20% tariff: ${dwl_series[idx_20]/1e9:.2f} billion")

# Visualize elasticity sensitivity
fig, ax = plt.subplots(figsize=(10, 6))

for elast, dwl_series in dwl_by_elasticity.items():
    ax.plot(tariff_rates * 100, dwl_series / 1e9, 
            label=f'ε = {elast:.2f}', linewidth=2)

ax.set_xlabel('Tariff Rate (%)')
ax.set_ylabel('Deadweight Loss ($ Billions)')
ax.set_title('Tariff Deadweight Loss: Elasticity Sensitivity Analysis')
ax.legend(title='Demand Elasticity')
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('dwl_elasticity_sensitivity.png', dpi=300)
plt.close()

print("\nElasticity sensitivity chart saved to dwl_elasticity_sensitivity.png")
```

The elasticity sensitivity reveals that welfare costs vary substantially with substitutability. When demand elasticity equals -1.5 (high substitutability), a 20% tariff generates DWL of approximately $15 billion; when elasticity equals -0.5 (low substitutability), the same tariff produces only $5 billion in losses. Gravity model estimation uncertainty around the distance coefficient therefore translates directly into welfare calculation uncertainty.

Extend the analysis to the large country case, where tariff imposition reduces world prices and generates terms-of-trade gains that partially offset deadweight losses:

```python
# Large country analysis
print("\n\nLARGE COUNTRY TARIFF ANALYSIS")
print("=" * 60)

demand_elast = -1.0
supply_elast = supply_elasticity_large_country

net_welfare = []
dwl_large = []
tot_gains = []

for t in tariff_rates:
    nw, dwl, tot = calculate_net_welfare_change(t, initial_imports, demand_elast, supply_elast)
    net_welfare.append(nw)
    dwl_large.append(dwl)
    tot_gains.append(tot)

net_welfare = np.array(net_welfare)
dwl_large = np.array(dwl_large)
tot_gains = np.array(tot_gains)

# Find optimal tariff (maximizes net welfare)
optimal_idx = np.argmax(net_welfare)
optimal_tariff = tariff_rates[optimal_idx]

print(f"\nLarge country foreign supply elasticity: {supply_elast}")
print(f"Optimal tariff rate: {optimal_tariff*100:.1f}%")
print(f"Net welfare gain at optimal tariff: ${net_welfare[optimal_idx]/1e9:.2f} billion")

print(f"\nWelfare Decomposition at Selected Tariff Rates:")
for i, t in enumerate([0.05, 0.10, 0.15, 0.20, 0.25]):
    idx = np.argmin(np.abs(tariff_rates - t))
    print(f"\n  {t*100:.0f}% tariff:")
    print(f"    TOT gain: ${tot_gains[idx]/1e9:.2f} billion")
    print(f"    Deadweight loss: ${dwl_large[idx]/1e9:.2f} billion")
    print(f"    Net welfare change: ${net_welfare[idx]/1e9:.2f} billion")

# Visualize large country welfare decomposition
fig, ax = plt.subplots(figsize=(10, 6))

ax.plot(tariff_rates * 100, tot_gains / 1e9, 
        label='Terms-of-Trade Gain', linewidth=2)
ax.plot(tariff_rates * 100, dwl_large / 1e9, 
        label='Deadweight Loss', linewidth=2, linestyle='--')
ax.plot(tariff_rates * 100, net_welfare / 1e9, 
        label='Net Welfare Change', linewidth=2.5, color='black')
ax.axhline(y=0, color='gray', linestyle='-', linewidth=0.8)
ax.axvline(x=optimal_tariff * 100, color='red', linestyle=':', 
           linewidth=1.5, label=f'Optimal Tariff ({optimal_tariff*100:.1f}%)')

ax.set_xlabel('Tariff Rate (%)')
ax.set_ylabel('Welfare Change ($ Billions)')
ax.set_title('Large Country Tariff: Welfare Decomposition')
ax.legend()
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('large_country_welfare_decomposition.png', dpi=300)
plt.close()

print("\nLarge country welfare chart saved to large_country_welfare_decomposition.png")
```

The large country faces an optimal tariff where marginal terms-of-trade gains equal marginal deadweight losses. This optimal rate typically falls between 5% and 15% depending on supply elasticity—low enough to avoid excessive distortions but high enough to exploit market power. However, foreign retaliation eliminates these gains in practice, leading to mutual tariff escalation that harms all parties. The Nash equilibrium of reciprocal optimal tariffs leaves every country worse off than free trade, demonstrating the classic prisoners' dilemma structure of trade policy.

Complete the sensitivity analysis with Monte Carlo simulation over joint uncertainty in demand and supply elasticities:

```python
# Monte Carlo simulation: joint elasticity uncertainty
print("\n\nMONTE CARLO SIMULATION: JOINT ELASTICITY UNCERTAINTY")
print("=" * 60)

n_simulations = 10000
tariff_shock = 0.20  # Simulate 20% tariff

# Draw elasticity parameters from distributions
demand_elast_draws = np.random.normal(elasticity_mean, elasticity_std, n_simulations)
supply_elast_draws = np.random.uniform(3, 8, n_simulations)  # Large country supply elasticity range

dwl_distribution = []
net_welfare_distribution = []

for i in range(n_simulations):
    demand_e = demand_elast_draws[i]
    supply_e = supply_elast_draws[i]
    
    nw, dwl, tot = calculate_net_welfare_change(tariff_shock, initial_imports, 
                                                demand_e, supply_e)
    dwl_distribution.append(dwl)
    net_welfare_distribution.append(nw)

dwl_distribution = np.array(dwl_distribution)
net_welfare_distribution = np.array(net_welfare_distribution)

# Calculate confidence intervals
dwl_mean = np.mean(dwl_distribution)
dwl_ci_lower = np.percentile(dwl_distribution, 2.5)
dwl_ci_upper = np.percentile(dwl_distribution, 97.5)

nw_mean = np.mean(net_welfare_distribution)
nw_ci_lower = np.percentile(net_welfare_distribution, 2.5)
nw_ci_upper = np.percentile(net_welfare_distribution, 97.5)

print(f"\n{tariff_shock*100:.0f}% Tariff Shock - Monte Carlo Results ({n_simulations:,} simulations):")
print(f"\nDeadweight Loss:")
print(f"  Mean: ${dwl_mean/1e9:.2f} billion")
print(f"  95% CI: [${dwl_ci_lower/1e9:.2f}, ${dwl_ci_upper/1e9:.2f}] billion")
print(f"  Standard deviation: ${np.std(dwl_distribution)/1e9:.2f} billion")

print(f"\nNet Welfare Change (Large Country):")
print(f"  Mean: ${nw_mean/1e9:.2f} billion")
print(f"  95% CI: [${nw_ci_lower/1e9:.2f}, ${nw_ci_upper/1e9:.2f}] billion")
print(f"  Probability of net welfare gain: {(net_welfare_distribution > 0).mean()*100:.1f}%")

# Visualize distributions
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

axes[0].hist(dwl_distribution / 1e9, bins=50, edgecolor='black', alpha=0.7)
axes[0].axvline(dwl_mean / 1e9, color='red', linestyle='--', 
                linewidth=2, label=f'Mean: ${dwl_mean/1e9:.2f}B')
axes[0].axvline(dwl_ci_lower / 1e9, color='orange', linestyle=':', 
                linewidth=1.5, label=f'95% CI')
axes[0].axvline(dwl_ci_upper / 1e9, color='orange', linestyle=':', linewidth=1.5)
axes[0].set_xlabel('Deadweight Loss ($ Billions)')
axes[0].set_ylabel('Frequency')
axes[0].set_title(f'DWL Distribution: {tariff_shock*100:.0f}% Tariff')
axes[0].legend()
axes[0].grid(True, alpha=0.3)

axes[1].hist(net_welfare_distribution / 1e9, bins=50, edgecolor='black', alpha=0.7)
axes[1].axvline(nw_mean / 1e9, color='red', linestyle='--', 
                linewidth=2, label=f'Mean: ${nw_mean/1e9:.2f}B')
axes[1].axvline(0, color='black', linestyle='-', linewidth=1)
axes[1].set_xlabel('Net Welfare Change ($ Billions)')
axes[1].set_ylabel('Frequency')
axes[1].set_title('Net Welfare Distribution (Large Country)')
axes[1].legend()
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('monte_carlo_welfare_distributions.png', dpi=300)
plt.close()

# Export simulation results
simulation_results = pd.DataFrame({
    'demand_elasticity': demand_elast_draws,
    'supply_elasticity': supply_elast_draws,
    'deadweight_loss': dwl_distribution,
    'net_welfare_change': net_welfare_distribution
})
simulation_results.to_csv('tariff_welfare_monte_carlo.csv', index=False)

print("\nMonte Carlo simulation results exported to tariff_welfare_monte_carlo.csv")
print("Distribution charts saved to monte_carlo_welfare_distributions.png")
```

The Monte Carlo simulation quantifies the uncertainty in welfare estimates arising from elasticity parameter uncertainty. For a 20% tariff, deadweight loss typically ranges from $8-15 billion with 95% confidence, while net welfare change (for a large country) spans from negative to positive values depending on the realized elasticity draw. This uncertainty underscores the importance of precise gravity model estimation: measurement error in the distance coefficient propagates directly into trade policy evaluation.

### Exercise 2.2: Exchange Rate Pass-Through and Import Price Dynamics

Exchange rate movements transmit to import prices through an incomplete pass-through channel: foreign exporters absorb part of the exchange rate change through markup adjustments rather than fully passing it to destination-currency prices. The degree of pass-through determines how exchange rate depreciation affects trade balances, inflation, and relative competitiveness. This exercise estimates pass-through elasticities from exchange rate and import price time series, then simulates the dynamic adjustment path following a currency shock.

The exchange rate pass-through elasticity $\phi$ measures the percentage change in import prices (in domestic currency) following a 1% exchange rate depreciation:

$$\phi = \frac{\partial \ln P_M}{\partial \ln E}$$

where $P_M$ denotes the import price index in domestic currency and $E$ represents the nominal exchange rate (domestic currency per foreign currency unit). Complete pass-through implies $\phi = 1$: a 10% depreciation raises import prices by 10%. Incomplete pass-through ($\phi < 1$) indicates pricing-to-market behavior where exporters compress markups to maintain market share.

Download monthly import price index data from the Bureau of Labor Statistics (BLS) at `https://www.bls.gov/mxp/`. Select "Import Price Index - All Commodities" series ID `EIUIR` and download in CSV format as `import_price_index.csv` with columns `date` and `import_price_index`.

Download nominal effective exchange rate data from the Federal Reserve H.10 statistical release or the BIS effective exchange rate database. Use the trade-weighted US dollar index (broad), available at FRED with series ID `DTWEXBGS`. Download as `exchange_rate_index.csv` with columns `date` and `exchange_rate_index`.

Create a new Python script `exchange_rate_passthrough.py`:

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf

# Load time series data
import_prices = pd.read_csv('import_price_index.csv', parse_dates=['date'])
exchange_rates = pd.read_csv('exchange_rate_index.csv', parse_dates=['date'])

# Merge datasets
df = import_prices.merge(exchange_rates, on='date', how='inner')
df = df.sort_values('date').reset_index(drop=True)

# Create log-transformed series
df['ln_import_price'] = np.log(df['import_price_index'])
df['ln_exchange_rate'] = np.log(df['exchange_rate_index'])

# Calculate log changes (month-over-month)
df['d_ln_import_price'] = df['ln_import_price'].diff()
df['d_ln_exchange_rate'] = df['ln_exchange_rate'].diff()

# Drop missing values
df = df.dropna()

print(f"Sample period: {df['date'].min()} to {df['date'].max()}")
print(f"Number of observations: {len(df)}")
print("\nSummary Statistics:")
print(df[['import_price_index', 'exchange_rate_index']].describe())
```

Test for stationarity in the level and differenced series using the Augmented Dickey-Fuller test. Exchange rates and import prices typically exhibit unit roots in levels but are stationary in first differences:

```python
# Stationarity tests
def adf_test(series, series_name):
    """Perform Augmented Dickey-Fuller test for unit root."""
    result = adfuller(series.dropna(), autolag='AIC')
    print(f"\n{series_name}:")
    print(f"  ADF Statistic: {result[0]:.4f}")
    print(f"  p-value: {result[1]:.4f}")
    print(f"  Critical Values: {result[4]}")
    if result[1] < 0.05:
        print(f"  → Reject unit root (stationary at 5% level)")
    else:
        print(f"  → Cannot reject unit root (non-stationary)")
    return result

print("\nSTATIONARITY TESTS (Augmented Dickey-Fuller)")
print("=" * 60)

adf_test(df['ln_import_price'], 'Log Import Price (Level)')
adf_test(df['ln_exchange_rate'], 'Log Exchange Rate (Level)')
adf_test(df['d_ln_import_price'], 'Log Import Price (First Difference)')
adf_test(df['d_ln_exchange_rate'], 'Log Exchange Rate (First Difference)')
```

The level series typically fail to reject the unit root null hypothesis, confirming non-stationarity. The differenced series reject the null, confirming stationarity. This justifies estimation in first differences (growth rates) to avoid spurious regression.

Estimate the contemporaneous pass-through elasticity via OLS regression of import price changes on exchange rate changes:

```python
# Contemporaneous pass-through regression
print("\n\nCONTEMPORANEOUS PASS-THROUGH ESTIMATION")
print("=" * 60)

X = sm.add_constant(df['d_ln_exchange_rate'])
y = df['d_ln_import_price']

model_contemp = sm.OLS(y, X).fit(cov_type='HAC', cov_kwds={'maxlags': 6})

print(model_contemp.summary())

phi_contemp = model_contemp.params['d_ln_exchange_rate']
phi_se = model_contemp.bse['d_ln_exchange_rate']

print(f"\nContemporaneous Pass-Through Elasticity: {phi_contemp:.3f}")
print(f"Standard Error: {phi_se:.3f}")
print(f"95% Confidence Interval: [{phi_contemp - 1.96*phi_se:.3f}, {phi_contemp + 1.96*phi_se:.3f}]")

if phi_contemp < 1:
    print(f"\nIncomplete pass-through detected ({phi_contemp*100:.1f}% of exchange rate changes)")
    print(f"Exporters absorb {(1-phi_contemp)*100:.1f}% through markup adjustment")
```

Typical estimates show contemporaneous pass-through around 0.3-0.5 for US imports: a 10% dollar depreciation raises import prices by only 3-5% within the same month. Foreign exporters absorb 50-70% of the exchange rate movement to maintain competitiveness in the US market.

Exchange rate effects accumulate over multiple periods as contracts adjust and inventories turn over. Estimate a distributed lag model to capture the full cumulative pass-through:

```python
# Distributed lag model: current and 6 lags of exchange rate changes
print("\n\nDISTRIBUTED LAG PASS-THROUGH ESTIMATION")
print("=" * 60)

max_lags = 6
lag_cols = ['d_ln_exchange_rate']

for lag in range(1, max_lags + 1):
    col_name = f'd_ln_exchange_rate_L{lag}'
    df[col_name] = df['d_ln_exchange_rate'].shift(lag)
    lag_cols.append(col_name)

# Drop missing from lags
df_lags = df.dropna()

X_lags = sm.add_constant(df_lags[lag_cols])
y_lags = df_lags['d_ln_import_price']

model_lags = sm.OLS(y_lags, X_lags).fit(cov_type='HAC', cov_kwds={'maxlags': 12})

print(model_lags.summary())

# Calculate cumulative pass-through
lag_coefficients = [model_lags.params[col] for col in lag_cols]
cumulative_passthrough = np.cumsum(lag_coefficients)

print(f"\nCumulative Pass-Through by Horizon:")
for i, cum_pt in enumerate(cumulative_passthrough):
    print(f"  {i} months: {cum_pt:.3f}")

print(f"\nTotal Long-Run Pass-Through: {cumulative_passthrough[-1]:.3f}")

# Visualize impulse response
fig, ax = plt.subplots(figsize=(10, 6))
horizons = np.arange(len(cumulative_passthrough))
ax.plot(horizons, cumulative_passthrough, marker='o', linewidth=2, markersize=6)
ax.axhline(y=1.0, color='red', linestyle='--', label='Complete Pass-Through')
ax.set_xlabel('Months After Exchange Rate Shock')
ax.set_ylabel('Cumulative Pass-Through Elasticity')
ax.set_title('Exchange Rate Pass-Through: Impulse Response Function')
ax.legend()
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('exchange_rate_passthrough_impulse_response.png', dpi=300)
plt.close()

print("\nImpulse response chart saved to exchange_rate_passthrough_impulse_response.png")
```

The cumulative pass-through increases over time as more contracts adjust, typically reaching 0.6-0.8 after six months. This implies that long-run pass-through exceeds short-run pass-through but remains incomplete even at a one-year horizon. The gradual adjustment reflects menu costs, customer relationships, and strategic pricing behavior.

Simulate a 10% dollar depreciation shock and project the dynamic path of import prices and the trade balance:

```python
# Dynamic simulation of depreciation shock
print("\n\nDYNAMIC SIMULATION: 10% DOLLAR DEPRECIATION")
print("=" * 60)

shock_size = 0.10  # 10% depreciation
simulation_periods = 12

# Initialize simulation vectors
import_price_response = np.zeros(simulation_periods)
trade_balance_response = np.zeros(simulation_periods)

# Assume trade balance improves when import prices rise (reduces import volume)
# Import demand elasticity approximately -0.5
import_demand_elasticity = -0.5

for t in range(simulation_periods):
    # Import price increases by cumulative pass-through up to lag t
    if t < len(cumulative_passthrough):
        import_price_response[t] = cumulative_passthrough[t] * shock_size
    else:
        import_price_response[t] = cumulative_passthrough[-1] * shock_size
    
    # Import volume declines by elasticity × price increase
    import_volume_change = import_demand_elasticity * import_price_response[t]
    
    # Trade balance improves (imports fall) but partially offset by higher import prices
    # Net effect = volume effect + price effect
    # Simplification: TB improvement ≈ -import_volume_change × initial_imports
    trade_balance_response[t] = -import_volume_change * initial_imports / 1e9  # In billions

print("\nDynamic Effects of 10% Dollar Depreciation:")
print(f"\n{'Month':<8}{'Import Price':<15}{'Trade Balance'}")
print(f"{'':8}{'Change (%)':<15}{'Improvement ($B)'}")
print("-" * 40)
for t in range(simulation_periods):
    print(f"{t:<8}{import_price_response[t]*100:>10.2f}     {trade_balance_response[t]:>10.2f}")

# Visualize dynamic adjustment
fig, axes = plt.subplots(2, 1, figsize=(10, 10))

axes[0].plot(range(simulation_periods), import_price_response * 100, 
             marker='o', linewidth=2, color='darkblue')
axes[0].axhline(y=shock_size * 100, color='red', linestyle='--', 
                label=f'{shock_size*100:.0f}% Depreciation (Full Pass-Through)')
axes[0].set_ylabel('Import Price Increase (%)')
axes[0].set_title('Import Price Response to 10% Dollar Depreciation')
axes[0].legend()
axes[0].grid(True, alpha=0.3)

axes[1].plot(range(simulation_periods), trade_balance_response, 
             marker='s', linewidth=2, color='darkgreen')
axes[1].axhline(y=0, color='black', linestyle='-', linewidth=0.8)
axes[1].set_xlabel('Months After Shock')
axes[1].set_ylabel('Trade Balance Improvement ($ Billions)')
axes[1].set_title('Trade Balance Adjustment Path')
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('depreciation_shock_simulation.png', dpi=300)
plt.close()

print("\nSimulation charts saved to depreciation_shock_simulation.png")
```

The J-curve pattern emerges naturally from incomplete and delayed pass-through. Import prices rise gradually over the first 6-12 months, reducing import volume through the demand elasticity channel. The trade balance initially worsens (not shown in this simplified model) as the price effect dominates, then improves as volume adjustment proceeds. This dynamic explains why currency depreciation fails to improve trade balances immediately—a critical consideration for macroeconomic policy evaluation.

## Exercise 3: Stress Testing, Boundary Failure & Recovery Protocol

### Exercise 3.1: Trade War Simulation and Equilibrium Retaliation Dynamics

Trade wars represent the boundary failure case where non-cooperative tariff setting destroys mutual gains from trade. When large countries simultaneously impose optimal tariffs to exploit terms-of-trade effects, each country's action provokes retaliation, leading to a Nash equilibrium with reciprocally high tariffs and lower welfare than the free trade baseline. This exercise simulates a two-country trade war using iterative best-response dynamics, quantifies the equilibrium welfare losses, and identifies conditions for Pareto-improving trade agreements.

The theoretical framework models two symmetric countries, Home and Foreign, each choosing tariff rates to maximize national welfare taking the other country's tariff as given. The welfare function incorporates consumer surplus, producer surplus, tariff revenue, and terms-of-trade effects. The best-response function $t_H^*(t_F)$ gives Home's optimal tariff conditional on Foreign's tariff $t_F$. The Nash equilibrium $(t_H^N, t_F^N)$ occurs where best-response functions intersect: each country's tariff is optimal given the other's.

Create a new Python script `trade_war_simulation.py` and define the welfare and best-response functions:

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import minimize_scalar, fsolve

# Model parameters (symmetric countries)
initial_trade_volume = 200e9  # $200 billion bilateral trade (each direction)
gdp_home = 20e12  # $20 trillion GDP
gdp_foreign = 20e12

# Elasticity parameters
import_demand_elasticity = -1.0
export_supply_elasticity = 5.0

# Welfare function components
def calculate_consumer_surplus_loss(tariff, trade_volume, demand_elasticity):
    """Consumer surplus loss from tariff-induced price increase."""
    # CS loss approximation: 0.5 * tariff^2 * M * |elasticity|
    cs_loss = 0.5 * (tariff ** 2) * trade_volume * abs(demand_elasticity)
    return cs_loss

def calculate_producer_surplus_gain(tariff, trade_volume, supply_elasticity):
    """Producer surplus gain from protection (import-competing sector)."""
    # PS gain from higher domestic prices
    ps_gain = 0.5 * (tariff ** 2) * trade_volume * supply_elasticity * 0.3  # Scale factor
    return ps_gain

def calculate_tariff_revenue(tariff, trade_volume, demand_elasticity):
    """Tariff revenue collected by government."""
    # Post-tariff import volume
    volume_after_tariff = trade_volume * (1 + demand_elasticity * tariff)
    revenue = tariff * trade_volume * volume_after_tariff / trade_volume  # Simplified
    return revenue

def calculate_terms_of_trade_gain(tariff_home, tariff_foreign, trade_volume, supply_elasticity):
    """Terms-of-trade improvement from tariff (large country effect)."""
    # Home tariff reduces world price of imports (Foreign's exports)
    # Benefit proportional to import volume and foreign supply elasticity
    price_reduction = tariff_home / (1 + supply_elasticity)
    tot_gain = price_reduction * trade_volume
    
    # Foreign's tariff worsens Home's terms of trade (on exports)
    price_reduction_exports = tariff_foreign / (1 + supply_elasticity)
    tot_loss = price_reduction_exports * trade_volume
    
    net_tot = tot_gain - tot_loss
    return net_tot

def national_welfare(tariff_home, tariff_foreign, trade_volume, 
                    demand_elast, supply_elast):
    """
    Calculate national welfare for Home country given both tariffs.
    
    Welfare = Consumer Surplus - Producer Surplus Loss + Tariff Revenue + TOT Gain - DWL
    Simplified to focus on key trade-offs.
    """
    # Deadweight loss
    dwl = 0.5 * (tariff_home ** 2) * trade_volume * (abs(demand_elast) + supply_elast)
    
    # Terms-of-trade gain
    tot_gain = calculate_terms_of_trade_gain(tariff_home, tariff_foreign, 
                                             trade_volume, supply_elast)
    
    # Tariff revenue
    post_tariff_volume = trade_volume * (1 + demand_elast * tariff_home)
    tariff_revenue = tariff_home * post_tariff_volume
    
    # Net welfare (simplified)
    welfare = tariff_revenue + tot_gain - dwl
    
    return welfare

def best_response_tariff(tariff_foreign, trade_volume, demand_elast, supply_elast):
    """
    Calculate Home's optimal tariff given Foreign's tariff (best-response function).
    """
    def neg_welfare(t_home):
        return -national_welfare(t_home, tariff_foreign, trade_volume, 
                                demand_elast, supply_elast)
    
    result = minimize_scalar(neg_welfare, bounds=(0, 0.5), method='bounded')
    optimal_tariff = result.x
    
    return optimal_tariff

# Compute best-response functions
print("TRADE WAR GAME THEORY SETUP")
print("=" * 60)

foreign_tariff_grid = np.linspace(0, 0.40, 50)
home_best_responses = []

for t_f in foreign_tariff_grid:
    t_h_optimal = best_response_tariff(t_f, initial_trade_volume, 
                                       import_demand_elasticity, export_supply_elasticity)
    home_best_responses.append(t_h_optimal)

home_best_responses = np.array(home_best_responses)

print("\nBest-Response Function (Home tariff optimal given Foreign tariff):")
print(f"When Foreign tariff = 0%:   Home optimal = {home_best_responses[0]*100:.1f}%")
print(f"When Foreign tariff = 10%:  Home optimal = {home_best_responses[np.argmin(np.abs(foreign_tariff_grid - 0.10))]*100:.1f}%")
print(f"When Foreign tariff = 20%:  Home optimal = {home_best_responses[np.argmin(np.abs(foreign_tariff_grid - 0.20))]*100:.1f}%")
```

The best-response function slopes upward: when Foreign raises its tariff, Home's optimal tariff increases to recapture terms-of-trade losses and respond to worsened market access. This strategic complementarity drives the escalation dynamic.

Find the Nash equilibrium where both countries play best responses simultaneously:

```python
# Solve for Nash equilibrium (symmetric case)
def nash_equilibrium_condition(t):
    """
    For symmetric countries, Nash equilibrium satisfies t_H = BR_H(t_F) and t_F = BR_F(t_H).
    In symmetric case: t_H = t_F = t* at equilibrium.
    Solve: t* = BR(t*)
    """
    t_home = t[0]
    t_foreign = t[0]  # Symmetry
    
    br_home = best_response_tariff(t_foreign, initial_trade_volume, 
                                   import_demand_elasticity, export_supply_elasticity)
    
    residual = t_home - br_home
    return [residual]

# Initial guess
initial_guess = [0.15]

# Solve for Nash equilibrium
nash_solution = fsolve(nash_equilibrium_condition, initial_guess)
nash_tariff = nash_solution[0]

print(f"\n\nNASH EQUILIBRIUM (NON-COOPERATIVE TARIFFS)")
print("=" * 60)
print(f"Equilibrium tariff rate (both countries): {nash_tariff*100:.1f}%")

# Calculate welfare at different outcomes
welfare_free_trade = national_welfare(0, 0, initial_trade_volume, 
                                     import_demand_elasticity, export_supply_elasticity)

welfare_nash = national_welfare(nash_tariff, nash_tariff, initial_trade_volume,
                               import_demand_elasticity, export_supply_elasticity)

welfare_optimal_single = national_welfare(
    best_response_tariff(0, initial_trade_volume, import_demand_elasticity, export_supply_elasticity),
    0, initial_trade_volume, import_demand_elasticity, export_supply_elasticity
)

print(f"\nWelfare Comparison (per country):")
print(f"  Free Trade:              ${welfare_free_trade/1e9:.2f} billion")
print(f"  Optimal Tariff (other=0): ${welfare_optimal_single/1e9:.2f} billion")
print(f"  Nash Equilibrium:         ${welfare_nash/1e9:.2f} billion")

print(f"\nWelfare Loss from Trade War:")
print(f"  Nash vs Free Trade: ${(welfare_nash - welfare_free_trade)/1e9:.2f} billion ({(welfare_nash/welfare_free_trade - 1)*100:.1f}%)")
```

The Nash equilibrium tariff typically falls between 15-25%, substantially higher than the single-country optimal tariff (5-10% when the trading partner maintains free trade). Both countries suffer welfare losses relative to free trade—the classic prisoners' dilemma outcome. Each country would prefer mutual free trade to mutual protection, but unilateral deviation to optimal tariff yields higher payoff, making cooperation unstable without enforcement.

Simulate the dynamic adjustment path from free trade to Nash equilibrium using iterative best-response dynamics:

```python
# Dynamic tariff war simulation (iterative best responses)
print("\n\nDYNAMIC TARIFF WAR SIMULATION")
print("=" * 60)

max_rounds = 20
tariff_home_path = [0.0]  # Start at free trade
tariff_foreign_path = [0.0]
welfare_home_path = []
welfare_foreign_path = []

for round in range(max_rounds):
    # Home responds to Foreign's previous tariff
    t_home_new = best_response_tariff(tariff_foreign_path[-1], initial_trade_volume,
                                      import_demand_elasticity, export_supply_elasticity)
    tariff_home_path.append(t_home_new)
    
    # Foreign responds to Home's new tariff (symmetric)
    t_foreign_new = best_response_tariff(t_home_new, initial_trade_volume,
                                        import_demand_elasticity, export_supply_elasticity)
    tariff_foreign_path.append(t_foreign_new)
    
    # Calculate welfare
    w_home = national_welfare(t_home_new, t_foreign_new, initial_trade_volume,
                             import_demand_elasticity, export_supply_elasticity)
    w_foreign = national_welfare(t_foreign_new, t_home_new, initial_trade_volume,
                                import_demand_elasticity, export_supply_elasticity)
    
    welfare_home_path.append(w_home)
    welfare_foreign_path.append(w_foreign)
    
    # Check convergence
    if abs(t_home_new - tariff_foreign_path[-1]) < 0.001:
        print(f"\nConverged to Nash equilibrium in {round+1} rounds")
        break

print(f"\nFinal tariff rates:")
print(f"  Home:    {tariff_home_path[-1]*100:.2f}%")
print(f"  Foreign: {tariff_foreign_path[-1]*100:.2f}%")

print(f"\nTariff Escalation Path:")
print(f"{'Round':<8}{'Home Tariff':<15}{'Foreign Tariff':<15}{'Home Welfare'}")
print(f"{'':8}{'(%)':15}{'(%)':15}{'($B)'}")
print("-" * 55)
for i in range(len(welfare_home_path)):
    print(f"{i:<8}{tariff_home_path[i+1]*100:>10.2f}     {tariff_foreign_path[i+1]*100:>10.2f}     {welfare_home_path[i]/1e9:>10.2f}")

# Visualize escalation dynamics
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

axes[0].plot(range(len(tariff_home_path)-1), np.array(tariff_home_path[1:])*100, 
             marker='o', label='Home', linewidth=2)
axes[0].plot(range(len(tariff_foreign_path)-1), np.array(tariff_foreign_path[1:])*100, 
             marker='s', label='Foreign', linewidth=2)
axes[0].axhline(y=nash_tariff*100, color='red', linestyle='--', 
                label=f'Nash Equilibrium ({nash_tariff*100:.1f}%)')
axes[0].set_xlabel('Negotiation Round')
axes[0].set_ylabel('Tariff Rate (%)')
axes[0].set_title('Tariff Escalation Dynamics')
axes[0].legend()
axes[0].grid(True, alpha=0.3)

axes[1].plot(range(len(welfare_home_path)), np.array(welfare_home_path)/1e9, 
             marker='o', label='Home', linewidth=2)
axes[1].plot(range(len(welfare_foreign_path)), np.array(welfare_foreign_path)/1e9, 
             marker='s', label='Foreign', linewidth=2)
axes[1].axhline(y=welfare_free_trade/1e9, color='green', linestyle='--', 
                label='Free Trade Welfare')
axes[1].set_xlabel('Negotiation Round')
axes[1].set_ylabel('National Welfare ($ Billions)')
axes[1].set_title('Welfare Deterioration During Trade War')
axes[1].legend()
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('trade_war_escalation_dynamics.png', dpi=300)
plt.close()

print("\nEscalation dynamics chart saved to trade_war_escalation_dynamics.png")
```

The simulation shows tariffs ratcheting upward over successive rounds as each country responds to the other's protection, converging to the Nash equilibrium within 5-10 iterations. Welfare declines monotonically throughout the escalation, with both countries ending worse off than at the starting point of free trade.

### Exercise 3.2: Trade Agreement Design and Self-Enforcement Constraints

Trade agreements resolve the prisoners' dilemma by coordinating tariff reductions below Nash equilibrium levels. However, agreements must be self-enforcing: each country must prefer honoring the agreement over cheating (reverting to optimal tariff) accounting for future punishment. This exercise calculates the threshold discount factor required for agreement stability under grim trigger strategies, designs optimal punishment schemes, and identifies the Pareto frontier of sustainable cooperation.

The self-enforcement constraint requires that the present value of cooperation exceeds the present value of deviation plus punishment:

$$\frac{W^{coop}}{1 - \delta} \geq W^{dev} + \delta \frac{W^{pun}}{1 - \delta}$$

where $W^{coop}$ denotes welfare under the cooperative agreement, $W^{dev}$ gives the one-period gain from cheating, $W^{pun}$ represents welfare during punishment, and $\delta$ is the discount factor. Rearranging yields the minimum discount factor for sustainability:

$$\delta \geq \frac{W^{dev} - W^{coop}}{W^{dev} - W^{pun}}$$

Continue the script from Exercise 3.1 by adding agreement analysis:

```python
# Trade agreement analysis
print("\n\nTRADE AGREEMENT SELF-ENFORCEMENT ANALYSIS")
print("=" * 60)

# Define candidate cooperative tariff rates
cooperative_tariffs = np.linspace(0, nash_tariff, 30)

# Calculate welfare and sustainability for each cooperative tariff
agreement_results = []

for t_coop in cooperative_tariffs:
    # Cooperative welfare (both countries maintain t_coop)
    w_coop = national_welfare(t_coop, t_coop, initial_trade_volume,
                             import_demand_elasticity, export_supply_elasticity)
    
    # Deviation welfare (Home deviates to best-response while Foreign stays at t_coop)
    t_deviation = best_response_tariff(t_coop, initial_trade_volume,
                                       import_demand_elasticity, export_supply_elasticity)
    w_dev = national_welfare(t_deviation, t_coop, initial_trade_volume,
                            import_demand_elasticity, export_supply_elasticity)
    
    # Punishment welfare (revert to Nash equilibrium forever)
    w_pun = welfare_nash
    
    # Calculate minimum discount factor
    if w_dev - w_pun != 0:
        delta_min = (w_dev - w_coop) / (w_dev - w_pun)
    else:
        delta_min = np.inf
    
    # Gains from trade (cooperation vs Nash)
    gains_from_agreement = w_coop - welfare_nash
    
    agreement_results.append({
        'cooperative_tariff': t_coop,
        'coop_welfare': w_coop,
        'deviation_welfare': w_dev,
        'punishment_welfare': w_pun,
        'min_discount_factor': delta_min,
        'gains_from_agreement': gains_from_agreement
    })

agreement_df = pd.DataFrame(agreement_results)

print("\nCooperative Tariff Sustainability:")
print(f"{'Tariff (%)':<15}{'Coop Welfare':<15}{'Min Discount':<15}{'Gains vs Nash'}")
print(f"{'':15}{'($B)':15}{'Factor':15}{'($B)'}")
print("-" * 60)

for idx in [0, 5, 10, 15, 20, 25, 29]:
    row = agreement_df.iloc[idx]
    print(f"{row['cooperative_tariff']*100:>10.1f}     {row['coop_welfare']/1e9:>10.2f}     {row['min_discount_factor']:>10.3f}     {row['gains_from_agreement']/1e9:>10.2f}")

# Identify maximum sustainable cooperation for given discount factor
discount_factor_realistic = 0.95  # Typical annual discount factor

sustainable = agreement_df[agreement_df['min_discount_factor'] <= discount_factor_realistic]

if len(sustainable) > 0:
    best_sustainable = sustainable.loc[sustainable['coop_welfare'].idxmax()]
    print(f"\n\nOptimal Sustainable Agreement (δ = {discount_factor_realistic}):")
    print(f"  Cooperative tariff: {best_sustainable['cooperative_tariff']*100:.1f}%")
    print(f"  Welfare: ${best_sustainable['coop_welfare']/1e9:.2f} billion")
    print(f"  Gains over Nash: ${best_sustainable['gains_from_agreement']/1e9:.2f} billion")
else:
    print(f"\n\nNo cooperative tariffs sustainable at δ = {discount_factor_realistic}")
    print(f"Minimum required discount factor: {agreement_df['min_discount_factor'].min():.3f}")
```

The self-enforcement constraint tightens as cooperative tariffs fall below the Nash level. Free trade requires the highest discount factor (most patience) because the temptation to deviate is greatest. Realistic discount factors (0.90-0.95 annually) typically sustain tariffs of 5-10%, achieving most but not all gains from trade. Countries with higher discount factors (longer time horizons, stable governments) can sustain deeper liberalization.

Visualize the sustainability frontier:

```python
# Visualize agreement sustainability frontier
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Panel A: Discount factor requirements
axes[0].plot(agreement_df['cooperative_tariff']*100, 
             agreement_df['min_discount_factor'],
             linewidth=2, color='darkblue')
axes[0].axhline(y=discount_factor_realistic, color='red', linestyle='--', 
                label=f'Realistic δ = {discount_factor_realistic}')
axes[0].axhline(y=1.0, color='gray', linestyle=':', label='δ = 1 (Perfect Patience)')
axes[0].set_xlabel('Cooperative Tariff Rate (%)')
axes[0].set_ylabel('Minimum Discount Factor Required')
axes[0].set_title('Trade Agreement Sustainability Constraint')
axes[0].legend()
axes[0].grid(True, alpha=0.3)
axes[0].set_ylim([0, 1.1])

# Panel B: Pareto frontier (welfare vs tariff)
axes[1].plot(agreement_df['cooperative_tariff']*100, 
             agreement_df['coop_welfare']/1e9,
             linewidth=2, color='darkgreen', label='Cooperative Welfare')
axes[1].axhline(y=welfare_nash/1e9, color='red', linestyle='--', 
                label='Nash Equilibrium Welfare')
axes[1].axhline(y=welfare_free_trade/1e9, color='blue', linestyle='--',
                label='Free Trade Welfare')

if len(sustainable) > 0:
    axes[1].scatter([best_sustainable['cooperative_tariff']*100], 
                   [best_sustainable['coop_welfare']/1e9],
                   color='orange', s=100, zorder=5,
                   label=f'Best Sustainable (δ={discount_factor_realistic})')

axes[1].set_xlabel('Cooperative Tariff Rate (%)')
axes[1].set_ylabel('National Welfare ($ Billions)')
axes[1].set_title('Pareto Frontier of Trade Agreements')
axes[1].legend()
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('trade_agreement_sustainability.png', dpi=300)
plt.close()

# Export agreement analysis
agreement_df.to_csv('trade_agreement_analysis.csv', index=False)

print("\nAgreement sustainability analysis exported to trade_agreement_analysis.csv")
print("Sustainability charts saved to trade_agreement_sustainability.png")
```

The Pareto frontier shows welfare increasing as cooperative tariffs fall from Nash toward free trade, but the sustainability constraint prevents achieving full liberalization when discount factors are realistic. The optimal sustainable agreement balances maximizing welfare gains against maintaining self-enforcement incentives.

### Exercise 3.3: Recovery Protocol - Trade Liberalization Sequencing

When trade wars have destroyed cooperation, rebuilding liberalized trade requires careful sequencing to overcome trust deficits and domestic political economy constraints. This exercise designs a multi-stage liberalization protocol that begins with sectors where gains from trade are largest and political resistance weakest, gradually expands coverage, and incorporates safeguards to prevent backsliding.

The sequencing strategy prioritizes sectors by the ratio of consumer gains to producer adjustment costs. Liberalization generates concentrated losses for import-competing producers but diffuse gains for consumers. Sectors with high consumer gains relative to producer dislocation offer the best political economy profile for initial liberalization, building momentum for broader reform.

Create a new Python script `liberalization_sequencing.py`:

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Sectoral trade liberalization data
# Create synthetic dataset representing different sectors
np.random.seed(42)

n_sectors = 20

sectors = pd.DataFrame({
    'sector': [f'Sector_{i:02d}' for i in range(n_sectors)],
    'initial_tariff': np.random.uniform(0.05, 0.30, n_sectors),
    'import_penetration': np.random.uniform(0.10, 0.60, n_sectors),
    'consumer_surplus_gain': np.random.uniform(5, 50, n_sectors),  # $billions
    'producer_adjustment_cost': np.random.uniform(2, 30, n_sectors),  # $billions
    'employment_affected': np.random.randint(10000, 200000, n_sectors),
    'political_sensitivity': np.random.uniform(1, 10, n_sectors)  # 1=low, 10=high
})

# Calculate benefit-cost ratio for prioritization
sectors['bc_ratio'] = sectors['consumer_surplus_gain'] / sectors['producer_adjustment_cost']
sectors['net_welfare_gain'] = sectors['consumer_surplus_gain'] - sectors['producer_adjustment_cost']

# Calculate political feasibility score (inverse of sensitivity × employment)
sectors['feasibility_score'] = 1 / (sectors['political_sensitivity'] * sectors['employment_affected'] / 100000)

# Combined priority score (benefits × feasibility)
sectors['priority_score'] = sectors['bc_ratio'] * sectors['feasibility_score']

# Sort by priority
sectors_sorted = sectors.sort_values('priority_score', ascending=False).reset_index(drop=True)

print("TRADE LIBERALIZATION SEQUENCING PROTOCOL")
print("=" * 60)
print("\nSector Prioritization (Top 10):")
print(sectors_sorted[['sector', 'initial_tariff', 'bc_ratio', 
                      'net_welfare_gain', 'priority_score']].head(10).to_string(index=False))

# Design multi-phase liberalization schedule
def design_liberalization_phases(sectors_df, n_phases=4):
    """
    Allocate sectors across phases based on priority scores.
    Each phase implements tariff cuts on assigned sectors.
    """
    sectors_per_phase = len(sectors_df) // n_phases
    phases = []
    
    for phase in range(n_phases):
        start_idx = phase * sectors_per_phase
        end_idx = start_idx + sectors_per_phase if phase < n_phases - 1 else len(sectors_df)
        
        phase_sectors = sectors_df.iloc[start_idx:end_idx].copy()
        phase_sectors['phase'] = phase + 1
        
        # Calculate phase-level tariff reduction (gradual approach)
        phase_sectors['tariff_reduction'] = phase_sectors['initial_tariff'] * (0.5 + 0.1 * phase)
        phase_sectors['final_tariff'] = phase_sectors['initial_tariff'] - phase_sectors['tariff_reduction']
        
        phases.append(phase_sectors)
    
    return pd.concat(phases, ignore_index=True)

liberalization_schedule = design_liberalization_phases(sectors_sorted, n_phases=4)

print("\n\nLIBERALIZATION PHASE DESIGN")
print("=" * 60)

for phase in range(1, 5):
    phase_data = liberalization_schedule[liberalization_schedule['phase'] == phase]
    
    total_welfare_gain = phase_data['net_welfare_gain'].sum()
    avg_tariff_cut = phase_data['tariff_reduction'].mean() * 100
    total_employment = phase_data['employment_affected'].sum()
    
    print(f"\nPhase {phase}:")
    print(f"  Sectors: {len(phase_data)}")
    print(f"  Average tariff reduction: {avg_tariff_cut:.1f} percentage points")
    print(f"  Total net welfare gain: ${total_welfare_gain:.1f} billion")
    print(f"  Workers affected: {total_employment:,}")
    print(f"  Key sectors: {', '.join(phase_data['sector'].head(3).tolist())}")
```

Phase 1 focuses on sectors with highest benefit-cost ratios and lowest political resistance—typically high-tech intermediate goods and capital equipment where domestic production is minimal. Later phases tackle more sensitive sectors like agriculture and labor-intensive manufacturing, by which point early reform successes have built political capital and demonstrated gains from liberalization.

Simulate the cumulative welfare path and adjustment dynamics across phases:

```python
# Simulate cumulative impacts across phases
cumulative_results = []

for phase in range(1, 5):
    phase_to_date = liberalization_schedule[liberalization_schedule['phase'] <= phase]
    
    cumulative_welfare_gain = phase_to_date['net_welfare_gain'].sum()
    cumulative_consumer_gain = phase_to_date['consumer_surplus_gain'].sum()
    cumulative_producer_cost = phase_to_date['producer_adjustment_cost'].sum()
    cumulative_employment = phase_to_date['employment_affected'].sum()
    
    # Average tariff rate (weighted by import penetration)
    avg_tariff_before = (phase_to_date['initial_tariff'] * phase_to_date['import_penetration']).sum() / phase_to_date['import_penetration'].sum()
    avg_tariff_after = (phase_to_date['final_tariff'] * phase_to_date['import_penetration']).sum() / phase_to_date['import_penetration'].sum()
    
    cumulative_results.append({
        'phase': phase,
        'cumulative_welfare_gain': cumulative_welfare_gain,
        'cumulative_consumer_gain': cumulative_consumer_gain,
        'cumulative_producer_cost': cumulative_producer_cost,
        'cumulative_employment_affected': cumulative_employment,
        'avg_tariff_before': avg_tariff_before,
        'avg_tariff_after': avg_tariff_after
    })

cumulative_df = pd.DataFrame(cumulative_results)

print("\n\nCUMULATIVE LIBERALIZATION IMPACTS")
print("=" * 60)
print(cumulative_df.to_string(index=False))

# Visualize sequencing strategy
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Panel A: Cumulative welfare gains
axes[0, 0].bar(cumulative_df['phase'], cumulative_df['cumulative_welfare_gain'],
               color='darkgreen', alpha=0.7, edgecolor='black')
axes[0, 0].set_xlabel('Phase')
axes[0, 0].set_ylabel('Cumulative Net Welfare Gain ($B)')
axes[0, 0].set_title('Cumulative Welfare Gains Across Phases')
axes[0, 0].grid(True, alpha=0.3, axis='y')

# Panel B: Consumer gains vs producer costs
x = cumulative_df['phase']
axes[0, 1].plot(x, cumulative_df['cumulative_consumer_gain'], 
                marker='o', label='Consumer Gains', linewidth=2)
axes[0, 1].plot(x, cumulative_df['cumulative_producer_cost'], 
                marker='s', label='Producer Costs', linewidth=2)
axes[0, 1].set_xlabel('Phase')
axes[0, 1].set_ylabel('Cumulative Impact ($B)')
axes[0, 1].set_title('Distribution of Gains and Costs')
axes[0, 1].legend()
axes[0, 1].grid(True, alpha=0.3)

# Panel C: Employment adjustment path
axes[1, 0].plot(cumulative_df['phase'], cumulative_df['cumulative_employment_affected']/1000,
                marker='D', color='darkred', linewidth=2)
axes[1, 0].set_xlabel('Phase')
axes[1, 0].set_ylabel('Cumulative Workers Affected (Thousands)')
axes[1, 0].set_title('Employment Adjustment Path')
axes[1, 0].grid(True, alpha=0.3)

# Panel D: Average tariff reduction trajectory
axes[1, 1].plot(cumulative_df['phase'], cumulative_df['avg_tariff_before']*100,
                marker='o', label='Before Liberalization', linewidth=2)
axes[1, 1].plot(cumulative_df['phase'], cumulative_df['avg_tariff_after']*100,
                marker='s', label='After Phase Completion', linewidth=2)
axes[1, 1].set_xlabel('Phase')
axes[1, 1].set_ylabel('Average Tariff Rate (%)')
axes[1, 1].set_title('Tariff Reduction Trajectory')
axes[1, 1].legend()
axes[1, 1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('liberalization_sequencing_strategy.png', dpi=300)
plt.close()

# Export detailed schedule
liberalization_schedule.to_csv('liberalization_phase_schedule.csv', index=False)

print("\n\nLiberalization schedule exported to liberalization_phase_schedule.csv")
print("Sequencing strategy charts saved to liberalization_sequencing_strategy.png")
```

The sequencing visualization shows welfare gains accumulating across phases while employment dislocation spreads over time, reducing adjustment pressure in any single period. The average tariff falls gradually from initial levels above 15% to final levels below 5%, minimizing economic disruption while maximizing long-run efficiency gains.

Design safeguard mechanisms to prevent backsliding and manage adjustment:

```python
# Safeguard and adjustment assistance protocol
print("\n\nSAFEGUARD AND ADJUSTMENT ASSISTANCE DESIGN")
print("=" * 60)

# Calculate required adjustment assistance funding
assistance_per_worker = 20000  # $20k per displaced worker (retraining, income support)
total_assistance_cost = (liberalization_schedule['employment_affected'] * assistance_per_worker / 1e9).sum()

print(f"\nTotal adjustment assistance required: ${total_assistance_cost:.1f} billion")
print(f"Financed by: {total_assistance_cost / cumulative_df['cumulative_welfare_gain'].iloc[-1] * 100:.1f}% of total welfare gains")

# Design temporary safeguard triggers
safeguard_threshold_import_surge = 1.3  # 30% import increase triggers safeguard
safeguard_duration = 2  # years

print(f"\nSafeguard Mechanism:")
print(f"  Trigger: Import volume increase > {(safeguard_threshold_import_surge-1)*100:.0f}% year-over-year")
print(f"  Response: Temporary tariff restoration up to 50% of original level")
print(f"  Duration: Maximum {safeguard_duration} years, subject to declining schedule")
print(f"  Eligibility: Sectors demonstrating serious injury to domestic industry")

# Monitor and evaluate protocol
print(f"\nMonitoring and Evaluation Framework:")
print(f"  Quarterly assessment of:")
print(f"    - Import penetration rates by sector")
print(f"    - Employment levels in affected industries")
print(f"    - Consumer price index changes")
print(f"    - Trade balance impacts")
print(f"  Annual review of liberalization pace and adjustment adequacy")
print(f"  Mid-phase evaluation with option to accelerate or pause subsequent phases")

print("\n" + "="*60)
print("LIBERALIZATION PROTOCOL COMPLETE")
print("="*60)
```

The complete protocol balances ambition with realism. Front-loading politically feasible sectors builds momentum, while adjustment assistance and temporary safeguards manage transition costs and provide political cover for sustained reform. The multi-phase structure allows mid-course corrections based on observed outcomes, reducing the risk of collapse from excessive disruption.

## Operational Reference Guide & Diagnostic Checklist

### Data Sources and Maintenance

**Bilateral Trade Flows**: UN Comtrade (`comtradeplus.un.org`) provides the authoritative global bilateral trade database at HS6 product classification. Update quarterly for recent years, annually for historical series. Cross-validate total trade flows against WTO and IMF Direction of Trade Statistics. Missing observations indicate non-trading relationships or statistical suppression; treat zeros as structural rather than measurement error.

**Tariff Schedules**: WITS (`wits.worldbank.org`) aggregates tariff data from national customs agencies and WTO bound rates. Download at HS6 level to match trade data. Distinguish between MFN (most-favored-nation) rates, preferential rates under regional trade agreements, and applied rates accounting for temporary exemptions. Use applied rates for welfare calculations, bound rates for policy space analysis.

**Gravity Variables**: CEPII (`cepii.fr`) provides comprehensive bilateral distance, contiguity, language, and colonial relationship indicators. The GeoDist dataset gives population-weighted bilateral distances accounting for internal geography. Update annually for new country formations or significant administrative changes.

**GDP and Exchange Rates**: Penn World Tables provide PPP-adjusted real GDP for cross-country comparisons; World Bank WDI gives nominal USD GDP for trade share calculations. Federal Reserve H.10 statistical release and BIS effective exchange rate database supply nominal and real effective exchange rate indices.

### Common Estimation Failures and Remedies

**Zero Trade Flows**: Never drop zeros before estimation. Use PPML with Poisson family in statsmodels GLM framework. If convergence fails with full fixed effects, aggregate to country-pair averages or use higher-level country fixed effects. Zeros containing economic information about prohibitive trade costs; dropping them biases distance elasticity toward zero.

**Endogeneity in Gravity**: Distance and language are predetermined, but trade agreements and exchange rates are potentially endogenous. Use lagged agreement implementation dates (t-1) or instrument with historical political relationships. For exchange rates, instrument with monetary policy shocks or use exogenous third-country exchange rate movements.

**Multicollinearity with Fixed Effects**: Exporter-year and importer-year fixed effects perfectly collinear with time-varying country characteristics (GDP, tariffs). Absorb all time-varying country variables into fixed effects rather than including explicitly. Report fixed effects as multilateral resistance indices rather than individual coefficients.

**Heteroskedasticity and Clustering**: Bilateral trade errors exhibit spatial correlation (shocks to region A affect region A's trade with all partners). Use HAC standard errors with maxlags=6 for time series; use two-way clustering by exporter and importer for cross-sectional gravity. Never use uncorrected standard errors—they severely understate true uncertainty.

### Welfare Calculation Validation Protocol

**Elasticity Bounds Check**: Import demand elasticity should fall between -2.0 and -0.3 (literature consensus range). Values outside this range indicate misspecification or measurement error. Re-estimate gravity with different functional forms (log-log vs PPML) and check robustness. Export supply elasticity typically ranges 2-10 for large economies.

**Deadweight Loss Proportionality**: DWL as share of import value should approximately equal $0.5 \times t^2 \times |\epsilon|$ where $t$ is tariff rate and $\epsilon$ is demand elasticity. For 20% tariff and elasticity -1.0, expect DWL around 2% of imports. Values exceeding 5% suggest quadratic approximation breaking down (use numerical integration for high tariffs).

**Terms-of-Trade Consistency**: Terms-of-trade gains require large-country assumption (foreign supply elasticity < 20). Small countries (trade share < 5% of world) should set foreign supply elasticity to 999 to approximate perfectly elastic supply. Verify that calculated terms-of-trade improvement does not exceed tariff revenue (physically impossible).

**Monte Carlo Coverage Diagnostics**: Confidence intervals from Monte Carlo simulation should have correct empirical coverage. For 95% nominal CI, verify that 94-96% of repeated samples contain true parameter. Under-coverage indicates too-narrow elasticity distributions; over-coverage indicates correlation not captured by independent draws.

### Trade War Nash Equilibrium Verification

**Best-Response Monotonicity**: Best-response function $BR(t_F)$ should be continuously differentiable and slope upward (strategic complementarity). Non-monotonic best responses indicate numerical optimization failure—reduce tolerance on minimize_scalar and increase bounds.

**Symmetry Check**: For symmetric countries (equal GDP, elasticities), Nash equilibrium must satisfy $t_H^N = t_F^N$. Asymmetric equilibria in symmetric game indicate convergence to unstable fixed point. Re-solve with initial guess near symmetric point.

**Welfare Ordering**: Must hold $W^{free} > W^{optimal(single)} > W^{Nash} > W^{autarky}$. Violations indicate sign errors in welfare function components (check that DWL enters negative, revenue enters positive). Optimal single-country tariff welfare exceeds free trade only through terms-of-trade extraction, requiring large-country assumption.

**Discount Factor Bounds**: Minimum discount factor for cooperation must fall in (0,1). Values below 0 indicate cooperation sustainability with zero patience (cooperation dominates deviation even in one-shot game—check that deviation welfare truly exceeds cooperation). Values exceeding 1 indicate no finite discount factor sustains cooperation (gains from deviation too large or punishment too weak).

### Diagnostic Command Reference

```python
# Gravity estimation convergence diagnostics
fitted_values = ppml_model.fittedvalues
residuals = ppml_model.resid_pearson

print(f"Convergence: {ppml_model.mle_retvals['converged']}")
print(f"Log-likelihood: {ppml_model.llf:.2f}")
print(f"Pseudo R-squared: {1 - ppml_model.deviance / ppml_model.null_deviance:.3f}")

# Check for separation (perfect prediction of zeros)
print(f"Zero trade flows predicted as zero: {((fitted_values < 0.01) & (df['trade_value'] == 0)).sum()}")

# Residual normality and heteroskedasticity
from scipy.stats import shapiro, jarque_bera
stat, p_value = jarque_bera(residuals)
print(f"Jarque-Bera test for normality: p = {p_value:.4f}")

# Export diagnostic plots
fig, axes = plt.subplots(2, 2, figsize=(12, 10))
axes[0,0].scatter(fitted_values, residuals, alpha=0.3)
axes[0,0].axhline(0, color='red', linestyle='--')
axes[0,0].set_xlabel('Fitted Values')
axes[0,0].set_ylabel('Pearson Residuals')
axes[0,0].set_title('Residual vs Fitted')

axes[0,1].hist(residuals, bins=50, edgecolor='black')
axes[0,1].set_xlabel('Pearson Residuals')
axes[0,1].set_title('Residual Distribution')

from statsmodels.graphics.gofplots import qqplot
qqplot(residuals, line='45', ax=axes[1,0])
axes[1,0].set_title('Q-Q Plot')

axes[1,1].scatter(df['ln_dist'], residuals, alpha=0.3)
axes[1,1].axhline(0, color='red', linestyle='--')
axes[1,1].set_xlabel('Log Distance')
axes[1,1].set_ylabel('Pearson Residuals')
axes[1,1].set_title('Residuals vs Distance')

plt.tight_layout()
plt.savefig('gravity_diagnostics.png', dpi=300)
```

Systematic patterns in residual plots indicate misspecification. Funnel shapes suggest heteroskedasticity (use robust standard errors). Trends against distance indicate omitted variables or non-linear distance effects (add squared distance term). Heavy-tailed residual distributions indicate outlier trade flows (investigate politically motivated trade or measurement error).

### Production Deployment Checklist

Before deploying trade policy analysis to inform actual government decisions:

1. **Data Provenance Audit**: Document exact data sources, download dates, and any manual adjustments. Trade data errors propagate directly to tariff recommendations.

2. **Elasticity Sensitivity Analysis**: Report welfare calculations under low, central, and high elasticity scenarios spanning literature consensus range. Policy-makers need uncertainty bands, not point estimates.

3. **Political Economy Constraints**: Identify sectors with employment concentration exceeding 5% of regional workforce. These require special adjustment assistance regardless of national welfare calculations.

4. **Dynamic General Equilibrium**: Partial equilibrium calculations omit input-output linkages, exchange rate adjustment, and capital reallocation. For tariff changes exceeding 10 percentage points, recommend CGE modeling to capture general equilibrium effects.

5. **International Retaliation Modeling**: Any tariff increase risks foreign retaliation. Game-theoretic analysis assumes rational play; behavioral factors (nationalism, political cycles) can trigger disproportionate responses. Scenario planning should include worst-case escalation paths.

6. **Legal Compliance Review**: WTO rules restrict tariff increases beyond bound rates except under safeguard provisions (Article XIX) requiring injury demonstration. Verify all proposed tariffs comply with international commitments.

7. **Stakeholder Consultation**: Consumer groups, producer associations, and labor unions hold information about sector-specific adjustment costs not visible in aggregate data. Solicit feedback before finalizing recommendations.

The ultimate validation is retrospective evaluation. After policy implementation, compare predicted welfare changes and trade flows to realized outcomes. Systematic forecast errors indicate model misspecification requiring methodological refinement. Trade economics is an empirical discipline—theoretical rigor matters only insofar as it generates accurate predictions about real-world policy effects.
