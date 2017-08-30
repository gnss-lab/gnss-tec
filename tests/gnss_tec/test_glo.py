#!/usr/bin/env python
# coding=utf8

from datetime import datetime
from io import StringIO
import pytest

from gnss_tec.glo import fetch_slot_freq_num
from gnss_tec.glo import collect_freq_nums


def test_collect_freq_nums():
    nav_file = '''\
     2.01           GLONASS NAV DATA                        RINEX VERSION / TYPE
CCRINEXG V1.4 UX    CDDIS               09-MAR-16 12:44     PGM / RUN BY / DATE 
IGS BROADCAST EPHEMERIS FILE                                COMMENT             
teqc  2013Mar15     GPS Operator        20160102  0:05:     COMMENT             
  2016     1     1    0.279396772385D-07                    CORR TO SYSTEM TIME 
    17                                                      LEAP SECONDS        
                                                            END OF HEADER       
 1 16  1  1  0 15  0.0-0.147201120853D-03 0.000000000000D+00 0.300000000000D+02
    0.634915380859D+04-0.254754066467D+00 0.000000000000D+00 0.000000000000D+00
    0.170520444336D+05 0.243410968780D+01 0.186264514923D-08 0.100000000000D+01
   -0.178746152344D+05 0.223380565643D+01 0.186264514923D-08 0.000000000000D+00
 2 16  1  1  0 15  0.0 0.169292092323D-03 0.909494701773D-12 0.000000000000D+00
    0.112042094727D+05-0.474354743957D+00-0.931322574616D-09 0.000000000000D+00
   -0.190359375000D+04 0.309479141235D+01 0.000000000000D+00-0.400000000000D+01
   -0.228054150391D+05-0.494022369385D+00 0.279396772385D-08 0.000000000000D+00
 3 16  1  1  0 15  0.0 0.588288530707D-04 0.000000000000D+00 0.000000000000D+00
    0.948807763672D+04-0.397904396057D+00-0.931322574616D-09 0.000000000000D+00
   -0.192305532227D+05 0.185273551941D+01-0.931322574616D-09 0.500000000000D+01
   -0.137629448242D+05-0.285944557190D+01 0.186264514923D-08 0.000000000000D+00
 3 16  1  1  0 15  2.0 0.588288530707D-04 0.000000000000D+00 0.200000000000D+01
    0.948807763672D+04-0.397904396057D+00-0.931322574615D-09 0.000000000000D+00
   -0.192305532227D+05 0.185273551941D+01-0.931322574615D-09 0.500000000000D+01
   -0.137629448242D+05-0.285944557190D+01 0.186264514923D-08 0.000000000000D+00
'''
    freq_nums = collect_freq_nums(StringIO(nav_file))
    std_freq_nums = {
        1: {datetime(2016, 1, 1, 0, 15): 1},
        2: {datetime(2016, 1, 1, 0, 15): -4},
        3: {datetime(2016, 1, 1, 0, 15): 5},
    }

    assert freq_nums == std_freq_nums


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

    with pytest.raises(KeyError):
        fetch_slot_freq_num(std[0][0], 5, glo_freq_nums)

    with pytest.raises(ValueError):
        fetch_slot_freq_num(
            datetime(2017, 12, 8, 0, 0, 0),
            2,
            glo_freq_nums,
        )
