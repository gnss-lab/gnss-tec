# coding=utf8
"""Functions to test tec.rinex.ObsFileV2 class."""

from io import StringIO

import datetime
import pytest

from gnss_tec.rinex import ObsFileV2

RNX = """\
     2.11           OBSERVATION DATA    M (MIXED)           RINEX VERSION / TYPE
teqc  2016Nov7      NOAA/NOS/NGS/CORS   20170707 04:06:33UTCPGM / RUN BY / DATE
ASPA                                                        MARKER NAME
50503S006                                                   MARKER NUMBER
Giovanni Sella      NGS                                     OBSERVER / AGENCY
4733K06635          TRIMBLE NETR5       4.85                REC # / TYPE / VERS
30517456            TRM55971.00     NONE                    ANT # / TYPE
 -6100258.8690  -996506.1670 -1567978.8630                  APPROX POSITION XYZ
        0.0000        0.0000        0.0000                  ANTENNA: DELTA H/E/N
     1     1                                                WAVELENGTH FACT L1/2
    11    L1    L2    L5    C1    P1    C2    P2    C5    S1# / TYPES OF OBSERV
          S2    S5                                          # / TYPES OF OBSERV
    30.0000                                                 INTERVAL
    18                                                      LEAP SECONDS
  2017     7     6     0     0    0.0000000     GPS         TIME OF FIRST OBS
                                                            END OF HEADER
                            4  5
ASPA (COGO code)                                            COMMENT
   0.000      (antenna height)                              COMMENT
 -14.32609534 (latitude)                                    COMMENT
-170.72243361 (longitude)                                   COMMENT
0053.667      (elevation)                                   COMMENT
 17  7  6  0  0  0.0000000  0 18G18R15G31G03R06G16G01R09G25G22R05G29-0.000392832
                                R16G26R04G10G32G14
 129609926.497 6 100994793.77642                  24663965.641
                  24663974.148                          38.600          17.800

 120505665.941 6  93726662.377 6                  22550992.016    22550991.051
                  22550998.707                          41.700          39.400

 113401304.102 8  88364763.776 7                  21579566.188
  21579571.359    21579571.531                          50.300          46.200

 132701874.619 5 103404140.724 5                  25252336.969
  25252347.414                                          33.700          34.400

 119263436.899 6  92760508.769 5                  22349925.250    22349924.051
                  22349927.602                          38.100          35.100

 116184238.344 7  90533145.56945                  22109098.484
                  22109105.234                          45.600          33.200

 129470789.804 6 100886299.783 6                  24637455.992
  24637464.797    24637466.082                          37.100          37.300

 114931261.449 7  89391042.915 7                  21522933.477    21522934.391
                  21522939.465                          45.900          43.900

 131228058.513 6 102255791.926 6                  24971881.508
  24971889.785    24971890.309                          38.400          36.300

 119420387.410 7  93054887.93344                  22724945.750
                  22724949.512                          43.200          29.400

 104095002.622 7  80962839.312 7                  19473125.563    19473125.184
                  19473131.082                          43.900          42.200

 131232157.556 6 102258880.431 5                  24972645.516
  24972654.613    24972654.199                          38.300          34.800

 106080541.169 7  82507163.624 7                  19858497.734    19858498.063
                  19858503.371                          44.000          42.800

 108649979.923 8  84662364.399 8                  20675386.594
  20675395.574    20675395.805                          48.400          51.100

 112909742.180 8  87818759.471 7                  21085104.797    21085103.715
                  21085108.438                          48.100          44.700

 115661530.779 8  90125872.381 7                  22009648.641
  22009657.211    22009657.441                          48.500          47.600

 115505192.609 7  90004072.298 7                  21979890.539
  21979899.461    21979899.281                          47.500          47.600

 113491920.675 7  88435293.67545                  21596788.523
                  21596794.160                          46.100          32.700

 17  7  6  0  1  0.0000000  0 18 18R15G31G03R06G16G01R09G25G22R05G29
                                R16G26R04G10G32G14
 129714491.092 6 101076272.53043                  24683863.789
                  24683872.414                          39.200          18.600

 120613774.752 7  93810746.963 6                  22571222.727    22571222.703
                  22571230.711                          42.500          39.700

 113438416.847 8  88393682.795 7                  21586628.695
  21586633.398    21586633.336                          50.300          46.600

 132599072.037 5 103324034.869 6                  25232775.227
  25232785.262    25232781.449                          34.600          36.400

 119149217.493 6  92671671.486 5                  22328518.555    22328518.293
                  22328522.430                          38.300          35.000

 116099973.097 7  90467484.36845                  22093063.586
                  22093069.574                          45.900          33.100

 129470125.015 6 100885781.713 6                  24637328.750
  24637339.078    24637340.129                          36.200          37.000

 114869248.525 7  89342810.692 7                  21511321.695    21511321.555
                  21511325.922                          46.600          44.500

 131324730.690 6 102331120.877 6                  24990277.883
  24990285.867    24990286.273                          38.900          37.100

 119340545.428 7  92992673.42545                  22709753.359
                  22709755.480                          46.100          31.200

 104062372.020 7  80937459.929 7                  19467020.781    19467021.227
                  19467027.590                          44.100          42.700

 131219712.462 6 102249182.977 6                  24970277.469
  24970285.688    24970286.094                          39.900          36.900

 106112572.378 7  82532076.791 7                  19864493.438    19864493.176
                  19864498.133                          43.700          42.700

 108609118.768 8  84630524.539 8                  20667611.063
  20667619.516    20667619.746                          48.500          51.000

 112981641.858 7  87874681.372 7                  21098530.055    21098530.383
                  21098535.574                          47.800          45.400

 115746528.568 8  90192104.390 7                  22025823.547
  22025831.473    22025832.172                          49.600          47.100

 115506300.717 8  90004935.735 7                  21980103.695
  21980111.211    21980110.855                          48.800          47.200

 113479270.250 7  88425436.16745                  21594381.758
                  21594386.398                          45.500          32.700

"""
RNX_HEADER = """\
     2.11           OBSERVATION DATA    M (MIXED)           RINEX VERSION / TYPE
teqc  2016Apr1      BKG Frankfurt       20170707 00:23:29UTCPGM / RUN BY / DATE
ADIS                                                        MARKER NAME
31502M001                                                   MARKER NUMBER
NTRIPS05-769322-52  ADDIS ABABA UNIVERSITY                  OBSERVER / AGENCY
MT300102915         JPS LEGACY          2.6.1 JAN,10,2008   REC # / TYPE / VERS
0220173805          TRM29659.00     NONE                    ANT # / TYPE
  4913652.8072  3945922.6351   995383.2858                  APPROX POSITION XYZ
        0.0010        0.0000        0.0000                  ANTENNA: DELTA H/E/N
     1     1                                                WAVELENGTH FACT L1/2
    21    L1    P1    C1    L2    P2    D1    D2    S1    S2# / TYPES OF OBSERV
          L5    C5    D5    S5    L7    C7    D7    S7    L8# / TYPES OF OBSERV
          C8    D8    S8                                    # / TYPES OF OBSERV
    30.0000                                                 INTERVAL
    17                                                      LEAP SECONDS
     0                                                      RCV CLOCK OFFS APPL
  2017     7     6     0     0    0.0000000     GPS         TIME OF FIRST OBS
Linux 2.4.21-27.ELsmp|Opteron|gcc -static|Linux x86_64|=+   COMMENT
MAKERINEX 2.0.20973 AAU/NTRIPS05        2017-07-06 01:04    COMMENT
                                                            END OF HEADER
"""


@pytest.fixture
def dumb_obs():
    obs_file = StringIO(RNX_HEADER)
    return ObsFileV2(
        obs_file,
        version=2.11,
    )


@pytest.fixture
def obs():
    obs_file = StringIO(RNX)
    glo_freq_nums = {
        4: {datetime.datetime(2017, 7, 6, 0, 15): 6.0},
        5: {datetime.datetime(2017, 7, 6, 0, 15): 1.0},
        6: {datetime.datetime(2017, 7, 6, 0, 15): -4.0},
        9: {datetime.datetime(2017, 7, 6, 0, 15): -2.0},
        15: {datetime.datetime(2017, 7, 6, 0, 15): 0.0},
        16: {datetime.datetime(2017, 7, 6, 0, 15): -1.0},
    }
    return ObsFileV2(
        obs_file,
        version=2.11,
        glo_freq_nums=glo_freq_nums,
    )


def test_init(dumb_obs):
    std_obs_types = [
        'L1', 'P1', 'C1', 'L2', 'P2', 'D1', 'D2', 'S1', 'S2',
        'L5', 'C5', 'D5', 'S5', 'L7', 'C7', 'D7', 'S7', 'L8',
        'C8', 'D8', 'S8',
    ]
    std_time_system = 'GPS'

    assert dumb_obs.time_system == std_time_system
    assert len(dumb_obs.obs_types) == 21
    assert dumb_obs.obs_types == std_obs_types


def test_parse_epoch_record(obs):
    # event
    event_flag, num_of_sats = 4, 5
    epoch_record = obs._parse_epoch_record()
    assert epoch_record == (None, event_flag, num_of_sats, None)

    # skip comments
    obs.handle_event(4, 5)

    # regular epoch
    timestamp = datetime.datetime(2017, 7, 6)
    epoch_flag = 0
    num_of_sats = 18
    list_of_sats = ['G18', 'R15', 'G31', 'G03', 'R06', 'G16', 'G01', 'R09',
                    'G25', 'G22', 'R05', 'G29', 'R16', 'G26', 'R04', 'G10',
                    'G32', 'G14']

    epoch_record = obs._parse_epoch_record()
    assert epoch_record == (timestamp, epoch_flag, num_of_sats, list_of_sats)

# def test_next_tec(obs):
#     pytest.skip()
#     for tec in obs:
#         print(tec)
