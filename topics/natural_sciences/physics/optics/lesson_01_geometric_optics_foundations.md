# Lesson 1: Geometric Optics Foundations

## 1. First-Principles Intuition & Invariants

The study of optics begins not with the wave nature of light nor with quantum photon statistics, but with the ancient and profoundly useful approximation that light travels in straight lines. This geometric optics regime dominates whenever the wavelength of light ($\lambda \sim 400\text{–}700\,\text{nm}$ for visible radiation) remains negligibly small compared to the characteristic dimensions of optical elements—lenses with radii of curvature measured in centimeters, mirrors spanning tens of centimeters, apertures several millimeters across. Under these conditions, diffraction effects vanish into insignificance, and we may treat light as a collection of rays propagating along well-defined trajectories through space.

The ray model provides the foundation for designing telescopes, microscopes, cameras, eyeglasses, fiber optic cables, and virtually every macroscopic optical instrument in existence. It reduces the formidable complexity of Maxwell's electromagnetic field equations to simple geometric constructions involving angles, triangles, and algebraic ratios. Yet this simplicity conceals profound physical principles. The trajectories that light rays follow through space are not arbitrary; they obey Fermat's principle of least time, a variational statement that unifies reflection, refraction, and more exotic phenomena within a single elegant framework.

### Fermat's Principle: The Variational Foundation of Ray Optics

Pierre de Fermat formulated his principle in 1662 as a theological argument: light, in traveling from point $A$ to point $B$, always takes the path requiring the least time. Mathematically, if we parameterize a candidate ray path by arc length $s$ and denote the position-dependent refractive index as $n(\vec{r})$, then the optical path length functional becomes:

$$\mathcal{L} = \int_A^B n(\vec{r})\,ds$$

Fermat's principle demands that physical ray paths satisfy the variational condition $\delta \mathcal{L} = 0$. Since the speed of light in a medium with refractive index $n$ equals $c/n$, and time equals distance divided by speed, the optical path length $\mathcal{L}$ directly corresponds to travel time multiplied by $c$. Extremizing $\mathcal{L}$ thus extremizes transit time.

This variational formulation possesses extraordinary power. It predicts that in homogeneous media where $n$ remains constant, light travels in straight lines—the shortest geometric path coincides with the shortest temporal path. It predicts that at boundaries separating media with different refractive indices, rays bend according to Snell's law, which emerges as a necessary condition for minimizing optical path length across the interface. It even predicts subtle phenomena like mirages, where spatially varying refractive index distributions in heated air create curved ray trajectories that fool the eye into perceiving water on desert highways.

### The Law of Reflection: Specular Bounce Dynamics

When a light ray strikes a smooth interface—a polished metal surface, a glass plate coated with aluminum, or the silvered backing of a household mirror—the electromagnetic boundary conditions at the interface compel the incident ray to reflect. The law of reflection states that the angle of incidence $\theta_i$ (measured from the surface normal) equals the angle of reflection $\theta_r$:

$$\theta_i = \theta_r$$

Moreover, the incident ray, reflected ray, and surface normal all lie in a single plane. This seemingly trivial relationship derives directly from Fermat's principle. Consider a ray traveling from point $A$ above the mirror surface to point $B$, also above the surface, via reflection at point $P$ on the mirror. The total optical path length equals $n(AP + PB)$, where $n$ represents the refractive index of the surrounding medium. To minimize this sum, we invoke elementary calculus: differentiate the path length with respect to the horizontal position of point $P$, set the derivative to zero, and solve. The resulting geometry forces $\theta_i = \theta_r$.

In the laboratory, verifying the law of reflection requires minimal apparatus: a laser pointer (wavelength typically $\lambda = 532\,\text{nm}$ or $650\,\text{nm}$), a plane mirror mounted on an optical breadboard, and a protractor or rotational stage with angular graduations. Mount the laser to emit a beam at a known angle $\theta_i$ relative to the mirror normal—measure this angle using the protractor. Observe the reflected beam's angle $\theta_r$ on a distant screen or with a second protractor. Across incident angles spanning $10°$ to $80°$, the equality $\theta_i = \theta_r$ holds to within $\pm 0.5°$, limited only by mechanical alignment precision and beam divergence.

### Snell's Law: Refraction at Dielectric Boundaries

Refraction—the bending of light rays upon crossing boundaries between materials with differing refractive indices—constitutes the fundamental mechanism enabling lenses, prisms, and waveguides. When a ray traveling through medium 1 (refractive index $n_1$) encounters an interface with medium 2 (refractive index $n_2$), Snell's law governs the angular deflection:

$$n_1 \sin\theta_1 = n_2 \sin\theta_2$$

Here $\theta_1$ denotes the angle between the incident ray and the surface normal, while $\theta_2$ denotes the angle between the refracted ray and the normal. Like reflection, refraction obeys Fermat's principle. The derivation proceeds by writing the total optical path length from point $A$ in medium 1 to point $B$ in medium 2, passing through interface point $P$. Minimizing this path length with respect to $P$'s position yields Snell's law as the Euler-Lagrange equation for the optical trajectory.

The refractive index $n$ itself arises from the microscopic interaction between electromagnetic waves and the bound electrons within the material's atomic lattice. For most transparent solids and liquids in the visible spectrum, $n$ ranges from approximately $1.3$ (aerogels) to $2.4$ (diamond). Air at standard temperature and pressure exhibits $n \approx 1.000293$, negligibly different from vacuum ($n = 1$ by definition). Water at $20°\,\text{C}$ has $n \approx 1.333$, while common optical glasses span $1.5$ to $1.9$ depending on composition—crown glasses around $1.52$, flint glasses reaching $1.7$ or higher.

To experimentally verify Snell's law, construct a refraction apparatus consisting of a semicircular glass block (diameter $\sim 10\,\text{cm}$, refractive index measured separately via minimum deviation through a prism) mounted on a rotational stage. Direct a collimated laser beam toward the flat face of the semicircle such that the beam enters perpendicular to the curved surface (to avoid refraction at entry) and refracts at the flat face upon exiting into air. Measure $\theta_1$ (angle in glass) and $\theta_2$ (angle in air) for incident angles ranging from $10°$ to $60°$. Plot $\sin\theta_2$ versus $\sin\theta_1$; the slope equals $n_{\text{glass}}/n_{\text{air}} \approx n_{\text{glass}}$. Typical measurements yield linearity within $1\%$ across this angular range.

### Total Internal Reflection and the Critical Angle

A remarkable boundary phenomenon emerges when light travels from a denser medium ($n_1 > n_2$) toward a less dense medium. Snell's law requires $\sin\theta_2 = (n_1/n_2)\sin\theta_1$. Since the sine function cannot exceed unity, there exists a critical incident angle $\theta_c$ beyond which no real refracted ray exists:

$$\sin\theta_c = \frac{n_2}{n_1}$$

For $\theta_1 > \theta_c$, the incident ray undergoes total internal reflection—it bounces back into the denser medium with zero transmission into the less dense medium. This phenomenon enables fiber optic communication: light injected into a glass fiber (core index $n_1 \sim 1.46$) at sufficiently steep angles relative to the fiber axis reflects repeatedly off the core-cladding interface (cladding index $n_2 \sim 1.45$), propagating over kilometers with minimal loss. For a glass-air interface ($n_1 = 1.5$, $n_2 = 1.0$), the critical angle equals $\theta_c = \arcsin(1.0/1.5) \approx 41.8°$.

Laboratory observation of total internal reflection requires only the semicircular glass block used previously. Increase the incident angle $\theta_1$ beyond $\theta_c$. The transmitted beam vanishes abruptly, and the reflected beam intensifies to carry the full incident power. Measure the transmitted intensity with a photodiode or optical power meter as a function of $\theta_1$; the intensity drops precipitously within a degree or two of $\theta_c$, demonstrating the sharpness of this transition.

## 2. Core Architecture & Mechanics

### Spherical Mirrors: Paraxial Ray Tracing and Focal Properties

Curved mirrors form images by redirecting light rays through geometric reflection. The simplest analytically tractable geometry involves spherical surfaces—mirrors whose reflective surface forms a section of a sphere with radius of curvature $R$. A concave mirror curves inward toward the incident light, concentrating rays toward a focal point. A convex mirror curves outward, dispersing rays as though they originated from a virtual focal point behind the mirror.

For a concave spherical mirror illuminated by rays parallel to the optical axis (the axis of rotational symmetry passing through the mirror's center of curvature), geometric analysis reveals that all paraxial rays—rays making small angles with the optical axis—converge to a common focal point located at distance $f = R/2$ from the mirror vertex. This paraxial approximation, valid when ray angles remain below $\sim 10°$, eliminates spherical aberration effects that plague rays at larger angles.

The mirror equation relates object distance $s_o$ (measured from the vertex to the object), image distance $s_i$ (measured from the vertex to the image), and focal length $f$:

$$\frac{1}{s_o} + \frac{1}{s_i} = \frac{1}{f} = \frac{2}{R}$$

This equation applies to both concave ($f > 0$) and convex ($f < 0$) mirrors when sign conventions are enforced: real objects and images correspond to positive distances, virtual images correspond to negative $s_i$, and concave mirrors have positive $f$ while convex mirrors have negative $f$.

Ray tracing through spherical mirrors involves three principal rays that enable graphical construction of image locations:

1. A ray parallel to the optical axis reflects through the focal point (concave) or appears to diverge from the focal point (convex).
2. A ray passing through the focal point reflects parallel to the optical axis.
3. A ray striking the mirror vertex reflects symmetrically about the optical axis, maintaining equal angles with the normal at the vertex.

The intersection of any two of these rays determines the image location. For a concave mirror with $f = 10\,\text{cm}$, placing an object at $s_o = 15\,\text{cm}$ yields $s_i = 30\,\text{cm}$, forming a real, inverted image. Placing the object at $s_o = 5\,\text{cm}$ (inside the focal point) yields $s_i = -10\,\text{cm}$, forming a virtual, upright, magnified image behind the mirror—the principle underlying shaving and makeup mirrors.

### Thin Lenses: Refraction-Based Image Formation

Lenses manipulate light through refraction at two curved surfaces. A thin lens—defined as one whose thickness $d$ is negligible compared to the radii of curvature $R_1$ and $R_2$ of its surfaces—provides the simplest case for analysis. The lensmaker's equation relates the focal length $f$ of a thin lens to its geometry and the refractive index $n$ of the glass:

$$\frac{1}{f} = (n - 1)\left(\frac{1}{R_1} - \frac{1}{R_2}\right)$$

Here $R_1$ represents the radius of curvature of the surface facing the incident light, and $R_2$ represents the radius of curvature of the exit surface. Convex surfaces (curving outward from the lens center) have positive $R$, while concave surfaces (curving inward) have negative $R$. A biconvex lens (both surfaces convex) with $R_1 = +20\,\text{cm}$, $R_2 = -20\,\text{cm}$, and $n = 1.5$ yields $f = 20\,\text{cm}$, forming a converging lens.

The thin lens equation, identical in form to the mirror equation, governs image formation:

$$\frac{1}{s_o} + \frac{1}{s_i} = \frac{1}{f}$$

Sign conventions mirror those for mirrors: real objects have $s_o > 0$, real images have $s_i > 0$, converging lenses have $f > 0$, and diverging lenses have $f < 0$. The lateral magnification $m = -s_i/s_o$ quantifies image size relative to object size; negative magnification indicates an inverted image.

Ray tracing through thin lenses employs three principal rays:

1. A ray parallel to the optical axis refracts through the far focal point (converging lens) or appears to diverge from the near focal point (diverging lens).
2. A ray passing through the near focal point emerges parallel to the optical axis.
3. A ray passing through the lens center (the point where the optical axis intersects the lens midplane) continues undeviated.

The intersection of any two principal rays locates the image. For a converging lens with $f = 50\,\text{mm}$ and an object at $s_o = 75\,\text{mm}$, the thin lens equation yields $s_i = 150\,\text{mm}$, producing a real, inverted image with magnification $m = -2.0$. If the object moves to $s_o = 30\,\text{mm}$ (inside the focal point), $s_i = -75\,\text{mm}$, forming a virtual, upright, magnified image on the same side as the object—the magnifying glass configuration.

### Compound Optical Systems: Telescopes and Microscopes

Real-world optical instruments combine multiple lenses or mirrors to achieve performance unattainable with single elements. The compound microscope, invented in the late 16th century, employs two converging lenses: an objective lens with short focal length $f_o$ (typically $2\text{–}10\,\text{mm}$) and an eyepiece lens with longer focal length $f_e$ (typically $20\text{–}50\,\text{mm}$). The objective forms a real, magnified intermediate image of the specimen, which the eyepiece then magnifies further as a virtual final image at the viewer's near point (conventionally $25\,\text{cm}$ from the eye).

The total angular magnification of a microscope equals:

$$M = -\frac{L}{f_o} \cdot \frac{25\,\text{cm}}{f_e}$$

where $L$ represents the optical tube length—the distance between the objective's back focal plane and the eyepiece's front focal plane, standardized at $160\,\text{mm}$ for classical finite-conjugate microscopes. For $f_o = 4\,\text{mm}$, $f_e = 25\,\text{mm}$, and $L = 160\,\text{mm}$, the magnification reaches $M = -400$. The negative sign indicates inversion.

To construct a laboratory microscope for quantitative measurements, mount the objective and eyepiece in precision lens tubes secured to an optical rail with micrometer translation stages. Position a specimen (e.g., a calibrated stage micrometer with $10\,\mu\text{m}$ graduations) at the objective's focal plane. Illuminate the specimen with a collimated LED source (wavelength $\lambda = 530\,\text{nm}$, power $\sim 1\,\text{mW}$) passed through a diffuser to ensure uniform intensity. Focus by translating the specimen stage until the intermediate image appears sharp on a ground glass screen placed at the eyepiece's focal plane. Measure the separation between micrometer rulings in the intermediate image using a calibrated reticle. The ratio of observed spacing to known specimen spacing confirms the magnification.

The refracting telescope inverts the microscope's logic: it accepts parallel rays from a distant object (at effective infinity), forms a real intermediate image with a long-focal-length objective ($f_o = 500\text{–}5000\,\text{mm}$), then uses a short-focal-length eyepiece ($f_e = 10\text{–}50\,\text{mm}$) to magnify the angular size of that intermediate image. The angular magnification equals:

$$M = \frac{f_o}{f_e}$$

A telescope with $f_o = 1000\,\text{mm}$ and $f_e = 20\,\text{mm}$ provides $M = 50$, rendering the Moon's angular diameter (approximately $0.5°$ as seen from Earth) into an apparent $25°$ subtense.

The reflecting telescope, pioneered by Newton and perfected by Cassegrain, replaces the objective lens with a concave primary mirror. This substitution eliminates chromatic aberration—the wavelength-dependent focal length shift that plagues refracting objectives—since reflection depends only on geometry, not on dispersion. A Newtonian telescope with a parabolic primary mirror of diameter $D = 200\,\text{mm}$ and focal ratio $f/6$ (meaning $f_o = 1200\,\text{mm}$) paired with a $25\,\text{mm}$ eyepiece delivers $M = 48$ with a diffraction-limited angular resolution of approximately $\theta_{\text{min}} = 1.22\lambda/D \approx 0.7$ arcseconds at $\lambda = 550\,\text{nm}$.

### Aberrations: Departures from Paraxial Perfection

Real optical systems deviate from the idealized thin-lens and paraxial approximations. Aberrations—systematic defects in image formation—arise from the failure of Snell's law and spherical geometry to maintain perfect focus across extended fields or finite apertures. The five primary monochromatic Seidel aberrations are:

**Spherical aberration** occurs when rays striking a lens or mirror far from the optical axis focus at different axial positions than paraxial rays. For a spherical mirror or simple lens, the longitudinal spherical aberration scales as the fourth power of the aperture radius. Correcting spherical aberration requires aspheric surfaces (parabolic mirrors, hyperbolic lens surfaces) or compound lens designs that balance positive and negative aberrations across multiple elements.

**Coma** manifests when off-axis object points generate comet-shaped image blurs, with rays entering different annular zones of the aperture focusing at different lateral positions. Coma scales linearly with field angle and quadratically with aperture radius. A well-corrected aplanatic lens eliminates both spherical aberration and coma simultaneously.

**Astigmatism** arises because off-axis rays encounter lens surfaces at oblique angles, causing tangential and sagittal ray fans to focus at different axial positions. This creates elliptical image blurs for point objects located away from the optical axis.

**Field curvature** (Petzval curvature) causes the locus of best focus to lie on a curved surface rather than a flat plane. For a single thin lens, the field curvature radius equals $f/(n-1)$. Correcting field curvature requires compound lens systems with carefully chosen element spacings and refractive indices.

**Distortion** produces geometrically correct but spatially warped images: barrel distortion compresses the periphery of the field, while pincushion distortion expands it. Distortion does not degrade sharpness but alters the mapping between object and image coordinates.

Additionally, chromatic aberration—variation of focal length with wavelength due to material dispersion—creates color fringing and focus shifts across the visible spectrum. The Abbe number $V = (n_d - 1)/(n_F - n_C)$, where subscripts denote refractive indices at specific spectral lines, quantifies a glass's dispersive properties. Achromatic doublets pair crown glass (high $V \sim 60$) with flint glass (low $V \sim 35$) to bring two wavelengths to a common focus. Apochromatic triplets correct three wavelengths and achieve superior color correction.

### Experimental Mapping of Aberrations

To quantify spherical aberration in a converging lens, construct a collimated beam using a laser diode and beam expander. Pass the beam through an iris diaphragm to control the effective aperture diameter. Focus the beam through the test lens onto a CCD camera sensor positioned on a precision translation stage. Record the axial position of best focus as a function of aperture diameter, varying from $5\,\text{mm}$ to the full lens diameter. Plot focal shift versus aperture radius. For an uncorrected singlet, the focal shift will grow as the fourth power of radius, reaching several millimeters for typical focal lengths and apertures.

To observe chromatic aberration, replace the laser with a broadband white LED source and insert narrow-band interference filters ($10\,\text{nm}$ FWHM) at wavelengths spanning $450\,\text{nm}$ (blue), $550\,\text{nm}$ (green), and $650\,\text{nm}$ (red). Measure the axial focus position for each wavelength. A simple singlet fabricated from BK7 glass will exhibit a blue-red focal shift of approximately $2\%$ of the focal length—for $f = 100\,\text{mm}$, this amounts to a $2\,\text{mm}$ longitudinal chromatic aberration.

## 3. High-Performance Optimization & Failure Modes

### Alignment Procedures: Achieving Diffraction-Limited Performance

Optical systems require precise alignment to realize their theoretical performance. Even minor misalignments—tilts of a few arc-minutes, decentrations of tens of micrometers—can degrade image quality by introducing additional aberrations and vignetting. For a multi-element compound lens, begin alignment by establishing a mechanical optical axis defined by precision mounting surfaces. Mount each lens element in a threaded cell with retaining rings torqued to $0.2\,\text{N·m}$ to prevent motion without inducing stress birefringence.

Verify collimation of a beam emerging from the assembled system by projecting it onto a distant screen ($\sim 10\,\text{m}$) or using a shear plate interferometer. The beam diameter should remain constant over propagation distances exceeding $5\,\text{m}$; any divergence or convergence indicates residual power. To null tilt errors, insert the lens system into an autocollimator setup: retroreflect a collimated reference beam from a flat mirror positioned at the nominal focal plane, and adjust the lens barrel rotation until the retroreflected beam coincides with the incident beam within $\pm 5$ arcseconds.

For reflecting telescopes, alignment (collimation) involves centering the secondary mirror relative to the primary, adjusting the secondary tilt to direct the beam along the optical axis, and positioning the focuser to place the eyepiece focal plane coincident with the image plane. A Cheshire eyepiece or laser collimator simplifies this process. Misalignment exceeding $0.5\,\text{mm}$ in secondary decentration or $0.1°$ in tilt produces comatic image distortion visible as asymmetric star images.

### Stray Light Suppression and Baffling

Unwanted scattered light—stray light—arises from reflections off mechanical mounts, lens edges, dust particles, and ghost images formed by inter-reflections between lens surfaces. In precision photometry or spectroscopy, stray light can dominate the signal, especially when imaging faint objects near bright sources. Effective stray light suppression requires careful attention to surface finishes, coatings, and mechanical baffling.

Black anodized aluminum, flocked paper, and carbon nanotube coatings exhibit reflectances below $1\%$ across the visible spectrum and should line all interior surfaces of lens tubes and housings. Anti-reflection coatings on lens surfaces—typically multi-layer dielectric stacks tuned for specific wavelength ranges—reduce surface reflectance from $4\%$ per surface (uncoated glass-air interface) to below $0.5\%$. For an $8$-element compound lens, eliminating surface reflections via AR coatings improves transmission from $(0.96)^{16} \approx 52\%$ to $(0.995)^{16} \approx 92\%$.

Insert aperture stops (baffles) at conjugate image planes to block rays that scatter off non-optical surfaces. Thread baffles into lens tubes at intervals of approximately one focal length, with aperture diameters sized to transmit the desired field angle while blocking wide-angle scattering. A baffle diameter $D_{\text{baffle}}$ at distance $z$ from the focal plane should satisfy $D_{\text{baffle}} \lesssim 2z \tan(\theta_{\text{field}}/2)$, where $\theta_{\text{field}}$ denotes the full-field angle.

### Thermal Stability and Athermal Design

Temperature fluctuations cause expansion of lens materials and shifts in refractive index, altering focal lengths and introducing defocus. For a glass lens with thermal expansion coefficient $\alpha \sim 7 \times 10^{-6}\,\text{K}^{-1}$ and thermo-optic coefficient $dn/dT \sim -3 \times 10^{-6}\,\text{K}^{-1}$, a $10\,\text{K}$ temperature rise produces a fractional focal length change $\Delta f / f \sim 5 \times 10^{-5}$. For $f = 100\,\text{mm}$, this corresponds to a $5\,\mu\text{m}$ focus shift—comparable to the depth of focus for a diffraction-limited system at $f/5$ aperture.

Athermal lens designs compensate thermal sensitivity by combining materials with opposing thermo-optic properties or by using mechanical spacers fabricated from materials with tailored expansion coefficients. A common approach pairs positive glass elements (crown glass with $dn/dT < 0$) and negative elements (fluorite or certain polymers with $dn/dT > 0$) such that their thermal focal length shifts cancel. Active temperature control—embedding the optical assembly in a temperature-stabilized enclosure maintained at $\pm 0.1\,\text{K}$—provides an alternative solution for laboratory instruments.

To measure thermal sensitivity experimentally, mount the lens in an environmental chamber and record the focus position (via autocollimator or through-focus scanning of a point source) while ramping temperature from $15°\text{C}$ to $35°\text{C}$ at $1\,\text{K/min}$. Plot focal shift versus temperature. The slope quantifies the athermal error and guides material selection for compensation.

### Coatings and Damage Thresholds

High-power laser applications demand attention to optical damage thresholds. Dielectric coatings, particularly multi-layer AR coatings, can delaminate or ablate when exposed to intense optical fields. The damage threshold for typical oxide-based AR coatings on fused silica substrates ranges from $10$ to $50\,\text{J/cm}^2$ for nanosecond pulses at $1064\,\text{nm}$. For continuous-wave lasers, thermal absorption becomes the limiting factor; coatings absorb $\sim 10$ to $100\,\text{ppm}$ of incident power, heating the substrate. At intensities exceeding $\sim 1\,\text{MW/cm}^2$, thermal runaway can crack the substrate.

To prevent damage, operate well below published thresholds (apply a safety factor of $5$), clean optics rigorously to remove particulate contaminants that seed damage, and use beam expanders to reduce intensity at critical surfaces. For UV applications below $350\,\text{nm}$, fused silica transmits efficiently, but organic contaminants polymerize under UV exposure, forming absorbing films. Clean UV optics with acetone or isopropanol in a laminar flow hood, then bake at $150°\text{C}$ to desorb residual organics.

### Measurement Protocols: Modulation Transfer Function and Wavefront Error

Objective characterization of optical system performance relies on standardized metrics. The modulation transfer function (MTF) quantifies the spatial frequency response—how well the system reproduces fine image details. For a diffraction-limited lens, the MTF at spatial frequency $\nu$ (cycles per millimeter at the image plane) equals the normalized area of overlap of two offset circular pupils in Fourier space:

$$\text{MTF}(\nu) = \frac{2}{\pi}\left[\arccos\left(\frac{\lambda f \nu}{D}\right) - \frac{\lambda f \nu}{D}\sqrt{1 - \left(\frac{\lambda f \nu}{D}\right)^2}\right]$$

where $D$ denotes the entrance pupil diameter and $f$ the effective focal length. The cutoff frequency $\nu_c = D/(\lambda f)$ corresponds to the Rayleigh resolution limit.

To measure MTF experimentally, image a calibrated Ronchi ruling or sinusoidal grating (spatial frequency $\nu_0$) onto a CCD sensor. Compute the contrast $C = (I_{\max} - I_{\min})/(I_{\max} + I_{\min})$ of the recorded intensity pattern, where $I_{\max}$ and $I_{\min}$ denote the maximum and minimum pixel intensities. Repeat for gratings spanning $\nu_0 = 10$ to $200\,\text{cycles/mm}$. Plot $\text{MTF}(\nu_0)$ versus $\nu_0$ and compare to the diffraction limit. Aberrations reduce the MTF below the ideal curve.

Wavefront error—the root-mean-square departure of the actual optical wavefront from a perfect spherical reference—provides a complementary performance metric. Use a Fizeau or Twyman-Green interferometer to measure wavefront error. A diffraction-limited system exhibits wavefront error below $\lambda/14$ RMS (the Maréchal criterion). Systems with $\lambda/4$ RMS wavefront error show significant degradation in Strehl ratio (the peak intensity of the point spread function relative to the ideal).

### Failure Modes: Contamination, Mechanical Stress, and Degradation

Dust particles, fingerprints, and moisture films degrade optical performance by scattering light and introducing spatially varying phase errors. A single dust particle $10\,\mu\text{m}$ in diameter positioned near a focal plane creates a diffraction pattern spanning hundreds of micrometers at the image plane, obscuring fine details. Clean optics in a laminar flow hood using lens tissue moistened with reagent-grade methanol or acetone. Employ a rocket blower to remove loose particles before wiping to avoid scratching. For critical applications, store optics in nitrogen-purged desiccator cabinets to prevent moisture condensation.

Mechanical stress—induced by over-torqued retaining rings, thermal expansion mismatch, or mounting strain—introduces birefringence in glass elements, degrading polarization state and wavefront quality. Mount lenses with elastomeric spacers (silicone or Viton O-rings) to accommodate differential expansion. Torque retaining rings to $0.1\text{–}0.3\,\text{N·m}$; higher torques risk inducing fracture or stress-induced birefringence exceeding $10\,\text{nm/cm}$ retardance.

Optical coatings degrade over time due to UV exposure, humidity ingress, and mechanical abrasion. AR coatings exposed to ambient humidity for months can delaminate, while metal mirror coatings (aluminum, silver) oxidize, reducing reflectance. Protected silver coatings with dielectric overcoats maintain reflectance above $95\%$ for years, while bare aluminum drops to $85\%$ within weeks in humid environments. Re-coat mirrors every $1$ to $5$ years depending on usage and environment.

For systems exposed to vacuum (e.g., space telescopes), outgassing of adhesives, lubricants, and lens cements can deposit contaminating films on cold optical surfaces. Qualify all materials for vacuum compatibility via ASTM E595 testing, ensuring total mass loss below $1\%$ and collected volatile condensable material below $0.1\%$. Bake assembled systems at $60°\text{C}$ under vacuum for $48$ hours to desorb volatiles before deployment.
