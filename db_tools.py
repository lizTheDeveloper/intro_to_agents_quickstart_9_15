from agents import function_tool
import asyncio, os
import psycopg2
from psycopg2.extras import RealDictCursor, Json

# Single global connection and cursor using RealDictCursor for dict-like rows
conn = psycopg2.connect(os.environ['DATABASE_URL'])
conn.autocommit = True


def _fetchone_dict(cur):
    row = cur.fetchone()
    if row is None:
        return None
    return dict(row)


def _fetchall_list(cur):
    rows = cur.fetchall()
    return [dict(r) for r in rows]


# ---------------------- NOTES ----------------------
@function_tool
async def create_note(summary: str, content: str | None = None, tags: list | None = None, topics: list | None = None) -> dict:
    """Create a note.
    Args:
        summary: Short summary (required)
        content: Full text (optional)
        tags: List of tags (optional)
        topics: List of topics (optional)
    Returns: Created note row as dict.
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            INSERT INTO notes (summary, content, tags, topics)
            VALUES (%s, %s, %s, %s)
            RETURNING *
            """,
            (
                summary,
                content,
                Json(tags or []),
                Json(topics or []),
            ),
        )
        return _fetchone_dict(cur)


@function_tool
async def get_note(note_id: int) -> dict | None:
    """Fetch a single note by id."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT * FROM notes WHERE id = %s", (note_id,))
        return _fetchone_dict(cur)


# ---------------------- DAILY LOGS ----------------------
@function_tool
async def create_daily_log(
    log_date: str,
    mood: int | None = None,
    energy: int | None = None,
    summary: str | None = None,
    highlights: str | None = None,
    lowlights: str | None = None,
    lessons: str | None = None,
    next_day_focus: str | None = None,
) -> dict:
    """Create a daily_log for a given YYYY-MM-DD date. Enforces unique log_date.
    Returns the created row.
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            INSERT INTO daily_logs (
                log_date, mood, energy, summary, highlights, lowlights, lessons, next_day_focus
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (log_date) DO UPDATE SET
                mood = EXCLUDED.mood,
                energy = EXCLUDED.energy,
                summary = EXCLUDED.summary,
                highlights = EXCLUDED.highlights,
                lowlights = EXCLUDED.lowlights,
                lessons = EXCLUDED.lessons,
                next_day_focus = EXCLUDED.next_day_focus,
                updated_at = now()
            RETURNING *
            """,
            (log_date, mood, energy, summary, highlights, lowlights, lessons, next_day_focus),
        )
        return _fetchone_dict(cur)


@function_tool
async def link_note_to_daily_log(daily_log_id: int, note_id: int) -> dict:
    """Link a note to a daily_log (idempotent)."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            INSERT INTO daily_log_notes (daily_log_id, note_id)
            VALUES (%s, %s)
            ON CONFLICT (daily_log_id, note_id) DO NOTHING
            RETURNING daily_log_id, note_id
            """,
            (daily_log_id, note_id),
        )
        row = _fetchone_dict(cur)
        if row is None:
            # already existed; return the link
            return {"daily_log_id": daily_log_id, "note_id": note_id}
        return row


# ---------------------- PROJECTS ----------------------
@function_tool
async def create_project(
    name: str,
    description: str | None = None,
    status: str = "active",
    priority: int = 3,
    start_date: str | None = None,
    due_date: str | None = None,
    tags: list | None = None,
) -> dict:
    """Create a project. status: e.g., active, paused, done. priority: 1-5."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            INSERT INTO projects (name, description, status, priority, start_date, due_date, tags)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING *
            """,
            (name, description, status, priority, start_date, due_date, Json(tags or [])),
        )
        return _fetchone_dict(cur)


# ---------------------- TASKS ----------------------
@function_tool
async def create_task(
    title: str,
    description: str | None = None,
    status: str = "todo",
    priority: int = 3,
    starts_at: str | None = None,
    due_at: str | None = None,
    project_id: int | None = None,
    note_id: int | None = None,
    tags: list | None = None,
) -> dict:
    """Create a task. status: todo|doing|blocked|done. priority: 1-5."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            INSERT INTO tasks (title, description, status, priority, starts_at, due_at, project_id, note_id, tags)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *
            """,
            (
                title,
                description,
                status,
                priority,
                starts_at,
                due_at,
                project_id,
                note_id,
                Json(tags or []),
            ),
        )
        return _fetchone_dict(cur)


@function_tool
async def assign_task(task_id: int, person_id: int, role: str = "owner") -> dict:
    """Assign a task to a person with a role (idempotent)."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            INSERT INTO task_assignments (task_id, person_id, role)
            VALUES (%s, %s, %s)
            ON CONFLICT (task_id, person_id) DO UPDATE SET role = EXCLUDED.role
            RETURNING *
            """,
            (task_id, person_id, role),
        )
        return _fetchone_dict(cur)


# ---------------------- PEOPLE ----------------------
@function_tool
async def create_person(
    full_name: str,
    org_id: int | None = None,
    title: str | None = None,
    emails: list | None = None,
    phones: list | None = None,
    handles: dict | None = None,
    tags: list | None = None,
    notes: str | None = None,
) -> dict:
    """Create a person. emails/phones are lists, handles is a dict (e.g., {"slack": "@me"})."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            INSERT INTO people (full_name, org_id, title, emails, phones, handles, tags, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *
            """,
            (
                full_name,
                org_id,
                title,
                Json(emails or []),
                Json(phones or []),
                Json(handles or {}),
                Json(tags or []),
                notes,
            ),
        )
        return _fetchone_dict(cur)


# ---------------------- ORGANIZATIONS ----------------------
@function_tool
async def create_organization(name: str, domain: str | None = None, notes: str | None = None, tags: list | None = None) -> dict:
    """Create an organization."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            INSERT INTO organizations (name, domain, notes, tags)
            VALUES (%s, %s, %s, %s)
            RETURNING *
            """,
            (name, domain, notes, Json(tags or [])),
        )
        return _fetchone_dict(cur)


# ---------------------- EVENTS ----------------------
@function_tool
async def create_event(
    title: str,
    start_time: str,
    end_time: str | None = None,
    location: str | None = None,
    agenda: str | None = None,
    notes: str | None = None,
    project_id: int | None = None,
    note_id: int | None = None,
    tags: list | None = None,
) -> dict:
    """Create an event (start_time/end_time are ISO timestamps)."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            INSERT INTO events (title, start_time, end_time, location, agenda, notes, project_id, note_id, tags)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *
            """,
            (
                title,
                start_time,
                end_time,
                location,
                agenda,
                notes,
                project_id,
                note_id,
                Json(tags or []),
            ),
        )
        return _fetchone_dict(cur)


@function_tool
async def add_event_participant(event_id: int, person_id: int, role: str | None = None, attended: bool | None = None) -> dict:
    """Add or update an event participant (idempotent)."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            INSERT INTO event_participants (event_id, person_id, role, attended)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (event_id, person_id) DO UPDATE SET
                role = COALESCE(EXCLUDED.role, event_participants.role),
                attended = COALESCE(EXCLUDED.attended, event_participants.attended)
            RETURNING *
            """,
            (event_id, person_id, role, attended),
        )
        return _fetchone_dict(cur)


# ---------------------- DECISIONS ----------------------
@function_tool
async def create_decision(
    statement: str,
    project_id: int | None = None,
    context: str | None = None,
    decided_at: str | None = None,
    status: str = "decided",
    note_id: int | None = None,
    decided_by_person_id: int | None = None,
    tags: list | None = None,
) -> dict:
    """Create a decision. status: decided|revisited|retracted (depending on your checks)."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            INSERT INTO decisions (project_id, statement, context, decided_at, status, note_id, decided_by_person_id, tags)
            VALUES (%s, %s, %s, COALESCE(%s, now()), %s, %s, %s, %s)
            RETURNING *
            """,
            (
                project_id,
                statement,
                context,
                decided_at,
                status,
                note_id,
                decided_by_person_id,
                Json(tags or []),
            ),
        )
        return _fetchone_dict(cur)


# ---------------------- LINKS/ASSOCIATIONS ----------------------
@function_tool
async def link_note_to_task(task_id: int, note_id: int) -> dict | None:
    """Attach a note to a task by updating task.note_id. Returns updated task."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("UPDATE tasks SET note_id = %s, updated_at = now() WHERE id = %s RETURNING *", (note_id, task_id))
        return _fetchone_dict(cur)


@function_tool
async def link_note_to_event(event_id: int, note_id: int) -> dict | None:
    """Attach a note to an event by updating event.note_id. Returns updated event."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("UPDATE events SET note_id = %s, updated_at = now() WHERE id = %s RETURNING *", (note_id, event_id))
        return _fetchone_dict(cur)


# ---------------------- SIMPLE GETTERS (examples) ----------------------
@function_tool
async def get_task(task_id: int) -> dict | None:
    """Fetch a task by id."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
        return _fetchone_dict(cur)


@function_tool
async def get_project(project_id: int) -> dict | None:
    """Fetch a project by id."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT * FROM projects WHERE id = %s", (project_id,))
        return _fetchone_dict(cur)


@function_tool
async def get_person(person_id: int) -> dict | None:
    """Fetch a person by id."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT * FROM people WHERE id = %s", (person_id,))
        return _fetchone_dict(cur)
