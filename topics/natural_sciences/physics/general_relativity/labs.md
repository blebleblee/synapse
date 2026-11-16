# Operational Verification Labs: General Relativity

## Objective & Laboratory Bench Setup

General relativity stands as Einstein's geometric theory of gravitation, replacing Newton's instantaneous force-at-a-distance with the curvature of spacetime itself. While the full mathematical machinery of differential geometry and tensor calculus remains essential for theoretical development, the experimental physicist must ground these abstractions in measurable phenomena: the bending of starlight near massive bodies, the precession of planetary orbits, gravitational time dilation measured by atomic clocks, and the recent direct detection of gravitational waves. This laboratory guide prioritizes empirical verification techniques, computational modeling of observable effects, and error analysis protocols that connect Einstein's field equations to precision measurements.

The laboratory bench for general relativity verification differs fundamentally from traditional terrestrial physics setups. We operate primarily through computational simulation of astrophysical observables, analysis of published astronomical datasets, and precise timing measurements using GPS satellite telemetry. The core theoretical foundation rests on Einstein's field equations, which relate the curvature of spacetime (encoded in the Einstein tensor $G_{\mu\nu}$) to the energy-momentum distribution of matter and radiation (the stress-energy tensor $T_{\mu\nu}$):

$$G_{\mu\nu} + \Lambda g_{\mu\nu} = \frac{8\pi G}{c^4} T_{\mu\nu}$$

where $G$ denotes Newton's gravitational constant, $c$ the speed of light, $g_{\mu\nu}$ the metric tensor describing spacetime geometry, and $\Lambda$ the cosmological constant. For weak gravitational fields and slow velocities compared to light speed, these equations reduce to Newtonian gravity as a limiting case, but predict measurable deviations that constitute our experimental targets.

Your laboratory workstation requires a scientific Python environment with NumPy for numerical tensor operations, SciPy for integration of geodesic equations and root-finding algorithms, Matplotlib for visualization of spacetime trajectories and light deflection angles, and Astropy for handling astronomical coordinate systems and time standards. Verify installation integrity by executing `python -c 'import numpy, scipy, matplotlib, astropy; print("NumPy:", numpy.__version__, "SciPy:", scipy.__version__, "Astropy:", astropy.__version__)'` which should return version numbers for each package without import errors. Additionally, you will need access to published datasets: the orbital parameters of Mercury from JPL Horizons ephemerides, GPS satellite timing corrections documented in Interface Control Documents, and optionally gravitational wave strain data from the LIGO Open Science Center for advanced exercises.

The experimental methodology follows a three-stage protocol. First, we compute predictions from general relativity for specific observable effects using numerical integration of the equations of motion in curved spacetime. Second, we compare these predictions against either historical measurements (such as the 1919 Eddington eclipse expedition photographs) or modern high-precision data (GPS timing residuals, pulsar timing arrays). Third, we quantify the statistical significance of any deviations from Newtonian expectations and propagate measurement uncertainties through our computational models to establish confidence intervals on fundamental parameters like the post-Newtonian parameter $\gamma$ that characterizes the amount of spatial curvature per unit rest mass.

## Exercise 1: Empirical Observation & Measurement Protocol

The perihelion precession of Mercury provided the first quantitative confirmation of general relativity. Newton's theory predicts a closed elliptical orbit, but perturbations from other planets cause the perihelion (point of closest approach to the Sun) to slowly advance. After accounting for all Newtonian perturbations, a residual precession of approximately 43 arcseconds per century remained unexplained until Einstein's 1915 calculation from general relativity matched this value precisely. This exercise constructs a computational model of Mercury's orbit in the Schwarzschild spacetime surrounding the Sun, integrates the geodesic equations numerically, and extracts the perihelion precession rate for comparison against astronomical observations.

The Schwarzschild metric describes the spacetime geometry outside a spherically symmetric, non-rotating mass $M$. In standard Schwarzschild coordinates $(t, r, \theta, \phi)$ with geometric units where $G = c = 1$, the line element takes the form:

$$ds^2 = -\left(1 - \frac{2M}{r}\right)dt^2 + \left(1 - \frac{2M}{r}\right)^{-1}dr^2 + r^2(d\theta^2 + \sin^2\theta \, d\phi^2)$$

The Schwarzschild radius $r_s = 2GM/c^2$ defines the event horizon for a black hole, but for the Sun with $M_\odot = 1.989 \times 10^{30}$ kg, this yields $r_s \approx 2.95$ km, far smaller than the solar radius of 696,000 km. Mercury's orbital radius ranges from approximately $4.6 \times 10^{10}$ m at perihelion to $6.98 \times 10^{10}$ m at aphelion, yielding $r/r_s \sim 10^7$, a regime where relativistic corrections remain small but measurable.

For equatorial orbits ($\theta = \pi/2$), the geodesic equations reduce to a one-dimensional effective potential problem. The constants of motion—specific energy $\tilde{E} = (1 - 2M/r)\dot{t}$ and specific angular momentum $\tilde{L} = r^2\dot{\phi}$—allow elimination of coordinate time derivatives. The radial equation of motion becomes:

$$\left(\frac{dr}{d\lambda}\right)^2 = \tilde{E}^2 - \left(1 - \frac{2M}{r}\right)\left(1 + \frac{\tilde{L}^2}{r^2}\right)$$

where $\lambda$ denotes proper time along the worldline. The azimuthal equation $d\phi/dr$ can be derived by chain rule, yielding:

$$\frac{d\phi}{dr} = \frac{\tilde{L}/r^2}{\sqrt{\tilde{E}^2 - (1 - 2M/r)(1 + \tilde{L}^2/r^2)}}$$

The perihelion precession emerges as the difference between the azimuthal advance $\Delta\phi$ over one radial period and the Newtonian value of $2\pi$. For nearly circular orbits, the leading-order relativistic correction produces an advance per orbit of:

$$\Delta\phi_{\text{precession}} = \frac{6\pi GM}{c^2 a(1 - e^2)}$$

where $a$ denotes the semi-major axis and $e$ the orbital eccentricity. For Mercury with $a = 5.79 \times 10^{10}$ m and $e = 0.2056$, this predicts approximately 0.103 arcseconds per orbit, accumulating to 43 arcseconds per century given Mercury's 88-day orbital period.

Begin by creating a Python script `mercury_precession.py` that numerically integrates the orbital equations. Define physical constants in SI units to avoid unit conversion errors:

```python
import numpy as np
from scipy.integrate import solve_ivp
import matplotlib.pyplot as plt

# Physical constants (SI units)
G = 6.67430e-11  # m^3 kg^-1 s^-2
c = 299792458.0  # m/s
M_sun = 1.98892e30  # kg
AU = 1.495978707e11  # meters

# Mercury orbital parameters
a_mercury = 0.387098 * AU  # semi-major axis
e_mercury = 0.205630  # eccentricity
r_perihelion = a_mercury * (1 - e_mercury)
r_aphelion = a_mercury * (1 + e_mercury)

# Schwarzschild radius
r_s = 2 * G * M_sun / c**2
print(f"Solar Schwarzschild radius: {r_s:.2f} m = {r_s/1000:.3f} km")
print(f"Mercury perihelion: {r_perihelion/AU:.4f} AU = {r_perihelion/r_s:.2e} r_s")

# Compute specific energy and angular momentum
# For elliptical orbit: E = -GM/(2a), L = sqrt(GMa(1-e^2))
E_orbit = -G * M_sun / (2 * a_mercury)
L_orbit = np.sqrt(G * M_sun * a_mercury * (1 - e_mercury**2))

# Specific quantities (per unit test mass)
E_tilde = E_orbit / c**2  # dimensionless
L_tilde = L_orbit / c  # dimension [length]

print(f"Specific energy: {E_tilde:.6e}")
print(f"Specific angular momentum: {L_tilde:.6e} m")
```

The integration strategy follows the radial equation directly. Define the right-hand side function for `dr/dphi` by inverting the azimuthal derivative:

```python
def schwarzschild_orbit_rhs(phi, r, E_tilde, L_tilde, M, c):
    """
    Right-hand side for dr/dphi in Schwarzschild spacetime.
    
    Parameters:
        phi: azimuthal angle (independent variable)
        r: radial coordinate [m]
        E_tilde, L_tilde: conserved specific energy and angular momentum
        M: central mass [kg]
        c: speed of light [m/s]
    
    Returns:
        dr/dphi
    """
    r_s = 2 * G * M / c**2
    
    # Effective potential term
    V_eff_squared = (1 - r_s/r) * (1 + (L_tilde/r)**2)
    discriminant = E_tilde**2 - V_eff_squared
    
    if discriminant < 0:
        # Unphysical regime (particle cannot reach this radius)
        return 0.0
    
    # dphi/dr from geodesic equation
    dphi_dr = (L_tilde / r**2) / np.sqrt(discriminant)
    
    # Return dr/dphi (reciprocal)
    if dphi_dr > 1e-15:
        return 1.0 / dphi_dr
    else:
        return 0.0

# Initial conditions at perihelion
r0 = r_perihelion
phi0 = 0.0

# Integrate over multiple orbits to observe precession
phi_span = (0, 10 * 2 * np.pi)  # 10 orbits
phi_eval = np.linspace(0, 10 * 2 * np.pi, 10000)

solution = solve_ivp(
    schwarzschild_orbit_rhs,
    phi_span,
    [r0],
    args=(E_tilde, L_tilde, M_sun, c),
    t_eval=phi_eval,
    method='RK45',
    rtol=1e-10,
    atol=1e-12
)

phi_vals = solution.t
r_vals = solution.y[0]
```

To extract the precession angle, identify successive perihelion passages (local minima in $r(\phi)$) and measure the azimuthal separation between them:

```python
# Find perihelion passages (local minima in r)
from scipy.signal import find_peaks

# Invert to find minima as peaks of -r
peaks, _ = find_peaks(-r_vals, prominence=1e9)

if len(peaks) > 1:
    perihelion_angles = phi_vals[peaks]
    perihelion_radii = r_vals[peaks]
    
    print("\nPerihelion passages:")
    for i, (phi_p, r_p) in enumerate(zip(perihelion_angles, perihelion_radii)):
        print(f"  Orbit {i}: φ = {phi_p:.6f} rad, r = {r_p/AU:.6f} AU")
    
    # Measure precession per orbit
    delta_phi_per_orbit = np.diff(perihelion_angles)
    precession_per_orbit = delta_phi_per_orbit - 2 * np.pi
    
    print(f"\nPrecession per orbit (first orbit): {precession_per_orbit[0]:.6e} rad")
    print(f"  = {np.degrees(precession_per_orbit[0]) * 3600:.6f} arcsec/orbit")
    
    # Analytical prediction
    precession_analytic = 6 * np.pi * G * M_sun / (c**2 * a_mercury * (1 - e_mercury**2))
    print(f"\nAnalytical GR prediction: {precession_analytic:.6e} rad/orbit")
    print(f"  = {np.degrees(precession_analytic) * 3600:.6f} arcsec/orbit")
    
    # Convert to arcsec/century
    mercury_period_days = 87.969  # days
    orbits_per_century = 100 * 365.25 / mercury_period_days
    precession_per_century = np.degrees(precession_per_orbit[0]) * 3600 * orbits_per_century
    
    print(f"\nPrecession rate: {precession_per_century:.2f} arcsec/century")
    print(f"Observed (after Newtonian corrections): 43.0 ± 0.5 arcsec/century")
```

Visualize the orbit in polar coordinates to observe the rosette pattern characteristic of perihelion precession:

```python
# Convert to Cartesian for plotting
x_vals = r_vals * np.cos(phi_vals)
y_vals = r_vals * np.sin(phi_vals)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

# Polar plot
ax1.plot(phi_vals, r_vals / AU, linewidth=0.8)
ax1.axhline(r_perihelion / AU, color='red', linestyle='--', linewidth=1, alpha=0.5, label='Perihelion')
ax1.axhline(r_aphelion / AU, color='blue', linestyle='--', linewidth=1, alpha=0.5, label='Aphelion')
ax1.set_xlabel('Azimuthal angle φ [rad]', fontsize=11)
ax1.set_ylabel('Radial distance r [AU]', fontsize=11)
ax1.set_title('Mercury Orbit in Schwarzschild Spacetime', fontsize=12, fontweight='bold')
ax1.legend()
ax1.grid(True, alpha=0.3)

# Cartesian trajectory
ax2.plot(x_vals / AU, y_vals / AU, linewidth=0.8)
ax2.scatter([0], [0], c='orange', s=200, marker='o', label='Sun', zorder=5)
ax2.scatter(x_vals[peaks] / AU, y_vals[peaks] / AU, c='red', s=40, marker='x', label='Perihelia', zorder=4)
ax2.set_xlabel('x [AU]', fontsize=11)
ax2.set_ylabel('y [AU]', fontsize=11)
ax2.set_title('Orbital Rosette Pattern (10 Orbits)', fontsize=12, fontweight='bold')
ax2.axis('equal')
ax2.legend()
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('mercury_precession.png', dpi=300, bbox_inches='tight')
plt.show()
```

Execute the complete script with `python mercury_precession.py`. The numerical integration should yield a precession of approximately 0.103 arcseconds per orbit, accumulating to 43 arcseconds per century—matching both the analytical general relativity prediction and the observed astronomical value after subtracting Newtonian perturbations from other planets. The primary sources of numerical error arise from the finite integration tolerance (controlled by `rtol` and `atol` parameters) and the accuracy of the initial orbital parameters. Mercury's eccentricity varies slightly due to planetary perturbations; using time-averaged elements from the JPL Horizons system ensures consistency with published ephemerides.

The measurement protocol for comparison against observational data requires obtaining Mercury's actual perihelion longitude as a function of time from precise astrometric catalogs. The JPL Horizons system provides high-accuracy ephemerides incorporating both general relativistic and Newtonian perturbations. For a hands-on verification exercise, query the Horizons system for Mercury's heliocentric orbital elements over a century-long baseline, extract the argument of perihelion $\omega(t)$, and fit a linear trend to obtain the observed precession rate. The residual after subtracting all known Newtonian perturbations (primarily from Venus, Earth, and Jupiter) yields the general relativistic component, which should match the 43 arcsecond per century prediction within observational uncertainties of order 0.5 arcseconds per century arising from uncertainties in planetary masses and the solar quadrupole moment.

## Exercise 2: Parameter Variation, Calibration & Response Curve Plotting

Gravitational time dilation represents one of the most precisely tested predictions of general relativity, verified daily by the GPS satellite navigation system. Clocks in orbit experience both special relativistic time dilation due to their orbital velocity and general relativistic gravitational time dilation due to the weaker gravitational potential at altitude. The net effect requires satellite clocks to tick faster than ground-based clocks by approximately 38 microseconds per day; without correcting for this relativistic offset, GPS position errors would accumulate at roughly 10 kilometers per day. This exercise constructs a detailed model of GPS clock corrections, computes the fractional frequency shift as a function of orbital parameters, and generates calibration curves showing the dependence on altitude, eccentricity, and Earth's gravitational field strength.

The proper time $\tau$ measured by a clock moving along a worldline relates to coordinate time $t$ through the metric:

$$d\tau = \sqrt{-g_{\mu\nu}\frac{dx^\mu}{d\lambda}\frac{dx^\nu}{d\lambda}} \, d\lambda$$

For a clock in a circular orbit at radius $r$ around a spherical mass $M$, the Schwarzschild metric yields:

$$\frac{d\tau}{dt} = \sqrt{\left(1 - \frac{2GM}{c^2 r}\right) - \frac{v^2}{c^2}}$$

where $v = r\Omega$ denotes the orbital velocity and $\Omega$ the angular frequency. The first term captures gravitational redshift (general relativistic effect), while the second encodes special relativistic kinematic time dilation. For a satellite in a circular orbit, the gravitational and kinetic terms partially cancel. The orbital velocity satisfies $v^2 = GM/r$ from Newtonian dynamics, allowing the proper time ratio to be expressed as:

$$\frac{d\tau}{dt} = \sqrt{1 - \frac{3GM}{c^2 r}} \approx 1 - \frac{3GM}{2c^2 r}$$

in the weak-field limit. A clock on Earth's surface at radius $R_E$ runs at rate:

$$\frac{d\tau_{\text{ground}}}{dt} \approx 1 - \frac{GM}{c^2 R_E}$$

The fractional frequency difference between an orbiting satellite clock and a ground clock becomes:

$$\frac{\Delta f}{f} = \frac{d\tau_{\text{sat}}}{dt} - \frac{d\tau_{\text{ground}}}{dt} \approx \frac{GM}{c^2}\left(\frac{1}{R_E} - \frac{3}{2r}\right)$$

For GPS satellites orbiting at approximately 20,200 km altitude ($r \approx 26,600$ km from Earth's center, compared to $R_E = 6371$ km), this evaluates to roughly $+4.5 \times 10^{-10}$, corresponding to a clock rate increase of 45 microseconds per day. Including the special relativistic effect separately (a decrease of about 7 microseconds per day for the orbital velocity of 3.87 km/s), the net correction is approximately $+38$ microseconds per day.

Create a Python script `gps_time_dilation.py` to compute these corrections as functions of orbital parameters:

```python
import numpy as np
import matplotlib.pyplot as plt

# Physical constants
G = 6.67430e-11  # m^3 kg^-1 s^-2
c = 299792458.0  # m/s
M_earth = 5.972e24  # kg
R_earth = 6.371e6  # m (mean radius)

# GPS satellite parameters
h_gps = 20.2e6  # altitude above surface [m]
r_gps = R_earth + h_gps  # orbital radius

def gravitational_time_dilation(r, M, R_surface):
    """
    Compute fractional frequency shift due to gravitational potential difference.
    
    Parameters:
        r: orbital radius [m]
        M: central body mass [kg]
        R_surface: surface radius [m]
    
    Returns:
        Δf/f (dimensionless, positive means satellite clock runs faster)
    """
    # Gravitational potential at satellite
    phi_sat = -G * M / r
    # Gravitational potential at surface
    phi_surf = -G * M / R_surface
    # Frequency shift: Δf/f = Δφ/c^2
    return (phi_sat - phi_surf) / c**2

def kinematic_time_dilation(v):
    """
    Compute special relativistic time dilation for velocity v.
    
    Parameters:
        v: velocity [m/s]
    
    Returns:
        Δf/f (dimensionless, negative for moving clock)
    """
    gamma = 1.0 / np.sqrt(1 - (v/c)**2)
    # Moving clock runs slower: Δf/f = 1 - γ ≈ -v^2/(2c^2)
    return 1 - gamma

def orbital_velocity(r, M):
    """
    Circular orbital velocity from Newtonian dynamics.
    
    Parameters:
        r: orbital radius [m]
        M: central body mass [kg]
    
    Returns:
        v: orbital velocity [m/s]
    """
    return np.sqrt(G * M / r)

# GPS satellite time dilation
v_gps = orbital_velocity(r_gps, M_earth)
delta_f_grav = gravitational_time_dilation(r_gps, M_earth, R_earth)
delta_f_kin = kinematic_time_dilation(v_gps)
delta_f_total = delta_f_grav + delta_f_kin

print("GPS Satellite Time Dilation Analysis")
print("=" * 50)
print(f"Orbital altitude: {h_gps/1e6:.2f} km")
print(f"Orbital radius: {r_gps/1e6:.2f} km")
print(f"Orbital velocity: {v_gps/1e3:.3f} km/s")
print(f"\nGravitational time dilation (GR): {delta_f_grav:.6e}")
print(f"  → Clock rate shift: {delta_f_grav * 86400 * 1e6:.2f} μs/day")
print(f"\nKinematic time dilation (SR): {delta_f_kin:.6e}")
print(f"  → Clock rate shift: {delta_f_kin * 86400 * 1e6:.2f} μs/day")
print(f"\nTotal fractional frequency shift: {delta_f_total:.6e}")
print(f"  → Net clock rate shift: {delta_f_total * 86400 * 1e6:.2f} μs/day")
print(f"\nObserved GPS correction: ~38 μs/day (satellite faster than ground)")
```

Generate calibration curves showing the dependence of time dilation on orbital altitude. Sweep altitude from low Earth orbit (200 km) to geostationary orbit (35,786 km) and plot the gravitational, kinematic, and total frequency shifts:

```python
# Altitude sweep
altitudes = np.linspace(200e3, 50e6, 500)  # 200 km to 50,000 km
radii = R_earth + altitudes

# Compute frequency shifts
delta_f_grav_array = np.array([gravitational_time_dilation(r, M_earth, R_earth) for r in radii])
velocities = np.array([orbital_velocity(r, M_earth) for r in radii])
delta_f_kin_array = np.array([kinematic_time_dilation(v) for v in velocities])
delta_f_total_array = delta_f_grav_array + delta_f_kin_array

# Convert to microseconds per day
delta_t_grav = delta_f_grav_array * 86400 * 1e6
delta_t_kin = delta_f_kin_array * 86400 * 1e6
delta_t_total = delta_f_total_array * 86400 * 1e6

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10))

# Plot frequency shifts
ax1.plot(altitudes / 1e6, delta_t_grav, label='Gravitational (GR)', linewidth=2, color='blue')
ax1.plot(altitudes / 1e6, delta_t_kin, label='Kinematic (SR)', linewidth=2, color='red')
ax1.plot(altitudes / 1e6, delta_t_total, label='Total', linewidth=2.5, color='black', linestyle='--')
ax1.axhline(0, color='gray', linestyle=':', linewidth=1)
ax1.axvline((r_gps - R_earth) / 1e6, color='green', linestyle='--', linewidth=1.5, alpha=0.7, label='GPS altitude')
ax1.scatter([(r_gps - R_earth) / 1e6], [delta_t_total[np.argmin(np.abs(radii - r_gps))]], 
            c='green', s=100, zorder=5, marker='o')
ax1.set_xlabel('Altitude above surface [km]', fontsize=11)
ax1.set_ylabel('Clock rate shift [μs/day]', fontsize=11)
ax1.set_title('Relativistic Time Dilation vs Orbital Altitude', fontsize=12, fontweight='bold')
ax1.legend(fontsize=10)
ax1.grid(True, alpha=0.3)

# Plot orbital velocity
ax2.plot(altitudes / 1e6, velocities / 1e3, linewidth=2, color='purple')
ax2.axvline((r_gps - R_earth) / 1e6, color='green', linestyle='--', linewidth=1.5, alpha=0.7, label='GPS altitude')
ax2.set_xlabel('Altitude above surface [km]', fontsize=11)
ax2.set_ylabel('Orbital velocity [km/s]', fontsize=11)
ax2.set_title('Orbital Velocity vs Altitude', fontsize=12, fontweight='bold')
ax2.legend(fontsize=10)
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('gps_time_dilation_calibration.png', dpi=300, bbox_inches='tight')
plt.show()
```

The calibration curve reveals that the total time dilation crosses zero at an altitude where gravitational and kinematic effects exactly cancel—this occurs at roughly $r = 1.5 R_E$, or about 3,200 km altitude. Below this critical radius, kinematic time dilation dominates and clocks run slower than ground clocks; above it, gravitational time dilation dominates and clocks run faster. GPS satellites orbit well above this transition, firmly in the gravitational-dominated regime.

For eccentric orbits, the time-averaged frequency shift requires integration over the orbital period. The gravitational potential varies periodically between periapsis and apoapsis, and the instantaneous velocity likewise oscillates. For an elliptical orbit with semi-major axis $a$ and eccentricity $e$, the time-averaged gravitational time dilation can be computed using:

```python
def time_averaged_dilation_elliptical(a, e, M, R_surface):
    """
    Compute orbit-averaged time dilation for elliptical orbit.
    
    Parameters:
        a: semi-major axis [m]
        e: orbital eccentricity
        M: central body mass [kg]
        R_surface: surface radius [m]
    
    Returns:
        Time-averaged Δf/f
    """
    # Eccentric anomaly sampling
    E_anom = np.linspace(0, 2*np.pi, 1000)
    
    # True anomaly and radius as functions of eccentric anomaly
    # r(E) = a(1 - e*cos(E))
    r_orbit = a * (1 - e * np.cos(E_anom))
    
    # Velocity from vis-viva equation: v^2 = GM(2/r - 1/a)
    v_orbit = np.sqrt(G * M * (2.0 / r_orbit - 1.0 / a))
    
    # Instantaneous time dilation
    delta_f_grav_inst = ((-G*M/r_orbit) - (-G*M/R_surface)) / c**2
    delta_f_kin_inst = -0.5 * (v_orbit/c)**2  # Low-velocity approximation
    delta_f_inst = delta_f_grav_inst + delta_f_kin_inst
    
    # Time average (weighted by dt/dE ∝ r)
    weights = r_orbit
    delta_f_avg = np.average(delta_f_inst, weights=weights)
    
    return delta_f_avg

# Test with moderately eccentric orbit
a_test = r_gps
e_test = 0.01  # 1% eccentricity (typical GPS satellite)
delta_f_eccentric = time_averaged_dilation_elliptical(a_test, e_test, M_earth, R_earth)
print(f"\nEccentric orbit (a={a_test/1e6:.0f} km, e={e_test}):")
print(f"  Time-averaged Δf/f: {delta_f_eccentric:.6e}")
print(f"  Clock rate shift: {delta_f_eccentric * 86400 * 1e6:.2f} μs/day")
```

The GPS Interface Control Document (ICD-GPS-200) specifies that the satellite atomic clocks are precompensated by offsetting their nominal frequency by $-4.4467 \times 10^{-10}$ before launch, corresponding to a rate correction of $-38.4$ microseconds per day. This hardware correction accounts for the orbit-averaged relativistic effects, though residual perturbations from orbital eccentricity and Earth's quadrupole moment require continuous monitoring and periodic clock steering commands.

For experimental verification, download GPS satellite clock correction parameters (broadcast navigation messages containing satellite clock bias and drift terms) from the International GNSS Service (IGS) archives. Compare the accumulated clock corrections over multi-day intervals against the predicted relativistic offsets. Residuals after removing the mean relativistic trend reveal additional effects such as temperature-dependent frequency drift in the satellite oscillators, solar radiation pressure perturbations on orbital elements, and subtle tidal deformations of Earth's gravitational field. The measurement precision of modern GPS timing receivers reaches the sub-nanosecond level, enabling tests of general relativity at fractional accuracies approaching $10^{-5}$.

## Exercise 3: Boundary Condition Stress Testing & Uncertainty Analysis

Gravitational lensing provides a geometric test of general relativity independent of orbital dynamics or clock measurements. When light passes near a massive object, the curvature of spacetime bends the photon trajectories, causing distant background sources to appear displaced, magnified, or multiply imaged. The deflection angle for a ray grazing the Sun's limb measures approximately 1.75 arcseconds, first confirmed during the 1919 solar eclipse expeditions led by Arthur Eddington. Modern observations of quasar lensing by foreground galaxies, gravitational arcs in galaxy clusters, and microlensing events from stellar-mass objects enable precision tests of the mass-deflection relation predicted by Einstein's field equations. This exercise computes light deflection angles as functions of impact parameter and lens mass, simulates lensing caustics and Einstein ring configurations, and propagates measurement uncertainties to constrain deviations from general relativity parameterized by the post-Newtonian parameter $\gamma$.

For a photon passing a spherical mass $M$ at impact parameter $b$ (closest approach distance), the deflection angle in the weak-field limit is:

$$\alpha = \frac{4GM}{c^2 b}$$

This formula emerges from integrating the geodesic equation for null rays in the Schwarzschild metric. The factor of 4 represents twice the Newtonian prediction derived from corpuscular light models; the additional factor of 2 arises from spatial curvature effects encoded in the metric tensor. For the Sun with $M = M_\odot$ and impact parameter $b = R_\odot$ (grazing the photosphere), this yields:

$$\alpha_\odot = \frac{4 G M_\odot}{c^2 R_\odot} = \frac{4 \times 6.674 \times 10^{-11} \times 1.989 \times 10^{30}}{(2.998 \times 10^8)^2 \times 6.96 \times 10^8} \approx 8.49 \times 10^{-6} \, \text{rad} = 1.75''$$

For strong lensing by galaxies, the deflection angle can exceed the Einstein angle $\theta_E$, defined as the angular radius at which perfect alignment between source, lens, and observer produces a complete Einstein ring. For a lens of mass $M$ at distance $D_L$ from the observer, and a source at distance $D_S$ behind it (with lens-source separation $D_{LS}$), the Einstein radius is:

$$\theta_E = \sqrt{\frac{4GM}{c^2} \frac{D_{LS}}{D_L D_S}}$$

For a galaxy of mass $10^{12} M_\odot$ at redshift $z_L \sim 0.5$ lensing a quasar at $z_S \sim 2$, typical Einstein radii measure several arcseconds, easily resolved by ground-based telescopes.

Begin by implementing the lensing deflection formula and computing angular positions of lensed images. For an axially symmetric lens (circular mass distribution), the lens equation relates the true source position $\beta$ to the observed image position $\theta$:

$$\beta = \theta - \frac{D_{LS}}{D_S} \alpha(\theta)$$

where $\alpha(\theta) = 4GM/(c^2 D_L \theta)$ for a point mass. This transcendental equation has multiple solutions corresponding to multiple images:

```python
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import fsolve

# Physical constants
G = 6.67430e-11  # m^3 kg^-1 s^-2
c = 299792458.0  # m/s
M_sun = 1.98892e30  # kg
R_sun = 6.96e8  # m

# Solar light deflection
b_graze = R_sun
alpha_sun = (4 * G * M_sun) / (c**2 * b_graze)
print("Solar Gravitational Lensing")
print("=" * 50)
print(f"Deflection angle at solar limb: {alpha_sun:.6e} rad")
print(f"  = {np.degrees(alpha_sun) * 3600:.3f} arcseconds")
print(f"Classical (Newtonian) prediction: {np.degrees(alpha_sun/2) * 3600:.3f} arcseconds")

# Galaxy lensing scenario
M_lens = 1e12 * M_sun  # Galaxy mass
D_L = 1500e6 * 3.086e22  # 1.5 Gpc (lens distance)
D_S = 3000e6 * 3.086e22  # 3.0 Gpc (source distance)
D_LS = D_S - D_L

# Einstein radius
theta_E = np.sqrt((4 * G * M_lens / c**2) * (D_LS / (D_L * D_S)))
theta_E_arcsec = np.degrees(theta_E) * 3600

print(f"\nGalaxy Lensing Configuration")
print("=" * 50)
print(f"Lens mass: {M_lens/M_sun:.2e} M_sun")
print(f"Lens distance: {D_L/3.086e22/1e6:.1f} Mpc")
print(f"Source distance: {D_S/3.086e22/1e6:.1f} Mpc")
print(f"Einstein radius: {theta_E:.6e} rad = {theta_E_arcsec:.3f} arcseconds")

def lens_equation(theta, beta, theta_E_sq):
    """
    Lens equation for point-mass lens: β = θ - θ_E^2/θ
    
    Parameters:
        theta: image position (angular coordinate)
        beta: source position
        theta_E_sq: Einstein angle squared
    
    Returns:
        Residual (zero when lens equation satisfied)
    """
    return beta - theta + theta_E_sq / theta

def find_images(beta, theta_E):
    """
    Solve lens equation to find image positions.
    
    Parameters:
        beta: true source position [rad]
        theta_E: Einstein radius [rad]
    
    Returns:
        List of image positions [rad]
    """
    theta_E_sq = theta_E**2
    
    if beta == 0:
        # Perfect alignment: Einstein ring at θ = θ_E
        return [theta_E]
    
    # For β != 0, two images exist
    # Approximate solutions for initial guesses
    theta_plus_guess = 0.5 * (beta + np.sqrt(beta**2 + 4*theta_E_sq))
    theta_minus_guess = 0.5 * (beta - np.sqrt(beta**2 + 4*theta_E_sq))
    
    theta_plus = fsolve(lens_equation, theta_plus_guess, args=(beta, theta_E_sq))[0]
    theta_minus = fsolve(lens_equation, theta_minus_guess, args=(beta, theta_E_sq))[0]
    
    return [theta_plus, theta_minus]
```

Generate a diagram showing image positions and magnifications as functions of source position. The magnification $\mu$ for each image is given by the reciprocal of the Jacobian determinant:

$$\mu = \left|\frac{\theta}{\beta} \frac{d\theta}{d\beta}\right|^{-1} = \left|1 - \left(\frac{\theta_E}{\theta}\right)^4\right|^{-1}$$

```python
# Sweep source position
beta_array = np.linspace(0.01, 3, 300) * theta_E
image_positions = []
magnifications = []

for beta in beta_array:
    images = find_images(beta, theta_E)
    image_positions.append(images)
    
    # Compute magnification for each image
    mags = []
    for theta_img in images:
        mu = np.abs(1.0 / (1.0 - (theta_E / theta_img)**4))
        mags.append(mu)
    magnifications.append(mags)

# Extract image tracks
theta_plus = np.array([imgs[0] for imgs in image_positions])
theta_minus = np.array([imgs[1] if len(imgs) > 1 else np.nan for imgs in image_positions])
mu_plus = np.array([mags[0] for mags in magnifications])
mu_minus = np.array([mags[1] if len(mags) > 1 else np.nan for mags in magnifications])

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10))

# Image positions
ax1.plot(beta_array / theta_E, theta_plus / theta_E, label='Image 1 (outer)', linewidth=2, color='blue')
ax1.plot(beta_array / theta_E, np.abs(theta_minus) / theta_E, label='Image 2 (inner)', linewidth=2, color='red')
ax1.axhline(1, color='green', linestyle='--', linewidth=1.5, alpha=0.7, label='Einstein ring')
ax1.plot(beta_array / theta_E, beta_array / theta_E, 'k:', linewidth=1, label='Source position')
ax1.set_xlabel('Source position β/θ_E', fontsize=11)
ax1.set_ylabel('Image position |θ|/θ_E', fontsize=11)
ax1.set_title('Gravitational Lensing: Image Positions', fontsize=12, fontweight='bold')
ax1.legend(fontsize=10)
ax1.grid(True, alpha=0.3)
ax1.set_xlim(0, 3)
ax1.set_ylim(0, 3)

# Magnifications
ax2.semilogy(beta_array / theta_E, mu_plus, label='Image 1 magnification', linewidth=2, color='blue')
ax2.semilogy(beta_array / theta_E, mu_minus, label='Image 2 magnification', linewidth=2, color='red')
ax2.axvline(1, color='green', linestyle='--', linewidth=1.5, alpha=0.7, label='Einstein ring')
ax2.set_xlabel('Source position β/θ_E', fontsize=11)
ax2.set_ylabel('Magnification |μ|', fontsize=11)
ax2.set_title('Gravitational Lensing: Image Magnifications', fontsize=12, fontweight='bold')
ax2.legend(fontsize=10)
ax2.grid(True, alpha=0.3, which='both')
ax2.set_xlim(0, 3)
ax2.set_ylim(0.1, 1e3)

plt.tight_layout()
plt.savefig('gravitational_lensing_images.png', dpi=300, bbox_inches='tight')
plt.show()
```

The diagnostic plot reveals the characteristic lensing behavior: as the source approaches perfect alignment ($\beta \to 0$), the two images merge into an Einstein ring at $\theta = \theta_E$ with formally infinite magnification. For sources well outside the Einstein radius ($\beta \gg \theta_E$), one image remains near the true source position with magnification approaching unity (unlensed), while the second image lies close to the lens center with vanishing magnification.

To stress-test the lensing model and assess robustness against measurement uncertainties, implement a Monte Carlo simulation that perturbs the lens mass, distances, and observed image positions within their observational error bars, then reconstructs the source position and tests consistency with the lensing hypothesis. Real observations suffer from several systematic effects: uncertainty in the lens mass distribution (dark matter halos deviate from point-mass profiles), photometric redshift errors translating to distance uncertainties, and astrometric noise in measuring image centroids. The post-Newtonian parameterized framework introduces a dimensionless parameter $\gamma$ that quantifies deviations from general relativity; pure GR corresponds to $\gamma = 1$, while alternative theories predict different values. The deflection angle generalizes to:

$$\alpha = \frac{2(1+\gamma)GM}{c^2 b}$$

Current constraints from lensing observations yield $\gamma = 1.00 \pm 0.02$, consistent with general relativity at the 2% level.

```python
# Monte Carlo uncertainty propagation for lensing reconstruction
def reconstruct_source_position(theta_obs, M_lens, D_L, D_S, gamma_pn=1.0):
    """
    Reconstruct source position from observed image position.
    
    Parameters:
        theta_obs: observed image angular position [rad]
        M_lens: lens mass [kg]
        D_L, D_S: lens and source distances [m]
        gamma_pn: post-Newtonian parameter (1.0 for GR)
    
    Returns:
        β: reconstructed source position [rad]
    """
    D_LS = D_S - D_L
    # Deflection angle modified by gamma
    alpha_theta = (2 * (1 + gamma_pn) * G * M_lens) / (c**2 * D_L * theta_obs)
    beta_recon = theta_obs - (D_LS / D_S) * alpha_theta
    return beta_recon

# Observational parameters with uncertainties
theta_obs_mean = 2.5 * theta_E  # Observed image position
theta_obs_sigma = 0.05 * theta_E  # Astrometric error (5%)

M_lens_mean = M_lens
M_lens_sigma = 0.1 * M_lens  # Mass uncertainty (10%)

D_L_mean = D_L
D_L_sigma = 0.05 * D_L  # Distance uncertainty (5%)

D_S_mean = D_S
D_S_sigma = 0.05 * D_S

# Monte Carlo sampling
n_samples = 10000
np.random.seed(42)

theta_obs_samples = np.random.normal(theta_obs_mean, theta_obs_sigma, n_samples)
M_lens_samples = np.random.normal(M_lens_mean, M_lens_sigma, n_samples)
D_L_samples = np.random.normal(D_L_mean, D_L_sigma, n_samples)
D_S_samples = np.random.normal(D_S_mean, D_S_sigma, n_samples)

beta_recon_samples = []
for i in range(n_samples):
    beta_rec = reconstruct_source_position(
        theta_obs_samples[i],
        M_lens_samples[i],
        D_L_samples[i],
        D_S_samples[i],
        gamma_pn=1.0
    )
    beta_recon_samples.append(beta_rec)

beta_recon_samples = np.array(beta_recon_samples)

# Statistical summary
beta_mean = np.mean(beta_recon_samples)
beta_std = np.std(beta_recon_samples)
beta_median = np.median(beta_recon_samples)

print(f"\nMonte Carlo Source Position Reconstruction")
print("=" * 50)
print(f"Observed image position: {theta_obs_mean/theta_E:.3f} θ_E")
print(f"  (σ = {theta_obs_sigma/theta_E:.3f} θ_E)")
print(f"\nReconstructed source position:")
print(f"  Mean: {beta_mean/theta_E:.3f} θ_E")
print(f"  Std dev: {beta_std/theta_E:.3f} θ_E")
print(f"  Median: {beta_median/theta_E:.3f} θ_E")
print(f"  68% confidence interval: [{np.percentile(beta_recon_samples/theta_E, 16):.3f}, "
      f"{np.percentile(beta_recon_samples/theta_E, 84):.3f}] θ_E")

# Histogram of reconstructed positions
plt.figure(figsize=(10, 6))
plt.hist(beta_recon_samples / theta_E, bins=50, density=True, alpha=0.7, color='blue', edgecolor='black')
plt.axvline(beta_mean / theta_E, color='red', linestyle='--', linewidth=2, label=f'Mean: {beta_mean/theta_E:.3f}')
plt.axvline(beta_median / theta_E, color='orange', linestyle='--', linewidth=2, label=f'Median: {beta_median/theta_E:.3f}')
plt.xlabel('Reconstructed source position β/θ_E', fontsize=11)
plt.ylabel('Probability density', fontsize=11)
plt.title('Monte Carlo Uncertainty Propagation in Lensing Reconstruction', fontsize=12, fontweight='bold')
plt.legend(fontsize=10)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('lensing_uncertainty_propagation.png', dpi=300, bbox_inches='tight')
plt.show()
```

The uncertainty analysis quantifies how observational errors in image positions, lens masses, and cosmological distances propagate through the lensing inversion to constrain the true source position. The width of the posterior distribution indicates the achievable precision for testing the mass-deflection scaling law. To test for deviations from general relativity, repeat the reconstruction for a range of $\gamma$ values and compute the likelihood of each $\gamma$ given the observed data:

```python
# Test gamma parameter
gamma_test_values = np.linspace(0.8, 1.2, 50)
chi_squared_values = []

# True source position (ground truth for this simulation)
beta_true = 2.0 * theta_E

for gamma_test in gamma_test_values:
    beta_pred = reconstruct_source_position(theta_obs_mean, M_lens_mean, D_L_mean, D_S_mean, gamma_pn=gamma_test)
    chi_sq = ((beta_pred - beta_true) / beta_std)**2
    chi_squared_values.append(chi_sq)

chi_squared_values = np.array(chi_squared_values)

# Find best-fit gamma (minimum chi-squared)
gamma_best = gamma_test_values[np.argmin(chi_squared_values)]
chi_sq_min = np.min(chi_squared_values)

print(f"\nPost-Newtonian Parameter Constraint")
print("=" * 50)
print(f"Best-fit γ: {gamma_best:.4f}")
print(f"Minimum χ²: {chi_sq_min:.3f}")
print(f"General Relativity prediction: γ = 1.0000")

# Plot chi-squared as function of gamma
plt.figure(figsize=(10, 6))
plt.plot(gamma_test_values, chi_squared_values, linewidth=2, color='blue')
plt.axvline(1.0, color='red', linestyle='--', linewidth=2, alpha=0.7, label='GR prediction (γ=1)')
plt.axvline(gamma_best, color='green', linestyle='--', linewidth=2, alpha=0.7, label=f'Best fit (γ={gamma_best:.3f})')
plt.axhline(chi_sq_min + 1, color='gray', linestyle=':', linewidth=1, label='Δχ² = 1 (68% CL)')
plt.xlabel('Post-Newtonian parameter γ', fontsize=11)
plt.ylabel('χ² statistic', fontsize=11)
plt.title('Constraining Deviations from General Relativity', fontsize=12, fontweight='bold')
plt.legend(fontsize=10)
plt.grid(True, alpha=0.3)
plt.xlim(0.8, 1.2)
plt.tight_layout()
plt.savefig('gamma_parameter_constraint.png', dpi=300, bbox_inches='tight')
plt.show()
```

The $\chi^2$ profile quantifies the statistical consistency between the observed lensing configuration and predictions for different values of $\gamma$. The minimum occurs near $\gamma = 1.0$ for data consistent with general relativity, while the width of the $\chi^2$ valley determines the precision of the constraint. Current state-of-the-art lensing surveys (e.g., Hubble Space Telescope imaging of galaxy-scale lenses) achieve $\sim 1\%$ astrometric precision and $\sim 5\%$ mass measurement accuracy, yielding constraints $\gamma = 1.00 \pm 0.02$ that rule out many alternative gravity theories.

Additional boundary stress tests should probe the strong-field regime near black holes, where higher-order corrections to the deflection angle become significant. For impact parameters approaching the photon sphere at $r = 3GM/c^2 = 1.5 r_s$, photons can orbit the black hole multiple times before escaping, producing secondary and higher-order images with exponentially increasing deflection angles. Numerical integration of null geodesics in the Schwarzschild metric reveals these exotic features, though observing them requires resolving sub-microarcsecond scales achievable only via very long baseline interferometry of supermassive black holes (as demonstrated by the Event Horizon Telescope collaboration's imaging of M87* and Sgr A*).

## Laboratory Cheat Sheet & Metric Verification Guide

This quick-reference section consolidates the essential formulas, computational recipes, and verification protocols for general relativity experiments. Use this as a troubleshooting guide when simulation results deviate from expectations or observational data exhibit unexpected systematic trends.

**Schwarzschild Metric and Key Coordinates:**
- Line element: $ds^2 = -(1 - r_s/r)c^2 dt^2 + (1 - r_s/r)^{-1}dr^2 + r^2(d\theta^2 + \sin^2\theta \, d\phi^2)$
- Schwarzschild radius: $r_s = 2GM/c^2$
- Event horizon for black holes: $r = r_s$; photon sphere: $r = 3GM/c^2$
- For weak fields ($r \gg r_s$): expand metric as $g_{tt} \approx -1 + 2\Phi/c^2$, recovering Newtonian potential $\Phi = -GM/r$

**Perihelion Precession:**
- GR prediction per orbit: $\Delta\phi = 6\pi GM/(c^2 a(1-e^2))$
- Mercury parameters: $a = 5.79 \times 10^{10}$ m, $e = 0.206$, orbital period 87.97 days
- Expected precession: 0.103 arcsec/orbit = 43 arcsec/century
- Numerical integration: use `solve_ivp` with `rtol=1e-10`, integrate $d\phi/dr$ over multiple orbits, extract perihelion passages via `find_peaks(-r(phi))`
- Common errors: insufficient integration tolerance (premature termination), incorrect units (mix of SI and geometric units), failure to account for coordinate time vs proper time in non-equatorial orbits

**Gravitational Time Dilation:**
- Frequency shift: $\Delta f/f = (1/c^2)(\phi_1 - \phi_2)$ for gravitational potential difference
- GPS satellite correction: $\Delta f/f \approx (GM/c^2)(1/R_E - 3/(2r_{\text{sat}}))$
- Expected GPS clock advance: $+38$ μs/day (net of $+45$ μs gravitational $-7$ μs kinematic)
- Verification command: query GPS broadcast ephemeris for satellite clock polynomial coefficients, extract long-term clock drift rate, compare to relativistic prediction
- Einstein radius for time delay experiments: $\Delta t = (2GM/c^3)\ln(r_2/r_1)$ for radial displacement from $r_1$ to $r_2$

**Gravitational Lensing:**
- Deflection angle (weak field): $\alpha = 4GM/(c^2 b)$
- Solar limb deflection: 1.75 arcseconds (factor of 2 larger than Newtonian)
- Einstein radius: $\theta_E = \sqrt{4GM/c^2 \cdot D_{LS}/(D_L D_S)}$
- Lens equation: $\beta = \theta - (D_{LS}/D_S)\alpha(\theta)$
- Magnification: $\mu = |1 - (theta_E/\theta)^4|^{-1}$
- Post-Newtonian parameter: $\gamma = 1$ (GR); deflection angle $\propto (1+\gamma)$
- Current observational constraint: $\gamma = 1.00 \pm 0.02$ from galaxy lensing

**Computational Verification Checklist:**
1. Unit consistency: Convert all inputs to SI (meters, kilograms, seconds) before computation; convert outputs to conventional astronomical units (AU, arcseconds, microseconds) for reporting
2. Numerical precision: Orbital integrations require `rtol < 1e-9` to resolve sub-arcsecond precession; lensing calculations tolerate `rtol ~ 1e-6` due to larger angular scales
3. Coordinate singularities: Schwarzschild coordinates singular at $r = r_s$; switch to Eddington-Finkelstein or Kruskal-Szekeres coordinates for black hole interiors
4. Weak-field validation: Compare numerical geodesics against analytical weak-field expansions (post-Newtonian approximation) to verify code correctness
5. Observational data formats: JPL Horizons uses barycentric TDB time and ICRF coordinates; GPS uses WGS84 geodetic coordinates and UTC(USNO) timescale—apply proper coordinate and time transformations
6. Error propagation: Use Monte Carlo sampling (10,000+ trials) for uncertainty quantification when analytical Jacobians intractable; report 68% confidence intervals (16th–84th percentiles) for consistency with standard $1\sigma$ error bars

**Common Failure Modes and Diagnostics:**
- Orbital precession simulation diverges or produces negative radii: Check that initial conditions satisfy energy and angular momentum constraints from orbital elements; verify $E^2 - V_{\text{eff}}^2 > 0$ at perihelion
- GPS time dilation disagrees with published corrections: Confirm orbital altitude and eccentricity match current GPS constellation (Block IIF satellites at 20,180 km altitude); account for Earth's oblateness ($J_2$ term) in gravitational potential
- Lensing reconstruction yields unphysical source positions (negative angles or superluminal separations): Validate lens mass estimate via stellar velocity dispersion or weak lensing shear; check for source redshift degeneracies (multiple sources at different $z$ can mimic single-source multi-image lensing)
- Post-Newtonian parameter constraint yields $\gamma \gg 1$ or $\gamma < 0$: Systematic errors likely dominate (lens mass calibration, photometric redshift bias, or astrometric zeropoint offset); cross-check against independent lensing systems or alternative mass tracers (X-ray temperature, Sunyaev-Zeldovich effect)

**Reference Datasets and Archives:**
- JPL Horizons System: `https://ssd.jpl.nasa.gov/horizons/` (planetary ephemerides, orbital elements, observer geometry)
- International GNSS Service: `https://igs.org/` (GPS satellite orbits, clock corrections, station coordinates)
- LIGO Open Science Center: `https://www.gw-openscience.org/` (gravitational wave strain data, event catalogs, tutorials)
- Hubble Legacy Archive: `https://hla.stsci.edu/` (galaxy lensing images, astrometric catalogs, photometry)
- Astropy documentation: `https://docs.astropy.org/` (coordinate transformations, time standards, cosmological distance calculators)

**Python Environment Validation Commands:**
```bash
python -c "import numpy; print('NumPy:', numpy.__version__)"
python -c "import scipy; print('SciPy:', scipy.__version__)"
python -c "import matplotlib; print('Matplotlib:', matplotlib.__version__)"
python -c "import astropy; print('Astropy:', astropy.__version__)"
python -c "from astropy import units as u, constants as c; print('G =', c.G, 'c =', c.c)"
```

Expected output should confirm package versions (NumPy ≥1.20, SciPy ≥1.7, Matplotlib ≥3.3, Astropy ≥4.0) and proper import of physical constants without deprecation warnings. If import errors occur, reinstall via `pip install numpy scipy matplotlib astropy` in a fresh virtual environment to avoid version conflicts with system-wide packages.
