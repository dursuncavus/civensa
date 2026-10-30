"""Shared PP activity mapping completeness for queues and progress views."""
from sqlalchemy import exists, select

from .models import Activity, ActivityCatalogueLink


def activity_mapping_states(db, period_id):
    linked = exists().where(ActivityCatalogueLink.activity_id == Activity.id)
    rows = db.execute(select(
        Activity.id, Activity.subprogram_id.is_not(None), Activity.card_id.is_not(None), linked,
    ).where(Activity.period_id == period_id)).all()
    return {
        activity_id: dict(subprogram=subprogram, card=card, catalogue=catalogue,
                          ready=subprogram and card and catalogue)
        for activity_id, subprogram, card, catalogue in rows
    }


def mapping_gap_counts(states):
    """Total counts distinct incomplete activities; kind counts may overlap."""
    return {
        **{kind: sum(not state[kind] for state in states.values())
           for kind in ('subprogram', 'card', 'catalogue')},
        'total': sum(not state['ready'] for state in states.values()),
    }


def activity_mapping_counts(db, period_id):
    return mapping_gap_counts(activity_mapping_states(db, period_id))
