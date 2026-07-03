"""
Append-only audit trail (Slice #7). Every annotation decision — who did what to which
item, when, through which channel — lands as an immutable row in `audit_events`. Nothing
here overwrites; the item's current label lives on project_items, the *history* lives here.

Defensibility: for any delivered result you can answer "who labeled this, who later
reviewed/corrected it, with what value, and when" from this log alone.

Recording NEVER breaks the labeling flow: a failed audit write is logged, not raised.
"""
import logging

logger = logging.getLogger(__name__)

# Distinguish a first-pass label from a later edit of an already-done item.
LABEL = "label"
REVIEW = "review"
SKIP = "skip"


def record(db, *, item_id, project_id, action, actor_id, actor_name,
           source="app", value=None) -> None:
    """Insert one audit event. Best-effort: logs and swallows on failure so a labeling
    save is never lost just because the audit write hiccuped."""
    if db is None:
        return
    try:
        db.table("audit_events").insert({
            "item_id": item_id,
            "project_id": project_id,
            "action": action,
            "actor_id": str(actor_id) if actor_id is not None else None,
            "actor_name": actor_name,
            "source": source,
            "value": value,
        }).execute()
    except Exception as exc:
        logger.error("Audit write failed (item=%s action=%s): %s", item_id, action, exc)


def history(db, project_id: str, limit: int = 500) -> list[dict]:
    """Events for a project, newest first."""
    r = (
        db.table("audit_events").select("*")
        .eq("project_id", project_id).order("created_at", desc=True).limit(limit).execute()
    )
    return r.data or []
