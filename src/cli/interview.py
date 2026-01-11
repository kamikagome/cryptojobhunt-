"""Interview CLI commands."""

import click

from src.db.models import Interview
from src.db.queries import (
    create_interview,
    get_interview,
    list_interviews,
    update_interview,
    list_applications,
    get_application,
    get_job,
    get_company,
)


TYPE_OPTIONS = ["recruiter", "technical", "sql-challenge", "culture", "final"]
OUTCOME_OPTIONS = ["pending", "passed", "failed", "cancelled"]


@click.group()
def interview():
    """Manage interviews."""
    pass


@interview.command()
def add():
    """Add a new interview (interactive)."""
    click.echo("Add a new interview\n")

    # Show applications that are in interview stage or earlier
    apps = list_applications()
    active_apps = [a for a in apps if a.status not in ["rejected", "offer", "ghosted", "withdrawn"]]

    if not active_apps:
        click.echo("No active applications found.")
        click.echo("Run: python -m src.cli.main application add")
        raise click.Abort()

    click.echo("Active applications:")
    for app in active_apps:
        job = get_job(app.job_id)
        if job:
            company = get_company(job.company_id)
            company_name = company.name if company else "Unknown"
            click.echo(f"  {app.id}: {job.title} at {company_name} ({app.status})")
        else:
            click.echo(f"  {app.id}: Unknown job ({app.status})")

    app_id = click.prompt("\nApplication ID", type=int)
    app = get_application(app_id)
    if not app:
        click.echo(f"Application with ID {app_id} not found.", err=True)
        raise click.Abort()

    job = get_job(app.job_id)
    job_title = job.title if job else "Unknown"
    click.echo(f"\nAdding interview for: {job_title}\n")

    # Interview type
    click.echo("Interview types:")
    for i, t in enumerate(TYPE_OPTIONS, 1):
        click.echo(f"  {i}. {t}")

    type_choice = click.prompt("Type number", type=int, default=1)
    if 1 <= type_choice <= len(TYPE_OPTIONS):
        interview_type = TYPE_OPTIONS[type_choice - 1]
    else:
        interview_type = TYPE_OPTIONS[0]

    # Scheduled date/time
    scheduled_at = click.prompt(
        "Scheduled at (YYYY-MM-DD HH:MM, or Enter if not scheduled)",
        default="",
        show_default=False
    )
    scheduled_at = scheduled_at if scheduled_at else None

    # Notes
    notes = click.prompt("Notes (preparation, interviewer name, etc.)", default="", show_default=False)
    notes = notes if notes else None

    intv = Interview(
        application_id=app_id,
        scheduled_at=scheduled_at,
        type=interview_type,
        notes=notes,
        outcome="pending",
    )

    try:
        intv_id = create_interview(intv)
        click.echo(f"\nCreated interview with ID {intv_id}")
        click.echo(f"Type: {interview_type}")
        if scheduled_at:
            click.echo(f"Scheduled: {scheduled_at}")
    except Exception as e:
        click.echo(f"\nError: {e}", err=True)
        raise click.Abort()


@interview.command("list")
@click.option("--app", "app_id", type=int, help="Filter by application ID")
def list_cmd(app_id: int):
    """List interviews."""
    interviews = list_interviews(application_id=app_id)

    if not interviews:
        click.echo("No interviews found.")
        return

    click.echo(f"\nInterviews ({len(interviews)}):\n")
    click.echo(f"{'ID':<5} {'Job':<25} {'Type':<15} {'Scheduled':<18} {'Outcome':<10}")
    click.echo("-" * 73)

    for intv in interviews:
        app = get_application(intv.application_id)
        if app:
            job = get_job(app.job_id)
            job_title = job.title[:23] + ".." if job and len(job.title) > 25 else (job.title if job else "Unknown")
        else:
            job_title = "Unknown"

        scheduled = intv.scheduled_at[:16] if intv.scheduled_at else "-"
        outcome = intv.outcome or "pending"
        click.echo(f"{intv.id:<5} {job_title:<25} {intv.type:<15} {scheduled:<18} {outcome:<10}")


@interview.command()
@click.argument("interview_id", type=int)
def view(interview_id: int):
    """View an interview's details."""
    intv = get_interview(interview_id)

    if not intv:
        click.echo(f"Interview with ID {interview_id} not found.", err=True)
        raise click.Abort()

    app = get_application(intv.application_id)
    if app:
        job = get_job(app.job_id)
        if job:
            job_title = job.title
            company = get_company(job.company_id)
            company_name = company.name if company else "Unknown"
        else:
            job_title = "Unknown"
            company_name = "Unknown"
    else:
        job_title = "Unknown"
        company_name = "Unknown"

    click.echo(f"\nInterview #{intv.id}")
    click.echo("-" * 50)
    click.echo(f"Job:          {job_title}")
    click.echo(f"Company:      {company_name}")
    click.echo(f"Type:         {intv.type or '-'}")
    click.echo(f"Scheduled:    {intv.scheduled_at or 'Not scheduled'}")
    click.echo(f"Outcome:      {intv.outcome or 'pending'}")
    click.echo(f"Notes:        {intv.notes or '-'}")


@interview.command()
@click.argument("interview_id", type=int)
def outcome(interview_id: int):
    """Record an interview outcome (interactive)."""
    intv = get_interview(interview_id)

    if not intv:
        click.echo(f"Interview with ID {interview_id} not found.", err=True)
        raise click.Abort()

    app = get_application(intv.application_id)
    job = get_job(app.job_id) if app else None
    job_title = job.title if job else "Unknown"

    click.echo(f"\nRecording outcome for: {job_title} ({intv.type})")
    click.echo(f"Current outcome: {intv.outcome or 'pending'}\n")

    click.echo("Outcome options:")
    for i, o in enumerate(OUTCOME_OPTIONS, 1):
        marker = " (current)" if o == intv.outcome else ""
        click.echo(f"  {i}. {o}{marker}")

    choice = click.prompt("\nOutcome number", type=int, default=1)

    if 1 <= choice <= len(OUTCOME_OPTIONS):
        new_outcome = OUTCOME_OPTIONS[choice - 1]
        intv.outcome = new_outcome

        # Add notes about the outcome
        add_note = click.confirm("Add a note about this outcome?", default=False)
        if add_note:
            note = click.prompt("Note")
            if intv.notes:
                intv.notes = f"{intv.notes}\n[{new_outcome}] {note}"
            else:
                intv.notes = f"[{new_outcome}] {note}"

        update_interview(intv)
        click.echo(f"\nUpdated outcome to: {new_outcome}")
    else:
        click.echo("Invalid choice.", err=True)
