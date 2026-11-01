"""CLI d'administration : synapse-admin."""
from __future__ import annotations

from pathlib import Path

import typer

from . import repository
from .db import get_engine
from .decisions import render_report, write_decisions_template
from .excel_reader import WorkbookFormatError
from .importer import ImportRefused, run_import

app = typer.Typer(help="Administration de la nomenclature nationale (Synapse).", no_args_is_help=True)


@app.callback()
def main(ctx: typer.Context,
         workdir: Path = typer.Option(Path("nomenclature"), "--workdir", help="Répertoire des rapports, décisions et publications")):
    ctx.obj = {"workdir": workdir}


def _fail(message: str) -> None:
    typer.secho(f"Refusé : {message}", fg=typer.colors.RED, err=False)
    raise typer.Exit(1)


@app.command("import")
def import_cmd(fichier: Path = typer.Argument(..., exists=True, dir_okay=False, help="Fichier Excel du ministère"),
               version: str = typer.Option(..., "--version", help="Version AAAA-MM, ex. 2026-08"),
               remplacer: bool = typer.Option(False, "--remplacer", help="Refaire un brouillon existant")):
    """Importer un fichier mensuel en brouillon."""
    try:
        with get_engine().connect() as conn:
            s = run_import(conn, fichier, version, replace=remplacer)
    except (ImportRefused, WorkbookFormatError) as e:
        _fail(str(e))
    typer.echo(f"Brouillon {s.label} : {s.rows_read} lignes lues")
    for cat, n in sorted(s.counts_by_category.items()):
        typer.echo(f"  {cat:<10} {n}")
    typer.echo(f"  à trancher {s.cases}")
    typer.echo(f"  anomalies  {s.anomalies}")
    typer.echo(f"Suite : synapse-admin review {s.label}")


@app.command()
def status():
    """Lister les versions."""
    with get_engine().connect() as conn:
        versions = repository.list_versions(conn)
    if not versions:
        typer.echo("Aucune version importée.")
    for v in versions:
        typer.echo(f"{v.label}  {v.state:<10} {v.reference_date}  {v.source_filename}")


@app.command()
def review(ctx: typer.Context, version: str = typer.Argument(..., help="Version AAAA-MM")):
    """Écrire le rapport et le fichier de décisions d'un brouillon."""
    workdir: Path = ctx.obj["workdir"]
    with get_engine().connect() as conn:
        try:
            draft = repository.load_draft(conn, version)
        except LookupError as e:
            _fail(str(e))
    report = workdir / "reports" / f"{version}.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(render_report(draft), encoding="utf-8")
    decisions = workdir / "decisions" / f"{version}.yaml"
    write_decisions_template(draft, decisions)
    typer.echo(f"Rapport : {report}")
    typer.echo(f"Décisions : {decisions} ({len(draft.cases)} cas à trancher)")
    typer.echo(f"Suite : remplir les choix puis synapse-admin publish {version}")
