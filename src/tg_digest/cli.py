import typer

app = typer.Typer(help="Local read-only Telegram digest pipeline.")


@app.callback()
def main() -> None:
    """Local read-only Telegram digest pipeline."""


@app.command()
def version() -> None:
    """Print package version."""
    from tg_digest import __version__

    typer.echo(__version__)
