"""
Regression & Compliance Tests for Domain Strategy Architecture.
Verifies that curriculum blueprints and toolchains are strictly domain-native,
type-safe, and that non-computing domains never receive Linux kernel CLI tools.
"""

from learning_engine.domain_strategies import (
    GLOBAL_REGISTRY,
    LabEnvironmentType,
    ArtsMusicStrategy,
    NaturalSciencesStrategy,
    MotorsportsStrategy,
    InfrastructureStrategy,
    GenericDomainStrategy,
    build_topic_modules
)

LINUX_KERNEL_TERMS = [
    "bpftool",
    "kubectl",
    "dmesg",
    "sysctl",
    "strace",
    "tcpdump",
    "linux-tools",
    "apt-get",
    "crictl"
]

def test_music_strategy_is_domain_native():
    """Verify Arts / Music strategy uses DAW/audio tooling and zero Linux commands."""
    strategy = GLOBAL_REGISTRY.get_strategy("arts", "composition")
    assert isinstance(strategy, ArtsMusicStrategy)
    toolchain = strategy.get_toolchain()
    assert toolchain.environment_type == LabEnvironmentType.SOFTWARE_GUI
    assert any("DAW" in f for f in toolchain.frameworks)

    blueprint = strategy.get_blueprint("Counterpoint", "Composition")
    modules = build_topic_modules("arts", "composition", "counterpoint", "Counterpoint")
    assert len(modules) == 4

    lab_module = next(m for m in modules if m["filename"] == "labs.md")
    for term in LINUX_KERNEL_TERMS:
        assert term not in lab_module["prompt"].lower(), f"Leaked Linux term '{term}' into Arts/Music lab prompt"

def test_natural_sciences_strategy_is_domain_native():
    """Verify Natural Sciences uses scientific instrumentation and zero Linux commands."""
    strategy = GLOBAL_REGISTRY.get_strategy("natural_sciences", "physics")
    assert isinstance(strategy, NaturalSciencesStrategy)
    toolchain = strategy.get_toolchain()
    assert toolchain.environment_type == LabEnvironmentType.FIELDWORK

    modules = build_topic_modules("natural_sciences", "physics", "thermodynamics", "Thermodynamics")
    lab_module = next(m for m in modules if m["filename"] == "labs.md")
    for term in LINUX_KERNEL_TERMS:
        assert term not in lab_module["prompt"].lower(), f"Leaked Linux term '{term}' into Natural Sciences lab prompt"

def test_motorsports_strategy_is_domain_native():
    """Verify Motorsports uses telemetry and vehicle dynamics tooling."""
    strategy = GLOBAL_REGISTRY.get_strategy("motorsports", "chassis_dynamics")
    assert isinstance(strategy, MotorsportsStrategy)
    toolchain = strategy.get_toolchain()
    assert toolchain.environment_type == LabEnvironmentType.SOFTWARE_GUI
    assert any("MoTeC" in f for f in toolchain.frameworks)

    modules = build_topic_modules("motorsports", "chassis_dynamics", "suspension", "Suspension")
    lab_module = next(m for m in modules if m["filename"] == "labs.md")
    for term in LINUX_KERNEL_TERMS:
        assert term not in lab_module["prompt"].lower(), f"Leaked Linux term '{term}' into Motorsports lab prompt"

def test_infrastructure_strategy_is_targeted():
    """Verify computing infrastructure produces targeted diagnostic tools without copy-paste junk."""
    strategy = GLOBAL_REGISTRY.get_strategy("computing", "infrastructure")
    assert isinstance(strategy, InfrastructureStrategy)
    toolchain = strategy.get_toolchain()
    assert toolchain.environment_type == LabEnvironmentType.CLI_TOOLS
    assert "kubectl" in toolchain.frameworks

def test_generic_domain_strategy_dispatch():
    """Verify business, humanities, and economics cleanly receive GenericDomainStrategy."""
    strategy_biz = GLOBAL_REGISTRY.get_strategy("business", "strategy")
    assert isinstance(strategy_biz, GenericDomainStrategy)
    assert strategy_biz.domain == "business"

    strategy_econ = GLOBAL_REGISTRY.get_strategy("economics", "macroeconomics")
    assert isinstance(strategy_econ, GenericDomainStrategy)
    assert strategy_econ.domain == "economics"
