"""Main CLI entry point."""

import click

from .company import company
from .job import job
from .application import application
from .interview import interview
from .reports import report
from .discover import discover


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Crypto Jobs Database - Track crypto/web3 job postings and applications."""
    pass


# Register command groups
cli.add_command(company)
cli.add_command(job)
cli.add_command(application)
cli.add_command(interview)
cli.add_command(report)
cli.add_command(discover)


if __name__ == "__main__":
    cli()
