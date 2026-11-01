"""CLI d'administration : synapse-admin."""
from __future__ import annotations

from pathlib import Path

import typer

from . import repository
from .db import get_engine
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
