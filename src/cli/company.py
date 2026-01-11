"""Company CLI commands."""

import click

from src.db.models import Company
from src.db.queries import (
    create_company,
    get_company,
    list_companies,
    update_company,
)


SECTORS = ["DeFi", "NFT", "Infrastructure", "Exchange", "Analytics", "Other"]
SIZES = ["startup", "small", "medium", "large"]


@click.group()
def company():
    """Manage companies."""
    pass


@company.command()
def add():
    """Add a new company (interactive)."""
    click.echo("Add a new company\n")

    name = click.prompt("Company name")
    website = click.prompt("Website URL", default="", show_default=False)
    website = website if website else None

    click.echo("\nSectors: " + ", ".join(SECTORS))
    sector = click.prompt("Sector", default="", show_default=False)
    sector = sector if sector in SECTORS else None

    chain_focus = click.prompt("Chain focus (e.g., Ethereum, Solana)", default="", show_default=False)
    chain_focus = chain_focus if chain_focus else None

    click.echo("\nSizes: " + ", ".join(SIZES))
    size = click.prompt("Company size", default="", show_default=False)
    size = size if size in SIZES else None

    notes = click.prompt("Notes", default="", show_default=False)
    notes = notes if notes else None

    company_obj = Company(
        name=name,
        website=website,
        sector=sector,
        chain_focus=chain_focus,
        size=size,
        notes=notes,
    )

    try:
        company_id = create_company(company_obj)
        click.echo(f"\nCreated company '{name}' with ID {company_id}")
    except Exception as e:
        click.echo(f"\nError: {e}", err=True)
        raise click.Abort()


@company.command("list")
def list_cmd():
    """List all companies."""
    companies = list_companies()

    if not companies:
        click.echo("No companies found.")
        return

    click.echo(f"\nCompanies ({len(companies)}):\n")
    click.echo(f"{'ID':<5} {'Name':<25} {'Sector':<15} {'Chain Focus':<20}")
    click.echo("-" * 65)

    for c in companies:
        sector = c.sector or "-"
        chain = c.chain_focus or "-"
        click.echo(f"{c.id:<5} {c.name:<25} {sector:<15} {chain:<20}")


@company.command()
@click.argument("company_id", type=int)
def view(company_id: int):
    """View a company's details."""
    c = get_company(company_id)

    if not c:
        click.echo(f"Company with ID {company_id} not found.", err=True)
        raise click.Abort()

    click.echo(f"\nCompany: {c.name}")
    click.echo("-" * 40)
    click.echo(f"ID:          {c.id}")
    click.echo(f"Website:     {c.website or '-'}")
    click.echo(f"Sector:      {c.sector or '-'}")
    click.echo(f"Chain Focus: {c.chain_focus or '-'}")
    click.echo(f"Size:        {c.size or '-'}")
    click.echo(f"Notes:       {c.notes or '-'}")
    click.echo(f"Created:     {c.created_at}")


@company.command()
@click.argument("company_id", type=int)
def edit(company_id: int):
    """Edit an existing company (interactive)."""
    c = get_company(company_id)

    if not c:
        click.echo(f"Company with ID {company_id} not found.", err=True)
        raise click.Abort()

    click.echo(f"Editing company: {c.name}")
    click.echo("(Press Enter to keep current value)\n")

    name = click.prompt("Company name", default=c.name)
    website = click.prompt("Website URL", default=c.website or "")
    website = website if website else None

    click.echo("\nSectors: " + ", ".join(SECTORS))
    sector = click.prompt("Sector", default=c.sector or "")
    sector = sector if sector in SECTORS else None

    chain_focus = click.prompt("Chain focus", default=c.chain_focus or "")
    chain_focus = chain_focus if chain_focus else None

    click.echo("\nSizes: " + ", ".join(SIZES))
    size = click.prompt("Company size", default=c.size or "")
    size = size if size in SIZES else None

    notes = click.prompt("Notes", default=c.notes or "")
    notes = notes if notes else None

    c.name = name
    c.website = website
    c.sector = sector
    c.chain_focus = chain_focus
    c.size = size
    c.notes = notes

    try:
        update_company(c)
        click.echo(f"\nUpdated company '{name}'")
    except Exception as e:
        click.echo(f"\nError: {e}", err=True)
        raise click.Abort()
