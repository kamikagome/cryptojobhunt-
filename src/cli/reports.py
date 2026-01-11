"""Report CLI commands."""

import click

from src.db.connection import get_db


@click.group()
def report():
    """Generate reports and analytics."""
    pass


@report.command()
def pipeline():
    """Show application pipeline by status."""
    conn = get_db()

    # Get status counts
    rows = conn.execute(
        """
        SELECT status, COUNT(*) as count
        FROM applications
        GROUP BY status
        ORDER BY
            CASE status
                WHEN 'applied' THEN 1
                WHEN 'screening' THEN 2
                WHEN 'interview' THEN 3
                WHEN 'offer' THEN 4
                WHEN 'rejected' THEN 5
                WHEN 'ghosted' THEN 6
                WHEN 'withdrawn' THEN 7
            END
        """
    ).fetchall()

    total = conn.execute("SELECT COUNT(*) FROM applications").fetchone()[0]
    conn.close()

    if total == 0:
        click.echo("No applications yet.")
        return

    click.echo(f"\nApplication Pipeline ({total} total)\n")
    click.echo(f"{'Status':<15} {'Count':<8} {'Percentage':<12} Bar")
    click.echo("-" * 55)

    for row in rows:
        status = row["status"]
        count = row["count"]
        pct = (count / total) * 100
        bar_len = int(pct / 5)  # Scale to max 20 chars
        bar = "#" * bar_len

        click.echo(f"{status:<15} {count:<8} {pct:>5.1f}%       {bar}")

    # Summary stats
    click.echo("\n" + "-" * 55)

    active_statuses = ["applied", "screening", "interview"]
    active = sum(r["count"] for r in rows if r["status"] in active_statuses)
    offers = sum(r["count"] for r in rows if r["status"] == "offer")
    rejected = sum(r["count"] for r in rows if r["status"] == "rejected")

    click.echo(f"Active: {active}  |  Offers: {offers}  |  Rejected: {rejected}")


@report.command()
def skills():
    """Show most in-demand skills across all jobs."""
    conn = get_db()

    rows = conn.execute(
        """
        SELECT s.name, s.category, COUNT(*) as demand,
               SUM(CASE WHEN js.importance = 'required' THEN 1 ELSE 0 END) as required_count,
               SUM(CASE WHEN js.importance = 'nice-to-have' THEN 1 ELSE 0 END) as nice_count
        FROM skills s
        JOIN job_skills js ON s.id = js.skill_id
        GROUP BY s.id, s.name, s.category
        ORDER BY demand DESC
        """
    ).fetchall()

    total_jobs = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
    conn.close()

    if not rows:
        click.echo("No skills tagged on any jobs yet.")
        return

    click.echo(f"\nSkill Demand ({total_jobs} jobs tracked)\n")
    click.echo(f"{'Skill':<20} {'Category':<12} {'Total':<8} {'Required':<10} {'Nice-to-have':<12}")
    click.echo("-" * 62)

    for row in rows:
        click.echo(
            f"{row['name']:<20} {row['category'] or '-':<12} "
            f"{row['demand']:<8} {row['required_count']:<10} {row['nice_count']:<12}"
        )


@report.command()
def unapplied():
    """Show open jobs you haven't applied to yet."""
    conn = get_db()

    rows = conn.execute(
        """
        SELECT j.id, j.title, c.name as company, j.date_found, j.remote_status
        FROM jobs j
        JOIN companies c ON j.company_id = c.id
        LEFT JOIN applications a ON j.id = a.job_id
        WHERE a.id IS NULL AND j.status = 'open'
        ORDER BY j.date_found DESC
        """
    ).fetchall()

    conn.close()

    if not rows:
        click.echo("No unapplied open jobs. You're all caught up!")
        return

    click.echo(f"\nUnapplied Jobs ({len(rows)})\n")
    click.echo(f"{'ID':<5} {'Title':<30} {'Company':<20} {'Found':<12} {'Remote':<10}")
    click.echo("-" * 77)

    for row in rows:
        title = row["title"][:28] + ".." if len(row["title"]) > 30 else row["title"]
        company = row["company"][:18] + ".." if len(row["company"]) > 20 else row["company"]
        found = row["date_found"] or "-"
        remote = row["remote_status"] or "-"

        click.echo(f"{row['id']:<5} {title:<30} {company:<20} {found:<12} {remote:<10}")


@report.command()
def sql_matches():
    """Show jobs requiring SQL skills (your best matches)."""
    conn = get_db()

    rows = conn.execute(
        """
        SELECT DISTINCT j.id, j.title, c.name as company, j.url, j.remote_status,
               GROUP_CONCAT(s.name, ', ') as sql_skills
        FROM jobs j
        JOIN companies c ON j.company_id = c.id
        JOIN job_skills js ON j.id = js.job_id
        JOIN skills s ON js.skill_id = s.id
        WHERE s.category = 'SQL' AND js.importance = 'required'
        GROUP BY j.id
        ORDER BY j.date_found DESC
        """
    ).fetchall()

    conn.close()

    if not rows:
        click.echo("No jobs with required SQL skills found.")
        return

    click.echo(f"\nSQL-Required Jobs ({len(rows)})\n")
    click.echo(f"{'ID':<5} {'Title':<25} {'Company':<18} {'SQL Skills':<25}")
    click.echo("-" * 73)

    for row in rows:
        title = row["title"][:23] + ".." if len(row["title"]) > 25 else row["title"]
        company = row["company"][:16] + ".." if len(row["company"]) > 18 else row["company"]
        skills = row["sql_skills"][:23] + ".." if len(row["sql_skills"]) > 25 else row["sql_skills"]

        click.echo(f"{row['id']:<5} {title:<25} {company:<18} {skills:<25}")


@report.command()
def summary():
    """Show overall job search summary."""
    conn = get_db()

    # Gather stats
    total_companies = conn.execute("SELECT COUNT(*) FROM companies").fetchone()[0]
    total_jobs = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
    open_jobs = conn.execute("SELECT COUNT(*) FROM jobs WHERE status = 'open'").fetchone()[0]
    total_apps = conn.execute("SELECT COUNT(*) FROM applications").fetchone()[0]
    total_interviews = conn.execute("SELECT COUNT(*) FROM interviews").fetchone()[0]

    # Application outcomes
    offers = conn.execute("SELECT COUNT(*) FROM applications WHERE status = 'offer'").fetchone()[0]
    rejected = conn.execute("SELECT COUNT(*) FROM applications WHERE status = 'rejected'").fetchone()[0]
    active = conn.execute(
        "SELECT COUNT(*) FROM applications WHERE status IN ('applied', 'screening', 'interview')"
    ).fetchone()[0]

    # Interviews pending
    pending_interviews = conn.execute(
        "SELECT COUNT(*) FROM interviews WHERE outcome = 'pending'"
    ).fetchone()[0]

    conn.close()

    click.echo("\n" + "=" * 40)
    click.echo("       JOB SEARCH SUMMARY")
    click.echo("=" * 40)

    click.echo(f"\nTracking:")
    click.echo(f"  Companies:     {total_companies}")
    click.echo(f"  Jobs:          {total_jobs} ({open_jobs} open)")

    click.echo(f"\nApplications:    {total_apps}")
    if total_apps > 0:
        click.echo(f"  Active:        {active}")
        click.echo(f"  Offers:        {offers}")
        click.echo(f"  Rejected:      {rejected}")

    click.echo(f"\nInterviews:      {total_interviews}")
    if total_interviews > 0:
        click.echo(f"  Pending:       {pending_interviews}")

    # Offer rate
    if total_apps > 0:
        offer_rate = (offers / total_apps) * 100
        click.echo(f"\nOffer Rate:      {offer_rate:.1f}%")

    click.echo("")
