"""
Project intake API — companies submit data-annotation projects.

POST /project/submit  — a company submits a project (stored in Supabase, emails fired)
"""

import logging
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, EmailStr

from app.core.config import settings
from app.services.supabase_client import get_client
from app.services import email_service
from app.services.portal_tokens import make_token, verify_token

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/project", tags=["Project Intake"])

# The six customer-facing phases, in order. `stage` on a submission is one of these.
STAGES = ["submitted", "scoping", "agreement", "pilot", "production", "delivered"]

# How long a claimed-but-unsubmitted item is held before it returns to the pool.
CLAIM_TTL_MINUTES = 20


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _resolve_labeler(db, code: str | None) -> dict | None:
    """Resolve a work access code to a labeler.

    The operator's admin key works (id='admin'); otherwise the code must match an
    active clinician's access_code. Returns {'id', 'name'} or None if unauthorised.
    """
    if not code:
        return None
    if settings.ADMIN_API_KEY and code == settings.ADMIN_API_KEY:
        return {"id": "admin", "name": "Operator"}
    try:
        rows = db.table("clinicians").select("id,name,active").eq("access_code", code).limit(1).execute()
    except Exception as exc:
        logger.error("Clinician lookup failed: %s", exc)
        return None
    if rows.data and rows.data[0].get("active", True):
        c = rows.data[0]
        return {"id": c["id"], "name": c["name"]}
    return None


# ── Schemas ────────────────────────────────────────────────────────────────────

class ProjectSubmission(BaseModel):
    name: str
    email: EmailStr
    company: str
    description: str
    data_type: str | None = None
    task_type: str | None = None
    volume: str | None = None
    timeline: str | None = None
    data_sensitivity: str | None = None
    sample_link: str | None = None
    budget_notes: str | None = None


class SubmissionResponse(BaseModel):
    ok: bool
    message: str


class PortalRequest(BaseModel):
    email: EmailStr


class AdminAdvance(BaseModel):
    submission_id: str
    stage: str
    note: str | None = None


class ItemsIn(BaseModel):
    project_id: str
    items: list[dict]          # list of content dicts, e.g. {"prompt": ..., "output": ...}


class LabelIn(BaseModel):
    item_id: str
    label: dict                # e.g. {"score": 4, "unsafe": false, "rationale": "..."}


class ClinicianIn(BaseModel):
    name: str
    email: EmailStr | None = None


# ── Submit ─────────────────────────────────────────────────────────────────────

@router.post("/submit", response_model=SubmissionResponse, summary="Submit an annotation project")
def submit(submission: ProjectSubmission):
    db = get_client()
    if db is None:
        logger.warning("Project submission ignored — Supabase not configured (email=%s)", submission.email)
        raise HTTPException(
            status_code=503,
            detail="Submissions are temporarily unavailable. Please try again shortly.",
        )

    try:
        db.table("project_submissions").insert(
            {
                "name": submission.name,
                "email": submission.email.lower(),
                "company": submission.company,
                "description": submission.description,
                "data_type": submission.data_type,
                "task_type": submission.task_type,
                "volume": submission.volume,
                "timeline": submission.timeline,
                "data_sensitivity": submission.data_sensitivity,
                "sample_link": submission.sample_link,
                "budget_notes": submission.budget_notes,
                "status": "new",
            }
        ).execute()
    except Exception as exc:
        logger.error("Project submission insert failed: %s", exc)
        raise HTTPException(status_code=500, detail="Could not save your submission. Please try again.")

    # Emails — fire after DB write succeeds
    email_service.send_project_submission_confirmation(
        name=submission.name,
        email=submission.email,
    )
    email_service.send_project_submission_admin_alert(submission=submission)

    logger.info("Project submission received: %s (%s)", submission.company, submission.email)
    return SubmissionResponse(
        ok=True,
        message="Submission received. We will be in touch within one business day to scope your pilot.",
    )


# ── Customer portal ────────────────────────────────────────────────────────────

@router.post("/portal/request", response_model=SubmissionResponse, summary="Email a portal sign-in link")
def portal_request(req: PortalRequest):
    """Email a magic-link to a company that has submitted a project.

    Always returns ok (even if no project exists for the email) so the endpoint
    never reveals whether an address is in the system.
    """
    db = get_client()
    if db is None:
        raise HTTPException(status_code=503, detail="The portal is temporarily unavailable. Please try again shortly.")

    email = req.email.lower()
    try:
        rows = db.table("project_submissions").select("id").eq("email", email).limit(1).execute()
    except Exception as exc:
        logger.error("Portal request lookup failed: %s", exc)
        raise HTTPException(status_code=500, detail="Something went wrong. Please try again.")

    if rows.data:
        link = f"{settings.SITE_URL.rstrip('/')}/portal?token={make_token(email)}"
        email_service.send_portal_link(email=email, link=link)
        logger.info("Portal link sent to %s", email)
    else:
        logger.info("Portal request for unknown email %s (no link sent)", email)

    return SubmissionResponse(ok=True, message="If that email has a project with us, a sign-in link is on its way.")


@router.get("/portal/projects", summary="List a company's projects (magic-link token)")
def portal_projects(token: str):
    email = verify_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="This link has expired or is invalid. Request a new one.")

    db = get_client()
    if db is None:
        raise HTTPException(status_code=503, detail="The portal is temporarily unavailable. Please try again shortly.")

    try:
        rows = (
            db.table("project_submissions")
            .select("id,company,description,task_type,stage,stage_note,created_at")
            .eq("email", email)
            .order("created_at", desc=True)
            .execute()
        )
    except Exception as exc:
        logger.error("Portal projects fetch failed: %s", exc)
        raise HTTPException(status_code=500, detail="Could not load your projects. Please try again.")

    projects = [
        {
            "id": r["id"],
            "company": r.get("company"),
            "description": r.get("description"),
            "task_type": r.get("task_type"),
            "stage": r.get("stage") or "submitted",
            "stage_note": r.get("stage_note"),
            "created_at": r.get("created_at"),
        }
        for r in (rows.data or [])
    ]
    return {"ok": True, "email": email, "projects": projects}


# ── Admin ──────────────────────────────────────────────────────────────────────

def _require_admin(x_admin_key: str | None) -> None:
    if not settings.ADMIN_API_KEY or x_admin_key != settings.ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="Not authorised.")


@router.get("/admin/submissions", summary="List all project submissions (admin)")
def admin_submissions(x_admin_key: str | None = Header(default=None)):
    _require_admin(x_admin_key)
    db = get_client()
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable.")
    try:
        rows = (
            db.table("project_submissions")
            .select("id,name,email,company,description,task_type,volume,timeline,stage,stage_note,status,created_at,updated_at")
            .order("created_at", desc=True)
            .execute()
        )
    except Exception as exc:
        logger.error("Admin list failed: %s", exc)
        raise HTTPException(status_code=500, detail="Could not load submissions.")

    subs = rows.data or []
    # Attach real item progress (total / done) to each submission in one query.
    try:
        items = db.table("project_items").select("project_id,status").execute()
        counts: dict[str, dict[str, int]] = {}
        for it in (items.data or []):
            c = counts.setdefault(it["project_id"], {"total": 0, "done": 0})
            c["total"] += 1
            if it.get("status") == "done":
                c["done"] += 1
        for s in subs:
            c = counts.get(s["id"], {"total": 0, "done": 0})
            s["total"], s["done"] = c["total"], c["done"]
    except Exception as exc:
        logger.error("Progress aggregation failed: %s", exc)
        for s in subs:
            s.setdefault("total", 0)
            s.setdefault("done", 0)

    return {"ok": True, "submissions": subs, "stages": STAGES}


@router.post("/admin/advance", response_model=SubmissionResponse, summary="Advance a project's stage (admin)")
def admin_advance(body: AdminAdvance, x_admin_key: str | None = Header(default=None)):
    _require_admin(x_admin_key)
    if body.stage not in STAGES:
        raise HTTPException(status_code=422, detail=f"stage must be one of: {', '.join(STAGES)}")

    db = get_client()
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable.")

    # Reality-check the stages the system can verify, so status can't be set to a lie.
    if body.stage in ("pilot", "production", "delivered"):
        total, done = _progress(db, body.submission_id)
        if total == 0:
            raise HTTPException(status_code=422, detail=f"Add items to this project before moving it to “{body.stage}”.")
        if body.stage == "delivered" and done < total:
            raise HTTPException(status_code=422, detail=f"Can’t mark delivered — only {done} of {total} items are labeled.")

    try:
        db.table("project_submissions").update(
            {
                "stage": body.stage,
                "stage_note": body.note,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        ).eq("id", body.submission_id).execute()
    except Exception as exc:
        logger.error("Admin advance failed: %s", exc)
        raise HTTPException(status_code=500, detail="Update failed.")

    logger.info("Project %s advanced to %s", body.submission_id, body.stage)
    return SubmissionResponse(ok=True, message=f"Project advanced to {body.stage}.")


# ── Work: items + labeling ──────────────────────────────────────────────────────

def _progress(db, project_id: str) -> tuple[int, int]:
    rows = db.table("project_items").select("status").eq("project_id", project_id).execute()
    data = rows.data or []
    return len(data), sum(1 for r in data if r.get("status") == "done")


@router.post("/admin/items", response_model=SubmissionResponse, summary="Add work items to a project (admin)")
def admin_add_items(body: ItemsIn, x_admin_key: str | None = Header(default=None)):
    _require_admin(x_admin_key)
    db = get_client()
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable.")
    if not body.items:
        return SubmissionResponse(ok=True, message="No items to add.")
    try:
        existing = (
            db.table("project_items").select("idx").eq("project_id", body.project_id)
            .order("idx", desc=True).limit(1).execute()
        )
        start = (existing.data[0]["idx"] + 1) if existing.data else 0
        rows = [{"project_id": body.project_id, "idx": start + i, "content": c} for i, c in enumerate(body.items)]
        db.table("project_items").insert(rows).execute()
    except Exception as exc:
        logger.error("Add items failed: %s", exc)
        raise HTTPException(status_code=500, detail="Could not add items.")
    return SubmissionResponse(ok=True, message=f"Added {len(body.items)} items.")


@router.get("/admin/progress", summary="Item progress for a project (admin)")
def admin_progress(project_id: str, x_admin_key: str | None = Header(default=None)):
    _require_admin(x_admin_key)
    db = get_client()
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable.")
    total, done = _progress(db, project_id)
    return {"ok": True, "total": total, "done": done}


def _claim_fallback(db, project_id: str, labeler_id: str) -> dict | None:
    """App-level claim used if the atomic claim_next_item() DB function is absent.

    Compare-and-swap on the row status so two labelers can never take the same item.
    Heavier (several round trips) but correct; the RPC path is preferred.
    """
    cutoff = (datetime.now(timezone.utc) - timedelta(minutes=CLAIM_TTL_MINUTES)).isoformat()
    db.table("project_items").update({"status": "pending", "assigned_to": None, "claimed_at": None}) \
        .eq("project_id", project_id).eq("status", "in_progress").lt("claimed_at", cutoff).execute()

    held = (
        db.table("project_items").select("id,idx,content")
        .eq("project_id", project_id).eq("status", "in_progress").eq("assigned_to", labeler_id)
        .order("idx").limit(1).execute()
    )
    if held.data:
        return held.data[0]

    for _ in range(30):
        nxt = (
            db.table("project_items").select("id,idx,content")
            .eq("project_id", project_id).eq("status", "pending").order("idx").limit(1).execute()
        )
        if not nxt.data:
            return None
        cand = nxt.data[0]
        claim = (
            db.table("project_items")
            .update({"status": "in_progress", "assigned_to": labeler_id, "claimed_at": _now_iso()})
            .eq("id", cand["id"]).eq("status", "pending").execute()
        )
        if claim.data:
            return {"id": cand["id"], "idx": cand["idx"], "content": cand["content"]}
    return None


@router.get("/work/next", summary="Claim the next item to label (clinician or operator)")
def work_next(project_id: str, x_work_code: str | None = Header(default=None)):
    db = get_client()
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable.")
    labeler = _resolve_labeler(db, x_work_code)
    if not labeler:
        raise HTTPException(status_code=403, detail="Invalid or inactive access code.")

    item = None
    try:
        # Preferred: one atomic round trip via FOR UPDATE SKIP LOCKED in Postgres.
        res = db.rpc("claim_next_item", {
            "p_project": project_id,
            "p_labeler": labeler["id"],
            "p_ttl_minutes": CLAIM_TTL_MINUTES,
        }).execute()
        if res.data:
            row = res.data[0]
            item = {"id": row["id"], "idx": row["idx"], "content": row["content"]}
    except Exception as exc:
        logger.warning("claim_next_item RPC unavailable, using fallback: %s", exc)
        try:
            item = _claim_fallback(db, project_id, labeler["id"])
        except Exception as exc2:
            logger.error("Work next fallback failed: %s", exc2)
            raise HTTPException(status_code=500, detail="Could not load the next item.")

    total, done = _progress(db, project_id)
    return {"ok": True, "item": item, "total": total, "done": done, "labeler": labeler["name"]}


@router.post("/work/label", response_model=SubmissionResponse, summary="Save a label and mark item done")
def work_label(body: LabelIn, x_work_code: str | None = Header(default=None)):
    db = get_client()
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable.")
    labeler = _resolve_labeler(db, x_work_code)
    if not labeler:
        raise HTTPException(status_code=403, detail="Invalid or inactive access code.")

    try:
        row = db.table("project_items").select("assigned_to,status").eq("id", body.item_id).limit(1).execute()
    except Exception as exc:
        logger.error("Label lookup failed: %s", exc)
        raise HTTPException(status_code=500, detail="Could not save the label.")
    if not row.data:
        raise HTTPException(status_code=404, detail="Item not found.")

    # A clinician may only label the item they hold. The operator can label anything.
    if labeler["id"] != "admin" and row.data[0].get("assigned_to") != labeler["id"]:
        raise HTTPException(status_code=409, detail="This item is assigned to someone else. Skipping to the next.")

    try:
        db.table("project_items").update(
            {
                "label": body.label,
                "status": "done",
                "labeled_by": labeler["name"],
                "labeled_at": _now_iso(),
            }
        ).eq("id", body.item_id).execute()
    except Exception as exc:
        logger.error("Save label failed: %s", exc)
        raise HTTPException(status_code=500, detail="Could not save the label.")
    return SubmissionResponse(ok=True, message="Saved.")


@router.post("/admin/clinicians", summary="Create a clinician + access code (admin)")
def admin_create_clinician(body: ClinicianIn, x_admin_key: str | None = Header(default=None)):
    _require_admin(x_admin_key)
    db = get_client()
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable.")
    code = secrets.token_urlsafe(9)
    try:
        row = db.table("clinicians").insert(
            {"name": body.name, "email": body.email, "access_code": code}
        ).execute()
    except Exception as exc:
        logger.error("Create clinician failed: %s", exc)
        raise HTTPException(status_code=500, detail="Could not create the clinician.")
    c = row.data[0]
    return {
        "ok": True,
        "clinician": {"id": c["id"], "name": c["name"], "email": c.get("email"), "access_code": code},
    }


@router.get("/admin/clinicians", summary="List clinicians (admin)")
def admin_list_clinicians(x_admin_key: str | None = Header(default=None)):
    _require_admin(x_admin_key)
    db = get_client()
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable.")
    try:
        rows = (
            db.table("clinicians").select("id,name,email,access_code,active,created_at")
            .order("created_at", desc=True).execute()
        )
    except Exception as exc:
        logger.error("List clinicians failed: %s", exc)
        raise HTTPException(status_code=500, detail="Could not load clinicians.")
    return {"ok": True, "clinicians": rows.data or []}


@router.get("/admin/export", summary="Export a project's items + labels (admin)")
def admin_export(project_id: str, x_admin_key: str | None = Header(default=None)):
    _require_admin(x_admin_key)
    db = get_client()
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable.")
    try:
        rows = (
            db.table("project_items").select("idx,content,label,status,labeled_by,labeled_at")
            .eq("project_id", project_id).order("idx").execute()
        )
    except Exception as exc:
        logger.error("Export failed: %s", exc)
        raise HTTPException(status_code=500, detail="Could not export.")
    return {"ok": True, "items": rows.data or []}
