"""Reject guides that the retrieved pages do not support."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime

from app.research.draft import DraftClaim, DraftGuide, DraftItem
from app.research.errors import CredentialsInOutput, InsufficientEvidence


@dataclass(frozen=True)
class EvidencePage:
    key: str
    url: str
    title: str
    text: str
    preferred: bool
    retrieved_at: datetime

SECRET_PATTERNS = (
    re.compile(r"(?i)client_secret\s*[\"':=]+\s*[A-Za-z0-9_\-]{8,}"),
    re.compile(r"(?i)\b(?:api[_-]?key|access[_-]?token|secret)\s*[:=]\s*[\"']?[A-Za-z0-9_\-]{12,}"),
    re.compile(r"\bsk-[A-Za-z0-9]{16,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
)
DURATION = re.compile(
    r"\b(?:\d+\s*[-–]\s*\d+|\d+)\s*(?:business\s+days?|days?|weeks?|hours?|minutes?)\b",
    re.IGNORECASE,
)
URL_IN_TEXT = re.compile(r"https?://[^\s)>\"]+")
TOKEN = re.compile(r"[a-z0-9]{4,}")
REVIEW_WORDS = ("review", "approval", "verification", "verify", "wait")
TESTED_CLAIM = re.compile(r"\b(verified by|we tested|was tested|i tested|has been tested)\b", re.IGNORECASE)


@dataclass
class CheckedClaim:
    value: str | None
    status: str
    note: str | None
    evidence_ids: list[str]


@dataclass
class CheckedItem:
    title: str
    body: str
    status: str
    note: str | None
    evidence_ids: list[str]


@dataclass
class CheckedGuide:
    summary: str
    decision: str
    auth_type: CheckedClaim
    setup_path_value: str
    setup_path_label: str
    setup_path_status: str
    setup_path_note: str | None
    setup_path_evidence_ids: list[str]
    difficulty: CheckedClaim
    active_effort: CheckedClaim
    approval_wait: CheckedClaim
    confidence: CheckedClaim
    managed: CheckedClaim
    bring_your_own: CheckedClaim
    redirect_uri: CheckedClaim
    prerequisites: list[CheckedItem] = field(default_factory=list)
    steps: list[CheckedItem] = field(default_factory=list)
    blockers: list[CheckedItem] = field(default_factory=list)
    human_actions: list[CheckedItem] = field(default_factory=list)
    supports: dict[str, list[str]] = field(default_factory=dict)
    conflicts: list[str] = field(default_factory=list)


def contains_secret(text: str) -> bool:
    return any(pattern.search(text) for pattern in SECRET_PATTERNS)


def _plain(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = re.sub(r"<[^>]+>", "", value)
    cleaned = "".join(char for char in cleaned if char in "\n\t" or ord(char) >= 32)
    collapsed = " ".join(cleaned.split())
    return collapsed or None


def _tokens(value: str) -> set[str]:
    return set(TOKEN.findall(value.lower()))


def _overlap(claim: str, evidence: str) -> float:
    claim_tokens = _tokens(claim)
    if not claim_tokens:
        return 0
    return len(claim_tokens & _tokens(evidence)) / len(claim_tokens)


def _cited_text(evidence_ids: list[str], pages: dict[str, EvidencePage]) -> str:
    return "\n".join(pages[item].text for item in evidence_ids if item in pages)


def _preferred(evidence_ids: list[str], pages: dict[str, EvidencePage]) -> bool:
    return any(pages[item].preferred for item in evidence_ids if item in pages)


def _append_note(note: str | None, extra: str) -> str:
    if not note:
        return extra
    if extra in note:
        return note
    return f"{note} {extra}"


def _record(supports: dict[str, list[str]], evidence_ids: list[str], claim_key: str) -> None:
    for evidence_id in evidence_ids:
        supports.setdefault(evidence_id, [])
        if claim_key not in supports[evidence_id]:
            supports[evidence_id].append(claim_key)


def _durations_in_review(text: str) -> list[str]:
    found: list[str] = []
    for sentence in re.split(r"(?<=[.!?])\s+", text):
        if not any(word in sentence.lower() for word in REVIEW_WORDS):
            continue
        for match in DURATION.finditer(sentence):
            phrase = " ".join(match.group(0).split())
            if phrase.lower() not in {item.lower() for item in found}:
                found.append(phrase)
    return found


def _assess(
    claim: DraftClaim,
    pages: dict[str, EvidencePage],
    *,
    material: bool,
    literal_urls: bool,
) -> CheckedClaim:
    value = _plain(claim.value)
    note = _plain(claim.note)
    status = claim.status
    evidence_ids = list(dict.fromkeys(item for item in claim.evidence_ids if item in pages))
    if claim.evidence_ids and not evidence_ids and status != "unknown":
        status = "unknown"
        value = None
        note = _append_note(note, "A citation did not match a retrieved page.")

    if status == "unknown":
        return CheckedClaim(value=None, status="unknown", note=note, evidence_ids=[])

    if not evidence_ids:
        if material:
            return CheckedClaim(
                value=None,
                status="unknown",
                note=_append_note(note, "No retrieved page was cited for this claim."),
                evidence_ids=[],
            )
        return CheckedClaim(
            value=None,
            status="unknown",
            note=_append_note(note, "No retrieved page states this estimate."),
            evidence_ids=[],
        )

    evidence = _cited_text(evidence_ids, pages)
    compared = value or ""
    if status in {"documented", "inferred"} and compared:
        overlap = _overlap(compared, evidence)
        if overlap == 0 or (status == "documented" and overlap < 0.4):
            note = _append_note(note, "The retrieved pages do not state this in matching language.")
            if overlap == 0:
                status = "unknown"
                value = None
            else:
                status = "inferred"
    if status == "documented" and not _preferred(evidence_ids, pages):
        status = "inferred"
        note = _append_note(note, "The citation is not an official documentation host.")
    if literal_urls and value:
        for url in URL_IN_TEXT.findall(value):
            if url.rstrip(".,") not in evidence:
                value = None
                status = "unknown"
                note = _append_note(note, "The cited pages do not contain that URL.")
                break
    if value:
        for phrase in DURATION.findall(value):
            if phrase.lower() not in evidence.lower():
                value = None
                status = "unknown"
                note = _append_note(note, "The cited pages do not contain that duration.")
                break
    if status != "unknown" and not value:
        status = "unknown"
    return CheckedClaim(value=value, status=status, note=note, evidence_ids=evidence_ids if status != "unknown" else evidence_ids)


def _assess_item(item: DraftItem, pages: dict[str, EvidencePage]) -> CheckedItem | None:
    checked = _assess(
        DraftClaim(value=item.body, status=item.status, note=item.note, evidence_ids=item.evidence_ids),
        pages,
        material=True,
        literal_urls=True,
    )
    if checked.status == "unknown" and checked.value is None and "No retrieved page was cited" in (checked.note or ""):
        return None
    if checked.status == "unknown" and checked.value is None and "matching language" in (checked.note or ""):
        return None
    if checked.value is None:
        return None
    title = _plain(item.title) or "Untitled step"
    return CheckedItem(
        title=title[:200],
        body=checked.value[:2000],
        status=checked.status,
        note=checked.note,
        evidence_ids=checked.evidence_ids,
    )


def _apply_wait_conflict(claim: CheckedClaim, pages: dict[str, EvidencePage]) -> tuple[CheckedClaim, str | None]:
    phrases = _durations_in_review("\n".join(page.text for page in pages.values()))
    if len(phrases) < 2:
        return claim, None
    combined = f"{claim.value or ''} {claim.note or ''}".lower()
    if all(phrase.lower() in combined for phrase in phrases) and claim.status in {"unknown", "inferred"}:
        return claim, None
    listed = "; ".join(phrases)
    note = (
        f"Retrieved pages disagree on the approval wait ({listed}). "
        "Neither figure is chosen. The wait is unknown."
    )
    return CheckedClaim(value=None, status="unknown", note=note, evidence_ids=claim.evidence_ids), note


def _json_object(raw: str) -> str:
    """Take the JSON object out of a fenced or prefaced model response."""

    text = raw.strip()
    fenced = re.match(r"^```(?:json)?\s*(.*?)\s*```$", text, flags=re.IGNORECASE | re.DOTALL)
    if fenced:
        text = fenced.group(1).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        return text[start : end + 1]
    return text


def validate_draft(raw: str, pages: list[EvidencePage]) -> CheckedGuide:
    if contains_secret(raw):
        raise CredentialsInOutput()
    payload = _json_object(raw)
    if contains_secret(payload):
        raise CredentialsInOutput()
    by_key = {page.key: page for page in pages}
    draft = DraftGuide.model_validate_json(payload)
    if contains_secret(draft.model_dump_json()):
        raise CredentialsInOutput()

    supports: dict[str, list[str]] = {}
    auth = _assess(draft.auth_type, by_key, material=True, literal_urls=False)
    setup_ids = [item for item in draft.setup_path_evidence_ids if item in by_key]
    setup = _assess(
        DraftClaim(
            value=draft.setup_path_label,
            status=draft.setup_path_status,
            note=draft.setup_path_note,
            evidence_ids=setup_ids,
        ),
        by_key,
        material=True,
        literal_urls=False,
    )
    managed = _assess(draft.managed, by_key, material=True, literal_urls=False)
    bring_your_own = _assess(draft.bring_your_own, by_key, material=True, literal_urls=False)
    redirect = _assess(draft.redirect_uri, by_key, material=True, literal_urls=True)
    difficulty = _assess(draft.difficulty, by_key, material=False, literal_urls=False)
    active_effort = _assess(draft.active_effort, by_key, material=False, literal_urls=True)
    approval = _assess(draft.approval_wait, by_key, material=False, literal_urls=False)
    confidence = _assess(draft.confidence, by_key, material=False, literal_urls=False)
    approval, conflict_note = _apply_wait_conflict(approval, by_key)

    steps = [item for item in (_assess_item(step, by_key) for step in draft.steps) if item and item.status != "unknown"]
    prerequisites = [item for item in (_assess_item(step, by_key) for step in draft.prerequisites) if item]
    blockers = [item for item in (_assess_item(step, by_key) for step in draft.blockers) if item]
    human_actions = [item for item in (_assess_item(step, by_key) for step in draft.human_actions) if item]

    conflicts = [conflict_note] if conflict_note else []
    for item in draft.conflicts:
        summary = _plain(item.summary)
        if summary:
            conflicts.append(summary)

    if auth.status == "unknown" or not auth.value:
        raise InsufficientEvidence(
            "The retrieved pages do not support an authentication type, so no guide was saved."
        )
    if not steps:
        raise InsufficientEvidence(
            "The retrieved pages do not support registration steps, so no guide was saved."
        )
    human_actions = [item for item in human_actions if item.status != "unknown"]
    if not human_actions:
        raise InsufficientEvidence(
            "The retrieved pages do not support a step a person has to perform, so no guide was saved."
        )
    if setup.status == "unknown":
        draft_setup_value = "own_app_unless_confirmed"
        draft_setup_label = "Own app unless managed auth is confirmed"
    else:
        draft_setup_value = draft.setup_path_value
        draft_setup_label = setup.value or draft.setup_path_label

    for key, claim in (
        ("auth_type", auth),
        ("setup_path", setup),
        ("managed", managed),
        ("bring_your_own", bring_your_own),
        ("redirect_uri", redirect),
        ("approval_wait", approval),
    ):
        if claim.status != "unknown":
            _record(supports, claim.evidence_ids, key)
    for kind, items in (
        ("prerequisite", prerequisites),
        ("step", steps),
        ("blocker", blockers),
        ("human_action", human_actions),
    ):
        for index, item in enumerate(items, start=1):
            if item.status != "unknown":
                _record(supports, item.evidence_ids, f"{kind}:{index}")

    summary = _plain(draft.summary) or ""
    decision = _plain(draft.decision) or ""
    if TESTED_CLAIM.search(summary) or TESTED_CLAIM.search(decision):
        summary = "This guide only restates pages retrieved for this run. Nothing was executed."
        decision = summary
    if conflict_note and not any(conflict_note in (item.body or "") for item in blockers):
        cited = [page.key for page in pages]
        blockers.append(
            CheckedItem(
                title="Sources disagree on the approval wait",
                body=conflict_note,
                status="inferred",
                note="Both figures are quoted. Neither is selected.",
                evidence_ids=cited,
            )
        )
        _record(supports, cited, f"blocker:{len(blockers)}")

    return CheckedGuide(
        summary=summary[:2000],
        decision=decision[:2000],
        auth_type=auth,
        setup_path_value=draft_setup_value,
        setup_path_label=draft_setup_label[:160],
        setup_path_status=setup.status if setup.status != "unknown" else "unknown",
        setup_path_note=setup.note,
        setup_path_evidence_ids=setup.evidence_ids,
        difficulty=difficulty,
        active_effort=active_effort,
        approval_wait=approval,
        confidence=confidence,
        managed=managed,
        bring_your_own=bring_your_own,
        redirect_uri=redirect,
        prerequisites=prerequisites,
        steps=steps,
        blockers=blockers,
        human_actions=human_actions,
        supports=supports,
        conflicts=conflicts,
    )
