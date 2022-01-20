# coding=utf8

from datetime import datetime

import pytest

from gnss_tec.glo import collect_freq_nums, FetchSlotFreqNumError
from gnss_tec.glo import fetch_slot_freq_num


@pytest.fixture(scope='function')
def freq_nums(request):
    return request.getfixturevalue(request.param)


@pytest.mark.parametrize(
    'nav_stream,freq_nums',
    [
        ('nav_v2_stream', 'nav_v2_freq_nums'),
        ('nav_v3_stream', 'nav_v3_freq_nums'),
    ],
    indirect=['nav_stream', 'freq_nums'],
)
def test_collect_freq_nums(nav_stream, freq_nums):
    test_freq_nums = collect_freq_nums(nav_stream)
    assert freq_nums == test_freq_nums


def test_fetch_slot_freq_num():
    slot = 2

    glo_freq_nums = {
        1: {
            datetime(2016, 12, 8, 0, 15): 1,
        },
        2: {
            datetime(2016, 12, 8, 13, 15): -5,
            datetime(2016, 12, 8, 0, 15): -3,
            datetime(2016, 12, 8, 10, 15): -4,
        }
    }

    std = (
        (datetime(2016, 12, 8, 0, 0, 0), -3),
        (datetime(2016, 12, 8, 12, 12, 0), -4),
        (datetime(2016, 12, 8, 13, 16, 0), -5),
    )

    for std_ts, std_fn in std:
        freq_num = fetch_slot_freq_num(
            std_ts,
            slot,
            glo_freq_nums
        )
        assert std_fn == freq_num


def test_fetch_slot_num_key_error(nav_v2_stream):
    glo_freq_nums = collect_freq_nums(nav_v2_stream)
    timestamp = datetime(2016, 1, 1, 0, 15)
    with pytest.raises(FetchSlotFreqNumError, match="Can't find slot"):
        fetch_slot_freq_num(
            timestamp=timestamp,
            slot=5,
            freq_nums=glo_freq_nums,
        )


def test_fetch_slot_num_value_error(nav_v2_freq_nums):
    with pytest.raises(FetchSlotFreqNumError,
                       match="Can't find GLONASS frequency"):
        fetch_slot_freq_num(
            datetime(2017, 12, 8, 0, 0, 0),
            2,
            nav_v2_freq_nums,
        )
