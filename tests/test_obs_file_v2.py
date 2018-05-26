# coding=utf8
"""Functions to test tec.rinex.ObsFileV2 class."""

import datetime


def test_init(dumb_obs_v2):
    std_obs_types = [
        'L1', 'P1', 'C1', 'L2', 'P2', 'D1', 'D2', 'S1', 'S2',
        'L5', 'C5', 'D5', 'S5', 'L7', 'C7', 'D7', 'S7', 'L8',
        'C8', 'D8', 'S8',
    ]
    std_time_system = 'GPS'

    assert dumb_obs_v2.time_system == std_time_system
    assert len(dumb_obs_v2.obs_types) == 21
    assert dumb_obs_v2.obs_types == std_obs_types


def test_parse_epoch_record(obs_v2):
    # event
    event_flag, num_of_sats = 4, 5
    epoch_record = obs_v2._parse_epoch_record()
    assert epoch_record == (None, event_flag, num_of_sats, None)

    # skip comments
    obs_v2.handle_event(4, 5)

    # regular epoch
    timestamp = datetime.datetime(2017, 7, 6)
    epoch_flag = 0
    num_of_sats = 18
    list_of_sats = ['G18', 'R15', 'G31', 'G03', 'R06', 'G16', 'G01', 'R09',
                    'G25', 'G22', 'R05', 'G29', 'R16', 'G26', 'R04', 'G10',
                    'G32', 'G14']

    epoch_record = obs_v2._parse_epoch_record()
    assert epoch_record == (timestamp, epoch_flag, num_of_sats, list_of_sats)
