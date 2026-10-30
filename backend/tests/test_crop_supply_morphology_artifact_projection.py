"""Stored arithmetic/shape QC; these fixtures do not validate crop biology."""
from fractions import Fraction

import pytest


@pytest.mark.parametrize('value', [True, 1, float('nan'), float('inf'), -1.])
def test_stored_nonnegative_coordinates_reject_wrong_types_and_domains(value):
    from app import crop_supply_morphology_artifact_projection as projection
    with pytest.raises(ValueError):
        projection.nonnegative(value)


def test_exact_clock_composition_preserves_original_fraction_and_units():
    from app import crop_supply_morphology_artifact_projection as projection
    origin = {'thermal_age_exact': projection.q(Fraction(1, 8), 'degC_day'),
              'at_elapsed_seconds_exact': projection.q(Fraction(3, 2), 's'),
              'air_temperature_integral_exact': projection.q(Fraction(30), 'degC_s'),
              'base_temperature': {'value': 10., 'unit': 'degC'}}
    actual = projection.clock(origin, projection.q(Fraction(7, 2), 's'),
                              projection.q(Fraction(74), 'degC_s'))
    assert actual == {'numerator': '451', 'denominator': '3600', 'unit': 'degC_day'}
    assert projection.x(actual) == Fraction(1, 8) + Fraction(44 - 10 * 2, 86400)


@pytest.mark.parametrize('quantity', [
    {'numerator': '2', 'denominator': '2', 'unit': 's'},
    {'numerator': '1', 'denominator': '0', 'unit': 's'},
    {'numerator': True, 'denominator': '1', 'unit': 's'},
    {'numerator': '1', 'denominator': '1', 'unit': 'm'},
])
def test_exact_stored_quantity_requires_canonical_rational_and_correct_unit(quantity):
    from app import crop_supply_morphology_artifact_projection as projection
    with pytest.raises(ValueError):
        projection.x(quantity, 's')
