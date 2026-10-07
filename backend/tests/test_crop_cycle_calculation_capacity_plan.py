"""Capacity cursors are integer positions, never simulated crop states."""
import pytest

from crop_cycle_full_capacity_smoke import plan_chunks


def test_dense_boundaries_retain_all_outputs_and_events():
    cuts = plan_chunks([(0, i+1, i+1) for i in range(269)])
    assert [c['sequence'] for c in cuts] == [128, 256, 269]
    assert [(c['steps'], c['samples'], c['events']) for c in cuts] == [
        (0, 128, 128), (0, 256, 256), (0, 269, 269)]


def test_long_interval_stops_at_transition_budget_without_skipping_boundary():
    cuts = plan_chunks([(0, 1, 0), (5000, 2, 0), (10000, 3, 0)])
    assert [c['sequence'] for c in cuts] == [4096, 8192, 10003]
    assert [(c['steps'], c['boundary_cursor'], c['samples']) for c in cuts] == [
        (4095, 1, 1), (8190, 2, 2), (10000, 3, 3)]


def test_pending_boundary_and_combined_output_event_are_consumed_once():
    cuts = plan_chunks([(0, 1, 1), (1, 2, 2), (2, 3, 3)], transitions=2, boundaries=2)
    assert [(c['sequence'], c['steps'], c['boundary_cursor']) for c in cuts] == [
        (2, 1, 1), (4, 2, 2), (5, 2, 3)]
    assert [(c['samples'], c['events']) for c in cuts] == [(1, 1), (2, 2), (3, 3)]


def test_forcing_only_boundaries_count_toward_resource_cap():
    cuts = plan_chunks([(0, 0, 0)]*128+[(0, 1, 1)])
    assert [(c['sequence'], c['samples'], c['events']) for c in cuts] == [(128, 0, 0), (129, 1, 1)]


@pytest.mark.parametrize('rows', [[], [(0, 2, 0)], [(0, 0, 2)], [(1, 1, 0), (0, 2, 0)], [(0, 1, 0), (0, 0, 0)]])
def test_invalid_grid_is_rejected(rows):
    with pytest.raises(ValueError): plan_chunks(rows)
