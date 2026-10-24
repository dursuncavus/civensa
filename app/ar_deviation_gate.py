"""Validate deviation explanations in the already loaded unit submission."""
from fastapi import HTTPException
from sqlalchemy import select

from .activity_contract_service import needs_deviation_explanation
from .models import IndicatorDefinitionRevision, PublicationIndicatorBinding, ReportIndicator


def require_deviation_explanations(db, payload):
    core = payload['core']
    # CORE rows and captured identities share ReportIndicator.id order. Use the
    # captured identity rather than matching names, which need not be unique.
    missing = [(source['indicator_id'], row['name'])
               for row, source in zip(core['indicators'], payload['_typeset']['indicators'], strict=True)
               if needs_deviation_explanation(row['actual_state'], row['deviation'].get('delta'), row['explanation'])]
    if not missing:
        return
    # CORE already supplies the current revision's scoped values. Fetch only
    # anchor IDs; do not rebuild the payload or reread actuals for validation.
    ids = dict(db.execute(select(IndicatorDefinitionRevision.indicator_id, ReportIndicator.id)
        .join(PublicationIndicatorBinding,
              PublicationIndicatorBinding.definition_revision_id == IndicatorDefinitionRevision.id)
        .join(ReportIndicator, ReportIndicator.publication_binding_id == PublicationIndicatorBinding.id)
        .where(ReportIndicator.report_revision_id == core['revision_id'],
               PublicationIndicatorBinding.department_id == payload['department_id'],
               IndicatorDefinitionRevision.indicator_id.in_([identity for identity, _ in missing]))).all())
    message = ('Birim faaliyet raporu gönderilemedi. Şu göstergelerde hedef farkı açıklaması eksik: '
               + '; '.join(name for _, name in missing) + '.')
    blockers = [{'indicator': name, 'report_indicator_id': ids[identity],
                 'link': f"{core['link']}#indicator-{ids[identity]}",
                 'message': 'Hedef ile gerçekleşme farkı için açıklama girin.'}
                for identity, name in missing]
    raise HTTPException(409, {'message': message, 'blockers': blockers})
