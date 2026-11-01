"""Rapport de revue (Markdown) et fichier de décisions (YAML)."""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import yaml

from .matching import changed_fields
from .model import Case, Product
from .repository import Draft

FIELD_LABELS = {"brand": "marque", "form": "forme", "dosage": "dosage", "packaging": "conditionnement",
                "reg_raw": "n° enregistrement", "dci_code": "code DCI", "dci": "DCI", "liste": "liste",
                "hospital": "hôpital", "pharmacy": "officine", "type": "type", "origin": "origine", "lab": "labo",
                "country": "pays", "initial_date": "date initiale", "final_date": "date finale",
                "stability": "stabilité", "obs": "OBS", "withdrawal_date": "date de retrait",
                "withdrawal_reason": "motif de retrait", "withdrawal_kind": "type de retrait"}
CATEGORY_ORDER = ["nouveau", "statut", "modifie", "disparu", "inchange"]


@dataclass
class Decision:
    case_id: str
    choice: str
    decided_by: str
    decided_at: date


class DecisionsInvalid(Exception):
    def __init__(self, problems: list[str]):
        self.problems = problems
        super().__init__("Fichier de décisions invalide :\n- " + "\n- ".join(problems))


def possible_choices(case: Case) -> list[str]:
    refs = [c.ref for c in case.candidates]
    if case.kind == "disparu_sans_retrait":
        return ["disparu"]
    if case.kind == "double_feuille":
        return [f"garder:{r}" for r in refs]
    return [f"meme_produit:{r}" for r in refs] + ["nouveau"]


def describe(p: Product | None) -> str:
    if p is None:
        return "—"
    return f"{p.brand} {p.dosage} {p.form} — {p.packaging} ({p.reg_raw}, {p.lab}) [{p.sheet}, ligne {p.row_number}]"


def _fmt(v) -> str:
    return "∅" if v in (None, "") else str(v)


def _diff_lines(old: Product, new: Product, names: list[str] | None = None) -> list[str]:
    names = names if names is not None else changed_fields(old, new)
    return [f"{FIELD_LABELS.get(n, n)} : {_fmt(getattr(old, n))} → {_fmt(getattr(new, n))}" for n in names]


def render_report(draft: Draft) -> str:
    v = draft.version
    counts = Counter(g.category for g in draft.gaps)
    out = [f"# Revue de la nomenclature {v.label}", "",
           f"- Fichier : `{v.source_filename}` (SHA-256 `{v.source_sha256}`)",
           f"- Arrêtée au : {v.reference_date}", f"- État : {v.state}", "",
           "| Catégorie | Nombre |", "| --- | --- |"]
    out += [f"| {c} | {counts.get(c, 0)} |" for c in CATEGORY_ORDER]
    out += [f"| à trancher | {len(draft.cases)} |", f"| anomalies | {len(draft.anomalies)} |", ""]

    out += ["## À trancher", ""]
    if not draft.cases:
        out.append("Aucun cas.")
    for c in draft.cases:
        out += [f"### `{c.case_id}` — {c.kind}", ""]
        if c.subject is not None:
            out.append(f"- Nouvelle ligne : {describe(c.subject)}")
        if c.subject_product_id is not None:
            out.append(f"- Produit publié disparu sans retrait : `{c.subject_product_id}`")
        for k in c.candidates:
            out.append(f"- Candidat {k.ref} : {describe(k.product)}")
            if c.subject is not None and k.product is not None and c.kind != "double_feuille":
                out += [f"  - {line}" for line in _diff_lines(k.product, c.subject)]
        out += [f"- Choix possibles : {', '.join(possible_choices(c))}", ""]

    titles = {"nouveau": "Nouveaux produits", "statut": "Changements de statut", "modifie": "Modifications",
              "disparu": "Disparus (déjà retirés ou non renouvelés)"}
    for cat in ("nouveau", "statut", "modifie", "disparu"):
        items = [g for g in draft.gaps if g.category == cat]
        out += [f"## {titles[cat]} ({len(items)})", ""]
        for g in items:
            out.append(f"- {describe(g.new or g.old)}")
            if g.old is not None and g.new is not None:
                out += [f"  - {line}" for line in _diff_lines(g.old, g.new, g.changed_fields)]
        out.append("")

    out += [f"## Anomalies ({len(draft.anomalies)})", ""]
    by_field = defaultdict(list)
    for a in draft.anomalies:
        by_field[a.field].append(a)
    for f, items in sorted(by_field.items()):
        out += [f"### {f} ({len(items)})", ""]
        out += [f"- {a.sheet}, ligne {a.row_number} : « {a.value} » — {a.message}" for a in items]
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def _brief(p: Product | None) -> dict | None:
    if p is None:
        return None
    return {"n_enregistrement": p.reg_raw, "marque": p.brand, "dosage": p.dosage, "forme": p.form,
            "conditionnement": p.packaging, "labo": p.lab, "feuille": p.sheet, "ligne": p.row_number}


def write_decisions_template(draft: Draft, path: Path) -> None:
    path = Path(path)
    existing = {}
    if path.exists():
        old = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        existing = {c.get("id"): c for c in old.get("cas") or [] if isinstance(c, dict)}
    cas = []
    for c in draft.cases:
        prev = existing.get(c.case_id, {})
        cas.append({
            "id": c.case_id,
            "type": c.kind,
            "sujet": _brief(c.subject) if c.subject is not None else {"produit_id": str(c.subject_product_id)},
            "candidats": [{"ref": k.ref, "produit_id": str(k.product_id) if k.product_id else None, **(_brief(k.product) or {})}
                          for k in c.candidates],
            "choix_possibles": possible_choices(c),
            "choix": prev.get("choix"),
            "par": prev.get("par"),
            "le": prev.get("le"),
        })
    path.parent.mkdir(parents=True, exist_ok=True)
    header = (f"# Décisions pour la nomenclature {draft.version.label}.\n"
              "# Pour chaque cas : remplir `choix` (une valeur de choix_possibles), `par` (votre nom) et `le` (AAAA-MM-JJ).\n")
    path.write_text(header + yaml.safe_dump({"version": draft.version.label, "cas": cas}, allow_unicode=True,
                                            sort_keys=False, width=120), encoding="utf-8")


def _as_date(v) -> date | None:
    if isinstance(v, date):
        return v
    if isinstance(v, str):
        try:
            return date.fromisoformat(v.strip())
        except ValueError:
            return None
    return None


def load_decisions(path: Path, draft: Draft) -> list[Decision]:
    path = Path(path)
    if not path.exists():
        raise DecisionsInvalid([f"Fichier {path} absent : lancer d'abord `synapse-admin review {draft.version.label}`"])
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as e:
        raise DecisionsInvalid([f"YAML illisible : {e}"]) from e
    problems: list[str] = []
    if str(data.get("version")) != draft.version.label:
        problems.append(f"version {data.get('version')} dans le fichier, {draft.version.label} attendue")
    cases = {c.case_id: c for c in draft.cases}
    seen: set[str] = set()
    decisions: list[Decision] = []
    claimed: dict[str, list[str]] = defaultdict(list)
    for entry in data.get("cas") or []:
        cid = entry.get("id") if isinstance(entry, dict) else None
        if cid not in cases:
            problems.append(f"cas inconnu : {cid}")
            continue
        seen.add(cid)
        case, choice = cases[cid], entry.get("choix")
        if choice in (None, ""):
            problems.append(f"{cid} : sans choix")
            continue
        choice = str(choice).strip()
        if choice not in possible_choices(case):
            ref = choice.split(":", 1)[1] if ":" in choice else None
            if ref and choice.split(":", 1)[0] in ("meme_produit", "garder"):
                problems.append(f"{cid} : référence {ref} absente des candidats")
            else:
                problems.append(f"{cid} : choix invalide « {choice} » (possibles : {', '.join(possible_choices(case))})")
            continue
        by = entry.get("par")
        if not by or not str(by).strip():
            problems.append(f"{cid} : champ par (auteur) vide")
            continue
        when = _as_date(entry.get("le"))
        if when is None:
            problems.append(f"{cid} : champ le doit être une date AAAA-MM-JJ")
            continue
        if choice.startswith("meme_produit:"):
            k = next(k for k in case.candidates if k.ref == choice.split(":", 1)[1])
            if k.product_id:
                claimed[str(k.product_id)].append(cid)
        decisions.append(Decision(cid, choice, str(by).strip(), when))
    for cid in cases.keys() - seen:
        problems.append(f"{cid} : cas manquant dans le fichier")
    for pid, cids in claimed.items():
        if len(cids) > 1:
            problems.append(f"produit {pid} rattaché à plusieurs cas : {', '.join(cids)}")
    if problems:
        raise DecisionsInvalid(problems)
    return decisions
