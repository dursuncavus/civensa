"""Read-only PP publication succession and reasoned reopen trace."""
from bisect import bisect_left

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from .models import Department, Publication, SubmissionEvent


def publication_history(db, period_id, user, department_names):
    publications = db.scalars(select(Publication).where(Publication.period_id == period_id)
        .options(joinedload(Publication.creator)).order_by(Publication.version.desc())).all()
    history = {publication.id: [] for publication in publications}
    result = dict(publications=publications, publication_reopens=history,
                  superseded_by={}, stale_departments=[])
    if not publications:
        return result
    query = (select(SubmissionEvent, Department.name).join(Department,
        Department.id == SubmissionEvent.department_id)
        .where(SubmissionEvent.period_id == period_id, SubmissionEvent.event_type == 'reopen')
        .options(joinedload(SubmissionEvent.actor))
        .order_by(SubmissionEvent.created_at, SubmissionEvent.id))
    # The builder is strategy-only; keep reasons scoped if reused elsewhere.
    if user.role != 'strategy':
        query = query.where(SubmissionEvent.department_id == user.department_id)
    chronological = list(reversed(publications))
    times = [publication.created_at for publication in chronological]
    for previous, successor in zip(chronological, chronological[1:]):
        result['superseded_by'][previous.id] = successor.version
    stale = {}
    for event, fallback_name in db.execute(query):
        name = department_names.get(event.department_id, fallback_name)
        if event.created_at > publications[0].created_at:
            stale[event.department_id] = name
            continue
        # A transition owns (previous.created_at, publication.created_at].
        index = bisect_left(times, event.created_at)
        if 0 < index < len(chronological):
            history[chronological[index].id].append(dict(event=event, department_name=name))
    result['stale_departments'] = list(stale.values())
    return result
