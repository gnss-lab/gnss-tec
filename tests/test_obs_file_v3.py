# coding=utf8
"""Functions to test tec.rinex.ObsFileV3 class."""
from collections import namedtuple
from datetime import datetime, timedelta


def test_init(dumb_obs_v3):
    std_obs_types = dict(
        G=('C1C', 'L1C', 'D1C', 'S1C', 'C2S', 'L2S',
           'D2S', 'S2S', 'C2W', 'L2W', 'D2W', 'S2W',
           'C5Q', 'L5Q', 'D5Q', 'S5Q'),
        R=(
            'C1C', 'L1C', 'D1C', 'S1C', 'C2P', 'L2P', 'D2P', 'S2P', 'C2C',
            'L2C',
            'D2C', 'S2C'),
        E=('C1C', 'L1C', 'D1C', 'S1C', 'C5Q', 'L5Q', 'D5Q', 'S5Q', 'C7Q',
           'L7Q', 'D7Q', 'S7Q', 'C8Q', 'L8Q', 'D8Q', 'S8Q'),
        J=(
            'C1C', 'L1C', 'D1C', 'S1C', 'C2S', 'L2S', 'D2S', 'S2S', 'C5Q',
            'L5Q',
            'D5Q', 'S5Q'),
        S=('C1C', 'L1C', 'D1C', 'S1C'),
        C=('C2I', 'L2I', 'D2I', 'S2I', 'C7I', 'L7I', 'D7I', 'S7I'),
    )

    assert dumb_obs_v3.obs_types == std_obs_types
    assert dumb_obs_v3.time_system == 'GPS'


def test_obs_slice_indices(dumb_obs_v3):
    std_slices = (
        [3, 19], [19, 35], [35, 51], [51, 67], [67, 83], [83, 99], [99, 115],
        [115, 131], [131, 147], [147, 163],
        [163, 179], [179, 195], [195, 211], [211, 227], [227, 243], [243, 259]
    )
    test_slices = dumb_obs_v3._obs_slice_indices()
    assert std_slices == test_slices


def test_indices_according_priority(dumb_obs_v3):
    sat_system = 'J'

    indices = namedtuple('observation_indices', ['phase', 'pseudo_range'])

    std_indices = indices(
        {1: 1, 2: 5},
        {1: 0, 2: 4},
    )
    test_indices = dumb_obs_v3.indices_according_priority(sat_system)

    assert std_indices == test_indices


def test_parse_epoch_record(dumb_obs_v3):
    epoch_record = '> 2015 12 19 00 00  0.0000000  0 28'
    std_epoch_values = (datetime(2015, 12, 19), 0, 28, timedelta(0))
    test_epoch_values = dumb_obs_v3._parse_epoch_record(epoch_record)
    assert std_epoch_values == test_epoch_values

    epoch_record = '>                              4  1'
    std_epoch_values = (None, 4, 1, timedelta(0))
    test_epoch_values = dumb_obs_v3._parse_epoch_record(epoch_record)
    assert std_epoch_values == test_epoch_values


def test_parse_obs_record(dumb_obs_v3):
    """Codes
       G   16 C1C L1C D1C S1C C2S L2S D2S S2S C2W L2W D2W S2W C5Q L5Q D5Q S5Q
    """
    row = 'G05  22730608.640   119450143.06408      3001.057          48.850' \
          '    22730607.500    93078040.86407' \
          '      2338.485          44.050    22730606.840    93078053.86507' \
          '      2338.485          42.350'

    observation_records = namedtuple('observation_records',
                                     ['satellite', 'records'])
    std_obs = observation_records(
        satellite='G05',
        records=(
            ('C1C', 22730608.640, 0, 0),
            ('L1C', 119450143.064, 0, 8),
            ('D1C', 3001.057, 0, 0),
            ('S1C', 48.850, 0, 0),
            ('C2S', 22730607.500, 0, 0),
            ('L2S', 93078040.864, 0, 7),
            ('D2S', 2338.485, 0, 0),
            ('S2S', 44.050, 0, 0),
            ('C2W', 22730606.840, 0, 0),
            ('L2W', 93078053.865, 0, 7),
            ('D2W', 2338.485, 0, 0),
            ('S2W', 42.350, 0, 0),
            ('C5Q', 0, 0, 0),
            ('L5Q', 0, 0, 0),
            ('D5Q', 0, 0, 0),
            ('S5Q', 0, 0, 0),
        )
    )

    test_obs = dumb_obs_v3._parse_obs_record(row)
    assert test_obs == std_obs


def test_next_tec(obs_v3):
    tec = None
    for tec in obs_v3:
        break

    assert tec.satellite == 'G06'
    assert tec.timestamp == datetime(2017, 6, 26, 0)
    assert tec.phase_tec == 33.756676401749395
    assert tec.p_range_tec == -40.183956990827824
