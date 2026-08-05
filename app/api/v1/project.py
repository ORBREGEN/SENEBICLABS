"""
Project intake API — companies submit data-annotation projects.

POST /project/submit  — a company submits a project (stored in Supabase, emails fired)
"""

import logging
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Header, File, Form, UploadFile
from pydantic import BaseModel, EmailStr

from app.core.config import settings
from app.services.supabase_client import get_client
from app.services import email_service
from app.services import audit
from app.services import report as report_svc
from app.services import storage
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


def _labeler_can_access(db, labeler: dict, project_id: str) -> bool:
    """Slice #2 isolation: a clinician may only touch projects they're assigned to
    (via project_clinicians). The operator (admin) sees everything. Fails CLOSED —
    if the assignment can't be verified, access is denied. Project creation alone no
    longer grants access; a clinician must be assigned. See README onboarding.
    """
    if labeler.get("id") == "admin":
        return True
    try:
        r = (
            db.table("project_clinicians").select("project_id")
            .eq("project_id", project_id).eq("clinician_id", labeler["id"]).limit(1).execute()
        )
        return bool(r.data)
    except Exception as exc:
        logger.error("Access check failed (denying): %s", exc)
        return False


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


class SkipIn(BaseModel):
    item_id: str


class ProjectMetaIn(BaseModel):
    project_id: str
    rate_per_item: float | None = None
    difficulty: str | None = None


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

    subs = rows.data or []
    counts: dict[str, dict[str, int]] = {}
    if subs:
        try:
            its = db.table("project_items").select("project_id,status").in_("project_id", [s["id"] for s in subs]).execute()
            for it in (its.data or []):
                c = counts.setdefault(it["project_id"], {"total": 0, "done": 0})
                c["total"] += 1
                if it.get("status") == "done":
                    c["done"] += 1
        except Exception as exc:
            logger.error("Portal item counts failed: %s", exc)

    projects = [
        {
            "id": r["id"],
            "company": r.get("company"),
            "description": r.get("description"),
            "task_type": r.get("task_type"),
            "stage": r.get("stage") or "submitted",
            "stage_note": r.get("stage_note"),
            "created_at": r.get("created_at"),
            "total": counts.get(r["id"], {}).get("total", 0),
            "done": counts.get(r["id"], {}).get("done", 0),
        }
        for r in subs
    ]
    return {"ok": True, "email": email, "projects": projects}


class PortalItemsIn(BaseModel):
    token: str
    project_id: str
    items: list[dict]


@router.post("/portal/items", response_model=SubmissionResponse, summary="Customer uploads data for their own project")
def portal_add_items(body: PortalItemsIn):
    email = verify_token(body.token)
    if not email:
        raise HTTPException(status_code=401, detail="This session has expired. Request a new sign-in link.")
    db = get_client()
    if db is None:
        raise HTTPException(status_code=503, detail="The portal is temporarily unavailable. Please try again shortly.")
    if not body.items:
        return SubmissionResponse(ok=True, message="No items to upload.")

    # The customer may only upload to a project that belongs to their email.
    try:
        sub = db.table("project_submissions").select("id,email").eq("id", body.project_id).limit(1).execute()
    except Exception as exc:
        logger.error("Portal upload ownership check failed: %s", exc)
        raise HTTPException(status_code=500, detail="Could not upload. Please try again.")
    if not sub.data or sub.data[0].get("email") != email:
        raise HTTPException(status_code=403, detail="That project is not on this account.")

    try:
        existing = (
            db.table("project_items").select("idx").eq("project_id", body.project_id)
            .order("idx", desc=True).limit(1).execute()
        )
        start = (existing.data[0]["idx"] + 1) if existing.data else 0
        rows_in = [{"project_id": body.project_id, "idx": start + i, "content": c} for i, c in enumerate(body.items)]
        db.table("project_items").insert(rows_in).execute()
    except Exception as exc:
        logger.error("Portal upload insert failed: %s", exc)
        raise HTTPException(status_code=500, detail="Could not upload your data. Please try again.")

    logger.info("Customer %s uploaded %d items to %s", email, len(body.items), body.project_id)
    return SubmissionResponse(ok=True, message=f"Uploaded {len(body.items)} items.")


@router.post("/portal/upload-image", response_model=SubmissionResponse, summary="Customer uploads one image file for their own project")
async def portal_upload_image(
    token: str = Form(...),
    project_id: str = Form(...),
    idx: int = Form(...),
    prediction: str = Form(default=""),
    study_id: str = Form(default=""),
    file: UploadFile = File(...),
):
    """Self-serve image intake: the client uploads one image + its manifest row (idx,
    prediction, study id). Stored under the client's private prefix with a de-identified key,
    then a review task is created — the same isolation/de-id the operator script does."""
    email = verify_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="This session has expired. Request a new sign-in link.")
    db = get_client()
    if db is None:
        raise HTTPException(status_code=503, detail="The portal is temporarily unavailable. Please try again shortly.")
    # The customer may only upload to a project that belongs to their email.
    try:
        sub = db.table("project_submissions").select("id,email").eq("id", project_id).limit(1).execute()
    except Exception as exc:
        logger.error("Portal image-upload ownership check failed: %s", exc)
        raise HTTPException(status_code=500, detail="Could not upload. Please try again.")
    if not sub.data or sub.data[0].get("email") != email:
        raise HTTPException(status_code=403, detail="That project is not on this account.")

    try:
        client_id = storage.client_id_for(email)
        storage.ensure_bucket(db)
        data = await file.read()
        key = storage.upload_image_bytes(client_id, file.filename or "image.png", data, db)
        url = storage.signed_url(key, 30 * 24 * 3600, db)  # 30-day review window
        content = {"image": url, "prediction": (prediction or None)}
        if study_id:
            content["study_id"] = study_id
        db.table("project_items").insert({"project_id": project_id, "idx": int(idx), "content": content}).execute()
    except Exception as exc:
        logger.error("Portal image upload failed: %s", exc)
        raise HTTPException(status_code=500, detail="Could not upload that image. Please try again.")
    return SubmissionResponse(ok=True, message=f"Uploaded {file.filename}")


@router.get("/portal/results", summary="Customer downloads their delivered results (magic-link token)")
def portal_results(token: str, project_id: str):
    email = verify_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="This session has expired. Request a new sign-in link.")
    db = get_client()
    if db is None:
        raise HTTPException(status_code=503, detail="The portal is temporarily unavailable. Please try again shortly.")

    # Ownership check — a customer may only download results for their own project.
    try:
        sub = db.table("project_submissions").select("id,email,company,stage").eq("id", project_id).limit(1).execute()
    except Exception as exc:
        logger.error("Portal results lookup failed: %s", exc)
        raise HTTPException(status_code=500, detail="Could not load results. Please try again.")
    if not sub.data or sub.data[0].get("email") != email:
        raise HTTPException(status_code=403, detail="That project is not on this account.")
    s = sub.data[0]
    if s.get("stage") != "delivered":
        raise HTTPException(status_code=409, detail="Results are not ready yet. You can download them once the project is delivered.")

    try:
        rows = (
            db.table("project_items").select("idx,content,label,labeled_at")
            .eq("project_id", project_id).order("idx").execute()
        )
    except Exception as exc:
        logger.error("Portal results fetch failed: %s", exc)
        raise HTTPException(status_code=500, detail="Could not load results. Please try again.")
    # The computed model-performance report, so the client sees accuracy + critical misses
    # in the portal itself, not just the raw reviewed data.
    try:
        rep = report_svc.build_report(db, project_id)
    except Exception as exc:
        logger.error("Portal report build failed: %s", exc)
        rep = None
    return {"ok": True, "company": s.get("company"), "items": rows.data or [], "report": rep}


# ── Admin ──────────────────────────────────────────────────────────────────────

def _require_admin(x_admin_key: str | None) -> None:
    if not settings.ADMIN_API_KEY or x_admin_key != settings.ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="Not authorised.")


@router.get("/admin/report/{project_id}", summary="Model-performance report for a project (admin)")
def admin_report(project_id: str, x_admin_key: str | None = Header(default=None)):
    _require_admin(x_admin_key)
    db = get_client()
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable.")
    try:
        return {"ok": True, "report": report_svc.build_report(db, project_id)}
    except Exception as exc:
        logger.error("Report build failed: %s", exc)
        raise HTTPException(status_code=500, detail="Could not build the report.")


@router.get("/admin/audit/{project_id}", summary="Audit trail for a project (admin)")
def admin_audit(project_id: str, x_admin_key: str | None = Header(default=None)):
    _require_admin(x_admin_key)
    db = get_client()
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable.")
    try:
        events = audit.history(db, project_id)
    except Exception as exc:
        logger.error("Audit read failed: %s", exc)
        raise HTTPException(status_code=500, detail="Could not load the audit trail (is the audit_events migration applied?).")
    return {"ok": True, "project_id": project_id, "count": len(events), "events": events}


@router.get("/admin/submissions", summary="List all project submissions (admin)")
def admin_submissions(x_admin_key: str | None = Header(default=None)):
    _require_admin(x_admin_key)
    db = get_client()
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable.")
    base = "id,name,email,company,description,task_type,volume,timeline,stage,stage_note,status,created_at,updated_at"
    try:
        rows = (
            db.table("project_submissions")
            .select(base + ",rate_per_item,difficulty")
            .order("created_at", desc=True)
            .execute()
        )
    except Exception:
        # rate_per_item / difficulty migration not applied yet — degrade, don't 500.
        logger.warning("rate_per_item/difficulty columns missing; run the migration to enable pay/difficulty.")
        try:
            rows = db.table("project_submissions").select(base).order("created_at", desc=True).execute()
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


@router.post("/admin/project-meta", response_model=SubmissionResponse, summary="Set a project's pay rate + difficulty (admin)")
def admin_set_meta(body: ProjectMetaIn, x_admin_key: str | None = Header(default=None)):
    _require_admin(x_admin_key)
    db = get_client()
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable.")
    try:
        db.table("project_submissions").update(
            {"rate_per_item": body.rate_per_item, "difficulty": body.difficulty}
        ).eq("id", body.project_id).execute()
    except Exception as exc:
        logger.error("Set project meta failed: %s", exc)
        if "rate_per_item" in str(exc) or "difficulty" in str(exc) or "42703" in str(exc):
            raise HTTPException(
                status_code=400,
                detail="Pay/difficulty columns are missing. Run the migration (add rate_per_item + difficulty to project_submissions) and try again.",
            )
        raise HTTPException(status_code=500, detail="Could not save.")
    return SubmissionResponse(ok=True, message="Saved.")


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
    if not _labeler_can_access(db, labeler, project_id):
        raise HTTPException(status_code=403, detail="You are not assigned to this project.")

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
        row = db.table("project_items").select("assigned_to,status,project_id").eq("id", body.item_id).limit(1).execute()
    except Exception as exc:
        logger.error("Label lookup failed: %s", exc)
        raise HTTPException(status_code=500, detail="Could not save the label.")
    if not row.data:
        raise HTTPException(status_code=404, detail="Item not found.")
    item = row.data[0]
    if not _labeler_can_access(db, labeler, item.get("project_id")):
        raise HTTPException(status_code=403, detail="You are not assigned to this project.")

    # A clinician may only label the item they hold. The operator can label anything.
    if labeler["id"] != "admin" and item.get("assigned_to") != labeler["id"]:
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

    # Audit: a save onto an already-done item is a review/correction, not a first label.
    action = audit.REVIEW if item.get("status") == "done" else audit.LABEL
    audit.record(db, item_id=body.item_id, project_id=item.get("project_id"), action=action,
                 actor_id=labeler["id"], actor_name=labeler["name"], source="app", value=body.label)
    return SubmissionResponse(ok=True, message="Saved.")


@router.post("/work/skip", response_model=SubmissionResponse, summary="Skip the current item (release to back of queue)")
def work_skip(body: SkipIn, x_work_code: str | None = Header(default=None)):
    db = get_client()
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable.")
    labeler = _resolve_labeler(db, x_work_code)
    if not labeler:
        raise HTTPException(status_code=403, detail="Invalid or inactive access code.")

    try:
        row = db.table("project_items").select("project_id,status,assigned_to").eq("id", body.item_id).limit(1).execute()
    except Exception as exc:
        logger.error("Skip lookup failed: %s", exc)
        raise HTTPException(status_code=500, detail="Could not skip.")
    if not row.data:
        raise HTTPException(status_code=404, detail="Item not found.")
    it = row.data[0]
    if not _labeler_can_access(db, labeler, it.get("project_id")):
        raise HTTPException(status_code=403, detail="You are not assigned to this project.")
    if it["status"] == "done":
        return SubmissionResponse(ok=True, message="Already done.")
    if labeler["id"] != "admin" and it.get("assigned_to") != labeler["id"]:
        raise HTTPException(status_code=409, detail="This item is not yours.")

    try:
        mx = (
            db.table("project_items").select("idx").eq("project_id", it["project_id"])
            .order("idx", desc=True).limit(1).execute()
        )
        new_idx = (mx.data[0]["idx"] + 1) if mx.data else 0
        db.table("project_items").update(
            {"status": "pending", "assigned_to": None, "claimed_at": None, "idx": new_idx}
        ).eq("id", body.item_id).execute()
    except Exception as exc:
        logger.error("Skip failed: %s", exc)
        raise HTTPException(status_code=500, detail="Could not skip.")

    audit.record(db, item_id=body.item_id, project_id=it.get("project_id"), action=audit.SKIP,
                 actor_id=labeler["id"], actor_name=labeler["name"], source="app", value=None)
    return SubmissionResponse(ok=True, message="Skipped.")


@router.get("/work/home", summary="Contributor home: available projects + personal stats")
def work_home(x_work_code: str | None = Header(default=None)):
    db = get_client()
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable.")
    labeler = _resolve_labeler(db, x_work_code)
    if not labeler:
        raise HTTPException(status_code=403, detail="Invalid or inactive access code.")

    name = labeler["name"]

    # Isolation: a clinician only sees projects they're assigned to; the operator sees all.
    allowed = None
    if labeler["id"] != "admin":
        try:
            a = db.table("project_clinicians").select("project_id").eq("clinician_id", labeler["id"]).execute()
            allowed = {r["project_id"] for r in (a.data or [])}
        except Exception as exc:
            logger.error("Assigned-projects lookup failed (scoping to none): %s", exc)
            allowed = set()

    try:
        items = db.table("project_items").select("project_id,status,labeled_by,labeled_at").execute()
    except Exception as exc:
        logger.error("Work home aggregation failed: %s", exc)
        raise HTTPException(status_code=500, detail="Could not load your work.")

    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)
    days = [now.date() - timedelta(days=i) for i in range(6, -1, -1)]   # oldest → today
    daily_map = {d.isoformat(): 0 for d in days}

    by_proj: dict[str, dict[str, int]] = {}
    mine = 0
    this_week = 0
    my_projects: set[str] = set()
    my_dates: set = set()
    my_by_proj: dict[str, dict[str, int]] = {}   # per-project counts of MY labels (total / this week)
    recent: list[tuple[str, str]] = []   # (labeled_at, project_id)

    for it in (items.data or []):
        pid = it["project_id"]
        if allowed is not None and pid not in allowed:
            continue
        p = by_proj.setdefault(pid, {"total": 0, "done": 0})
        p["total"] += 1
        if it.get("status") == "done":
            p["done"] += 1
        if it.get("labeled_by") == name:
            mine += 1
            my_projects.add(pid)
            mp = my_by_proj.setdefault(pid, {"total": 0, "week": 0})
            mp["total"] += 1
            at = it.get("labeled_at")
            if at:
                recent.append((at, pid))
                try:
                    dt = datetime.fromisoformat(at.replace("Z", "+00:00"))
                    if dt >= week_ago:
                        this_week += 1
                        mp["week"] += 1
                    my_dates.add(dt.date())
                    dk = dt.date().isoformat()
                    if dk in daily_map:
                        daily_map[dk] += 1
                except Exception:
                    pass

    meta: dict[str, dict] = {}
    if by_proj:
        ids = list(by_proj.keys())
        try:
            subs = db.table("project_submissions").select("id,company,rate_per_item,difficulty").in_("id", ids).execute()
            meta = {s["id"]: s for s in (subs.data or [])}
        except Exception:
            # pay/difficulty columns not migrated yet — fall back to names only.
            try:
                subs = db.table("project_submissions").select("id,company").in_("id", ids).execute()
                meta = {s["id"]: s for s in (subs.data or [])}
            except Exception as exc:
                logger.error("Work home meta lookup failed: %s", exc)

    def _name(pid: str) -> str:
        return (meta.get(pid) or {}).get("company") or "Project"

    # current streak: consecutive days with activity ending today (or yesterday)
    streak = 0
    cur = now.date() if now.date() in my_dates else (now.date() - timedelta(days=1))
    while cur in my_dates:
        streak += 1
        cur -= timedelta(days=1)

    # earnings = sum(rate × my labeled items) per project, only where a rate is set
    earned_total = 0.0
    earned_week = 0.0
    for pid, mc in my_by_proj.items():
        rate = (meta.get(pid) or {}).get("rate_per_item")
        if rate:
            earned_total += rate * mc["total"]
            earned_week += rate * mc["week"]

    EST_MIN_PER_ITEM = 1
    projects = []
    for pid, c in by_proj.items():
        m = meta.get(pid) or {}
        pending = c["total"] - c["done"]
        rate = m.get("rate_per_item")
        projects.append({
            "id": pid,
            "company": m.get("company") or "Project",
            "total": c["total"],
            "done": c["done"],
            "pending": pending,
            "difficulty": m.get("difficulty"),
            "payout": round(rate * pending, 2) if rate else None,
            "est_minutes": pending * EST_MIN_PER_ITEM,
        })
    projects.sort(key=lambda x: (-x["pending"], x["company"]))

    recent.sort(reverse=True)
    recent_out = [{"company": _name(pid), "at": at} for at, pid in recent[:6]]
    daily = [daily_map[d.isoformat()] for d in days]

    return {
        "ok": True,
        "name": name,
        "total_labeled": mine,
        "this_week": this_week,
        "streak": streak,
        "earned_total": round(earned_total, 2),
        "earned_week": round(earned_week, 2),
        "active_projects": len(my_projects),
        "daily": daily,
        "recent": recent_out,
        "projects": projects,
    }


@router.get("/work/brief", summary="Project brief + Label Studio link for a clinician")
def work_brief(project_id: str, x_work_code: str | None = Header(default=None)):
    db = get_client()
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable.")
    labeler = _resolve_labeler(db, x_work_code)
    if not labeler:
        raise HTTPException(status_code=403, detail="Invalid or inactive access code.")
    if not _labeler_can_access(db, labeler, project_id):
        raise HTTPException(status_code=403, detail="You are not assigned to this project.")

    try:
        sub = db.table("project_submissions").select("id,company,task_type,ls_project_id,rate_per_item").eq("id", project_id).limit(1).execute()
    except Exception:
        # rate_per_item not migrated yet — fetch without it.
        sub = db.table("project_submissions").select("id,company,task_type,ls_project_id").eq("id", project_id).limit(1).execute()
    if not sub.data:
        raise HTTPException(status_code=404, detail="Project not found.")
    s = sub.data[0]
    total, done = _progress(db, project_id)
    pending = total - done
    ls_pid = s.get("ls_project_id")
    ls_link = f"{settings.LS_URL.rstrip('/')}/projects/{ls_pid}/data" if (ls_pid and settings.LS_URL) else None
    rate = s.get("rate_per_item")
    return {
        "ok": True,
        "company": s.get("company") or "Project",
        "task_type": s.get("task_type"),
        "ls_link": ls_link,
        "total": total,
        "done": done,
        "pending": pending,
        "rate_per_item": rate,
        "payout": round(rate * pending, 2) if rate else None,
        "labeler": labeler["name"],
    }


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
