"""Job CLI commands."""

import click

from src.db.models import Job
from src.db.queries import (
    create_job,
    get_job,
    list_jobs,
    list_companies,
    get_company,
    list_skills,
    get_job_skills,
    add_skill_to_job,
    remove_skill_from_job,
)


REMOTE_OPTIONS = ["remote", "hybrid", "onsite"]
STATUS_OPTIONS = ["open", "closed", "expired"]


@click.group()
def job():
    """Manage job postings."""
    pass


@job.command()
def add():
    """Add a new job posting (interactive)."""
    click.echo("Add a new job posting\n")

    # Select company
    companies = list_companies()
    if not companies:
        click.echo("No companies found. Please add a company first.")
        click.echo("Run: python -m src.cli.main company add")
        raise click.Abort()

    click.echo("Available companies:")
    for c in companies:
        click.echo(f"  {c.id}: {c.name}")

    company_id = click.prompt("\nCompany ID", type=int)
    company = get_company(company_id)
    if not company:
        click.echo(f"Company with ID {company_id} not found.", err=True)
        raise click.Abort()

    click.echo(f"\nAdding job for: {company.name}\n")

    title = click.prompt("Job title")

    url = click.prompt("Job URL", default="", show_default=False)
    url = url if url else None

    click.echo("\nSalary (USD annual, e.g., 120000 for $120k)")
    salary_min_str = click.prompt("Salary min", default="", show_default=False)
    salary_min = int(salary_min_str) if salary_min_str else None

    salary_max_str = click.prompt("Salary max", default="", show_default=False)
    salary_max = int(salary_max_str) if salary_max_str else None

    click.echo(f"\nRemote options: {', '.join(REMOTE_OPTIONS)}")
    remote_status = click.prompt("Remote status", default="", show_default=False)
    remote_status = remote_status if remote_status in REMOTE_OPTIONS else None

    date_posted = click.prompt("Date posted (YYYY-MM-DD)", default="", show_default=False)
    date_posted = date_posted if date_posted else None

    closing_date = click.prompt("Closing date (YYYY-MM-DD)", default="", show_default=False)
    closing_date = closing_date if closing_date else None

    source = click.prompt("Source (where you found it)", default="", show_default=False)
    source = source if source else None

    notes = click.prompt("Notes", default="", show_default=False)
    notes = notes if notes else None

    job_obj = Job(
        company_id=company_id,
        title=title,
        url=url,
        salary_min=salary_min,
        salary_max=salary_max,
        remote_status=remote_status,
        date_posted=date_posted,
        closing_date=closing_date,
        status="open",
        source=source,
        notes=notes,
    )

    try:
        job_id = create_job(job_obj)
        click.echo(f"\nCreated job '{title}' at {company.name} with ID {job_id}")
        click.echo(f"\nTo add skills, run: python -m src.cli.main job tag {job_id}")
    except Exception as e:
        click.echo(f"\nError: {e}", err=True)
        raise click.Abort()


@job.command("list")
@click.option("--sql", is_flag=True, help="Show only jobs requiring SQL skills")
@click.option("--status", type=click.Choice(STATUS_OPTIONS), help="Filter by status")
def list_cmd(sql: bool, status: str):
    """List job postings."""
    jobs = list_jobs(status=status)

    if sql:
        # Filter to jobs with SQL skills
        sql_jobs = []
        for j in jobs:
            skills = get_job_skills(j.id)
            has_sql = any(s.category == "SQL" for s, _ in skills)
            if has_sql:
                sql_jobs.append(j)
        jobs = sql_jobs

    if not jobs:
        click.echo("No jobs found.")
        return

    click.echo(f"\nJobs ({len(jobs)}):\n")
    click.echo(f"{'ID':<5} {'Title':<30} {'Company':<20} {'Remote':<10} {'Status':<10}")
    click.echo("-" * 75)

    for j in jobs:
        company = get_company(j.company_id)
        company_name = company.name if company else "Unknown"
        remote = j.remote_status or "-"
        click.echo(f"{j.id:<5} {j.title:<30} {company_name:<20} {remote:<10} {j.status:<10}")


@job.command()
@click.argument("job_id", type=int)
def view(job_id: int):
    """View a job's details."""
    j = get_job(job_id)

    if not j:
        click.echo(f"Job with ID {job_id} not found.", err=True)
        raise click.Abort()

    company = get_company(j.company_id)
    company_name = company.name if company else "Unknown"

    click.echo(f"\nJob: {j.title}")
    click.echo("-" * 50)
    click.echo(f"ID:           {j.id}")
    click.echo(f"Company:      {company_name}")
    click.echo(f"URL:          {j.url or '-'}")

    if j.salary_min or j.salary_max:
        salary = ""
        if j.salary_min:
            salary += f"${j.salary_min:,}"
        if j.salary_min and j.salary_max:
            salary += " - "
        if j.salary_max:
            salary += f"${j.salary_max:,}"
        click.echo(f"Salary:       {salary} USD/year")
    else:
        click.echo(f"Salary:       -")

    click.echo(f"Remote:       {j.remote_status or '-'}")
    click.echo(f"Date Posted:  {j.date_posted or '-'}")
    click.echo(f"Date Found:   {j.date_found or '-'}")
    click.echo(f"Closing Date: {j.closing_date or '-'}")
    click.echo(f"Status:       {j.status}")
    click.echo(f"Source:       {j.source or '-'}")
    click.echo(f"Notes:        {j.notes or '-'}")

    # Show skills
    skills = get_job_skills(job_id)
    if skills:
        click.echo(f"\nSkills:")
        for skill, importance in skills:
            click.echo(f"  - {skill.name} ({importance})")
    else:
        click.echo(f"\nSkills:       None tagged")


@job.command()
@click.argument("job_id", type=int)
def tag(job_id: int):
    """Manage skills for a job (interactive)."""
    j = get_job(job_id)

    if not j:
        click.echo(f"Job with ID {job_id} not found.", err=True)
        raise click.Abort()

    click.echo(f"\nManaging skills for: {j.title}")
    click.echo("-" * 50)

    # Show current skills
    current_skills = get_job_skills(job_id)
    if current_skills:
        click.echo("\nCurrent skills:")
        for skill, importance in current_skills:
            click.echo(f"  {skill.id}: {skill.name} ({importance})")
    else:
        click.echo("\nNo skills tagged yet.")

    # Show available skills
    all_skills = list_skills()
    current_skill_ids = {s.id for s, _ in current_skills}
    available_skills = [s for s in all_skills if s.id not in current_skill_ids]

    if available_skills:
        click.echo("\nAvailable skills to add:")
        for s in available_skills:
            click.echo(f"  {s.id}: {s.name} ({s.category})")

    # Menu
    click.echo("\nOptions:")
    click.echo("  1. Add a skill")
    click.echo("  2. Remove a skill")
    click.echo("  3. Done")

    choice = click.prompt("\nChoice", type=int, default=3)

    if choice == 1:
        if not available_skills:
            click.echo("No more skills available to add.")
            return

        skill_id = click.prompt("Skill ID to add", type=int)
        skill = next((s for s in all_skills if s.id == skill_id), None)

        if not skill:
            click.echo(f"Skill with ID {skill_id} not found.", err=True)
            return

        if skill_id in current_skill_ids:
            click.echo(f"Skill '{skill.name}' is already tagged.", err=True)
            return

        importance = click.prompt(
            "Importance (required/nice-to-have)",
            type=click.Choice(["required", "nice-to-have"]),
            default="required"
        )

        add_skill_to_job(job_id, skill_id, importance)
        click.echo(f"\nAdded '{skill.name}' as {importance}")

    elif choice == 2:
        if not current_skills:
            click.echo("No skills to remove.")
            return

        skill_id = click.prompt("Skill ID to remove", type=int)
        skill = next((s for s, _ in current_skills if s.id == skill_id), None)

        if not skill:
            click.echo(f"Skill with ID {skill_id} is not tagged on this job.", err=True)
            return

        remove_skill_from_job(job_id, skill_id)
        click.echo(f"\nRemoved '{skill.name}'")

    else:
        click.echo("Done.")
