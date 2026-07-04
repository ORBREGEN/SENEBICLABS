"""
Slice: model-performance report. Synthetic verdicts in -> correct accuracy / precision /
recall / confusion matrix out; missing corrected_label flagged not dropped; cannot_assess and
unlabeled excluded; critical-miss list complete. Run: PYTHONPATH=. python3 tests/test_report.py
(pytest not installed here, so self-running. Also prints a sample rendered report at the end.)
"""
from app.services import report as R


def _item(idx, pred, verdict=None, correct=None, cm=None, cannot=False, status="done", conf=None):
    label = {}
    if verdict is not None:
        label["verdict"] = verdict
    if correct is not None:
        label["correct_label"] = correct
    if cm is not None:
        label["critical_miss"] = cm
    if cannot:
        label["cannot_assess"] = "Cannot assess"
    if conf is not None:
        label["radiologist_confidence"] = conf
    return {"idx": idx, "status": status,
            "content": {"image": f"img{idx}", "prediction": pred},
            "label": label if status == "done" else None}


# 6 assessable + 1 cannot-assess + 1 incomplete + 1 unlabeled. Ground truth by the rules.
ITEMS = [
    _item(0, "Normal", "Correct", conf=5),                                   # TP Normal
    _item(1, "Normal", "Correct"),                                           # TP Normal
    _item(2, "Pneumonia", "Incorrect", correct="Normal"),                    # pred Pneu, true Normal
    _item(3, "Pneumonia", "Correct"),                                        # TP Pneumonia
    _item(4, "TB", "Incorrect", correct="Pneumonia",
          cm={"present": True, "finding": "Pneumonia"}),                     # pred TB, true Pneu + CRITICAL MISS
    _item(5, "Normal", "Partially correct", correct="TB"),                   # pred Normal, true TB
    _item(6, "Normal", cannot=True),                                         # excluded: cannot_assess
    _item(7, "Pneumonia", "Incorrect", correct=None),                        # excluded: incomplete (no corrected_label)
    _item(8, "Normal", status="pending"),                                    # excluded: unlabeled
]

CLASSES = ["Normal", "Pneumonia", "TB", "Effusion"]   # Effusion never appears -> support 0


def test_totals_and_exclusions():
    rep = R.compute_report(ITEMS, CLASSES)
    t = rep["totals"]
    assert t["items"] == 9
    assert t["assessable"] == 6
    assert t["excluded"]["cannot_assess"] == 1
    assert t["excluded"]["unlabeled"] == 1
    assert t["excluded"]["incomplete_missing_correct_label"] == 1
    # incomplete case is flagged, not dropped or guessed
    assert [c["idx"] for c in rep["incomplete_cases"]] == [7]


def test_accuracy():
    rep = R.compute_report(ITEMS, CLASSES)
    # correct verdicts: idx 0,1,3 -> 3 of 6
    assert rep["accuracy"] == {"correct": 3, "assessable": 6, "value": 0.5}


def test_confusion_matrix():
    rep = R.compute_report(ITEMS, CLASSES)
    L = rep["confusion_matrix"]["labels"]
    assert L == ["Effusion", "Normal", "Pneumonia", "TB"]
    M = {p: dict(zip(L, rep["confusion_matrix"]["matrix"][i])) for i, p in enumerate(L)}
    assert M["Normal"] == {"Effusion": 0, "Normal": 2, "Pneumonia": 0, "TB": 1}
    assert M["Pneumonia"] == {"Effusion": 0, "Normal": 1, "Pneumonia": 1, "TB": 0}
    assert M["TB"] == {"Effusion": 0, "Normal": 0, "Pneumonia": 1, "TB": 0}
    assert M["Effusion"] == {"Effusion": 0, "Normal": 0, "Pneumonia": 0, "TB": 0}


def test_per_class_prf():
    pc = R.compute_report(ITEMS, CLASSES)["per_class"]
    # Normal: tp2 fp1 fn1 -> p=r=f=2/3 ; support 3
    assert pc["Normal"]["support"] == 3 and pc["Normal"]["tp"] == 2
    assert round(pc["Normal"]["precision"], 4) == round(2 / 3, 4)
    assert round(pc["Normal"]["recall"], 4) == round(2 / 3, 4)
    # Pneumonia: tp1 fp1 fn1 -> 0.5 / 0.5 ; support 2
    assert pc["Pneumonia"]["support"] == 2
    assert pc["Pneumonia"]["precision"] == 0.5 and pc["Pneumonia"]["recall"] == 0.5
    # TB: tp0 fp1 fn1 -> 0 / 0 ; support 1
    assert pc["TB"]["support"] == 1
    assert pc["TB"]["precision"] == 0.0 and pc["TB"]["recall"] == 0.0 and pc["TB"]["f1"] == 0.0
    # Effusion: never true/predicted -> undefined, NOT zero
    assert pc["Effusion"]["support"] == 0
    assert pc["Effusion"]["precision"] is None and pc["Effusion"]["recall"] is None and pc["Effusion"]["f1"] is None


def test_critical_miss_list_complete():
    rep = R.compute_report(ITEMS, CLASSES)
    assert len(rep["critical_misses"]) == 1
    cm = rep["critical_misses"][0]
    assert cm["idx"] == 4 and cm["model_prediction"] == "TB"
    assert cm["correct_label"] == "Pneumonia" and cm["finding"] == "Pneumonia"


def test_failure_cases():
    rep = R.compute_report(ITEMS, CLASSES)
    assert sorted(c["idx"] for c in rep["failure_cases"]) == [2, 4, 5]


def test_support_sums_to_assessable():
    rep = R.compute_report(ITEMS, CLASSES)
    assert sum(m["support"] for m in rep["per_class"].values()) == rep["totals"]["assessable"]


def test_missing_correct_label_not_silently_dropped():
    # A wrong verdict with no corrected_label must be excluded AND flagged, never counted.
    rep = R.compute_report(ITEMS, CLASSES)
    incomplete_idx = {c["idx"] for c in rep["incomplete_cases"]}
    assessable_idx = {c["idx"] for c in rep["cases"] if c["disposition"] == "assessable"}
    assert 7 in incomplete_idx and 7 not in assessable_idx
    assert any("EXCLUDED" in cav for cav in rep["caveats"])


if __name__ == "__main__":
    for fn in [test_totals_and_exclusions, test_accuracy, test_confusion_matrix, test_per_class_prf,
               test_critical_miss_list_complete, test_failure_cases, test_support_sums_to_assessable,
               test_missing_correct_label_not_silently_dropped]:
        fn()
    print("PASS: tests/test_report.py (accuracy / PRF / confusion / critical-miss / exclusions correct)\n")
    print("=" * 70)
    print("SAMPLE RENDERED REPORT (synthetic data):")
    print("=" * 70)
    rep = R.compute_report(ITEMS, CLASSES)
    rep["project_id"] = "SAMPLE"
    print(R.render_markdown(rep))
