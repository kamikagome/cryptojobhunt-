"""Discovery CLI commands for automated job search."""

import click

from src.db.models import Company, Job, DiscoveredJob
from src.db.queries import (
    create_discovered_job,
    get_discovered_job,
    list_discovered_jobs,
    update_discovered_job_status,
    discovered_job_exists,
    job_url_exists,
    create_company,
    create_job,
    get_company_by_name,
)
from src.discovery.perplexity import search_jobs, get_api_key
from src.discovery.parser import parse_jobs, validate_job


@click.group()
def discover():
    """Automated job discovery using Perplexity API."""
    pass


@discover.command()
@click.option("--query", "-q", default=None, help="Custom search query")
def run(query: str):
    """Search for new jobs using Perplexity API."""

    # Check API key
    if not get_api_key():
        click.echo("Error: PERPLEXITY_API_KEY environment variable not set.", err=True)
        click.echo("\nTo set it, run:")
        click.echo("  export PERPLEXITY_API_KEY=your_api_key_here")
        raise click.Abort()

    click.echo("Searching for crypto/web3 jobs...\n")

    # Run search
    if query:
        click.echo(f"Custom query: {query}\n")
        result = search_jobs(user_prompt=query)
    else:
        result = search_jobs()

    if not result["success"]:
        click.echo(f"Error: {result['error']}", err=True)
        raise click.Abort()

    click.echo("Parsing results...")

    # Parse jobs
    jobs = parse_jobs(result["raw_response"])

    if not jobs:
        click.echo("No jobs found in response.")
        return

    # Store jobs, checking for duplicates
    new_count = 0
    dup_count = 0
    error_count = 0

    for job in jobs:
        # Skip if parse error
        if job.get("parse_error"):
            error_count += 1
            continue

        # Skip if no URL (can't dedupe)
        if not job.get("url"):
            error_count += 1
            continue

        # Check for duplicates
        if discovered_job_exists(job["url"]) or job_url_exists(job["url"]):
            dup_count += 1
            continue

        # Create discovered job
        dj = DiscoveredJob(
            title=job["title"],
            company_name=job["company"],
            url=job["url"],
            requirements_raw=job["requirements"],
            source="perplexity",
            raw_response=result["raw_response"],
            status="pending"
        )

        try:
            create_discovered_job(dj)
            new_count += 1
        except Exception as e:
            click.echo(f"  Error saving job: {e}", err=True)
            error_count += 1

    click.echo(f"\nResults:")
    click.echo(f"  New jobs found:  {new_count}")
    click.echo(f"  Duplicates:      {dup_count}")
    if error_count > 0:
        click.echo(f"  Parse errors:    {error_count}")

    if new_count > 0:
        click.echo(f"\nRun 'python -m src.cli.main discover review' to review new jobs.")


@discover.command()
def review():
    """Review pending discovered jobs."""
    jobs = list_discovered_jobs(status="pending")

    if not jobs:
        click.echo("No pending jobs to review.")
        return

    click.echo(f"\nPending Discovered Jobs ({len(jobs)})\n")
    click.echo(f"{'ID':<5} {'Title':<30} {'Company':<20} {'Discovered':<12}")
    click.echo("-" * 67)

    for job in jobs:
        title = job.title[:28] + ".." if job.title and len(job.title) > 30 else (job.title or "-")
        company = job.company_name[:18] + ".." if job.company_name and len(job.company_name) > 20 else (job.company_name or "-")
        discovered = job.discovered_at[:10] if job.discovered_at else "-"

        click.echo(f"{job.id:<5} {title:<30} {company:<20} {discovered:<12}")

    click.echo(f"\nCommands:")
    click.echo(f"  discover view <id>     - View job details")
    click.echo(f"  discover promote <id>  - Add to main jobs table")
    click.echo(f"  discover dismiss <id>  - Mark as dismissed")


@discover.command()
@click.argument("job_id", type=int)
def view(job_id: int):
    """View a discovered job's details."""
    job = get_discovered_job(job_id)

    if not job:
        click.echo(f"Discovered job with ID {job_id} not found.", err=True)
        raise click.Abort()

    click.echo(f"\nDiscovered Job #{job.id}")
    click.echo("-" * 50)
    click.echo(f"Title:        {job.title or '-'}")
    click.echo(f"Company:      {job.company_name or '-'}")
    click.echo(f"URL:          {job.url or '-'}")
    click.echo(f"Requirements: {job.requirements_raw or '-'}")
    click.echo(f"Source:       {job.source or '-'}")
    click.echo(f"Discovered:   {job.discovered_at or '-'}")
    click.echo(f"Status:       {job.status}")

    if job.status == "pending":
        click.echo(f"\nActions:")
        click.echo(f"  discover promote {job.id}  - Add to main jobs")
        click.echo(f"  discover dismiss {job.id}  - Dismiss")


@discover.command()
@click.argument("job_id", type=int)
def promote(job_id: int):
    """Promote a discovered job to the main jobs table."""
    dj = get_discovered_job(job_id)

    if not dj:
        click.echo(f"Discovered job with ID {job_id} not found.", err=True)
        raise click.Abort()

    if dj.status != "pending":
        click.echo(f"Job is already {dj.status}.", err=True)
        raise click.Abort()

    click.echo(f"\nPromoting: {dj.title}")
    click.echo(f"Company:   {dj.company_name}")
    click.echo(f"URL:       {dj.url}\n")

    # Check if company exists
    company = get_company_by_name(dj.company_name) if dj.company_name else None

    if company:
        click.echo(f"Found existing company: {company.name} (ID: {company.id})")
        company_id = company.id
    else:
        # Create new company
        click.echo(f"Creating new company: {dj.company_name}")

        sector = click.prompt(
            "Sector (DeFi/NFT/Infrastructure/Exchange/Analytics/Other)",
            default="",
            show_default=False
        )
        sector = sector if sector else None

        chain_focus = click.prompt("Chain focus", default="", show_default=False)
        chain_focus = chain_focus if chain_focus else None

        new_company = Company(
            name=dj.company_name or "Unknown",
            sector=sector,
            chain_focus=chain_focus
        )

        try:
            company_id = create_company(new_company)
            click.echo(f"Created company with ID {company_id}")
        except Exception as e:
            click.echo(f"Error creating company: {e}", err=True)
            raise click.Abort()

    # Get additional job details
    click.echo("\nAdd job details:")

    remote_status = click.prompt(
        "Remote status (remote/hybrid/onsite)",
        default="remote",
        show_default=True
    )

    source = click.prompt("Source", default="perplexity", show_default=True)

    notes = click.prompt("Notes", default="", show_default=False)
    notes = notes if notes else None

    # Create job
    new_job = Job(
        company_id=company_id,
        title=dj.title or "Unknown",
        url=dj.url,
        remote_status=remote_status if remote_status in ["remote", "hybrid", "onsite"] else None,
        source=source,
        notes=notes,
        status="open"
    )

    try:
        job_id_new = create_job(new_job)
        click.echo(f"\nCreated job with ID {job_id_new}")

        # Update discovered job status
        update_discovered_job_status(job_id, "promoted", promoted_to_job_id=job_id_new)
        click.echo("Marked discovered job as promoted.")

        click.echo(f"\nTo add skills, run: python -m src.cli.main job tag {job_id_new}")

    except Exception as e:
        click.echo(f"Error creating job: {e}", err=True)
        raise click.Abort()


@discover.command()
@click.argument("job_id", type=int)
def dismiss(job_id: int):
    """Dismiss a discovered job (not interested)."""
    dj = get_discovered_job(job_id)

    if not dj:
        click.echo(f"Discovered job with ID {job_id} not found.", err=True)
        raise click.Abort()

    if dj.status != "pending":
        click.echo(f"Job is already {dj.status}.", err=True)
        raise click.Abort()

    click.echo(f"Dismissing: {dj.title} at {dj.company_name}")

    if click.confirm("Are you sure?", default=True):
        update_discovered_job_status(job_id, "dismissed")
        click.echo("Job dismissed.")
    else:
        click.echo("Cancelled.")


@discover.command("list")
@click.option("--status", type=click.Choice(["pending", "promoted", "dismissed"]), help="Filter by status")
def list_cmd(status: str):
    """List all discovered jobs."""
    jobs = list_discovered_jobs(status=status)

    if not jobs:
        click.echo("No discovered jobs found.")
        return

    status_label = f" ({status})" if status else ""
    click.echo(f"\nDiscovered Jobs{status_label} ({len(jobs)})\n")
    click.echo(f"{'ID':<5} {'Title':<28} {'Company':<18} {'Status':<10} {'Discovered':<12}")
    click.echo("-" * 73)

    for job in jobs:
        title = job.title[:26] + ".." if job.title and len(job.title) > 28 else (job.title or "-")
        company = job.company_name[:16] + ".." if job.company_name and len(job.company_name) > 18 else (job.company_name or "-")
        discovered = job.discovered_at[:10] if job.discovered_at else "-"

        click.echo(f"{job.id:<5} {title:<28} {company:<18} {job.status:<10} {discovered:<12}")
