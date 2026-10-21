"""Closed CO2 admission authority before any database or numeric operation."""
import pytest
import psycopg

from app import crop_greenhouse_co2_execution as model
from app.crop_greenhouse_co2_farm_binding import Co2FarmBinding
from app.crop_greenhouse_solar_farm_binding import SolarFarmBinding


@pytest.mark.parametrize('binding', [None, object(), object.__new__(SolarFarmBinding), object.__new__(Co2FarmBinding)])
def test_exact_current_binding_required_before_io(monkeypatch,binding):
    calls=[]
    def forbidden(*a,**kw):calls.append(1);raise AssertionError('invalid authority performed I/O')
    monkeypatch.setattr(psycopg,'connect',forbidden)
    with pytest.raises(model.Co2ExecutionHold,match='^co2 execution authority unavailable$'):
        model.Co2ExecutionService(binding,input_resolver=forbidden)
    assert calls==[]
