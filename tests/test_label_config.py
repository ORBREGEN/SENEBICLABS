"""
Slice #1 test: build_label_config generates a valid, per-project Label Studio config
from an eval_config schema. Run: python tests/test_label_config.py
(pytest is not installed in this env, so this is self-running.)
"""
import xml.dom.minidom as minidom

from app.services.labelstudio import build_label_config

SAMPLE = {
    "title": "Chest X-ray classification review",
    "schema": {
        "classes": ["Normal", "Pneumonia", "TB", "Effusion"],
        "multi_label": False,
        "fields": {
            "verdict": {"type": "single", "options": ["Correct", "Incorrect", "Partially correct"], "required": True},
            "correct_label": {"type": "from_classes", "multi": False, "visible_when": "verdict!=Correct"},
            "critical_miss": {"type": "structured", "visible_when": "verdict!=Correct"},
            "radiologist_confidence": {"type": "scale", "min": 1, "max": 5},
            "cannot_assess": {"type": "flag", "label": "Cannot assess"},
            "rationale": {"type": "text"},
        },
    },
}


def test_generates_valid_config_from_schema():
    xml = build_label_config(SAMPLE)

    # 1. valid XML
    minidom.parseString(xml)

    # 2. per-project classes are present (kills the Normal/Abnormal hardcode)
    for cls in ("Pneumonia", "TB", "Effusion"):
        assert f'<Choice value="{cls}"/>' in xml, f"class {cls} missing from generated config"

    # 3. every configured field is emitted
    for field in ("verdict", "correct_label", "critical_miss", "radiologist_confidence", "cannot_assess", "rationale"):
        assert f'name="{field}"' in xml, f"field {field} missing"

    # 4. structured critical_miss produced its finding sub-field
    assert 'name="critical_miss_finding"' in xml

    # 5. conditional visibility derived from "verdict!=Correct"
    assert 'visibleWhen="choice-selected"' in xml
    assert 'whenTagName="verdict"' in xml
    assert 'whenChoiceValue="Incorrect,Partially correct"' in xml, "!= Correct not expanded to non-Correct options"


def test_invalid_configs_fail_loudly():
    for bad, why in [
        ({}, "missing schema"),
        ({"schema": {"classes": [], "fields": {}}}, "empty fields"),
        ({"schema": {"classes": [], "fields": {"x": {"type": "bogus"}}}}, "unknown field type"),
        ({"schema": {"classes": [], "fields": {"x": {"type": "single"}}}}, "single without options"),
        ({"schema": {"classes": [], "fields": {"x": {"type": "from_classes"}}}}, "from_classes without classes"),
    ]:
        try:
            build_label_config(bad)
        except ValueError:
            continue
        raise AssertionError(f"expected ValueError for: {why}")


if __name__ == "__main__":
    test_generates_valid_config_from_schema()
    test_invalid_configs_fail_loudly()
    print("PASS: tests/test_label_config.py (schema -> valid config, conditionals, loud failures)")
