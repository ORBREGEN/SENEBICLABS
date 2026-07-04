"""
Model-performance report (the client deliverable).

Turns the pulled, structured radiologist verdicts on a project (already in
project_items.label after /ls/pull) into "your model is X% accurate, here are the misses".

Ground truth is radiologist-adjudicated:
  - verdict == Correct              -> ground truth = the model's own prediction
  - verdict == Incorrect / Partial  -> ground truth = the radiologist's corrected_label

Only *assessable* cases enter the metrics. Excluded, with the reason stated:
  - unlabeled (not reviewed yet / no verdict)
  - cannot_assess (radiologist could not read it)
  - incomplete: a wrong verdict with NO corrected_label  -> flagged, never guessed, never dropped silently
  - missing model prediction in content (data problem)   -> flagged

Stats are pure Python (counts + a confusion matrix). No numpy/sklearn, so no version surface.

Honesty rails baked in:
  - reports n (support) per class and caveats that ~100 cases is a sample, not the truth
  - headline accuracy = % verdict==Correct; the confusion-matrix diagonal is derived from
    (prediction vs ground_truth) and can differ for 'Partially correct' cases whose corrected
    label equals the prediction. That divergence is surfaced, not hidden.
  - cases are keyed by their stable idx (the identity ingest guarantees), never list position.
"""
import csv
import io
from datetime import datetime, timezone

CORRECT, INCORRECT, PARTIAL = "correct", "incorrect", "partial"
THIN_SUPPORT = 10  # below this many ground-truth cases, per-class metrics are noisy


def _verdict_kind(label: dict):
    v = (label or {}).get("verdict")
    if not isinstance(v, str):
        return None
    s = v.strip().lower()
    if s.startswith("correct"):
        return CORRECT
    if s.startswith("incorrect"):
        return INCORRECT
    if s.startswith("partial"):
        return PARTIAL
    return None


def _prf(tp: int, fp: int, fn: int):
    p = tp / (tp + fp) if (tp + fp) else None      # None = never predicted this class
    r = tp / (tp + fn) if (tp + fn) else None      # None = class never in ground truth
    if p is None or r is None:
        f = None
    elif p + r == 0:
        f = 0.0
    else:
        f = 2 * p * r / (p + r)
    return p, r, f


def compute_report(items: list[dict], classes=None) -> dict:
    """Pure function: list of items ({idx, content, label, status}) -> structured report.
    `classes` is the canonical class list (e.g. from eval_config); observed classes are
    unioned in so nothing is missed."""
    excluded = {"unlabeled": 0, "cannot_assess": 0,
                "incomplete_missing_correct_label": 0, "missing_prediction": 0}
    assessable, cases = [], []
    critical_misses, failure_cases, incomplete_cases = [], [], []
    observed = set()

    for it in items:
        idx = it.get("idx")
        content = it.get("content") or {}
        label = it.get("label") or {}
        image = content.get("image")
        pred = content.get("prediction")
        kind = _verdict_kind(label)

        base = {"idx": idx, "image": image, "model_prediction": pred,
                "verdict": (label or {}).get("verdict"),
                "confidence": (label or {}).get("radiologist_confidence"),
                "rationale": (label or {}).get("rationale")}

        if it.get("status") != "done":
            excluded["unlabeled"] += 1
            cases.append({**base, "ground_truth": None, "correct_label": None,
                          "critical_miss": False, "finding": None, "disposition": "excluded:unlabeled"})
            continue
        # cannot_assess means the radiologist DID review it, so it outranks a missing verdict.
        if (label or {}).get("cannot_assess"):
            excluded["cannot_assess"] += 1
            cases.append({**base, "ground_truth": None, "correct_label": None,
                          "critical_miss": False, "finding": None, "disposition": "excluded:cannot_assess"})
            continue
        if kind is None:
            excluded["unlabeled"] += 1
            cases.append({**base, "ground_truth": None, "correct_label": None,
                          "critical_miss": False, "finding": None, "disposition": "excluded:unlabeled"})
            continue
        if not pred:
            excluded["missing_prediction"] += 1
            row = {**base, "ground_truth": None, "correct_label": None, "critical_miss": False,
                   "finding": None, "disposition": "excluded:missing_prediction", "reason": "no model prediction in content"}
            cases.append(row)
            incomplete_cases.append({"idx": idx, "image": image, "verdict": base["verdict"],
                                     "model_prediction": pred, "reason": "missing model prediction in content"})
            continue

        if kind == CORRECT:
            corrected, truth = None, pred
        else:
            corrected = (label or {}).get("correct_label")
            if not corrected or not isinstance(corrected, str):
                excluded["incomplete_missing_correct_label"] += 1
                row = {**base, "ground_truth": None, "correct_label": None, "critical_miss": False,
                       "finding": None, "disposition": "excluded:incomplete_missing_correct_label",
                       "reason": "wrong verdict but no corrected_label"}
                cases.append(row)
                incomplete_cases.append({"idx": idx, "image": image, "verdict": base["verdict"],
                                         "model_prediction": pred, "reason": "wrong verdict but no corrected_label"})
                continue
            truth = corrected

        observed.add(pred)
        observed.add(truth)
        cm = (label or {}).get("critical_miss")
        cm_present = isinstance(cm, dict) and cm.get("present") is True
        finding = cm.get("finding") if isinstance(cm, dict) else None

        assessable.append({"idx": idx, "model_prediction": pred, "ground_truth": truth, "kind": kind})
        cases.append({**base, "ground_truth": truth, "correct_label": corrected,
                      "critical_miss": cm_present, "finding": finding, "disposition": "assessable"})

        if kind in (INCORRECT, PARTIAL):
            failure_cases.append({"idx": idx, "image": image, "verdict": base["verdict"],
                                  "model_prediction": pred, "correct_label": corrected,
                                  "rationale": base["rationale"]})
        if cm_present:
            critical_misses.append({"idx": idx, "image": image, "model_prediction": pred,
                                    "correct_label": corrected if kind != CORRECT else pred,
                                    "finding": finding, "rationale": base["rationale"]})

    cls_list = sorted(set(classes or []) | observed)

    # Confusion matrix: conf[pred][true]
    conf = {p: {t: 0 for t in cls_list} for p in cls_list}
    for a in assessable:
        conf[a["model_prediction"]][a["ground_truth"]] += 1

    per_class = {}
    for c in cls_list:
        tp = conf[c][c]
        fp = sum(conf[c][t] for t in cls_list if t != c)
        fn = sum(conf[p][c] for p in cls_list if p != c)
        support = sum(conf[p][c] for p in cls_list)   # ground-truth count for c
        p, r, f = _prf(tp, fp, fn)
        per_class[c] = {"support": support, "tp": tp, "fp": fp, "fn": fn,
                        "precision": p, "recall": r, "f1": f}

    n_assess = len(assessable)
    n_correct = sum(1 for a in assessable if a["kind"] == CORRECT)
    accuracy = (n_correct / n_assess) if n_assess else None
    partial_on_diagonal = sum(1 for a in assessable
                              if a["kind"] == PARTIAL and a["model_prediction"] == a["ground_truth"])

    caveats = [
        f"Metrics are computed on {n_assess} assessable case(s). At this sample size, per-class "
        "numbers are indicative of this sample, not the model's true population performance. "
        "Read them alongside the support (n) per class.",
    ]
    thin = [c for c in cls_list if 0 < per_class[c]["support"] < THIN_SUPPORT]
    if thin:
        caveats.append(f"Thin support (under {THIN_SUPPORT} ground-truth cases): {thin}. "
                       "Their precision/recall are noisy and can swing on a single case.")
    zero = [c for c in cls_list if per_class[c]["support"] == 0]
    if zero:
        caveats.append(f"No ground-truth cases for: {zero}. Metrics are undefined (n/a), not zero.")
    if partial_on_diagonal:
        caveats.append(f"{partial_on_diagonal} 'Partially correct' case(s) had a corrected label equal "
                       "to the model prediction, so the confusion-matrix diagonal counts them as matches "
                       "while headline accuracy (verdict==Correct) does not. The two rates can differ by this much.")
    if excluded["incomplete_missing_correct_label"]:
        caveats.append(f"{excluded['incomplete_missing_correct_label']} wrong-verdict case(s) are missing a "
                       "corrected_label; they were EXCLUDED from metrics and flagged as incomplete (see "
                       "incomplete_cases), never guessed. Complete them for accurate metrics.")

    return {
        "totals": {
            "items": len(items),
            "assessable": n_assess,
            "excluded": excluded,
            "excluded_total": sum(excluded.values()),
        },
        "accuracy": {"correct": n_correct, "assessable": n_assess, "value": accuracy},
        "classes": cls_list,
        "per_class": per_class,
        "confusion_matrix": {
            "orientation": "rows=predicted, cols=true",
            "labels": cls_list,
            "matrix": [[conf[p][t] for t in cls_list] for p in cls_list],
        },
        "critical_misses": critical_misses,
        "failure_cases": failure_cases,
        "incomplete_cases": incomplete_cases,
        "cases": cases,
        "caveats": caveats,
    }


def build_report(db, project_id: str) -> dict:
    """Fetch a project's items + eval_config classes and compute the report."""
    classes = None
    try:
        sub = db.table("project_submissions").select("eval_config").eq("id", project_id).limit(1).execute()
        if sub.data and sub.data[0].get("eval_config"):
            classes = (((sub.data[0]["eval_config"] or {}).get("schema") or {}).get("classes")) or None
    except Exception:
        classes = None
    rows = (
        db.table("project_items").select("idx,content,label,status")
        .eq("project_id", project_id).order("idx").execute()
    )
    report = compute_report(rows.data or [], classes)
    report["project_id"] = project_id
    report["generated_at"] = datetime.now(timezone.utc).isoformat()
    return report


# ── Human-readable renderings ────────────────────────────────────────────────

def _pct(x):
    return "n/a" if x is None else f"{x * 100:.1f}%"


def render_markdown(rep: dict) -> str:
    t = rep["totals"]
    ex = t["excluded"]
    acc = rep["accuracy"]
    L = rep["confusion_matrix"]["labels"]
    out = []
    out.append(f"# Model performance report")
    if rep.get("project_id"):
        out.append(f"Project `{rep['project_id']}` · generated {rep.get('generated_at', '')}")
    out.append("")
    out.append(f"**Headline accuracy: {_pct(acc['value'])}** "
               f"({acc['correct']} of {acc['assessable']} assessable cases the model got right).")
    out.append("")
    out.append(f"- Items in project: **{t['items']}**")
    out.append(f"- Assessable (in metrics): **{t['assessable']}**")
    out.append(f"- Excluded: **{t['excluded_total']}** "
               f"(unlabeled {ex['unlabeled']}, cannot-assess {ex['cannot_assess']}, "
               f"incomplete {ex['incomplete_missing_correct_label']}, missing-prediction {ex['missing_prediction']})")
    out.append("")

    out.append("## Per-class metrics")
    out.append("| class | n (support) | precision | recall | F1 |")
    out.append("|---|---|---|---|---|")
    for c in L:
        m = rep["per_class"][c]
        out.append(f"| {c} | {m['support']} | {_pct(m['precision'])} | {_pct(m['recall'])} | {_pct(m['f1'])} |")
    out.append("")

    out.append("## Confusion matrix (rows = model predicted, cols = radiologist truth)")
    out.append("| pred \\ true | " + " | ".join(L) + " |")
    out.append("|" + "---|" * (len(L) + 1))
    for i, p in enumerate(L):
        row = rep["confusion_matrix"]["matrix"][i]
        out.append(f"| **{p}** | " + " | ".join(str(x) for x in row) + " |")
    out.append("")

    out.append(f"## Critical misses ({len(rep['critical_misses'])})")
    out.append("_Cases the radiologist flagged as a clinically critical miss — the highest-priority failures._")
    if rep["critical_misses"]:
        out.append("| idx | model said | correct | finding missed | note |")
        out.append("|---|---|---|---|---|")
        for c in rep["critical_misses"]:
            out.append(f"| {c['idx']} | {c['model_prediction']} | {c.get('correct_label')} | "
                       f"{c.get('finding')} | {(c.get('rationale') or '').replace(chr(10), ' ')} |")
    else:
        out.append("None flagged.")
    out.append("")

    out.append(f"## Failure cases ({len(rep['failure_cases'])})")
    if rep["failure_cases"]:
        out.append("| idx | verdict | model said | correct | note |")
        out.append("|---|---|---|---|---|")
        for c in rep["failure_cases"]:
            out.append(f"| {c['idx']} | {c['verdict']} | {c['model_prediction']} | "
                       f"{c.get('correct_label')} | {(c.get('rationale') or '').replace(chr(10), ' ')} |")
    else:
        out.append("None.")
    out.append("")

    if rep["incomplete_cases"]:
        out.append(f"## Incomplete cases ({len(rep['incomplete_cases'])}) — excluded from metrics, need fixing")
        out.append("| idx | verdict | model said | reason |")
        out.append("|---|---|---|---|")
        for c in rep["incomplete_cases"]:
            out.append(f"| {c['idx']} | {c.get('verdict')} | {c.get('model_prediction')} | {c['reason']} |")
        out.append("")

    out.append("## Read this before quoting the numbers")
    for c in rep["caveats"]:
        out.append(f"- {c}")
    out.append("")
    return "\n".join(out)


def render_cases_csv(rep: dict) -> str:
    cols = ["idx", "disposition", "model_prediction", "ground_truth", "verdict",
            "correct_label", "critical_miss", "finding", "confidence", "rationale", "image"]
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=cols, extrasaction="ignore")
    w.writeheader()
    for c in rep["cases"]:
        w.writerow(c)
    return buf.getvalue()
