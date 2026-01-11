"""Application CLI commands."""

import click

from src.db.models import Application
from src.db.queries import (
    create_application,
    get_application,
    list_applications,
    update_application,
    list_jobs,
    get_job,
    get_company,
)


STATUS_OPTIONS = ["applied", "screening", "interview", "rejected", "offer", "ghosted", "withdrawn"]


@click.group()
def application():
    """Manage job applications."""
    pass


@application.command()
def add():
    """Add a new application (interactive)."""
    click.echo("Add a new application\n")

    # Show available jobs
    jobs = list_jobs(status="open")
    if not jobs:
        click.echo("No open jobs found. Please add a job first.")
        click.echo("Run: python -m src.cli.main job add")
        raise click.Abort()

    click.echo("Available jobs (open):")
    for j in jobs:
        company = get_company(j.company_id)
        company_name = company.name if company else "Unknown"
        click.echo(f"  {j.id}: {j.title} at {company_name}")

    job_id = click.prompt("\nJob ID", type=int)
    job = get_job(job_id)
    if not job:
        click.echo(f"Job with ID {job_id} not found.", err=True)
        raise click.Abort()

    company = get_company(job.company_id)
    company_name = company.name if company else "Unknown"
    click.echo(f"\nApplying to: {job.title} at {company_name}\n")

    date_applied = click.prompt("Date applied (YYYY-MM-DD, or Enter for today)", default="", show_default=False)
    date_applied = date_applied if date_applied else None  # Will use DB default

    resume_version = click.prompt("Resume version (e.g., v2-sql-focused)", default="", show_default=False)
    resume_version = resume_version if resume_version else None

    cover_letter = click.confirm("Cover letter sent?", default=False)

    notes = click.prompt("Notes", default="", show_default=False)
    notes = notes if notes else None

    app = Application(
        job_id=job_id,
        date_applied=date_applied,
        resume_version=resume_version,
        cover_letter_sent=cover_letter,
        status="applied",
        notes=notes,
    )

    try:
        app_id = create_application(app)
        click.echo(f"\nCreated application with ID {app_id}")
        click.echo(f"Status: applied")
    except Exception as e:
        click.echo(f"\nError: {e}", err=True)
        raise click.Abort()


@application.command("list")
@click.option("--status", type=click.Choice(STATUS_OPTIONS), help="Filter by status")
def list_cmd(status: str):
    """List applications."""
    apps = list_applications(status=status)

    if not apps:
        click.echo("No applications found.")
        return

    click.echo(f"\nApplications ({len(apps)}):\n")
    click.echo(f"{'ID':<5} {'Job':<25} {'Company':<20} {'Status':<12} {'Date':<12}")
    click.echo("-" * 74)

    for app in apps:
        job = get_job(app.job_id)
        if job:
            job_title = job.title[:23] + ".." if len(job.title) > 25 else job.title
            company = get_company(job.company_id)
            company_name = company.name if company else "Unknown"
            company_name = company_name[:18] + ".." if len(company_name) > 20 else company_name
        else:
            job_title = "Unknown"
            company_name = "Unknown"

        date = app.date_applied or "-"
        click.echo(f"{app.id:<5} {job_title:<25} {company_name:<20} {app.status:<12} {date:<12}")


@application.command()
@click.argument("app_id", type=int)
def view(app_id: int):
    """View an application's details."""
    app = get_application(app_id)

    if not app:
        click.echo(f"Application with ID {app_id} not found.", err=True)
        raise click.Abort()

    job = get_job(app.job_id)
    if job:
        job_title = job.title
        company = get_company(job.company_id)
        company_name = company.name if company else "Unknown"
    else:
        job_title = "Unknown"
        company_name = "Unknown"

    click.echo(f"\nApplication #{app.id}")
    click.echo("-" * 50)
    click.echo(f"Job:            {job_title}")
    click.echo(f"Company:        {company_name}")
    click.echo(f"Date Applied:   {app.date_applied or '-'}")
    click.echo(f"Resume Version: {app.resume_version or '-'}")
    click.echo(f"Cover Letter:   {'Yes' if app.cover_letter_sent else 'No'}")
    click.echo(f"Status:         {app.status}")
    click.echo(f"Notes:          {app.notes or '-'}")


@application.command()
@click.argument("app_id", type=int)
def update(app_id: int):
    """Update an application's status (interactive)."""
    app = get_application(app_id)

    if not app:
        click.echo(f"Application with ID {app_id} not found.", err=True)
        raise click.Abort()

    job = get_job(app.job_id)
    job_title = job.title if job else "Unknown"

    click.echo(f"\nUpdating application for: {job_title}")
    click.echo(f"Current status: {app.status}\n")

    click.echo("Available statuses:")
    for i, s in enumerate(STATUS_OPTIONS, 1):
        marker = " (current)" if s == app.status else ""
        click.echo(f"  {i}. {s}{marker}")

    choice = click.prompt("\nNew status number (or Enter to keep current)", default="", show_default=False)

    if choice:
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(STATUS_OPTIONS):
                new_status = STATUS_OPTIONS[idx]
                app.status = new_status

                # Optionally add notes
                add_note = click.confirm("Add a note?", default=False)
                if add_note:
                    note = click.prompt("Note")
                    if app.notes:
                        app.notes = f"{app.notes}\n[{new_status}] {note}"
                    else:
                        app.notes = f"[{new_status}] {note}"

                update_application(app)
                click.echo(f"\nUpdated status to: {new_status}")
            else:
                click.echo("Invalid choice.", err=True)
        except ValueError:
            click.echo("Invalid input.", err=True)
    else:
        click.echo("Status unchanged.")
