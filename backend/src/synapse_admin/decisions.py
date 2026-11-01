"""Rapport de revue (Markdown) et fichier de décisions (YAML)."""
from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import yaml

from .matching import changed_fields, sole_candidate_ids
from .model import CONSOLIDATION_KINDS, Case, Product
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


def linked_old_ids(cases: list[Case]) -> set:
    """Anciens produits proposés comme candidats d'un cas de rapprochement."""
    return {k.product_id for c in cases if c.kind not in CONSOLIDATION_KINDS for k in c.candidates if k.product_id}


def possible_choices(case: Case, cases_or_linked=None) -> list[str]:
    """Choix permis ; `cases_or_linked` = tous les cas du brouillon (ou l'ensemble déjà calculé des produits liés)."""
    if isinstance(cases_or_linked, list):
        linked, sole = linked_old_ids(cases_or_linked), sole_candidate_ids(cases_or_linked)
    else:
        linked, sole = cases_or_linked or set(), set()
    refs = [c.ref for c in case.candidates]
    if (case.kind not in CONSOLIDATION_KINDS and len(case.candidates) == 1 and case.candidates[0].product_id in sole
            and case.candidates[0].product is not None and case.candidates[0].product.sheet == "en_vigueur"):
        return ["meme_produit:c1", "nouveau_et_disparu:c1"]
    if case.kind == "disparu_sans_retrait":
        return ["disparu", "rattache"] if linked and case.subject_product_id in linked else ["disparu"]
    if case.kind in CONSOLIDATION_KINDS:
        return [f"garder:{r}" for r in refs]
    return [f"meme_produit:{r}" for r in refs] + ["nouveau"]


def case_fingerprint(case: Case) -> str:
    """Empreinte du contenu d'un cas : un choix n'est repris que si le cas est resté identique."""
    payload = {"kind": case.kind, "sujet": _brief(case.subject), "sujet_id": str(case.subject_product_id),
               "candidats": [[k.ref, str(k.product_id), _brief(k.product)] for k in case.candidates]}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]


def draft_stamp(draft: Draft) -> dict:
    return {"sha256": draft.version.source_sha256, "importe_le": draft.version.imported_at.isoformat()}


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

    linked = linked_old_ids(draft.cases)
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
            if c.subject is not None and k.product is not None and c.kind not in CONSOLIDATION_KINDS:
                out += [f"  - {line}" for line in _diff_lines(k.product, c.subject)]
        out += [f"- Choix possibles : {', '.join(possible_choices(c, draft.cases))}", ""]

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
    linked = linked_old_ids(draft.cases)
    cas = []
    for c in draft.cases:
        fp = case_fingerprint(c)
        prev = existing.get(c.case_id, {})
        if prev.get("empreinte") != fp:
            prev = {}  # cas différent (brouillon refait) : l'ancien choix ne vaut plus
        cas.append({
            "id": c.case_id,
            "type": c.kind,
            "sujet": _brief(c.subject) if c.subject is not None else {"produit_id": str(c.subject_product_id)},
            "candidats": [{"ref": k.ref, "produit_id": str(k.product_id) if k.product_id else None, **(_brief(k.product) or {})}
                          for k in c.candidates],
            "choix_possibles": possible_choices(c, draft.cases),
            "empreinte": fp,
            "choix": prev.get("choix"),
            "par": prev.get("par"),
            "le": prev.get("le"),
        })
    path.parent.mkdir(parents=True, exist_ok=True)
    header = (f"# Décisions pour la nomenclature {draft.version.label}.\n"
              "# Pour chaque cas : remplir `choix` (une valeur de choix_possibles), `par` (votre nom) et `le` (AAAA-MM-JJ).\n")
    path.write_text(header + yaml.safe_dump({"version": draft.version.label, "brouillon": draft_stamp(draft), "cas": cas}, allow_unicode=True,
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
    elif data.get("brouillon") != draft_stamp(draft):
        problems.append(f"ce fichier a été établi pour un autre brouillon de {draft.version.label} : "
                        f"relancer `synapse-admin review {draft.version.label}` et revoir les choix")
    cases = {c.case_id: c for c in draft.cases}
    linked = linked_old_ids(draft.cases)
    disappearance: dict[str, tuple[str, str]] = {}  # produit_id -> (cas disparu_sans_retrait, choix)
    seen: set[str] = set()
    decisions: list[Decision] = []
    claimed: dict[str, list[str]] = defaultdict(list)
    for entry in data.get("cas") or []:
        cid = entry.get("id") if isinstance(entry, dict) else None
        if cid not in cases:
            problems.append(f"cas inconnu : {cid}")
            continue
        if cid in seen:
            problems.append(f"{cid} : cas en double dans le fichier")
            continue
        seen.add(cid)
        case, choice = cases[cid], entry.get("choix")
        if entry.get("empreinte") != case_fingerprint(case):
            problems.append(f"{cid} : contenu du cas modifié depuis la revue (empreinte) : relancer review")
            continue
        if choice in (None, ""):
            problems.append(f"{cid} : sans choix")
            continue
        choice = str(choice).strip()
        if choice not in possible_choices(case, draft.cases):
            ref = choice.split(":", 1)[1] if ":" in choice else None
            if ref and choice.split(":", 1)[0] in ("meme_produit", "garder"):
                problems.append(f"{cid} : référence {ref} absente des candidats")
            else:
                problems.append(f"{cid} : choix invalide « {choice} » (possibles : {', '.join(possible_choices(case, draft.cases))})")
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
        if case.kind == "disparu_sans_retrait":
            disappearance[str(case.subject_product_id)] = (cid, choice)
        decisions.append(Decision(cid, choice, str(by).strip(), when))
    for cid in cases.keys() - seen:
        problems.append(f"{cid} : cas manquant dans le fichier")
    for pid, (cid, choice) in disappearance.items():
        if choice == "rattache" and pid not in claimed:
            problems.append(f"{cid} : « rattache » mais aucun cas ne rattache ce produit (choisir disparu)")
        elif choice == "disparu" and pid in claimed:
            problems.append(f"{cid} : « disparu » alors que {', '.join(claimed[pid])} rattache ce produit (choisir rattache)")
    for pid, cids in claimed.items():
        if len(cids) > 1:
            problems.append(f"produit {pid} rattaché à plusieurs cas : {', '.join(cids)}")
    if problems:
        raise DecisionsInvalid(problems)
    return decisions
