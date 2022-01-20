import pytest


def test_absent_slot(obs_absent_slot):
    with pytest.warns(UserWarning) as record:
        list(obs_absent_slot.next_tec())
    # assert len(record) == 1
    assert "Can't find slot" in record[0].message.args[0]
