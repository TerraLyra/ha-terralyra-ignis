"""Conservative offline labels; neither operational alerts nor a complete taxonomy."""
from dataclasses import dataclass
from enum import Enum
import re

from act_feed import ActItem


class IncidentCategory(str, Enum):
    VEGETATION_FIRE_CANDIDATE = 'vegetation_fire_candidate'
    PLANNED_BURN = 'planned_burn'
    MEDICAL = 'medical'
    UNKNOWN = 'unknown'


class ExerciseEvidence(str, Enum):
    MARKED = 'marked'
    NOT_ESTABLISHED = 'not_established'


@dataclass(frozen=True)
class Classification:
    category: IncidentCategory
    exercise_evidence: ExerciseEvidence
    marker_fields: tuple[str, ...]


def classify_item(item: ActItem) -> Classification:
    """Classify exact source type labels without changing or retaining source data.

    A candidate is NOT a confirmed wildfire. Test wording is a conservative review
    flag, not proof that every unmarked event is real. Only known source field names
    are examined; CAP status semantics are not imposed on this RSS feed.
    """
    fields = dict(item.fields)
    if len(fields) != len(item.fields):
        raise ValueError('Duplicate raw fields')
    raw_type = ' '.join(fields.get('type', '').upper().split())
    category = {
        'GRASS AND BUSH FIRE': IncidentCategory.VEGETATION_FIRE_CANDIDATE,
        'AMBULANCE RESPONSE': IncidentCategory.MEDICAL,
        'HAZARD REDUCTION BURN': IncidentCategory.PLANNED_BURN,
    }.get(raw_type, IncidentCategory.UNKNOWN)
    markers = tuple(name for name in ('title', 'description', 'type')
                    if re.search(r'\b(?:TEST|EXERCISE|DRILL)\b',
                                 fields.get(name, ''), flags=re.IGNORECASE))
    return Classification(category,
                          ExerciseEvidence.MARKED if markers else ExerciseEvidence.NOT_ESTABLISHED,
                          markers)
