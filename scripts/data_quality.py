"""
Reusable ingestion data-quality validation (offline / CI).

GX is a DEV-only dependency (requirements-dev.txt). It is imported lazily inside
the functions, so `import scripts.data_quality` never forces GX on the runtime app.

Use as a library:
    from scripts.data_quality import validate_batch
    report = validate_batch(df, required_keys=["prompt","output"])
    if not report["passed"]: ...

Or as a CLI gate (exit 0 = clean, 1 = failed) for CI:
    python scripts/data_quality.py [project_id]
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def validate_batch(df, required_keys, classes=None, class_column=None, case_id_field=None):
    """Validate one ingestion batch (a DataFrame). Returns a structured report:
       {"passed": bool, "n_rows": int, "checks": [{expectation, column, passed, unexpected}]}"""
    import great_expectations as gx
    context = gx.get_context()          # must exist BEFORE building the suite
    suite = gx.ExpectationSuite(name="ingestion_schema_integrity")
    if required_keys:
        suite.add_expectation(gx.expectations.ExpectTableColumnsToMatchSet(
            column_set=list(required_keys), exact_match=False))
    for c in required_keys:
        suite.add_expectation(gx.expectations.ExpectColumnValuesToNotBeNull(column=c))
        suite.add_expectation(gx.expectations.ExpectColumnValueLengthsToBeBetween(column=c, min_value=1))
    if classes and class_column:
        suite.add_expectation(gx.expectations.ExpectColumnValuesToBeInSet(
            column=class_column, value_set=list(classes)))
    if case_id_field:
        suite.add_expectation(gx.expectations.ExpectColumnValuesToBeUnique(column=case_id_field))

    batch = (context.data_sources.add_pandas("ingest")
             .add_dataframe_asset("batch").add_batch_definition_whole_dataframe("all")
             .get_batch(batch_parameters={"dataframe": df}))
    result = batch.validate(suite)
    checks = []
    for r in result.results:
        cfg = r.expectation_config
        checks.append({"expectation": cfg.type,
                       "column": cfg.kwargs.get("column", cfg.kwargs.get("column_set")),
                       "passed": r.success,
                       "unexpected": None if r.success else r.result.get("partial_unexpected_list", r.result)})
    return {"passed": result.success, "n_rows": len(df), "checks": checks}


def _print(report, title=""):
    print(f"{title} rows={report['n_rows']}  PASS={report['passed']}")
    for c in report["checks"]:
        line = f"  [{'PASS' if c['passed'] else 'FAIL'}] {c['expectation']} ({c['column']})"
        if not c["passed"]:
            line += f"   unexpected: {c['unexpected']}"
        print(line)


if __name__ == "__main__":
    import pandas as pd
    from app.services.supabase_client import get_client
    from app.services.labelstudio import required_data_keys
    db = get_client()
    q = db.table("project_submissions").select("id,company,eval_config")
    subs = (q.eq("id", sys.argv[1]).execute().data if len(sys.argv) > 1 else q.execute().data)
    if not subs:
        print("No project found."); sys.exit(2)
    proj = subs[0]
    ec = proj["eval_config"] or {}
    required = required_data_keys(ec)
    case_id_field = ec.get("case_id_field") or (ec.get("schema") or {}).get("case_id_field")
    rows = db.table("project_items").select("content").eq("project_id", proj["id"]).execute().data
    df = pd.DataFrame([(r["content"] or {}) for r in rows])
    report = validate_batch(df, required, case_id_field=case_id_field)
    _print(report, title=f"[{proj['company']}] required={required}")
    sys.exit(0 if report["passed"] else 1)
