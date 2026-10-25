"""Deterministic graph-backed tuning answer engine. No LLM required."""
from __future__ import annotations

from app import db
from app.schemas import AskRequest, AskResponse, EvidenceItem, SafetyInfo

# ── Symptom keyword extraction ────────────────────────────────────────────────

_SYMPTOM_MAP: dict[str, list[str]] = {
    "understeer": ["understeer", "push", "tight", "plow", "plough", "washes out"],
    "oversteer": ["oversteer", "loose", "snap", "slide", "rotate", "rear steps out"],
    "wheelspin": ["wheelspin", "wheel spin", "traction", "spinning", "burnout"],
    "bounce": ["bounce", "bouncy", "float", "floaty", "skitter", "wallowing"],
    "brake": ["brake", "braking", "lock", "abs", "nose dive", "dive"],
    "drag": ["drag", "top speed", "mph", "acceleration", "launch"],
    "drift": ["drift", "angle", "initiation"],
    "bumps": ["bump", "curb", "kerb", "rough", "skitter"],
    "slow": ["slow", "sluggish", "lazy", "heavy", "unresponsive"],
}

_PHASE_MAP = {
    "understeer": "exit" if False else "mid-corner",
    "oversteer": "exit",
    "wheelspin": "exit",
    "bounce": "bumps/curbs",
    "brake": "braking",
    "drag": "exit",
    "drift": "exit",
    "bumps": "bumps/curbs",
    "slow": "transition",
}

_DRIVETRAIN_NORM = {
    "fwd": "FWD",
    "rwd": "RWD",
    "awd": "AWD",
    "front": "FWD",
    "rear": "RWD",
    "all wheel": "AWD",
    "all-wheel": "AWD",
    "4wd": "AWD",
    "4x4": "AWD",
}


def _extract_symptoms(text: str) -> list[str]:
    text_l = text.lower()
    found = []
    for symptom, keywords in _SYMPTOM_MAP.items():
        if any(k in text_l for k in keywords):
            found.append(symptom)
    return found or ["understeer"]


def _extract_drivetrain(req: AskRequest) -> str | None:
    if req.drivetrain:
        return _DRIVETRAIN_NORM.get(req.drivetrain.lower(), req.drivetrain.upper())
    text_l = req.question.lower()
    for k, v in _DRIVETRAIN_NORM.items():
        if k in text_l:
            return v
    return None


def _capitalize(s: str) -> str:
    return s.capitalize() if s else s


# ── Main answer builder ───────────────────────────────────────────────────────

def build_answer(req: AskRequest) -> AskResponse:
    symptoms = _extract_symptoms(req.question)
    drivetrain = _extract_drivetrain(req)
    evidence: list[EvidenceItem] = []

    # 1. Recommendations (highest value)
    recs = db.get_recommendations(symptoms, drivetrain, limit=10)

    # 2. Tuning effects
    effects = db.get_tuning_effects(symptoms, drivetrain, limit=8)

    # 3. Setting names from recommendations for interaction/baseline lookups
    setting_names = list({r["setting"] for r in recs if r.get("setting")})[:5]

    interactions = db.get_tuning_interactions(setting_names, limit=5) if setting_names else []
    baselines = db.get_tuning_baselines(setting_names, drivetrain, limit=5) if setting_names else []

    # 4. Car search evidence
    car_rows: list[dict] = []
    search_car_name = req.car
    if search_car_name:
        car_rows = db.search_cars(search_car_name, limit=3)
        for c in car_rows:
            evidence.append(EvidenceItem(
                type="car",
                title=c["full_name"],
                summary=f"{c.get('class_letter','?')}{c.get('pi','?')} — {c.get('car_type','')}",
            ))

    # 5. Build evidence from effects
    for e in effects[:4]:
        direction = e.get("effect_direction", "")
        action = e.get("action", "")
        evidence.append(EvidenceItem(
            type="effect",
            title=f"{e['control_name']}: {action} → {direction}",
            summary=e.get("evidence", "")[:160],
        ))

    # 6. Interaction evidence
    for i in interactions[:3]:
        evidence.append(EvidenceItem(
            type="interaction",
            title=f"{i['from_control']} ↔ {i.get('to_control','?')}",
            summary=(i.get("rationale") or i.get("evidence", ""))[:160],
        ))

    # 7. Baseline evidence
    for b in baselines[:3]:
        val = _format_baseline(b)
        evidence.append(EvidenceItem(
            type="baseline",
            title=f"{b['control_name']} baseline",
            summary=val,
        ))

    # ── Compose answer text ───────────────────────────────────────────────────
    likely_cause = _derive_likely_cause(symptoms, drivetrain, recs)
    try_list = _derive_try_list(recs, effects)
    watch_list = _derive_watch_list(symptoms, interactions, baselines)

    context_line = _build_context_line(req, drivetrain, symptoms)
    answer_md = _format_answer_md(context_line, likely_cause, try_list, watch_list, evidence)

    return AskResponse(
        answer=answer_md,
        likely_cause=likely_cause,
        try_in_order=try_list,
        watch_for=watch_list,
        evidence=evidence,
        safety=SafetyInfo(mode="deterministic", refused=False),
    )


def _format_baseline(b: dict) -> str:
    if b.get("value_text"):
        return b["value_text"][:120]
    if b.get("value_min") is not None and b.get("value_max") is not None:
        unit = b.get("unit") or ""
        return f"{b['value_min']}–{b['value_max']} {unit}".strip()
    return b.get("evidence", "")[:120]


def _derive_likely_cause(symptoms: list[str], drivetrain: str | None, recs: list[dict]) -> str:
    if not recs:
        symptom_str = " / ".join(symptoms)
        dt = f" ({drivetrain})" if drivetrain else ""
        return f"{_capitalize(symptom_str)}{dt} — no specific match in index; apply general tuning principles."

    top = recs[0]
    balance = top.get("balance", symptoms[0] if symptoms else "handling issue")
    phase = top.get("phase", "corner")
    dt_note = f" ({drivetrain})" if drivetrain else ""
    return f"{_capitalize(balance)} at {phase}{dt_note} — {top.get('rationale', 'see try list below')}."


def _derive_try_list(recs: list[dict], effects: list[dict]) -> list[str]:
    steps: list[str] = []
    seen: set[str] = set()

    for r in recs[:5]:
        setting = r.get("setting") or ""
        direction = r.get("direction") or ""
        rationale = r.get("rationale") or ""
        key = setting.lower()
        if key and key not in seen:
            seen.add(key)
            target = f" (focus: {r['target_end']})" if r.get("target_end") else ""
            step = f"{_capitalize(setting)}: {direction}{target}"
            if rationale and rationale.lower() not in step.lower():
                step += f" — {rationale[:100]}"
            steps.append(step)

    # Supplement from effects if we don't have enough recs
    if len(steps) < 3:
        for e in effects[:4]:
            control = e.get("control_name", "")
            action = e.get("action", "")
            direction = e.get("effect_direction", "")
            key = control.lower()
            if key and key not in seen:
                seen.add(key)
                steps.append(f"{control}: {action} to {direction}")
            if len(steps) >= 5:
                break

    return steps or ["Review suspension and differential settings for your drivetrain type."]


def _derive_watch_for(symptoms: list[str], interactions: list[dict], baselines: list[dict]) -> list[str]:
    watch: list[str] = []

    for i in interactions[:3]:
        rationale = (i.get("rationale") or "").strip()
        if rationale:
            watch.append(rationale[:140])

    if "understeer" in symptoms and "oversteer" not in symptoms:
        watch.append("Adding front grip can shift balance to oversteer — test gradually.")
    if "oversteer" in symptoms and "understeer" not in symptoms:
        watch.append("Adding rear grip reduces rotation — may introduce understeer.")
    if "wheelspin" in symptoms:
        watch.append("Differential locking increase improves traction but reduces rotation agility.")

    return watch or ["Test one change at a time; re-tune affected settings after major changes."]


# Alias used in build_answer — kept lowercase for internal consistency
_derive_watch_list = _derive_watch_for


def _build_context_line(req: AskRequest, drivetrain: str | None, symptoms: list[str]) -> str:
    parts = []
    if req.car:
        parts.append(req.car)
    if drivetrain:
        parts.append(drivetrain)
    if req.class_target:
        parts.append(req.class_target)
    if req.discipline:
        parts.append(req.discipline)
    if req.horsepower:
        parts.append(f"{req.horsepower} hp")
    if req.weight_lbs:
        parts.append(f"{req.weight_lbs} lb")
    if req.tires:
        parts.append(req.tires)
    if req.upgrades:
        parts.append("upgrades: " + ", ".join(req.upgrades[:6]))
    if req.build_notes:
        parts.append(req.build_notes)

    symptom_str = " / ".join(symptoms)
    context = ", ".join(parts)
    if context:
        return f"**{context}** — {symptom_str}"
    return f"**{_capitalize(symptom_str)}**"


def _format_answer_md(
    context_line: str,
    likely_cause: str,
    try_list: list[str],
    watch_list: list[str],
    evidence: list[EvidenceItem],
) -> str:
    lines = [
        f"{context_line}\n",
        f"**Likely cause:** {likely_cause}\n",
    ]

    if evidence:
        rel = [e for e in evidence if e.type in ("effect", "interaction", "recommendation")][:4]
        if rel:
            lines.append("**Relevant interactions:**")
            for ev in rel:
                lines.append(f"- {ev.title}: {ev.summary}")
            lines.append("")

    if try_list:
        lines.append("**Try in order:**")
        for i, step in enumerate(try_list, 1):
            lines.append(f"{i}. {step}")
        lines.append("")

    if watch_list:
        lines.append("**Watch for:**")
        for w in watch_list:
            lines.append(f"- {w}")

    return "\n".join(lines)
