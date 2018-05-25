# coding=utf8
"""Functions to test tec.rinex.ObsFileV3 class."""
from collections import namedtuple
from datetime import datetime, timedelta
from io import StringIO

import pytest

from gnss_tec.rinex import ObsFileV3

AJAC_RNX = '''\
     3.02           OBSERVATION DATA    M                   RINEX VERSION / TYPE
Converto v3.4.8     IGN-RGP             20170627 013115 UTC PGM / RUN BY / DATE
AJAC                                                        MARKER NAME
10077M005                                                   MARKER NUMBER
Automatic           Institut Geographique National          OBSERVER / AGENCY
1830139             LEICA GR25          4.02                REC # / TYPE / VERS
4611118324          TRM57971.00     NONE                    ANT # / TYPE
  4696989.7040   723994.2090  4239678.3140                  APPROX POSITION XYZ
        0.0000        0.0000        0.0000                  ANTENNA: DELTA H/E/N
G   12 C1C L1C D1C S1C C2W L2W D2W S2W C5Q L5Q D5Q S5Q      SYS / # / OBS TYPES
R    8 C1C L1C D1C S1C C2P L2P D2P S2P                      SYS / # / OBS TYPES
E   16 C1C L1C D1C S1C C5Q L5Q D5Q S5Q C7Q L7Q D7Q S7Q C8Q  SYS / # / OBS TYPES
       L8Q D8Q S8Q                                          SYS / # / OBS TYPES
C    8 C1I L1I D1I S1I C7I L7I D7I S7I                      SYS / # / OBS TYPES
S    4 C1C L1C D1C S1C                                      SYS / # / OBS TYPES
DBHZ                                                        SIGNAL STRENGTH UNIT
    30.000                                                  INTERVAL
  2017    06    26    00    00    0.0000000     GPS         TIME OF FIRST OBS
  2017    06    26    23    59   30.0000000     GPS         TIME OF LAST OBS
     0                                                      RCV CLOCK OFFS APPL
G L2S -0.25000                                              SYS / PHASE SHIFT
G L2X -0.25000                                              SYS / PHASE SHIFT
R L2P  0.25000                                              SYS / PHASE SHIFT
E L8Q -0.25000                                              SYS / PHASE SHIFT
 24 R01  1 R02 -4 R03  5 R04  6 R05  1 R06 -4 R07  5 R08  6 GLONASS SLOT / FRQ #
    R09 -2 R10 -7 R11  0 R12 -1 R13 -2 R14 -7 R15  0 R16 -1 GLONASS SLOT / FRQ #
    R17  4 R18 -3 R19  3 R20  2 R21  4 R22 -3 R23  3 R24  2 GLONASS SLOT / FRQ #
 C1C  -71.940 C1P  -71.940 C2C  -71.940 C2P  -71.940        GLONASS COD/PHS/BIS
    18    18  1929     7                                    LEAP SECONDS
                                                            END OF HEADER
> 2017 06 26 00 00  0.0000000  0  4
G06  20835332.939   109490435.32508      -587.633          50.500    20835328.717    85317207.80808      -457.896          48.250    20835330.401    81762343.64108      -438.821          52.350
R04  24135247.881   129243249.65706     -2964.509          39.250    24135244.262   100522446.54306     -2305.728          39.000
E02  25206580.771   132461485.07148      1704.855          50.900    25206579.417    98916045.45308      1273.096          50.150    25206576.244   101496450.89908      1306.281          51.950    25206577.942   100206247.02308      1289.659          48.650
C10  38625935.135   201135401.51606       436.003          40.600    38625926.793   155530626.32107       337.087          45.300
>                              4  1
                                                                         COMMENT
> 2017 06 26 00 00 30.0000000  0  5
G02  23269584.628   122282497.09607      2373.850          45.900    23269574.831    95285049.78406      1849.752          40.000
R06  20254437.775   108081579.18807      1594.895          44.050    20254434.977    84063449.71306      1240.474          41.000
E03  26199562.760   137679722.61448     -1953.987          49.350    26199562.201   102812831.22108     -1459.200          48.450    26199559.507   105494888.18008     -1497.248          50.800    26199561.223   104153862.04807     -1478.202          46.700
C05  39875325.769   207641286.35906         2.988          37.750    39875315.615   160561383.77107         2.041          43.350
S20  38144728.445   200451840.25607       -84.098          44.000
'''
HKWS_HEADER = '''\
     3.02           OBSERVATION DATA    M: MIXED            RINEX VERSION / TYPE
G   16 C1C L1C D1C S1C C2S L2S D2S S2S C2W L2W D2W S2W C5Q  SYS / # / OBS TYPES
       L5Q D5Q S5Q                                          SYS / # / OBS TYPES
R   12 C1C L1C D1C S1C C2P L2P D2P S2P C2C L2C D2C S2C      SYS / # / OBS TYPES
E   16 C1C L1C D1C S1C C5Q L5Q D5Q S5Q C7Q L7Q D7Q S7Q C8Q  SYS / # / OBS TYPES
       L8Q D8Q S8Q                                          SYS / # / OBS TYPES
C    8 C1I L1I D1I S1I C7I L7I D7I S7I                      SYS / # / OBS TYPES
J   12 C1C L1C D1C S1C C2S L2S D2S S2S C5Q L5Q D5Q S5Q      SYS / # / OBS TYPES
S    4 C1C L1C D1C S1C                                      SYS / # / OBS TYPES
    30.000                                                  INTERVAL
  2015    12    19    00    00    0.0000000     GPS         TIME OF FIRST OBS
  2015    12    19    23    59   30.0000000     GPS         TIME OF LAST OBS
                                                            END OF HEADER
'''


@pytest.fixture
def dumb_obs():
    obs_file = StringIO(HKWS_HEADER)

    return ObsFileV3(
        obs_file,
        version=3.02,
    )


@pytest.fixture
def obs():
    obs_file = StringIO(AJAC_RNX)
    glo_frq = {
        4: {datetime(2017, 6, 26, 0): 6},
        6: {datetime(2017, 6, 26, 0): -4},
    }
    return ObsFileV3(
        obs_file,
        version=3.02,
        glo_freq_nums=glo_frq,
    )


def test_init(dumb_obs):
    std_obs_types = dict(
        G=('C1C', 'L1C', 'D1C', 'S1C', 'C2S', 'L2S',
           'D2S', 'S2S', 'C2W', 'L2W', 'D2W', 'S2W',
           'C5Q', 'L5Q', 'D5Q', 'S5Q'),
        R=('C1C', 'L1C', 'D1C', 'S1C', 'C2P', 'L2P', 'D2P', 'S2P', 'C2C', 'L2C',
           'D2C', 'S2C'),
        E=('C1C', 'L1C', 'D1C', 'S1C', 'C5Q', 'L5Q', 'D5Q', 'S5Q', 'C7Q',
           'L7Q', 'D7Q', 'S7Q', 'C8Q', 'L8Q', 'D8Q', 'S8Q'),
        J=('C1C', 'L1C', 'D1C', 'S1C', 'C2S', 'L2S', 'D2S', 'S2S', 'C5Q', 'L5Q',
           'D5Q', 'S5Q'),
        S=('C1C', 'L1C', 'D1C', 'S1C'),
        C=('C2I', 'L2I', 'D2I', 'S2I', 'C7I', 'L7I', 'D7I', 'S7I'),
    )

    assert dumb_obs.obs_types == std_obs_types
    assert dumb_obs.time_system == 'GPS'


def test_obs_slice_indices(dumb_obs):
    std_slices = (
        [3, 19], [19, 35], [35, 51], [51, 67], [67, 83], [83, 99], [99, 115],
        [115, 131], [131, 147], [147, 163],
        [163, 179], [179, 195], [195, 211], [211, 227], [227, 243], [243, 259]
    )
    test_slices = dumb_obs._obs_slice_indices()
    assert std_slices == test_slices


def test_indices_according_priority(dumb_obs):
    sat_system = 'J'

    indices = namedtuple('observation_indices', ['phase', 'pseudo_range'])

    std_indices = indices(
        {1: 1, 2: 5},
        {1: 0, 2: 4},
    )
    test_indices = dumb_obs.indices_according_priority(sat_system)

    assert std_indices == test_indices


def test_parse_epoch_record(dumb_obs):
    epoch_record = '> 2015 12 19 00 00  0.0000000  0 28'
    std_epoch_values = (datetime(2015, 12, 19), 0, 28, timedelta(0))
    test_epoch_values = dumb_obs._parse_epoch_record(epoch_record)
    assert std_epoch_values == test_epoch_values

    epoch_record = '>                              4  1'
    std_epoch_values = (None, 4, 1, timedelta(0))
    test_epoch_values = dumb_obs._parse_epoch_record(epoch_record)
    assert std_epoch_values == test_epoch_values


def test_parse_obs_record(dumb_obs):
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

    test_obs = dumb_obs._parse_obs_record(row)
    assert test_obs == std_obs


def test_next_tec(obs):
    for tec in obs:
        break

    assert tec.satellite == 'G06'
    assert tec.timestamp == datetime(2017, 6, 26, 0)
    assert tec.phase_tec == 33.756676401749395
    assert tec.p_range_tec == -40.183956990827824
