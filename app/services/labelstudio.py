"""
Label Studio integration — Label Studio is the annotation surface only.

Your platform (Supabase) stays the system of record. We push tasks out to a Label
Studio project, clinicians label there, and a webhook writes annotations back into
project_items. Each task carries `_item_id` so the webhook can map an annotation
back to the right row.
"""

import logging
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

# A library of task types. Each is a Label Studio labeling config; the keys it reads
# from task data (e.g. $prompt, $output_a) are the columns that project's items must
# have. The webhook parses results back generically by from_name.
# Shared visual tokens so every task type looks the same and feels designed.
_WRAP = "font-family: 'Inter', system-ui, -apple-system, sans-serif; max-width: 780px; margin: 0 auto; padding: 8px 4px 24px;"
_HEAD = "padding-bottom: 16px; border-bottom: 1px solid #e9ecef; margin-bottom: 20px;"
_TITLE = "font-size: 19px; font-weight: 600; color: #0f172a; margin: 0;"
_SUB = "font-size: 14px; font-weight: 400; color: #64748b; margin: 4px 0 0;"
_CARD = "background: #f8fafc; border: 1px solid #e9ecef; border-radius: 12px; padding: 16px 18px; margin-bottom: 12px;"
_CARD_HI = "background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 16px 18px; margin-bottom: 24px; box-shadow: 0 1px 2px rgba(15,23,42,0.04);"
_CAPS = "font-size: 11px; letter-spacing: 0.08em; text-transform: uppercase; color: #94a3b8; font-weight: 700; margin: 0 0 6px;"
_BODY = "font-size: 15px; line-height: 1.65; color: #0f172a; margin: 0; white-space: pre-wrap;"
_SECT = "font-size: 14px; font-weight: 600; color: #0f172a; margin: 0 0 4px;"
_HINT = "font-size: 13px; font-weight: 400; color: #64748b; margin: 0 0 10px;"

CONFIGS: dict[str, str] = {
    # Rate a single response — needs columns: prompt, output
    "eval_rating": f"""<View style="{_WRAP}">
  <View style="{_HEAD}">
    <Header value="Clinical response evaluation" style="{_TITLE}"/>
    <Header value="Score the response for factual accuracy and clinical safety." style="{_SUB}"/>
  </View>

  <View style="{_CARD}">
    <Header value="Prompt" style="{_CAPS}"/>
    <Text name="prompt" value="$prompt" style="{_BODY}"/>
  </View>

  <View style="{_CARD_HI}">
    <Header value="Model response" style="{_CAPS}"/>
    <Text name="output" value="$output" style="{_BODY}"/>
  </View>

  <View style="margin-bottom: 22px;">
    <Header value="Accuracy and safety" style="{_SECT}"/>
    <Header value="1 = unsafe or incorrect     5 = fully correct and safe" style="{_HINT}"/>
    <Rating name="score" toName="output" maxRating="5" icon="star" size="large" required="true"/>
  </View>

  <View style="margin-bottom: 20px;">
    <Choices name="flag" toName="output" choice="single" showInline="true">
      <Choice value="Flag: unsafe or clinically incorrect"/>
    </Choices>
  </View>

  <View>
    <Header value="Rationale" style="{_SECT}"/>
    <TextArea name="rationale" toName="output" placeholder="One line on why you gave this score" rows="3"/>
  </View>
</View>""",

    # Compare two responses (RLHF preference) — needs columns: prompt, output_a, output_b
    "preference": f"""<View style="{_WRAP}">
  <View style="{_HEAD}">
    <Header value="Response preference" style="{_TITLE}"/>
    <Header value="Choose the response a clinician should prefer, and say why." style="{_SUB}"/>
  </View>

  <View style="{_CARD}">
    <Header value="Prompt" style="{_CAPS}"/>
    <Text name="prompt" value="$prompt" style="{_BODY}"/>
  </View>

  <View style="display: flex; gap: 14px; margin-bottom: 24px;">
    <View style="flex: 1; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 16px 18px;">
      <Header value="Response A" style="{_CAPS}"/>
      <Text name="output_a" value="$output_a" style="{_BODY}"/>
    </View>
    <View style="flex: 1; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 16px 18px;">
      <Header value="Response B" style="{_CAPS}"/>
      <Text name="output_b" value="$output_b" style="{_BODY}"/>
    </View>
  </View>

  <View style="margin-bottom: 20px;">
    <Header value="Which response is better?" style="{_SECT}"/>
    <Choices name="preference" toName="prompt" choice="single" showInline="true" required="true">
      <Choice value="A is better"/>
      <Choice value="B is better"/>
      <Choice value="Tie"/>
    </Choices>
  </View>

  <View>
    <Header value="Rationale" style="{_SECT}"/>
    <TextArea name="rationale" toName="prompt" placeholder="Why is it better, or why a tie" rows="3"/>
  </View>
</View>""",

    # Write the ideal answer (RLHF generation / gold answers) — needs column: prompt
    "response_writing": f"""<View style="{_WRAP}">
  <View style="{_HEAD}">
    <Header value="Write the ideal response" style="{_TITLE}"/>
    <Header value="Write the answer a careful clinician would give to this prompt." style="{_SUB}"/>
  </View>

  <View style="{_CARD_HI}">
    <Header value="Prompt" style="{_CAPS}"/>
    <Text name="prompt" value="$prompt" style="{_BODY}"/>
  </View>

  <View>
    <Header value="Your response" style="{_SECT}"/>
    <TextArea name="response" toName="prompt" placeholder="Write a clear, clinically sound answer" rows="8" required="true"/>
  </View>
</View>""",

    # Tag identifying information in clinical text — needs column: text
    "de_identification": f"""<View style="{_WRAP}">
  <View style="{_HEAD}">
    <Header value="De-identification" style="{_TITLE}"/>
    <Header value="Select a label, then highlight every piece of identifying information in the text." style="{_SUB}"/>
  </View>

  <View style="margin-bottom: 16px;">
    <Labels name="phi" toName="text">
      <Label value="Name" background="#e1746f"/>
      <Label value="Date" background="#6fa8e1"/>
      <Label value="Location" background="#7fd17f"/>
      <Label value="ID / MRN" background="#e1c96f"/>
      <Label value="Contact" background="#c79ae0"/>
    </Labels>
  </View>

  <View style="{_CARD_HI}">
    <Text name="text" value="$text" style="{_BODY}"/>
  </View>
</View>""",

    # Multi-axis rubric evaluation (the high-value clinical eval) — needs columns: prompt, output
    "rubric_eval": f"""<View style="{_WRAP}">
  <View style="{_HEAD}">
    <Header value="Clinical rubric evaluation" style="{_TITLE}"/>
    <Header value="Score the response on each dimension, then flag the primary issue." style="{_SUB}"/>
  </View>

  <View style="{_CARD}">
    <Header value="Prompt" style="{_CAPS}"/>
    <Text name="prompt" value="$prompt" style="{_BODY}"/>
  </View>

  <View style="{_CARD_HI}">
    <Header value="Model response" style="{_CAPS}"/>
    <Text name="output" value="$output" style="{_BODY}"/>
  </View>

  <View style="margin-bottom: 14px;">
    <Header value="Factual accuracy" style="{_SECT}"/>
    <Rating name="accuracy" toName="output" maxRating="5" icon="star" size="medium" required="true"/>
  </View>
  <View style="margin-bottom: 14px;">
    <Header value="Clinical safety" style="{_SECT}"/>
    <Rating name="safety" toName="output" maxRating="5" icon="star" size="medium" required="true"/>
  </View>
  <View style="margin-bottom: 14px;">
    <Header value="Completeness" style="{_SECT}"/>
    <Rating name="completeness" toName="output" maxRating="5" icon="star" size="medium" required="true"/>
  </View>
  <View style="margin-bottom: 22px;">
    <Header value="Free of hallucination" style="{_SECT}"/>
    <Rating name="grounding" toName="output" maxRating="5" icon="star" size="medium" required="true"/>
  </View>

  <View style="margin-bottom: 20px;">
    <Header value="Primary issue" style="{_SECT}"/>
    <Choices name="issue" toName="output" choice="single" showInline="true">
      <Choice value="None"/>
      <Choice value="Factual error"/>
      <Choice value="Unsafe recommendation"/>
      <Choice value="Missing critical info"/>
      <Choice value="Hallucinated content"/>
      <Choice value="Outdated guidance"/>
    </Choices>
  </View>

  <View>
    <Header value="Rationale" style="{_SECT}"/>
    <TextArea name="rationale" toName="output" placeholder="Briefly justify the scores" rows="3" required="true"/>
  </View>
</View>""",

    # Highlight and categorise errors in a response — needs columns: prompt, output
    "error_annotation": f"""<View style="{_WRAP}">
  <View style="{_HEAD}">
    <Header value="Error annotation" style="{_TITLE}"/>
    <Header value="Select an error type, then highlight every part of the response that contains it." style="{_SUB}"/>
  </View>

  <View style="{_CARD}">
    <Header value="Prompt" style="{_CAPS}"/>
    <Text name="prompt" value="$prompt" style="{_BODY}"/>
  </View>

  <View style="margin-bottom: 14px;">
    <Labels name="errors" toName="output">
      <Label value="Factual error" background="#e1746f"/>
      <Label value="Unsafe advice" background="#d6336c"/>
      <Label value="Missing info" background="#6fa8e1"/>
      <Label value="Hallucination" background="#b07fd1"/>
      <Label value="Outdated" background="#e1c96f"/>
    </Labels>
  </View>

  <View style="{_CARD_HI}">
    <Header value="Model response" style="{_CAPS}"/>
    <Text name="output" value="$output" style="{_BODY}"/>
  </View>

  <View style="margin: 20px 0;">
    <Header value="Overall severity" style="{_SECT}"/>
    <Choices name="severity" toName="output" choice="single" showInline="true">
      <Choice value="Minor"/>
      <Choice value="Moderate"/>
      <Choice value="Severe"/>
    </Choices>
  </View>

  <View>
    <Header value="Notes" style="{_SECT}"/>
    <TextArea name="rationale" toName="output" placeholder="Summarise the errors" rows="3"/>
  </View>
</View>""",

    # Verify each claim against the evidence — needs columns: prompt, output
    "fact_verification": f"""<View style="{_WRAP}">
  <View style="{_HEAD}">
    <Header value="Fact verification" style="{_TITLE}"/>
    <Header value="Highlight each claim and mark whether it is supported by the evidence." style="{_SUB}"/>
  </View>

  <View style="{_CARD}">
    <Header value="Prompt" style="{_CAPS}"/>
    <Text name="prompt" value="$prompt" style="{_BODY}"/>
  </View>

  <View style="margin-bottom: 14px;">
    <Labels name="claims" toName="output">
      <Label value="Supported" background="#7fd17f"/>
      <Label value="Unsupported" background="#e1746f"/>
      <Label value="Needs citation" background="#e1c96f"/>
    </Labels>
  </View>

  <View style="{_CARD_HI}">
    <Header value="Model response" style="{_CAPS}"/>
    <Text name="output" value="$output" style="{_BODY}"/>
  </View>

  <View style="margin: 20px 0;">
    <Header value="Overall verdict" style="{_SECT}"/>
    <Choices name="verdict" toName="output" choice="single" showInline="true" required="true">
      <Choice value="Fully supported"/>
      <Choice value="Partially supported"/>
      <Choice value="Not supported"/>
    </Choices>
  </View>

  <View>
    <Header value="Notes" style="{_SECT}"/>
    <TextArea name="notes" toName="output" placeholder="Optional notes" rows="2"/>
  </View>
</View>""",

    # Extract clinical entities (NER) — needs column: text
    "clinical_extraction": f"""<View style="{_WRAP}">
  <View style="{_HEAD}">
    <Header value="Clinical extraction" style="{_TITLE}"/>
    <Header value="Select an entity type, then highlight every matching span in the text." style="{_SUB}"/>
  </View>

  <View style="margin-bottom: 14px;">
    <Labels name="entities" toName="text">
      <Label value="Medication" background="#6fa8e1"/>
      <Label value="Dosage" background="#7fd17f"/>
      <Label value="Frequency" background="#9ad0c2"/>
      <Label value="Diagnosis" background="#e1746f"/>
      <Label value="Symptom" background="#e1c96f"/>
      <Label value="Procedure" background="#b07fd1"/>
      <Label value="Lab or vital" background="#c79ae0"/>
    </Labels>
  </View>

  <View style="{_CARD_HI}">
    <Text name="text" value="$text" style="{_BODY}"/>
  </View>
</View>""",

    # Categorise clinical text — needs column: text (operator edits the categories per project)
    "classification": f"""<View style="{_WRAP}">
  <View style="{_HEAD}">
    <Header value="Clinical classification" style="{_TITLE}"/>
    <Header value="Read the text and assign the correct category and urgency." style="{_SUB}"/>
  </View>

  <View style="{_CARD_HI}">
    <Text name="text" value="$text" style="{_BODY}"/>
  </View>

  <View style="margin-bottom: 20px;">
    <Header value="Category" style="{_SECT}"/>
    <Choices name="category" toName="text" choice="single" showInline="true" required="true">
      <Choice value="Primary care"/>
      <Choice value="Specialist referral"/>
      <Choice value="Emergency"/>
      <Choice value="Non-clinical"/>
    </Choices>
  </View>

  <View style="margin-bottom: 20px;">
    <Header value="Urgency" style="{_SECT}"/>
    <Choices name="urgency" toName="text" choice="single" showInline="true">
      <Choice value="Routine"/>
      <Choice value="Urgent"/>
      <Choice value="Emergent"/>
    </Choices>
  </View>

  <View>
    <Header value="Notes" style="{_SECT}"/>
    <TextArea name="notes" toName="text" placeholder="Optional notes" rows="2"/>
  </View>
</View>""",

    # Safety review of a response — needs columns: prompt, output
    "safety_review": f"""<View style="{_WRAP}">
  <View style="{_HEAD}">
    <Header value="Safety review" style="{_TITLE}"/>
    <Header value="Judge whether this response is safe to show a patient or clinician." style="{_SUB}"/>
  </View>

  <View style="{_CARD}">
    <Header value="Prompt" style="{_CAPS}"/>
    <Text name="prompt" value="$prompt" style="{_BODY}"/>
  </View>

  <View style="{_CARD_HI}">
    <Header value="Model response" style="{_CAPS}"/>
    <Text name="output" value="$output" style="{_BODY}"/>
  </View>

  <View style="margin-bottom: 20px;">
    <Header value="Is the response safe?" style="{_SECT}"/>
    <Choices name="safety" toName="output" choice="single" showInline="true" required="true">
      <Choice value="Safe"/>
      <Choice value="Borderline"/>
      <Choice value="Unsafe"/>
    </Choices>
  </View>

  <View style="margin-bottom: 20px;">
    <Header value="Harm category (if any)" style="{_SECT}"/>
    <Choices name="harm" toName="output" choice="single" showInline="true">
      <Choice value="None"/>
      <Choice value="Incorrect treatment"/>
      <Choice value="Missed red flag"/>
      <Choice value="Harmful advice"/>
      <Choice value="Privacy or PHI"/>
    </Choices>
  </View>

  <View>
    <Header value="Rationale" style="{_SECT}"/>
    <TextArea name="rationale" toName="output" placeholder="Explain your judgement" rows="3" required="true"/>
  </View>
</View>""",
}

# columns each task type expects (for operator guidance)
TASK_TYPE_COLUMNS = {
    "eval_rating": ["prompt", "output"],
    "rubric_eval": ["prompt", "output"],
    "preference": ["prompt", "output_a", "output_b"],
    "response_writing": ["prompt"],
    "de_identification": ["text"],
    "error_annotation": ["prompt", "output"],
    "fact_verification": ["prompt", "output"],
    "clinical_extraction": ["text"],
    "classification": ["text"],
    "safety_review": ["prompt", "output"],
}

DEFAULT_LABEL_CONFIG = CONFIGS["eval_rating"]


def get_config(task_type: str | None) -> str:
    return CONFIGS.get(task_type or "eval_rating", DEFAULT_LABEL_CONFIG)


def is_configured() -> bool:
    return bool(settings.LS_URL and settings.LS_TOKEN)


def _base() -> str:
    return (settings.LS_URL or "").rstrip("/")


def _headers() -> dict:
    return {"Authorization": f"Token {settings.LS_TOKEN}"}


def create_project(title: str, label_config: str = DEFAULT_LABEL_CONFIG) -> int:
    r = httpx.post(
        f"{_base()}/api/projects/",
        headers=_headers(),
        json={"title": title, "label_config": label_config},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["id"]


def push_tasks(ls_project_id: int, items: list[dict]) -> int:
    """Import items as tasks. Each item is {id, content}; we carry id as _item_id."""
    tasks = [{"data": {**(it.get("content") or {}), "_item_id": it["id"]}} for it in items]
    if not tasks:
        return 0
    r = httpx.post(
        f"{_base()}/api/projects/{ls_project_id}/import",
        headers=_headers(),
        json=tasks,
        timeout=120,
    )
    r.raise_for_status()
    return len(tasks)


def get_task(task_id: int) -> dict:
    r = httpx.get(f"{_base()}/api/tasks/{task_id}", headers=_headers(), timeout=30)
    r.raise_for_status()
    return r.json()


def export_tasks(ls_project_id: int) -> list:
    """All tasks for a project, each with its annotations (used to pull results back)."""
    r = httpx.get(
        f"{_base()}/api/projects/{ls_project_id}/export?exportType=JSON",
        headers=_headers(),
        timeout=120,
    )
    r.raise_for_status()
    return r.json()
