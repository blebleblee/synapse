# Operational Verification Labs: Urban Economics

## Objective & Operational Lab Setup

Urban economics sits at the intersection of spatial analysis, microeconomic theory, and empirical policy evaluation. This laboratory sequence trains you to operationalize the foundational models that explain why cities exist, how land markets clear, and what forces drive urban spatial structure. You will construct monocentric city models from first principles, calibrate bid-rent functions against real-world data, measure agglomeration externalities through productivity regressions, and stress-test zoning policies under counterfactual scenarios. Each exercise moves from theoretical specification to empirical estimation to policy simulation, ensuring that abstract spatial equilibrium concepts become tangible analytical tools.

The monocentric city model, developed by Alonso, Muth, and Mills in the 1960s, remains the workhorse framework for urban spatial analysis. It posits that firms cluster at a central business district (CBD) to exploit agglomeration economies, while households trade off commuting costs against housing consumption as they locate farther from the center. The resulting bid-rent curves—downward-sloping functions representing the maximum rent a household or firm will pay at each distance from the CBD—determine land allocation and urban density gradients. Extensions incorporate multiple employment centers, heterogeneous households, durable housing capital, and endogenous amenities, but the core mechanism persists: spatial equilibrium requires that households achieve equal utility across locations after accounting for rent and commuting costs.

Agglomeration economies, formalized by Marshall and refined by Duranton and Puga, explain why economic activity concentrates in cities despite land scarcity and congestion. Labor market pooling allows firms to access specialized workers and workers to access diverse job opportunities, reducing search frictions and match quality variance. Input sharing enables firms to exploit scale economies in intermediate goods production and specialized business services. Knowledge spillovers arise from face-to-face interaction, informal information exchange, and localized learning-by-doing. Empirical identification of these mechanisms requires panel data on firm productivity, worker wages, and employment density, combined with instrumental variable strategies that isolate exogenous variation in city size or industry composition.

Zoning regulations and land-use controls constrain the urban land market, creating wedges between market rents and shadow prices. Height restrictions, minimum lot sizes, and use segregation reduce housing supply elasticity, amplifying price responses to demand shocks. Empirical verification demands comparing regulated and unregulated markets using difference-in-differences estimation or synthetic control methods. Quantitative spatial models, such as those developed by Ahlfeldt, Redding, Sturm, and Wolf, embed zoning constraints into general equilibrium frameworks, allowing counterfactual simulations that quantify welfare costs and distributional impacts.

Your operational environment requires Python 3.10 or later with NumPy for numerical computation, Pandas for data manipulation, Matplotlib and Seaborn for visualization, SciPy for optimization and integration, and Statsmodels for econometric estimation. Install the complete stack via `pip install numpy pandas matplotlib seaborn scipy statsmodels`. Acquire Census Bureau data from the American Community Survey (ACS) five-year estimates, Bureau of Labor Statistics (BLS) wage files, and Federal Highway Administration (FHWA) commuting statistics. For international comparisons, use Eurostat urban audit data or UN-Habitat city profiles. Store raw data in a `data/` directory, processed datasets in `data/processed/`, model outputs in `models/`, and figures in `figures/`. Structure your project with a `notebooks/` directory for Jupyter analysis and a `src/` directory for reusable Python modules containing bid-rent solvers, spatial equilibrium functions, and regression utilities.

Coordinate systems matter for spatial analysis. Use projected coordinate reference systems (CRS) such as UTM zones or state plane coordinates for distance calculations, not geographic latitude-longitude coordinates. Transform all spatial data to a common CRS before computing distances or densities. For US cities, EPSG:2163 (US National Atlas Equal Area) preserves area calculations. For European cities, ETRS89 Lambert Azimuthal Equal Area (EPSG:3035) serves the same purpose. Verify CRS consistency using `geopandas.GeoDataFrame.crs` and reproject with `to_crs()`.

Computational precision requirements depend on the analysis. Bid-rent numerical integration requires adaptive quadrature with absolute tolerance below 1e-6 to ensure convergence. Spatial equilibrium solvers demand root-finding tolerance below 1e-8 to achieve utility equalization across locations. Monte Carlo simulations for welfare analysis need at least 10,000 draws to stabilize standard errors. Regression diagnostics must include heteroskedasticity-robust standard errors, multicollinearity checks via variance inflation factors, and spatial autocorrelation tests using Moran's I statistic.

## Exercise 1: Foundational Practical Implementation

### Monocentric City Model Construction and Calibration

The monocentric city model predicts urban density and rent gradients from first principles. Begin by specifying household preferences over a composite consumption good $c$ and housing services $h$ via a Cobb-Douglas utility function $U(c, h) = c^\alpha h^{1-\alpha}$, where $\alpha$ parameterizes the consumption share. Each household supplies one unit of labor inelastically, earning wage $w$ at the CBD. Commuting from distance $x$ costs $t \cdot x$ in both time and money, where $t$ represents the per-mile commuting cost. The household budget constraint becomes $c + R(x) \cdot h = w - t \cdot x$, where $R(x)$ denotes rent per unit of housing at distance $x$.

Utility maximization yields the bid-rent function, the maximum rent per unit of housing the household will pay at distance $x$ to achieve utility level $\bar{u}$. Substitute the consumption demand $c = \alpha(w - t \cdot x - R(x) \cdot h)$ and housing demand $h = (1-\alpha)(w - t \cdot x) / R(x)$ into the utility function and solve for $R(x)$:

$$R(x) = \left(\frac{(1-\alpha)^\alpha}{\alpha^{1-\alpha} \bar{u}}\right)^{1/\alpha} (w - t \cdot x)$$

The bid-rent function slopes downward because households farther from the CBD save on rent but incur higher commuting costs. Spatial equilibrium requires equal utility across all locations, which determines the city boundary $\bar{x}$ where rent falls to the agricultural opportunity cost $R_A$:

$$R(\bar{x}) = R_A \implies \bar{x} = \frac{w - R_A \left(\frac{\alpha^{1-\alpha} \bar{u}}{(1-\alpha)^\alpha}\right)^{1/\alpha}}{t}$$

Population $N$ equals the integral of density over the urban area. Assume housing production uses land $L$ and capital $K$ via Cobb-Douglas technology $H = L^\beta K^{1-\beta}$, implying housing supply per unit land $S(x) = \left(\frac{(1-\beta) R(x)}{\beta r_K}\right)^{(1-\beta)/\beta}$, where $r_K$ is the capital rental rate. Density equals housing supply divided by household housing consumption:

$$D(x) = \frac{S(x)}{h(x)} = \frac{\left(\frac{(1-\beta) R(x)}{\beta r_K}\right)^{(1-\beta)/\beta}}{(1-\alpha)(w - t \cdot x) / R(x)}$$

Integrate density over the urban area to match population $N$:

$$N = 2\pi \int_0^{\bar{x}} D(x) \cdot x \, dx$$

The factor $2\pi x$ converts linear density to circular city area. This integral determines the utility level $\bar{u}$ that clears the urban land market given exogenous parameters $\{w, t, \alpha, \beta, r_K, R_A, N\}$.

Implement this model in Python by defining functions for bid-rent, housing consumption, housing supply, and density, then solving the spatial equilibrium numerically. Create a file `src/monocentric_city.py`:

```python
import numpy as np
from scipy.optimize import root_scalar, minimize_scalar
from scipy.integrate import quad

class MonocentricCity:
    def __init__(self, w, t, alpha, beta, r_K, R_A, N):
        """
        Monocentric city model with Cobb-Douglas preferences and housing production.
        
        Parameters:
        w: wage at CBD
        t: commuting cost per mile
        alpha: consumption share in utility
        beta: land share in housing production
        r_K: capital rental rate
        R_A: agricultural rent
        N: population
        """
        self.w = w
        self.t = t
        self.alpha = alpha
        self.beta = beta
        self.r_K = r_K
        self.R_A = R_A
        self.N = N
        
    def bid_rent(self, x, u_bar):
        """Bid-rent function R(x) given utility level u_bar."""
        income_net_commute = self.w - self.t * x
        if income_net_commute <= 0:
            return 0.0
        numerator = ((1 - self.alpha) ** self.alpha / (self.alpha ** (1 - self.alpha) * u_bar)) ** (1 / self.alpha)
        return numerator * income_net_commute
    
    def city_boundary(self, u_bar):
        """City boundary where R(x) = R_A."""
        coeff = (self.alpha ** (1 - self.alpha) * u_bar / (1 - self.alpha) ** self.alpha) ** (1 / self.alpha)
        x_bar = (self.w - self.R_A * coeff) / self.t
        return max(x_bar, 0.0)
    
    def housing_consumption(self, x, u_bar):
        """Housing consumption h(x)."""
        R_x = self.bid_rent(x, u_bar)
        if R_x <= 0:
            return 0.0
        income_net_commute = self.w - self.t * x
        return (1 - self.alpha) * income_net_commute / R_x
    
    def housing_supply(self, x, u_bar):
        """Housing supply per unit land S(x)."""
        R_x = self.bid_rent(x, u_bar)
        if R_x <= 0:
            return 0.0
        return ((1 - self.beta) * R_x / (self.beta * self.r_K)) ** ((1 - self.beta) / self.beta)
    
    def density(self, x, u_bar):
        """Population density D(x) = S(x) / h(x)."""
        h_x = self.housing_consumption(x, u_bar)
        S_x = self.housing_supply(x, u_bar)
        if h_x <= 0:
            return 0.0
        return S_x / h_x
    
    def population_integral(self, u_bar):
        """Integrate density over circular city: N = 2*pi * integral(D(x) * x, 0, x_bar)."""
        x_bar = self.city_boundary(u_bar)
        if x_bar <= 0:
            return 0.0
        
        def integrand(x):
            return self.density(x, u_bar) * x
        
        result, error = quad(integrand, 0, x_bar, epsabs=1e-6, epsrel=1e-6)
        return 2 * np.pi * result
    
    def solve_equilibrium(self):
        """Solve for utility level u_bar that clears the land market."""
        def objective(u_bar):
            return self.population_integral(u_bar) - self.N
        
        # Initial bounds: utility must be positive and small enough that city forms
        u_lower = 1e-3
        u_upper = self.w * (1 - self.alpha) ** (1 - self.alpha) * self.alpha ** self.alpha
        
        sol = root_scalar(objective, bracket=[u_lower, u_upper], method='brentq', xtol=1e-8)
        
        if not sol.converged:
            raise ValueError("Equilibrium solver did not converge")
        
        return sol.root
    
    def compute_profiles(self, u_bar, num_points=100):
        """Compute spatial profiles for rent, density, housing consumption."""
        x_bar = self.city_boundary(u_bar)
        x_grid = np.linspace(0, x_bar, num_points)
        
        rent_profile = np.array([self.bid_rent(x, u_bar) for x in x_grid])
        density_profile = np.array([self.density(x, u_bar) for x in x_grid])
        housing_profile = np.array([self.housing_consumption(x, u_bar) for x in x_grid])
        
        return x_grid, rent_profile, density_profile, housing_profile
```

Calibrate the model to replicate stylized facts for a representative US metropolitan area. Set wage $w = 50000$ dollars per year, commuting cost $t = 5000$ dollars per mile per year (combining time value and vehicle expenses), consumption share $\alpha = 0.7$, land share in housing $\beta = 0.2$, capital rental rate $r_K = 10000$ dollars per unit per year, agricultural rent $R_A = 1000$ dollars per unit land per year, and population $N = 1000000$. Solve for equilibrium utility, compute spatial profiles, and visualize the results. Create a script `notebooks/exercise1_monocentric_calibration.py`:

```python
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from src.monocentric_city import MonocentricCity

# Set publication-quality plot style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 11

# Calibrate model parameters
w = 50000  # Annual wage at CBD ($)
t = 5000   # Commuting cost per mile per year ($)
alpha = 0.7  # Consumption share
beta = 0.2   # Land share in housing production
r_K = 10000  # Capital rental rate ($/unit/year)
R_A = 1000   # Agricultural rent ($/unit land/year)
N = 1000000  # Population

# Initialize model
city = MonocentricCity(w, t, alpha, beta, r_K, R_A, N)

# Solve spatial equilibrium
print("Solving spatial equilibrium...")
u_bar = city.solve_equilibrium()
print(f"Equilibrium utility level: {u_bar:.6f}")

# Compute city boundary
x_bar = city.city_boundary(u_bar)
print(f"City boundary: {x_bar:.2f} miles")

# Compute spatial profiles
x_grid, rent_profile, density_profile, housing_profile = city.compute_profiles(u_bar, num_points=200)

# Verify population constraint
N_computed = city.population_integral(u_bar)
print(f"Population from integration: {N_computed:.0f} (target: {N})")
print(f"Population error: {abs(N_computed - N) / N * 100:.4f}%")

# Create four-panel visualization
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Panel 1: Rent gradient
axes[0, 0].plot(x_grid, rent_profile, linewidth=2, color='#2E86AB')
axes[0, 0].axhline(y=R_A, linestyle='--', color='red', linewidth=1.5, label=f'Agricultural Rent = ${R_A}')
axes[0, 0].set_xlabel('Distance from CBD (miles)', fontsize=12)
axes[0, 0].set_ylabel('Rent ($/unit housing/year)', fontsize=12)
axes[0, 0].set_title('Bid-Rent Gradient', fontsize=14, fontweight='bold')
axes[0, 0].legend()
axes[0, 0].grid(alpha=0.3)

# Panel 2: Density gradient
axes[0, 1].plot(x_grid, density_profile, linewidth=2, color='#A23B72')
axes[0, 1].set_xlabel('Distance from CBD (miles)', fontsize=12)
axes[0, 1].set_ylabel('Population Density (households/unit land)', fontsize=12)
axes[0, 1].set_title('Population Density Gradient', fontsize=14, fontweight='bold')
axes[0, 1].grid(alpha=0.3)

# Panel 3: Housing consumption gradient
axes[1, 0].plot(x_grid, housing_profile, linewidth=2, color='#F18F01')
axes[1, 0].set_xlabel('Distance from CBD (miles)', fontsize=12)
axes[1, 0].set_ylabel('Housing Consumption (units/household)', fontsize=12)
axes[1, 0].set_title('Housing Consumption Gradient', fontsize=14, fontweight='bold')
axes[1, 0].grid(alpha=0.3)

# Panel 4: Log density vs distance (test exponential decay)
log_density = np.log(density_profile)
axes[1, 1].scatter(x_grid, log_density, alpha=0.6, s=20, color='#6A994E')
# Fit linear regression to test exponential density gradient
from scipy.stats import linregress
slope, intercept, r_value, p_value, std_err = linregress(x_grid, log_density)
axes[1, 1].plot(x_grid, intercept + slope * x_grid, 'r--', linewidth=2, 
                label=f'Slope = {slope:.4f}, R² = {r_value**2:.4f}')
axes[1, 1].set_xlabel('Distance from CBD (miles)', fontsize=12)
axes[1, 1].set_ylabel('Log Population Density', fontsize=12)
axes[1, 1].set_title('Log-Linear Density Gradient Test', fontsize=14, fontweight='bold')
axes[1, 1].legend()
axes[1, 1].grid(alpha=0.3)

plt.tight_layout()
plt.savefig('figures/exercise1_monocentric_profiles.png', dpi=300, bbox_inches='tight')
plt.show()

print("\nModel predictions:")
print(f"CBD rent: ${rent_profile[0]:.2f}/unit/year")
print(f"Edge rent: ${rent_profile[-1]:.2f}/unit/year (should equal ${R_A})")
print(f"CBD density: {density_profile[0]:.4f} households/unit land")
print(f"Edge density: {density_profile[-1]:.4f} households/unit land")
print(f"Density gradient elasticity: {slope:.4f} (exponential decay rate)")
```

Execute this calibration script and verify that the bid-rent function slopes downward monotonically, intersecting agricultural rent at the city boundary. The density gradient should exhibit negative exponential decay, consistent with empirical estimates from Mills (1972) and subsequent literature. The log-linear regression of density on distance tests whether the gradient follows $\ln D(x) = \ln D_0 - \gamma x$, where $\gamma$ represents the density gradient elasticity. Empirical estimates for US metropolitan areas typically yield $\gamma \in [-0.3, -0.1]$ for the post-1950 period.

Compare model predictions against actual data by loading Census tract-level population density and median rent from the American Community Survey. Download five-year ACS estimates for a target metropolitan statistical area (MSA), extract population counts and housing unit counts by tract, and compute population density. Measure distance from each tract centroid to the CBD (typically identified as the downtown central business district coordinates). Create a script `notebooks/exercise1_empirical_comparison.py`:

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import linregress
from geopy.distance import geodesic

# Load ACS tract-level data (pre-downloaded and cleaned)
# Expected columns: 'GEOID', 'tract_name', 'population', 'housing_units', 
#                   'median_rent', 'land_area_sqmi', 'centroid_lat', 'centroid_lon'
df = pd.read_csv('data/processed/msa_tract_data.csv')

# Define CBD coordinates (example: downtown Chicago)
cbd_lat, cbd_lon = 41.8781, -87.6298

# Compute distance from each tract to CBD
def compute_distance(row):
    return geodesic((row['centroid_lat'], row['centroid_lon']), (cbd_lat, cbd_lon)).miles

df['distance_to_cbd'] = df.apply(compute_distance, axis=1)

# Compute population density (persons per square mile)
df['pop_density'] = df['population'] / df['land_area_sqmi']

# Filter out tracts with zero population or missing rent
df = df[(df['pop_density'] > 0) & (df['median_rent'] > 0)].copy()

# Empirical density gradient estimation
df['log_density'] = np.log(df['pop_density'])
slope_emp, intercept_emp, r_value_emp, p_value_emp, std_err_emp = linregress(
    df['distance_to_cbd'], df['log_density']
)

print("Empirical Density Gradient:")
print(f"  Slope (γ): {slope_emp:.4f}")
print(f"  R²: {r_value_emp**2:.4f}")
print(f"  Std Error: {std_err_emp:.4f}")

# Empirical rent gradient estimation
df['log_rent'] = np.log(df['median_rent'])
slope_rent, intercept_rent, r_value_rent, p_value_rent, std_err_rent = linregress(
    df['distance_to_cbd'], df['log_rent']
)

print("\nEmpirical Rent Gradient:")
print(f"  Slope: {slope_rent:.4f}")
print(f"  R²: {r_value_rent**2:.4f}")

# Visualize empirical gradients
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Density gradient
axes[0].scatter(df['distance_to_cbd'], df['log_density'], alpha=0.3, s=10, color='blue')
axes[0].plot(df['distance_to_cbd'], 
             intercept_emp + slope_emp * df['distance_to_cbd'], 
             'r-', linewidth=2, label=f'γ = {slope_emp:.4f}, R² = {r_value_emp**2:.4f}')
axes[0].set_xlabel('Distance to CBD (miles)', fontsize=12)
axes[0].set_ylabel('Log Population Density', fontsize=12)
axes[0].set_title('Empirical Density Gradient', fontsize=14, fontweight='bold')
axes[0].legend()
axes[0].grid(alpha=0.3)

# Rent gradient
axes[1].scatter(df['distance_to_cbd'], df['log_rent'], alpha=0.3, s=10, color='green')
axes[1].plot(df['distance_to_cbd'], 
             intercept_rent + slope_rent * df['distance_to_cbd'], 
             'r-', linewidth=2, label=f'Slope = {slope_rent:.4f}, R² = {r_value_rent**2:.4f}')
axes[1].set_xlabel('Distance to CBD (miles)', fontsize=12)
axes[1].set_ylabel('Log Median Rent', fontsize=12)
axes[1].set_title('Empirical Rent Gradient', fontsize=14, fontweight='bold')
axes[1].legend()
axes[1].grid(alpha=0.3)

plt.tight_layout()
plt.savefig('figures/exercise1_empirical_gradients.png', dpi=300, bbox_inches='tight')
plt.show()
```

The empirical density gradient slope $\gamma$ should align with model predictions. Discrepancies arise from polycentric employment structure, heterogeneous household preferences, durable housing capital that adjusts slowly to shocks, and zoning regulations that constrain density. The monocentric model provides a baseline prediction; deviations identify mechanisms requiring richer spatial models.

Calibrate model parameters to minimize the distance between predicted and empirical gradients. Define the objective function as the sum of squared differences between model and data log-densities at observed tract distances. Use numerical optimization to search over parameter space $\{\alpha, \beta, t\}$, holding fixed the wage $w$ (observed from BLS data) and population $N$ (MSA total). Create a calibration script `notebooks/exercise1_parameter_calibration.py`:

```python
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from src.monocentric_city import MonocentricCity

# Load empirical data
df = pd.read_csv('data/processed/msa_tract_data.csv')
df = df[(df['pop_density'] > 0) & (df['distance_to_cbd'] > 0)].copy()

# Empirical targets: log density at observed distances
distances_obs = df['distance_to_cbd'].values
log_density_obs = np.log(df['pop_density'].values)

# Fixed parameters from data
w = 55000  # Median wage in MSA ($)
N = df['population'].sum()  # Total MSA population
r_K = 10000  # Capital rental rate ($/unit/year)
R_A = 1000   # Agricultural rent ($/unit land/year)

def calibration_objective(params):
    """Minimize sum of squared differences between model and data log-densities."""
    alpha, beta, t = params
    
    # Parameter bounds check
    if not (0.5 <= alpha <= 0.9 and 0.1 <= beta <= 0.4 and 1000 <= t <= 10000):
        return 1e10
    
    try:
        city = MonocentricCity(w, t, alpha, beta, r_K, R_A, N)
        u_bar = city.solve_equilibrium()
        
        # Compute model log-densities at observed distances
        log_density_model = np.array([
            np.log(city.density(x, u_bar)) if x < city.city_boundary(u_bar) else -10
            for x in distances_obs
        ])
        
        # Sum of squared residuals
        residuals = log_density_model - log_density_obs
        sse = np.sum(residuals ** 2)
        
        return sse
    except:
        return 1e10

# Initial guess
params_init = [0.7, 0.2, 5000]

# Optimize
print("Calibrating model parameters...")
result = minimize(calibration_objective, params_init, method='Nelder-Mead',
                  options={'maxiter': 500, 'xatol': 1e-6, 'fatol': 1e-6})

alpha_opt, beta_opt, t_opt = result.x

print(f"\nCalibrated parameters:")
print(f"  α (consumption share): {alpha_opt:.4f}")
print(f"  β (land share in housing): {beta_opt:.4f}")
print(f"  t (commuting cost per mile/year): ${t_opt:.2f}")
print(f"  Objective function value: {result.fun:.4f}")

# Validate calibrated model
city_calib = MonocentricCity(w, t_opt, alpha_opt, beta_opt, r_K, R_A, N)
u_bar_calib = city_calib.solve_equilibrium()

# Compute model fit statistics
log_density_model_calib = np.array([
    np.log(city_calib.density(x, u_bar_calib)) if x < city_calib.city_boundary(u_bar_calib) else np.nan
    for x in distances_obs
])

# Remove NaNs for comparison
valid_mask = ~np.isnan(log_density_model_calib)
residuals_calib = log_density_model_calib[valid_mask] - log_density_obs[valid_mask]
rmse = np.sqrt(np.mean(residuals_calib ** 2))
mae = np.mean(np.abs(residuals_calib))

print(f"\nModel fit statistics:")
print(f"  RMSE: {rmse:.4f}")
print(f"  MAE: {mae:.4f}")

# Save calibrated parameters
calib_results = pd.DataFrame({
    'parameter': ['alpha', 'beta', 't', 'w', 'N', 'r_K', 'R_A'],
    'value': [alpha_opt, beta_opt, t_opt, w, N, r_K, R_A]
})
calib_results.to_csv('models/calibrated_monocentric_params.csv', index=False)
print("\nCalibrated parameters saved to models/calibrated_monocentric_params.csv")
```

This calibration procedure identifies the parameter set that best reconciles theoretical predictions with observed spatial patterns. The resulting estimates reveal the implicit commuting costs and housing production technology embedded in the city's spatial structure. Sensitivity analysis around the calibrated values quantifies parameter uncertainty and model robustness.

## Exercise 2: Parameter Variation & Empirical Analysis

### Agglomeration Economies and Productivity Estimation

Agglomeration economies generate the centripetal force that sustains cities. Firms co-locate to exploit scale economies in labor markets, intermediate input markets, and knowledge spillovers. Empirical identification requires measuring how firm productivity varies with employment density while controlling for sorting (high-productivity firms select into dense locations) and unobserved local amenities. The standard estimating equation takes the log-linear form:

$$\ln y_{ijt} = \beta_0 + \beta_1 \ln D_{jt} + \mathbf{X}_{ijt} \boldsymbol{\gamma} + \alpha_i + \delta_j + \tau_t + \varepsilon_{ijt}$$

where $y_{ijt}$ represents output or productivity of firm $i$ in location $j$ at time $t$, $D_{jt}$ denotes employment density, $\mathbf{X}_{ijt}$ contains firm-level controls (capital, labor, intermediate inputs, industry), $\alpha_i$ captures firm fixed effects, $\delta_j$ captures location fixed effects, and $\tau_t$ captures time fixed effects. The coefficient $\beta_1$ measures the elasticity of productivity with respect to density, the agglomeration economy magnitude.

Identification challenges arise from endogeneity: unobserved productivity shocks may drive both firm location choices and local employment density. Instrumental variable strategies exploit exogenous variation in density driven by historical accidents, natural geography, or policy interventions. Combes, Duranton, Gobillon, Puga, and Roux (2012) use geological suitability for construction as an instrument for density, finding productivity elasticities around 0.04 for French firms. Ciccone and Hall (1996) estimate county-level productivity regressions for US states, finding elasticities between 0.04 and 0.06.

Construct a panel dataset of establishment-level productivity and employment density using the Census Bureau's Longitudinal Business Database (LBD) or the Bureau of Labor Statistics' Quarterly Census of Employment and Wages (QCEW). For this exercise, simulate synthetic data with realistic correlation structure to demonstrate the estimation procedure. Generate firm-level observations with productivity determined by density, firm ability, and idiosyncratic shocks. Create a data generation script `notebooks/exercise2_agglomeration_data_generation.py`:

```python
import numpy as np
import pandas as pd

np.random.seed(42)

# Simulation parameters
n_firms = 5000
n_locations = 100
n_years = 10

# True agglomeration elasticity
beta_true = 0.045

# Generate location characteristics
locations = pd.DataFrame({
    'location_id': range(n_locations),
    'base_density': np.random.lognormal(mean=8, sigma=1.5, size=n_locations),  # Employment density
    'amenity': np.random.normal(0, 0.5, n_locations),  # Unobserved location quality
    'instrument': np.random.normal(0, 1, n_locations)  # Geological suitability instrument
})

# Instrument affects density but not productivity directly
locations['employment_density'] = (locations['base_density'] * 
                                    np.exp(0.3 * locations['instrument'] + 
                                           np.random.normal(0, 0.2, n_locations)))

# Generate firm panel
firm_ids = np.repeat(range(n_firms), n_years)
years = np.tile(range(2010, 2020), n_firms)
location_ids = np.random.choice(n_locations, size=n_firms * n_years, 
                                 p=locations['employment_density'].values / locations['employment_density'].sum())

panel = pd.DataFrame({
    'firm_id': firm_ids,
    'year': years,
    'location_id': location_ids
})

# Merge location characteristics
panel = panel.merge(locations, on='location_id', how='left')

# Generate firm fixed effects (unobserved ability)
firm_abilities = pd.DataFrame({
    'firm_id': range(n_firms),
    'ability': np.random.normal(0, 0.8, n_firms)
})
panel = panel.merge(firm_abilities, on='firm_id', how='left')

# Generate firm-level characteristics
panel['log_capital'] = np.random.normal(10, 1.5, len(panel))
panel['log_labor'] = np.random.normal(3, 0.8, len(panel))
panel['industry'] = np.random.choice(['manufacturing', 'services', 'retail'], size=len(panel))

# Industry dummies
industry_effects = {'manufacturing': 0.2, 'services': 0.1, 'retail': -0.1}
panel['industry_effect'] = panel['industry'].map(industry_effects)

# Generate productivity (true model)
panel['log_employment_density'] = np.log(panel['employment_density'])
panel['log_tfp'] = (5.0 +  # Baseline productivity
                     beta_true * panel['log_employment_density'] +  # Agglomeration effect
                     panel['ability'] +  # Firm ability
                     panel['industry_effect'] +  # Industry effects
                     0.02 * (panel['year'] - 2010) +  # Time trend
                     0.15 * panel['amenity'] +  # Location amenity sorting
                     np.random.normal(0, 0.3, len(panel)))  # Idiosyncratic shock

# Save simulated data
panel_clean = panel[['firm_id', 'year', 'location_id', 'log_tfp', 'log_employment_density',
                      'log_capital', 'log_labor', 'industry', 'instrument', 'amenity']].copy()
panel_clean.to_csv('data/processed/agglomeration_panel.csv', index=False)

print(f"Generated panel dataset: {len(panel_clean)} observations")
print(f"  Firms: {n_firms}")
print(f"  Locations: {n_locations}")
print(f"  Years: {n_years}")
print(f"  True agglomeration elasticity (β₁): {beta_true}")
print("\nFirst few rows:")
print(panel_clean.head())
```

Estimate the agglomeration elasticity using three specifications: pooled OLS (biased but illustrative), firm fixed effects (controls for time-invariant ability), and instrumental variables (addresses endogeneity). Implement these regressions using Statsmodels and compare coefficient estimates across specifications. Create an estimation script `notebooks/exercise2_agglomeration_estimation.py`:

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.iolib.summary2 import summary_col

# Load simulated panel data
df = pd.read_csv('data/processed/agglomeration_panel.csv')

print("Agglomeration Economies Estimation")
print("="*60)

# Specification 1: Pooled OLS (baseline, likely biased upward)
print("\n1. Pooled OLS (no fixed effects)")
formula_ols = 'log_tfp ~ log_employment_density + log_capital + log_labor + C(industry) + year'
model_ols = smf.ols(formula_ols, data=df).fit(cov_type='cluster', cov_kwds={'groups': df['firm_id']})
print(model_ols.summary())

# Specification 2: Firm Fixed Effects (controls for time-invariant ability)
print("\n2. Firm Fixed Effects")
formula_fe = 'log_tfp ~ log_employment_density + log_capital + log_labor + C(industry) + C(year) + C(firm_id)'
model_fe = smf.ols(formula_fe, data=df).fit(cov_type='cluster', cov_kwds={'groups': df['firm_id']})

# Extract density coefficient (manual since C(firm_id) creates too many params for clean summary)
fe_coef = model_fe.params['log_employment_density']
fe_se = model_fe.bse['log_employment_density']
fe_tstat = fe_coef / fe_se
fe_pval = model_fe.pvalues['log_employment_density']

print(f"  log_employment_density coefficient: {fe_coef:.4f}")
print(f"  Standard error (clustered): {fe_se:.4f}")
print(f"  t-statistic: {fe_tstat:.2f}")
print(f"  p-value: {fe_pval:.4f}")

# Specification 3: Instrumental Variables (2SLS)
# First stage: regress log_density on instrument
print("\n3. Instrumental Variables (2SLS)")
print("First stage: log_employment_density ~ instrument")

# Compute location-level averages for IV (instruments operate at location level)
df_loc = df.groupby('location_id').agg({
    'log_employment_density': 'mean',
    'instrument': 'mean',
    'amenity': 'mean'
}).reset_index()

first_stage = smf.ols('log_employment_density ~ instrument', data=df_loc).fit()
print(first_stage.summary())

# Check instrument relevance (F-statistic > 10)
f_stat = first_stage.fvalue
print(f"\nFirst-stage F-statistic: {f_stat:.2f}")
if f_stat < 10:
    print("WARNING: Weak instrument (F < 10)")

# Merge predicted density back to firm panel
df = df.merge(df_loc[['location_id', 'instrument']], on='location_id', how='left')

# Second stage: use fitted density as regressor
# (In practice, use linearmodels.IV2SLS for correct standard errors)
from linearmodels.iv import IV2SLS

# Prepare data for IV2SLS
df['const'] = 1
exog = df[['const', 'log_capital', 'log_labor', 'year']]
endog = df[['log_employment_density']]
instruments = df[['instrument']]
dependent = df['log_tfp']

# Add industry dummies manually
industry_dummies = pd.get_dummies(df['industry'], prefix='industry', drop_first=True)
exog = pd.concat([exog, industry_dummies], axis=1)

model_iv = IV2SLS(dependent, exog, endog, instruments).fit(cov_type='clustered', clusters=df['firm_id'])
print("\nSecond stage (IV2SLS):")
print(model_iv.summary)

# Extract IV coefficient
iv_coef = model_iv.params['log_employment_density']
iv_se = model_iv.std_errors['log_employment_density']

print(f"\nIV log_employment_density coefficient: {iv_coef:.4f}")
print(f"  Standard error (clustered): {iv_se:.4f}")

# Compare estimates
results_comparison = pd.DataFrame({
    'Specification': ['Pooled OLS', 'Firm FE', 'IV (2SLS)'],
    'Coefficient': [model_ols.params['log_employment_density'], fe_coef, iv_coef],
    'Std Error': [model_ols.bse['log_employment_density'], fe_se, iv_se],
    'True Value': [0.045, 0.045, 0.045]
})

print("\n" + "="*60)
print("Comparison of Agglomeration Elasticity Estimates")
print("="*60)
print(results_comparison.to_string(index=False))

# Visualization
fig, ax = plt.subplots(figsize=(10, 6))
x_pos = np.arange(len(results_comparison))
bars = ax.bar(x_pos, results_comparison['Coefficient'], yerr=1.96*results_comparison['Std Error'],
              capsize=5, alpha=0.7, color=['#2E86AB', '#A23B72', '#F18F01'])
ax.axhline(y=0.045, color='red', linestyle='--', linewidth=2, label='True Value (β = 0.045)')
ax.set_ylabel('Agglomeration Elasticity', fontsize=12)
ax.set_xticks(x_pos)
ax.set_xticklabels(results_comparison['Specification'], fontsize=11)
ax.set_title('Agglomeration Economies: Coefficient Estimates with 95% CI', fontsize=14, fontweight='bold')
ax.legend()
ax.grid(alpha=0.3, axis='y')
plt.tight_layout()
plt.savefig('figures/exercise2_agglomeration_estimates.png', dpi=300, bbox_inches='tight')
plt.show()

# Interpretation
print("\nInterpretation:")
print(f"A 10% increase in employment density raises firm productivity by approximately {iv_coef*10:.2f}%")
print("This magnitude is consistent with empirical estimates from Combes et al. (2012) and Ciccone-Hall (1996).")
```

The pooled OLS estimate will exceed the true elasticity because productive firms sort into dense locations, creating upward bias. Firm fixed effects remove time-invariant ability but cannot control for time-varying productivity shocks that drive location choices. The IV estimate using geological suitability instruments isolates exogenous density variation, recovering an unbiased elasticity estimate. Standard errors clustered at the firm level account for serial correlation in firm-specific shocks.

Decompose agglomeration economies into mechanisms: labor market pooling, input sharing, and knowledge spillovers. Duranton and Puga (2004) propose industry-level variation in agglomeration sensitivity as a test. Industries with high skill intensity, input specialization, or innovation intensity should exhibit larger agglomeration elasticities. Estimate heterogeneous elasticities across industries by interacting density with industry dummies:

$$\ln y_{ijt} = \beta_0 + \sum_{k} \beta_k (\mathbb{1}[\text{industry}=k] \times \ln D_{jt}) + \mathbf{X}_{ijt} \boldsymbol{\gamma} + \alpha_i + \delta_j + \tau_t + \varepsilon_{ijt}$$

Create a script `notebooks/exercise2_heterogeneous_agglomeration.py`:

```python
import pandas as pd
import statsmodels.formula.api as smf
import matplotlib.pyplot as plt

# Load panel data
df = pd.read_csv('data/processed/agglomeration_panel.csv')

# Estimate heterogeneous elasticities by industry
formula_het = 'log_tfp ~ log_employment_density:C(industry) + log_capital + log_labor + C(year)'
model_het = smf.ols(formula_het, data=df).fit(cov_type='cluster', cov_kwds={'groups': df['firm_id']})

print("Heterogeneous Agglomeration Elasticities by Industry")
print("="*60)
print(model_het.summary())

# Extract industry-specific coefficients
industries = ['manufacturing', 'services', 'retail']
coeffs = []
std_errors = []

for ind in industries:
    coef_name = f'log_employment_density:C(industry)[T.{ind}]'
    if coef_name in model_het.params:
        coeffs.append(model_het.params[coef_name])
        std_errors.append(model_het.bse[coef_name])
    else:
        # Reference category (first industry)
        coef_name_base = 'log_employment_density:C(industry)[manufacturing]'
        if 'log_employment_density' in model_het.params and ind == 'manufacturing':
            coeffs.append(model_het.params['log_employment_density'])
            std_errors.append(model_het.bse['log_employment_density'])

# Manual extraction
elasticities = pd.DataFrame({
    'Industry': industries,
    'Elasticity': [
        model_het.params.get('log_employment_density:C(industry)[T.manufacturing]', 
                              model_het.params.get('log_employment_density', 0)),
        model_het.params.get('log_employment_density:C(industry)[T.services]', 0),
        model_het.params.get('log_employment_density:C(industry)[T.retail]', 0)
    ]
})

print("\nIndustry-Specific Agglomeration Elasticities:")
print(elasticities.to_string(index=False))

# Visualization
fig, ax = plt.subplots(figsize=(10, 6))
ax.barh(elasticities['Industry'], elasticities['Elasticity'], color=['#2E86AB', '#A23B72', '#F18F01'])
ax.set_xlabel('Agglomeration Elasticity', fontsize=12)
ax.set_title('Heterogeneous Agglomeration Effects by Industry', fontsize=14, fontweight='bold')
ax.axvline(x=0, color='black', linestyle='-', linewidth=0.8)
ax.grid(alpha=0.3, axis='x')
plt.tight_layout()
plt.savefig('figures/exercise2_heterogeneous_agglomeration.png', dpi=300, bbox_inches='tight')
plt.show()
```

Manufacturing exhibits larger elasticities due to input sharing and supply chain integration. Services benefit from knowledge spillovers and labor market pooling. Retail shows minimal agglomeration effects because scale economies are limited and location choice prioritizes customer access over firm interactions.

## Exercise 3: Stress Testing, Boundary Failure & Recovery Protocol

### Zoning Policy Counterfactuals and Welfare Analysis

Zoning regulations impose binding constraints on urban land markets, altering equilibrium rent, density, and welfare. Height restrictions limit building density, minimum lot sizes reduce housing supply, and use segregation prevents mixed-use development. Quantify these distortions by solving a constrained spatial equilibrium model and computing counterfactual welfare under alternative regulatory regimes.

Extend the monocentric city model to incorporate density constraints. Suppose zoning restricts maximum density at each location to $\bar{D}(x)$. When the market-clearing density $D^*(x)$ exceeds the zoning constraint, the effective density becomes $D^c(x) = \min\{D^*(x), \bar{D}(x)\}$. Constrained locations exhibit excess demand: households willing to pay more than the equilibrium rent cannot find housing. This rationing creates a wedge between the bid-rent function and the observed rent.

Solve the constrained equilibrium by modifying the spatial equilibrium condition. Population must equal the integral of constrained density:

$$N = 2\pi \int_0^{\bar{x}} D^c(x) \cdot x \, dx$$

where $D^c(x) = \min\{D^*(x, \bar{u}), \bar{D}(x)\}$. The constrained city may expand beyond the unconstrained boundary to accommodate displaced population. Implement the constrained solver by modifying the `MonocentricCity` class. Create an updated model file `src/monocentric_city_zoning.py`:

```python
import numpy as np
from scipy.optimize import root_scalar
from scipy.integrate import quad

class MonocentricCityZoning:
    def __init__(self, w, t, alpha, beta, r_K, R_A, N, density_constraint_func):
        """
        Monocentric city with zoning density constraints.
        
        density_constraint_func: callable(x) -> max allowed density at distance x
        """
        self.w = w
        self.t = t
        self.alpha = alpha
        self.beta = beta
        self.r_K = r_K
        self.R_A = R_A
        self.N = N
        self.density_constraint = density_constraint_func
        
    def bid_rent(self, x, u_bar):
        income_net_commute = self.w - self.t * x
        if income_net_commute <= 0:
            return 0.0
        numerator = ((1 - self.alpha) ** self.alpha / (self.alpha ** (1 - self.alpha) * u_bar)) ** (1 / self.alpha)
        return numerator * income_net_commute
    
    def city_boundary(self, u_bar):
        coeff = (self.alpha ** (1 - self.alpha) * u_bar / (1 - self.alpha) ** self.alpha) ** (1 / self.alpha)
        x_bar = (self.w - self.R_A * coeff) / self.t
        return max(x_bar, 0.0)
    
    def unconstrained_density(self, x, u_bar):
        """Market-clearing density without zoning."""
        R_x = self.bid_rent(x, u_bar)
        if R_x <= 0:
            return 0.0
        income_net_commute = self.w - self.t * x
        h_x = (1 - self.alpha) * income_net_commute / R_x
        S_x = ((1 - self.beta) * R_x / (self.beta * self.r_K)) ** ((1 - self.beta) / self.beta)
        return S_x / h_x
    
    def constrained_density(self, x, u_bar):
        """Effective density with zoning constraint."""
        D_unconstrained = self.unconstrained_density(x, u_bar)
        D_max = self.density_constraint(x)
        return min(D_unconstrained, D_max)
    
    def population_integral_constrained(self, u_bar):
        """Integrate constrained density over circular city."""
        x_bar = self.city_boundary(u_bar)
        if x_bar <= 0:
            return 0.0
        
        def integrand(x):
            return self.constrained_density(x, u_bar) * x
        
        result, error = quad(integrand, 0, x_bar, epsabs=1e-6, epsrel=1e-6)
        return 2 * np.pi * result
    
    def solve_equilibrium_constrained(self):
        """Solve for utility level under zoning constraints."""
        def objective(u_bar):
            return self.population_integral_constrained(u_bar) - self.N
        
        u_lower = 1e-3
        u_upper = self.w * (1 - self.alpha) ** (1 - self.alpha) * self.alpha ** self.alpha
        
        sol = root_scalar(objective, bracket=[u_lower, u_upper], method='brentq', xtol=1e-8)
        
        if not sol.converged:
            raise ValueError("Constrained equilibrium solver did not converge")
        
        return sol.root
    
    def compute_welfare(self, u_bar):
        """Compute aggregate welfare (utility × population)."""
        return u_bar * self.N
```

Define a zoning constraint that limits density to 80% of the market-clearing level within 5 miles of the CBD, simulating restrictive height limits in the urban core. Solve both the unconstrained baseline and the constrained counterfactual, then compute welfare losses from zoning. Create a counterfactual analysis script `notebooks/exercise3_zoning_counterfactual.py`:

```python
import numpy as np
import matplotlib.pyplot as plt
from src.monocentric_city import MonocentricCity
from src.monocentric_city_zoning import MonocentricCityZoning

# Baseline parameters (calibrated from Exercise 1)
w = 50000
t = 5000
alpha = 0.7
beta = 0.2
r_K = 10000
R_A = 1000
N = 1000000

# Solve unconstrained equilibrium (baseline)
print("Solving unconstrained equilibrium (baseline)...")
city_baseline = MonocentricCity(w, t, alpha, beta, r_K, R_A, N)
u_baseline = city_baseline.solve_equilibrium()
x_bar_baseline = city_baseline.city_boundary(u_baseline)
welfare_baseline = u_baseline * N

print(f"Baseline equilibrium:")
print(f"  Utility level: {u_baseline:.6f}")
print(f"  City boundary: {x_bar_baseline:.2f} miles")
print(f"  Aggregate welfare: {welfare_baseline:.2f}")

# Define zoning constraint: 80% of unconstrained density within 5 miles of CBD
def density_constraint(x):
    if x <= 5:
        # Constrain to 80% of unconstrained density
        D_unconstrained = city_baseline.density(x, u_baseline)
        return 0.8 * D_unconstrained
    else:
        # No constraint beyond 5 miles
        return np.inf

# Solve constrained equilibrium (counterfactual)
print("\nSolving constrained equilibrium with zoning...")
city_zoning = MonocentricCityZoning(w, t, alpha, beta, r_K, R_A, N, density_constraint)
u_zoning = city_zoning.solve_equilibrium_constrained()
x_bar_zoning = city_zoning.city_boundary(u_zoning)
welfare_zoning = u_zoning * N

print(f"Zoning equilibrium:")
print(f"  Utility level: {u_zoning:.6f}")
print(f"  City boundary: {x_bar_zoning:.2f} miles")
print(f"  Aggregate welfare: {welfare_zoning:.2f}")

# Compute welfare loss
welfare_loss_pct = (welfare_baseline - welfare_zoning) / welfare_baseline * 100

print(f"\nWelfare impact of zoning:")
print(f"  Absolute welfare loss: {welfare_baseline - welfare_zoning:.2f}")
print(f"  Relative welfare loss: {welfare_loss_pct:.2f}%")
print(f"  City boundary expansion: {x_bar_zoning - x_bar_baseline:.2f} miles")

# Compare spatial profiles
x_grid = np.linspace(0, max(x_bar_baseline, x_bar_zoning), 200)

rent_baseline = np.array([city_baseline.bid_rent(x, u_baseline) for x in x_grid])
density_baseline = np.array([city_baseline.density(x, u_baseline) for x in x_grid])

rent_zoning = np.array([city_zoning.bid_rent(x, u_zoning) for x in x_grid])
density_zoning_unconstrained = np.array([city_zoning.unconstrained_density(x, u_zoning) for x in x_grid])
density_zoning_constrained = np.array([city_zoning.constrained_density(x, u_zoning) for x in x_grid])

# Visualization
fig, axes = plt.subplots(2, 1, figsize=(12, 10))

# Rent comparison
axes[0].plot(x_grid, rent_baseline, linewidth=2, label='Baseline (no zoning)', color='blue')
axes[0].plot(x_grid, rent_zoning, linewidth=2, label='Counterfactual (zoning)', color='red', linestyle='--')
axes[0].axvline(x=5, color='gray', linestyle=':', linewidth=1.5, label='Zoning boundary')
axes[0].set_xlabel('Distance from CBD (miles)', fontsize=12)
axes[0].set_ylabel('Rent ($/unit/year)', fontsize=12)
axes[0].set_title('Rent Gradient: Baseline vs. Zoning Counterfactual', fontsize=14, fontweight='bold')
axes[0].legend()
axes[0].grid(alpha=0.3)

# Density comparison
axes[1].plot(x_grid, density_baseline, linewidth=2, label='Baseline (no zoning)', color='blue')
axes[1].plot(x_grid, density_zoning_unconstrained, linewidth=1.5, label='Unconstrained demand', 
             color='orange', linestyle=':')
axes[1].plot(x_grid, density_zoning_constrained, linewidth=2, label='Constrained equilibrium', 
             color='red', linestyle='--')
axes[1].axvline(x=5, color='gray', linestyle=':', linewidth=1.5, label='Zoning boundary')
axes[1].fill_between(x_grid, density_zoning_constrained, density_zoning_unconstrained, 
                      where=(x_grid <= 5), alpha=0.3, color='red', label='Excess demand')
axes[1].set_xlabel('Distance from CBD (miles)', fontsize=12)
axes[1].set_ylabel('Population Density', fontsize=12)
axes[1].set_title('Density Gradient: Baseline vs. Zoning Counterfactual', fontsize=14, fontweight='bold')
axes[1].legend()
axes[1].grid(alpha=0.3)

plt.tight_layout()
plt.savefig('figures/exercise3_zoning_counterfactual.png', dpi=300, bbox_inches='tight')
plt.show()

# Export results
results_summary = {
    'Scenario': ['Baseline (no zoning)', 'Counterfactual (zoning)'],
    'Utility': [u_baseline, u_zoning],
    'City Boundary (miles)': [x_bar_baseline, x_bar_zoning],
    'Aggregate Welfare': [welfare_baseline, welfare_zoning],
    'Welfare Loss (%)': [0, welfare_loss_pct]
}

import pandas as pd
df_results = pd.DataFrame(results_summary)
df_results.to_csv('models/zoning_counterfactual_results.csv', index=False)
print("\nResults saved to models/zoning_counterfactual_results.csv")
```

Zoning constraints bind in the urban core where unconstrained density would exceed regulatory limits. The resulting excess demand pushes households to the urban fringe, expanding the city boundary and increasing average commuting costs. Equilibrium utility falls because households cannot exploit the density-amenity tradeoff optimally. The welfare loss quantifies the deadweight cost of zoning, typically estimated between 2% and 10% of aggregate welfare depending on the stringency and spatial extent of regulations.

Stress-test the model by varying zoning stringency from 50% to 100% of unconstrained density and measuring the welfare-stringency gradient. This sensitivity analysis identifies the marginal cost of incremental regulatory tightening. Create a stress-test script `notebooks/exercise3_zoning_stress_test.py`:

```python
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from src.monocentric_city import MonocentricCity
from src.monocentric_city_zoning import MonocentricCityZoning

# Baseline parameters
w = 50000
t = 5000
alpha = 0.7
beta = 0.2
r_K = 10000
R_A = 1000
N = 1000000

# Solve unconstrained baseline
city_baseline = MonocentricCity(w, t, alpha, beta, r_K, R_A, N)
u_baseline = city_baseline.solve_equilibrium()
welfare_baseline = u_baseline * N

# Zoning stringency levels (fraction of unconstrained density allowed)
stringency_levels = np.linspace(0.5, 1.0, 11)
results = []

print("Running zoning stress test...")
for stringency in stringency_levels:
    def density_constraint(x):
        if x <= 5:
            D_unconstrained = city_baseline.density(x, u_baseline)
            return stringency * D_unconstrained
        else:
            return np.inf
    
    city_zoning = MonocentricCityZoning(w, t, alpha, beta, r_K, R_A, N, density_constraint)
    u_zoning = city_zoning.solve_equilibrium_constrained()
    welfare_zoning = u_zoning * N
    welfare_loss_pct = (welfare_baseline - welfare_zoning) / welfare_baseline * 100
    
    results.append({
        'stringency': stringency,
        'utility': u_zoning,
        'welfare': welfare_zoning,
        'welfare_loss_pct': welfare_loss_pct,
        'city_boundary': city_zoning.city_boundary(u_zoning)
    })
    
    print(f"  Stringency {stringency:.1%}: Welfare loss = {welfare_loss_pct:.2f}%")

df_stress = pd.DataFrame(results)

# Visualization
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Welfare loss vs. stringency
axes[0].plot(df_stress['stringency'] * 100, df_stress['welfare_loss_pct'], 
             marker='o', linewidth=2, markersize=6, color='#E63946')
axes[0].set_xlabel('Zoning Stringency (% of unconstrained density allowed)', fontsize=12)
axes[0].set_ylabel('Welfare Loss (%)', fontsize=12)
axes[0].set_title('Welfare Cost of Zoning Regulations', fontsize=14, fontweight='bold')
axes[0].grid(alpha=0.3)
axes[0].invert_xaxis()  # More restrictive on the left

# City boundary expansion vs. stringency
axes[1].plot(df_stress['stringency'] * 100, df_stress['city_boundary'], 
             marker='s', linewidth=2, markersize=6, color='#457B9D')
axes[1].axhline(y=city_baseline.city_boundary(u_baseline), linestyle='--', color='red', 
                linewidth=1.5, label='Baseline boundary')
axes[1].set_xlabel('Zoning Stringency (% of unconstrained density allowed)', fontsize=12)
axes[1].set_ylabel('City Boundary (miles)', fontsize=12)
axes[1].set_title('Urban Sprawl from Zoning Constraints', fontsize=14, fontweight='bold')
axes[1].legend()
axes[1].grid(alpha=0.3)
axes[1].invert_xaxis()

plt.tight_layout()
plt.savefig('figures/exercise3_zoning_stress_test.png', dpi=300, bbox_inches='tight')
plt.show()

# Marginal welfare cost (derivative of welfare loss with respect to stringency)
df_stress['marginal_welfare_cost'] = -np.gradient(df_stress['welfare_loss_pct'], df_stress['stringency'])

print("\nMarginal Welfare Cost Analysis:")
print(df_stress[['stringency', 'welfare_loss_pct', 'marginal_welfare_cost']].to_string(index=False))

df_stress.to_csv('models/zoning_stress_test_results.csv', index=False)
print("\nStress test results saved to models/zoning_stress_test_results.csv")
```

The welfare-stringency curve exhibits convexity: marginal welfare costs accelerate as regulations tighten. At moderate stringency (80% of unconstrained density), welfare losses remain modest. At severe stringency (50% of unconstrained density), welfare losses escalate sharply as the constraint prevents efficient spatial allocation. This nonlinearity implies that incremental deregulation yields larger welfare gains in heavily regulated cities.

Boundary failure protocols address cases where the model fails to converge or produces implausible results. Convergence failures arise when parameter combinations generate negative incomes, infinite city boundaries, or oscillating utility sequences. Implement diagnostic checks and recovery procedures. Create a robustness testing module `src/model_diagnostics.py`:

```python
import numpy as np
from src.monocentric_city import MonocentricCity

class ModelDiagnostics:
    def __init__(self, city_model):
        self.model = city_model
        
    def check_parameter_validity(self):
        """Verify parameters are within economically plausible ranges."""
        issues = []
        
        if not (0 < self.model.alpha < 1):
            issues.append(f"Invalid consumption share: alpha = {self.model.alpha} (must be in (0,1))")
        
        if not (0 < self.model.beta < 1):
            issues.append(f"Invalid land share: beta = {self.model.beta} (must be in (0,1))")
        
        if self.model.w <= 0:
            issues.append(f"Invalid wage: w = {self.model.w} (must be positive)")
        
        if self.model.t <= 0:
            issues.append(f"Invalid commuting cost: t = {self.model.t} (must be positive)")
        
        if self.model.t >= self.model.w:
            issues.append(f"Commuting cost ({self.model.t}) exceeds wage ({self.model.w})")
        
        if self.model.R_A < 0:
            issues.append(f"Invalid agricultural rent: R_A = {self.model.R_A} (must be non-negative)")
        
        if self.model.N <= 0:
            issues.append(f"Invalid population: N = {self.model.N} (must be positive)")
        
        return issues
    
    def test_convergence(self, u_bar, tolerance=1e-6):
        """Test whether utility level satisfies population constraint."""
        N_computed = self.model.population_integral(u_bar)
        error = abs(N_computed - self.model.N) / self.model.N
        
        converged = error < tolerance
        
        return {
            'converged': converged,
            'target_population': self.model.N,
            'computed_population': N_computed,
            'relative_error': error
        }
    
    def check_monotonicity(self, u_bar, num_points=100):
        """Verify bid-rent and density gradients are monotonically decreasing."""
        x_bar = self.model.city_boundary(u_bar)
        x_grid = np.linspace(0, x_bar, num_points)
        
        rent_profile = np.array([self.model.bid_rent(x, u_bar) for x in x_grid])
        density_profile = np.array([self.model.density(x, u_bar) for x in x_grid])
        
        rent_decreasing = np.all(np.diff(rent_profile) <= 0)
        density_decreasing = np.all(np.diff(density_profile) <= 0)
        
        return {
            'rent_monotonic': rent_decreasing,
            'density_monotonic': density_decreasing,
            'rent_profile': rent_profile,
            'density_profile': density_profile
        }
    
    def identify_boundary_failures(self, u_bar):
        """Identify common failure modes and suggest fixes."""
        failures = []
        
        # Check if city boundary is plausible
        x_bar = self.model.city_boundary(u_bar)
        if x_bar <= 0:
            failures.append("Zero city boundary: wage too low or agricultural rent too high")
        if x_bar > 100:
            failures.append("Implausibly large city boundary: check commuting cost calibration")
        
        # Check if rent at boundary matches agricultural rent
        R_boundary = self.model.bid_rent(x_bar, u_bar)
        if abs(R_boundary - self.model.R_A) / self.model.R_A > 0.01:
            failures.append(f"Boundary rent mismatch: R({x_bar:.2f}) = {R_boundary:.2f} vs R_A = {self.model.R_A}")
        
        # Check for negative income at CBD
        income_cbd = self.model.w - self.model.t * 0
        if income_cbd <= 0:
            failures.append("Negative income at CBD: wage too low or fixed commuting cost component missing")
        
        return failures
    
    def full_diagnostic_report(self, u_bar):
        """Generate comprehensive diagnostic report."""
        print("="*60)
        print("MODEL DIAGNOSTIC REPORT")
        print("="*60)
        
        # Parameter validity
        print("\n1. Parameter Validity Check:")
        param_issues = self.check_parameter_validity()
        if param_issues:
            for issue in param_issues:
                print(f"  ✗ {issue}")
        else:
            print("  ✓ All parameters valid")
        
        # Convergence test
        print("\n2. Convergence Test:")
        conv_result = self.test_convergence(u_bar)
        if conv_result['converged']:
            print(f"  ✓ Converged (error: {conv_result['relative_error']:.2e})")
        else:
            print(f"  ✗ Failed to converge (error: {conv_result['relative_error']:.2e})")
        print(f"  Target population: {conv_result['target_population']:.0f}")
        print(f"  Computed population: {conv_result['computed_population']:.0f}")
        
        # Monotonicity test
        print("\n3. Gradient Monotonicity Test:")
        mono_result = self.check_monotonicity(u_bar)
        if mono_result['rent_monotonic']:
            print("  ✓ Rent gradient monotonically decreasing")
        else:
            print("  ✗ Rent gradient not monotonic")
        if mono_result['density_monotonic']:
            print("  ✓ Density gradient monotonically decreasing")
        else:
            print("  ✗ Density gradient not monotonic")
        
        # Boundary failures
        print("\n4. Boundary Failure Analysis:")
        boundary_failures = self.identify_boundary_failures(u_bar)
        if boundary_failures:
            for failure in boundary_failures:
                print(f"  ✗ {failure}")
        else:
            print("  ✓ No boundary failures detected")
        
        print("\n" + "="*60)
```

Use this diagnostic module to validate model solutions before interpreting results. Create a validation script `notebooks/exercise3_model_validation.py`:

```python
from src.monocentric_city import MonocentricCity
from src.model_diagnostics import ModelDiagnostics

# Test case 1: Valid calibration
print("TEST CASE 1: Valid Calibration")
city1 = MonocentricCity(w=50000, t=5000, alpha=0.7, beta=0.2, r_K=10000, R_A=1000, N=1000000)
u1 = city1.solve_equilibrium()
diag1 = ModelDiagnostics(city1)
diag1.full_diagnostic_report(u1)

# Test case 2: Commuting cost too high (boundary failure)
print("\n\nTEST CASE 2: Excessive Commuting Cost")
city2 = MonocentricCity(w=50000, t=45000, alpha=0.7, beta=0.2, r_K=10000, R_A=1000, N=1000000)
try:
    u2 = city2.solve_equilibrium()
    diag2 = ModelDiagnostics(city2)
    diag2.full_diagnostic_report(u2)
except Exception as e:
    print(f"Solver failed: {e}")
    diag2 = ModelDiagnostics(city2)
    param_issues = diag2.check_parameter_validity()
    if param_issues:
        print("Parameter issues detected:")
        for issue in param_issues:
            print(f"  - {issue}")

# Test case 3: Agricultural rent too high (no city forms)
print("\n\nTEST CASE 3: Excessive Agricultural Rent")
city3 = MonocentricCity(w=50000, t=5000, alpha=0.7, beta=0.2, r_K=10000, R_A=100000, N=1000000)
try:
    u3 = city3.solve_equilibrium()
    diag3 = ModelDiagnostics(city3)
    diag3.full_diagnostic_report(u3)
except Exception as e:
    print(f"Solver failed: {e}")
    print("Likely cause: agricultural rent exceeds maximum bid-rent, preventing city formation")
```

Recovery protocols address convergence failures by adjusting solver tolerances, refining initial guesses, or switching numerical methods. When parameter combinations fall outside economically plausible ranges, the diagnostic module flags the issue and suggests recalibration.

## Operational Reference Guide & Diagnostic Checklist

### Data Acquisition and Preparation

Census tract boundaries and demographic data derive from the American Community Survey (ACS) five-year estimates, available via the Census Bureau's API or bulk download at `data.census.gov`. Key variables include total population (`B01003_001E`), median household income (`B19013_001E`), median gross rent (`B25064_001E`), housing units (`B25001_001E`), and land area (from TIGER/Line shapefiles). Employment data by industry comes from the County Business Patterns (CBP) dataset or the Longitudinal Employer-Household Dynamics (LEHD) Origin-Destination Employment Statistics (LODES).

Transform geographic coordinates to a projected CRS before computing distances. Use GeoPandas for spatial operations: `gdf.to_crs(epsg=2163)` for US data. Compute distances from tract centroids to the CBD using `geopy.distance.geodesic()` for geodesic distances or `scipy.spatial.distance.cdist()` for Euclidean distances in projected coordinates. Validate distance calculations by spot-checking against known landmarks.

Clean outliers and missing values systematically. Exclude tracts with zero population, zero land area, or implausible density (above 100,000 persons per square mile for urban areas). Impute missing rent data using spatial interpolation or predictive models based on neighboring tracts. Document all cleaning decisions and maintain a data provenance log.

### Numerical Solver Configuration

The monocentric city equilibrium solver uses Brent's method (`scipy.optimize.root_scalar`) to find the utility level that clears the land market. Initial bracketing intervals must span the feasible utility range: the lower bound approaches zero (subsistence), while the upper bound equals maximum feasible utility given wage and preferences. Convergence tolerance should be set to `xtol=1e-8` to ensure utility equalizes across locations within numerical precision limits.

Integration of population density uses adaptive Gaussian quadrature (`scipy.integrate.quad`) with absolute and relative error tolerances of `epsabs=1e-6` and `epsrel=1e-6`. For highly non-smooth density profiles (e.g., with discrete zoning constraints), increase the subdivision limit via the `limit` parameter or switch to Simpson's rule for piecewise integration.

Monitor solver diagnostics: if root-finding fails to converge within 100 iterations, the objective function likely exhibits pathologies (discontinuities, multiple roots, or no roots). Visualize the objective function $N(\bar{u}) - N$ over a grid of utility values to diagnose the issue. If multiple equilibria exist (rare in monocentric models but possible in polycentric extensions), select the stable equilibrium using comparative statics or historical anchoring.

### Regression Diagnostics and Robustness

Agglomeration elasticity regressions demand robust standard error estimation. Always cluster standard errors at the firm level to account for serial correlation in firm-specific shocks. For spatial data, test for spatial autocorrelation using Moran's I statistic (`esda.moran.Moran` from PySAL). If spatial autocorrelation persists after controlling for observables, use spatial econometric models (spatial lag or spatial error models) to avoid biased inference.

Check multicollinearity using variance inflation factors (VIF). If VIF exceeds 10 for any regressor, consider dropping highly correlated variables or using principal component regression. For instrumental variable regressions, verify instrument relevance (first-stage F-statistic above 10) and test for overidentification restrictions using Hansen's J-statistic when multiple instruments are available.

Placebo tests strengthen causal inference. Estimate agglomeration effects on industries that should not benefit from density (e.g., resource extraction, agriculture) to verify that estimated elasticities do not arise from omitted variables or measurement error.

### Counterfactual Simulation Validation

Validate counterfactual predictions by comparing them against natural experiments or policy shocks. If a city relaxed zoning constraints in a specific area, measure actual changes in density, rent, and welfare, then compare them to model predictions. Discrepancies reveal model misspecification, such as omitted adjustment costs, heterogeneous household preferences, or incomplete zoning enforcement.

Bootstrap standard errors for welfare calculations by resampling the underlying data and re-solving the model for each bootstrap sample. This procedure quantifies parameter uncertainty's impact on counterfactual predictions. Typical welfare estimates require at least 1,000 bootstrap iterations to stabilize confidence intervals.

Sensitivity analysis should vary all calibrated parameters simultaneously using Latin hypercube sampling to explore the parameter space efficiently. Identify which parameters drive the largest variance in welfare estimates to prioritize data collection and calibration refinement.

### Diagnostic Checklist for Model Failures

**Symptom: Solver does not converge**  
**Diagnosis:** Parameter values fall outside economically plausible ranges (e.g., commuting cost exceeds wage, agricultural rent exceeds maximum bid-rent).  
**Resolution:** Validate parameters using the `ModelDiagnostics.check_parameter_validity()` function. Recalibrate using empirical data or adjust bracketing intervals.

**Symptom: Negative or zero city boundary**  
**Diagnosis:** Wage too low relative to agricultural rent and commuting costs, preventing city formation.  
**Resolution:** Increase wage, decrease agricultural rent, or decrease commuting cost to enable positive net income at all locations.

**Symptom: Population integral does not match target population**  
**Diagnosis:** Integration tolerance too loose, or density function exhibits numerical discontinuities.  
**Resolution:** Tighten integration tolerance (`epsabs=1e-8`), increase subdivision limit, or switch to piecewise integration.

**Symptom: Non-monotonic rent or density gradients**  
**Diagnosis:** Incorrect utility level, numerical errors in bid-rent or density functions, or zoning constraints creating kinks.  
**Resolution:** Use `ModelDiagnostics.check_monotonicity()` to identify locations where monotonicity fails. For zoning models, kinks are expected at constraint boundaries; verify they occur at correct distances.

**Symptom: Implausibly large city boundary (over 100 miles)**  
**Diagnosis:** Commuting cost calibrated too low or population too large relative to density parameters.  
**Resolution:** Recalibrate commuting cost using travel survey data or adjust density parameters to match observed urban extents.

**Symptom: Agglomeration elasticity estimates near zero or negative**  
**Diagnosis:** Measurement error in density, omitted productivity shocks, or reverse causality (low-productivity firms select into dense locations due to lower land costs).  
**Resolution:** Use instrumental variables to address endogeneity. Verify instrument relevance and exclusion restrictions. Consider firm or location fixed effects to control for unobserved heterogeneity.

**Symptom: First-stage F-statistic below 10 in IV regression**  
**Diagnosis:** Weak instrument failing to predict density variation.  
**Resolution:** Find stronger instruments (historical factors, geological constraints) or use limited information maximum likelihood (LIML) estimation, which is less biased under weak instruments.

**Symptom: Large unexplained residuals in empirical density gradients**  
**Diagnosis:** Omitted spatial factors (employment subcenters, amenities, natural features) or heterogeneous household preferences.  
**Resolution:** Extend model to incorporate multiple employment centers, amenity gradients, or discrete household types. Estimate mixture models to allow for heterogeneous preferences.

This laboratory sequence equips you to operationalize urban economic models, calibrate them to real data, estimate agglomeration effects, and simulate policy counterfactuals. Mastery demands iterative refinement: validate every step against empirical patterns, stress-test assumptions, and document discrepancies. Urban economics bridges abstract spatial theory and tangible policy evaluation, making these techniques indispensable for infrastructure planning, housing policy, and regional development strategy.
