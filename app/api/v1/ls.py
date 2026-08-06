"""
Label Studio sync API.

POST /ls/sync     — (admin) create the LS project if needed and push pending items as tasks
POST /ls/webhook  — (Label Studio) receives annotations and writes them back to project_items
"""

import logging

import httpx

from fastapi import APIRouter, HTTPException, Header, Request
from pydantic import BaseModel

from app.core.config import settings
from app.services.supabase_client import get_client
from app.services import labelstudio as ls
from app.services import audit

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ls", tags=["Label Studio"])


def _require_admin(x_admin_key: str | None) -> None:
    if not settings.ADMIN_API_KEY or x_admin_key != settings.ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="Not authorised.")


class SyncIn(BaseModel):
    project_id: str
    task_type: str = "eval_rating"


class PullIn(BaseModel):
    project_id: str


def _collapse_structured(label: dict) -> dict:
    """Collapse a 'structured' field's two Label Studio controls into one object.

    build_label_config renders a structured field (e.g. critical_miss) as a Yes/No flag
    plus a '<name>_finding' picker. Those arrive as two flat sibling keys; here we merge
    them into label[name] = {"present": bool, "finding": <class or None>} so a critical
    miss lands as structured data, not two disconnected keys. Handles an orphan finding
    (finding chosen but flag left blank) by reporting present=None.
    """
    for fk in [k for k in list(label) if k != "_result" and k.endswith("_finding")]:
        base = fk[: -len("_finding")]
        finding = label.pop(fk)
        flag = label.get(base)
        present = (flag == "Yes") if isinstance(flag, str) else flag
        label[base] = {"present": present, "finding": finding}
    return label


def _parse_result(result: list) -> dict:
    """Flatten a Label Studio annotation result into a label dict (any task type)."""
    label: dict = {"_result": result}
    for r in result:
        fn = r.get("from_name")
        v = r.get("value", {}) or {}
        if "rating" in v:
            val = v["rating"]
        elif "choices" in v:
            c = v["choices"]
            val = c[0] if isinstance(c, list) and len(c) == 1 else c
        elif "text" in v:
            t = v["text"]
            val = t[0] if isinstance(t, list) and len(t) == 1 else t
        elif "labels" in v:
            val = {"labels": v.get("labels"), "start": v.get("start"), "end": v.get("end"), "text": v.get("text")}
        else:
            val = v
        if fn in label and fn != "_result":
            if not isinstance(label[fn], list):
                label[fn] = [label[fn]]
            label[fn].append(val)
        else:
            label[fn] = val
    return _collapse_structured(label)


@router.post("/sync", summary="Create LS project + push pending items as tasks (admin)")
def ls_sync(body: SyncIn, x_admin_key: str | None = Header(default=None)):
    _require_admin(x_admin_key)
    if not ls.is_configured():
        raise HTTPException(status_code=503, detail="Label Studio is not configured (set LS_URL and LS_TOKEN).")
    db = get_client()
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable.")

    # eval_config may not exist yet (pre-migration) — degrade to the static config.
    try:
        sub = db.table("project_submissions").select("id,company,ls_project_id,eval_config").eq("id", body.project_id).limit(1).execute()
    except Exception:
        sub = db.table("project_submissions").select("id,company,ls_project_id").eq("id", body.project_id).limit(1).execute()
    if not sub.data:
        raise HTTPException(status_code=404, detail="Project not found.")
    s = sub.data[0]
    ls_pid = s.get("ls_project_id")

    # Per-project schema drives the labeling config when present; otherwise fall back
    # to a built-in task-type config (keeps existing projects working).
    eval_config = s.get("eval_config")
    try:
        label_config = ls.build_label_config(eval_config) if eval_config else ls.get_config(body.task_type)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"Invalid eval_config: {exc}")

    # Pull the pending items first so we can check them against the config BEFORE
    # touching Label Studio — a mismatch here gives the operator a plain instruction
    # instead of a raw 400 from the import endpoint.
    items = (
        db.table("project_items").select("id,content")
        .eq("project_id", body.project_id).eq("status", "pending").execute()
    )
    rows = items.data or []
    if not rows:
        raise HTTPException(status_code=422, detail="No pending items to send. Add items to this project first.")

    for k in ls.required_data_keys(eval_config):
        n_missing = sum(1 for r in rows if not (r.get("content") or {}).get(k))
        if n_missing:
            hint = (
                " For images, upload them through the client portal so each item gets an image URL — "
                "a plain CSV of filenames can't carry the images."
                if k == "image"
                else f" Add a '{k}' column to your data, or switch to a config that matches it."
            )
            raise HTTPException(
                status_code=422,
                detail=(
                    f"{n_missing} of {len(rows)} item(s) have no '{k}' value, which this task needs.{hint}"
                ),
            )

    try:
        if not ls_pid:
            title = f"{s.get('company') or 'Senebiclabs project'} — {body.task_type}"
            ls_pid = ls.create_project(title=title, label_config=label_config)
            db.table("project_submissions").update({"ls_project_id": ls_pid}).eq("id", body.project_id).execute()
        else:
            # Keep the live LS project in step with the current config, so edits made
            # in "Set config" after the first sync are actually applied.
            ls.update_project_config(ls_pid, label_config)
        pushed = ls.push_tasks(ls_pid, rows)
    except httpx.HTTPStatusError as exc:
        logger.error("LS sync failed: %s", exc)
        raise HTTPException(status_code=502, detail=ls.explain_ls_error(exc))
    except Exception as exc:
        logger.error("LS sync failed: %s", exc)
        raise HTTPException(status_code=502, detail="Could not reach Label Studio. Check that it is running and LS_URL / LS_TOKEN are set.")

    return {"ok": True, "ls_project_id": ls_pid, "pushed": pushed}


@router.post("/pull", summary="Pull annotations from LS into the database (admin)")
def ls_pull(body: PullIn, x_admin_key: str | None = Header(default=None)):
    _require_admin(x_admin_key)
    if not ls.is_configured():
        raise HTTPException(status_code=503, detail="Label Studio is not configured.")
    db = get_client()
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable.")

    sub = db.table("project_submissions").select("id,ls_project_id").eq("id", body.project_id).limit(1).execute()
    if not sub.data:
        raise HTTPException(status_code=404, detail="Project not found.")
    ls_pid = sub.data[0].get("ls_project_id")
    if not ls_pid:
        raise HTTPException(status_code=400, detail="This project has not been sent to Label Studio yet.")

    try:
        tasks = ls.export_tasks(ls_pid)
    except Exception as exc:
        logger.error("LS pull failed: %s", exc)
        raise HTTPException(status_code=502, detail="Could not reach Label Studio.")

    written = 0
    for t in tasks:
        item_id = (t.get("data") or {}).get("_item_id")
        anns = t.get("annotations") or []
        if not item_id or not anns:
            continue
        a = anns[0]
        cb = a.get("completed_by")
        who = cb.get("email") if isinstance(cb, dict) else "clinician"
        parsed = _parse_result(a.get("result", []))
        try:
            db.table("project_items").update({
                "label": parsed,
                "status": "done",
                "labeled_by": who,
                "labeled_at": a.get("created_at"),
            }).eq("id", item_id).execute()
            written += 1
            audit.record(db, item_id=item_id, project_id=body.project_id, action=audit.LABEL,
                         actor_id=who, actor_name=who, source="label_studio", value=parsed)
        except Exception as exc:
            logger.error("LS pull item update failed (%s): %s", item_id, exc)

    return {"ok": True, "pulled": written}


@router.post("/webhook", summary="Receive annotations from Label Studio")
async def ls_webhook(req: Request, x_ls_secret: str | None = Header(default=None)):
    if settings.LS_WEBHOOK_SECRET and x_ls_secret != settings.LS_WEBHOOK_SECRET:
        raise HTTPException(status_code=403, detail="Bad webhook secret.")
    body = await req.json()
    if body.get("action") not in ("ANNOTATION_CREATED", "ANNOTATION_UPDATED"):
        return {"ok": True}

    ann = body.get("annotation") or {}
    task_ref = ann.get("task")
    try:
        task = ls.get_task(task_ref) if isinstance(task_ref, int) else (task_ref or {})
        item_id = (task.get("data") or {}).get("_item_id")
    except Exception as exc:
        logger.error("LS webhook task fetch failed: %s", exc)
        return {"ok": False}
    if not item_id:
        return {"ok": True}

    # Generic parse (same path as /ls/pull): flatten by field name, keep the raw result
    # list, and collapse structured fields (e.g. critical_miss) into one object.
    label = _parse_result(ann.get("result", []))

    db = get_client()
    if db is None:
        return {"ok": False}
    who = ann.get("created_username") or "label-studio"
    try:
        db.table("project_items").update(
            {
                "label": label,
                "status": "done",
                "labeled_by": who,
                "labeled_at": ann.get("created_at"),
            }
        ).eq("id", item_id).execute()
    except Exception as exc:
        logger.error("LS webhook update failed: %s", exc)
        return {"ok": False}

    # Audit needs the project id; the item carries it. Best-effort, never blocks the webhook.
    try:
        pr = db.table("project_items").select("project_id").eq("id", item_id).limit(1).execute()
        project_id = pr.data[0]["project_id"] if pr.data else None
    except Exception:
        project_id = None
    audit.record(db, item_id=item_id, project_id=project_id, action=audit.LABEL,
                 actor_id=who, actor_name=who, source="label_studio", value=label)
    return {"ok": True}
