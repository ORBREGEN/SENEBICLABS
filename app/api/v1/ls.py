"""
Label Studio sync API.

POST /ls/sync     — (admin) create the LS project if needed and push pending items as tasks
POST /ls/webhook  — (Label Studio) receives annotations and writes them back to project_items
"""

import logging

from fastapi import APIRouter, HTTPException, Header, Request
from pydantic import BaseModel

from app.core.config import settings
from app.services.supabase_client import get_client
from app.services import labelstudio as ls

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
    return label


@router.post("/sync", summary="Create LS project + push pending items as tasks (admin)")
def ls_sync(body: SyncIn, x_admin_key: str | None = Header(default=None)):
    _require_admin(x_admin_key)
    if not ls.is_configured():
        raise HTTPException(status_code=503, detail="Label Studio is not configured (set LS_URL and LS_TOKEN).")
    db = get_client()
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable.")

    sub = db.table("project_submissions").select("id,company,ls_project_id").eq("id", body.project_id).limit(1).execute()
    if not sub.data:
        raise HTTPException(status_code=404, detail="Project not found.")
    s = sub.data[0]
    ls_pid = s.get("ls_project_id")

    try:
        if not ls_pid:
            title = f"{s.get('company') or 'Senebiclabs project'} — {body.task_type}"
            ls_pid = ls.create_project(title=title, label_config=ls.get_config(body.task_type))
            db.table("project_submissions").update({"ls_project_id": ls_pid}).eq("id", body.project_id).execute()
        items = (
            db.table("project_items").select("id,content")
            .eq("project_id", body.project_id).eq("status", "pending").execute()
        )
        pushed = ls.push_tasks(ls_pid, items.data or [])
    except Exception as exc:
        logger.error("LS sync failed: %s", exc)
        raise HTTPException(status_code=502, detail="Could not sync to Label Studio. Check LS_URL / LS_TOKEN and that Label Studio is reachable.")

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
        try:
            db.table("project_items").update({
                "label": _parse_result(a.get("result", [])),
                "status": "done",
                "labeled_by": who,
                "labeled_at": a.get("created_at"),
            }).eq("id", item_id).execute()
            written += 1
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

    # Generic parse: works for any task type. Flatten each result by its field name,
    # and keep the raw result list for complex types (e.g. de-identification spans).
    label: dict = {"_result": ann.get("result", [])}
    for r in ann.get("result", []):
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

    db = get_client()
    if db is None:
        return {"ok": False}
    try:
        db.table("project_items").update(
            {
                "label": label,
                "status": "done",
                "labeled_by": ann.get("created_username") or "label-studio",
                "labeled_at": ann.get("created_at"),
            }
        ).eq("id", item_id).execute()
    except Exception as exc:
        logger.error("LS webhook update failed: %s", exc)
        return {"ok": False}
    return {"ok": True}
