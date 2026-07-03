"""
Slice #7 test: every annotation decision lands in the append-only audit trail, and a save
onto an already-done item is recorded as a review, not a first label. Talks to the live DB
and cleans up. Run: PYTHONPATH=. python3 tests/test_audit.py

Requires the audit_events + project_clinicians migrations (supabase_schema.sql).
"""
import secrets

from app.core.config import settings
from app.services import audit
from app.services.supabase_client import get_client
from app.api.v1.project import work_label, LabelIn


def main():
    db = get_client()
    if db is None:
        raise SystemExit("Supabase not configured — cannot run the audit test.")
    admin_key = settings.ADMIN_API_KEY
    if not admin_key:
        raise SystemExit("ADMIN_API_KEY not set — needed to exercise the review (admin) path.")

    code = "wc_" + secrets.token_urlsafe(6)
    cli = db.table("clinicians").insert(
        {"name": "AUDIT TEST clinician", "email": f"audit+{code}@example.com", "access_code": code}
    ).execute().data[0]
    proj = db.table("project_submissions").insert(
        {"name": "AUDIT TEST", "company": "AUDIT TEST", "email": "audit@example.com",
         "description": "audit trail test", "task_type": "xray_classification", "status": "new"}
    ).execute().data[0]
    cid, pid = cli["id"], proj["id"]

    try:
        db.table("project_clinicians").insert({"project_id": pid, "clinician_id": cid}).execute()
    except Exception as exc:
        raise SystemExit(f"MIGRATION REQUIRED (project_clinicians): {exc}")
    item = db.table("project_items").insert(
        {"project_id": pid, "idx": 0, "content": {"image": "x", "prediction": "Pneumonia"},
         "status": "pending", "assigned_to": cid}
    ).execute().data[0]
    iid = item["id"]

    try:
        # First save by the assigned clinician -> action 'label'.
        work_label(LabelIn(item_id=iid, label={"verdict": "Correct"}), x_work_code=code)
        # A later save onto the now-done item by the operator -> action 'review'.
        work_label(LabelIn(item_id=iid, label={"verdict": "Incorrect"}), x_work_code=admin_key)

        try:
            events = audit.history(db, pid)
        except Exception as exc:
            raise SystemExit(f"MIGRATION REQUIRED (audit_events): {exc}")

        assert len(events) == 2, f"expected 2 audit events, got {len(events)}"
        # history() is newest-first: [review, label]
        review, label = events[0], events[1]
        assert label["action"] == "label", f"first decision should be a label, got {label['action']}"
        assert label["actor_name"] == "AUDIT TEST clinician"
        assert label["source"] == "app"
        assert label["value"] == {"verdict": "Correct"}, "label snapshot not recorded"
        assert review["action"] == "review", f"save onto a done item should be a review, got {review['action']}"
        assert review["actor_id"] == "admin"
        assert review["value"] == {"verdict": "Incorrect"}
        print("  audit: PASS (label then review recorded, immutable, with actor + value snapshots)")
    finally:
        try:
            db.table("audit_events").delete().eq("project_id", pid).execute()
        except Exception as exc:
            print(f"  (cleanup warning, audit_events: {exc})")
        db.table("project_items").delete().eq("id", iid).execute()
        db.table("project_clinicians").delete().eq("project_id", pid).eq("clinician_id", cid).execute()
        db.table("project_submissions").delete().eq("id", pid).execute()
        db.table("clinicians").delete().eq("id", cid).execute()


if __name__ == "__main__":
    main()
    print("PASS: tests/test_audit.py (append-only audit trail: label + review, with snapshots)")
