"""Resource plans never duplicate recognized cards or mutate inventory."""
from copy import deepcopy
import pytest
from custom_components.terralyra_ignis.card_resource_plan import plan_card_resource

URL = '/terralyra_ignis/cards/ignis-location-summary.js'

@pytest.mark.parametrize('resources,status', [
    ([], 'confirm_no_renamed_copy'),
    ([{'url': URL+'?v=0.38.1', 'type':'module'}], 'already_registered'),
    ([{'url': URL, 'type':'js'}], 'type_review'),
    ([{'url':'/local/ignis-location-summary-0.33.0.js','type':'module'}], 'legacy_review'),
    ([{'url':'https://example.org'+URL,'type':'module'}], 'legacy_review'),
    ([{'url':URL,'type':'module'},{'url':URL+'?v=old','type':'module'}], 'duplicate_review'),
    ([{'url':'/local/renamed.js','type':'module'}], 'confirm_no_renamed_copy'),
])
def test_conservative_plan(resources, status):
    original = deepcopy(resources)
    result = plan_card_resource('summary', resources)
    assert result['status'] == status
    assert result['url'] == URL
    assert resources == original

@pytest.mark.parametrize('resources', [None, {}, [{}], [{'url':URL}]])
def test_incomplete_inventory_is_not_an_empty_inventory(resources):
    with pytest.raises(ValueError):
        plan_card_resource('summary', resources)

def test_unknown_card_rejected():
    with pytest.raises(ValueError):
        plan_card_resource('unknown', [])
