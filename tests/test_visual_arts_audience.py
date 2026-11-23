"""Visual-arts courses are written for visual learners.

Until 2026-11-23 the arts generator used a music persona for every arts
category, so drawing, design, 3D and media lessons addressed "composers,
producers and audio engineers" and taught through DAWs, chords and mixing
consoles (one lab built perspective drawing around a conductor's podium).
The persona is fixed; this keeps such text from coming back. Lessons that
are genuinely about sound for picture are exempt."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VISUAL = ("topics/arts/3d_graphics/", "topics/arts/design/", "topics/arts/visual_arts/",
          "topics/arts/visual_media/", "topics/arts/creative_software/adobe_creative_cloud/")
SOUND_FOR_PICTURE = re.compile(r"fairlight|audio_design|output_formats|render_delivery|editorial_theory")
AUDIENCE = re.compile(
    r"\b(composers?|musicians?|audio engineers?|mixing engineers?|mastering engineers?|music producers?|"
    r"voice[- ]leading|counterpoint|symphon\w*|chord progressions?|DAWs?|digital audio workstations?|"
    r"Ableton|Pro Tools|Logic Pro|Cubase|sample librar\w*|synthesi[sz]ers?|liner notes)\b", re.I)


def visual_files():
    files = []
    for prefix in VISUAL:
        files += [p for p in (ROOT / prefix).rglob("*.md") if not SOUND_FOR_PICTURE.search(p.name)]
    return sorted(files)


def test_visual_arts_text_does_not_address_musicians():
    offenders = []
    for path in visual_files():
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            m = AUDIENCE.search(line)
            if m:
                offenders.append(f"{path.relative_to(ROOT)}:{n}: {m.group(0)}")
    assert offenders == [], "\n".join(offenders[:40])


def test_the_check_still_sees_the_visual_courses():
    assert len(visual_files()) > 100
