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


MUSIC_TERMS = ["daw", "voice-leading", "composer", "audio engineer", "timbre", "mixdown", "orchestration", "musician"]


def test_visual_arts_courses_do_not_get_the_music_blueprint():
    """Every arts course got the music blueprint: visual lessons were written
    for "composers, music producers, audio engineers", and the labs of 18
    visual-arts, design and 3D courses were DAW / voice-leading / mixing
    exercises (e.g. UX Design labs: "Timbre Synthesis, Waveform Shaping")."""
    for category, subtopic in [("visual_arts", "sculpture"), ("design", "ux_design"),
                               ("visual_media", "photography"), ("3d_graphics", "blender")]:
        strategy = GLOBAL_REGISTRY.get_strategy("arts", category)
        assert not isinstance(strategy, ArtsMusicStrategy), category
        blueprint = strategy.get_blueprint(subtopic.replace("_", " ").title(), category.replace("_", " ").title())
        assert blueprint.lessons[0].audience
        modules = build_topic_modules("arts", category, subtopic, subtopic.replace("_", " ").title())
        assert [m["filename"] for m in modules][-1] == "labs.md"
        for m in modules:
            text = m["prompt"].lower()
            for term in MUSIC_TERMS:
                assert term not in text, f"music term {term!r} in {category}/{m['filename']} prompt"
        for lesson in blueprint.lessons:
            for term in MUSIC_TERMS:
                assert term not in lesson.audience.lower()


def test_music_categories_keep_the_music_blueprint():
    for category in ["music_production", "music_performance", "composition", "creative_software"]:
        assert isinstance(GLOBAL_REGISTRY.get_strategy("arts", category), ArtsMusicStrategy), category


def test_topic_outline_lessons_use_the_music_template_only_for_music(tmp_path):
    """With a TOPIC_OUTLINE.md, every course that was not SUSE, studio
    hardware, languages or maths got the "MUSIC PRODUCTION MASTERCLASS"
    chapter template (Berklee professor, DAW shortcuts, commercial records)."""
    from learning_engine.generator import scope_topic_curriculum
    outline = "\n".join(
        f"* **Lesson {i}: Topic {i}**\n    * *Focus:* focus {i}\n    * *Hands-On:* exercise {i}\n" for i in (1, 2, 3)
    )
    cases = [("computing", "infrastructure", False), ("arts", "visual_arts", False),
             ("business", "markets", False), ("arts", "music_production", True)]
    for domain, category, music in cases:
        d = tmp_path / domain / category / "course"
        d.mkdir(parents=True)
        (d / "TOPIC_OUTLINE.md").write_text(outline, encoding="utf-8")
        modules = scope_topic_curriculum(domain, category, "course", "Course", subtopic_dir=d)
        lessons = [m for m in modules if m["filename"].startswith("lesson_")]
        assert len(lessons) == 3, (domain, category)
        for m in lessons:
            assert ("MUSIC PRODUCTION MASTERCLASS" in m["prompt"]) is music, (domain, category)
            assert ("Ableton" in m["prompt"]) is music, (domain, category)


def test_visual_course_inside_a_music_category_gets_the_visual_blueprint():
    """creative_software holds Ableton, Cubase and Logic, but also Adobe Creative
    Cloud; that course was generated with the music blueprint (its lab had 23
    music and audio references)."""
    from learning_engine.domain_strategies import ArtsVisualStrategy
    assert isinstance(GLOBAL_REGISTRY.get_strategy("arts", "creative_software", "adobe_creative_cloud"), ArtsVisualStrategy)
    assert isinstance(GLOBAL_REGISTRY.get_strategy("arts", "creative_software", "ableton_live"), ArtsMusicStrategy)
    modules = build_topic_modules("arts", "creative_software", "adobe_creative_cloud", "Adobe Creative Cloud")
    for m in modules:
        for term in MUSIC_TERMS:
            assert term not in m["prompt"].lower(), f"music term {term!r} in {m['filename']} prompt"
