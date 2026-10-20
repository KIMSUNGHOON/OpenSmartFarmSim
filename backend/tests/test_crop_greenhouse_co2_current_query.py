"""The current CO2 reader requires an initialized exact family store."""
import pytest

from app import crop_greenhouse_co2_current_query as current
from app.crop_greenhouse_solar_result_store import SolarResultStore


@pytest.mark.parametrize('store', [None, False, object(),
    current.storage.Co2ResultStore.__new__(current.storage.Co2ResultStore),
    SolarResultStore.__new__(SolarResultStore)])
def test_exact_initialized_store_required(store):
    with pytest.raises(current.Co2CurrentQueryHold):
        current.Co2CurrentQuery(store)
