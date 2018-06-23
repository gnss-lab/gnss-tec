from datetime import datetime
from io import StringIO

from pytest import fixture, raises, mark

from gnss_tec.nav import NavMessageFileV2, NavMessageFileV3, \
    NavMessageFileError, _read_version_type, nav


@fixture
def nav_v2_object(nav_v2_stream):
    return NavMessageFileV2(nav_v2_stream)


@fixture
def nav_v3_object(nav_v3_stream):
    return NavMessageFileV3(nav_v3_stream)


@fixture(params=['nav_v2_object', 'nav_v3_object'])
def nav_object(request):
    return request.getfixturevalue(request.param)


def test_skip_header_unexpected_end(nav_object):
    # skip header (see conftest.nav_(v2/v3)_steam)
    for i in range(5):
        next(nav_object.stream)
    with raises(
            NavMessageFileError,
            message="Expecting NavMessageFileError",
            match="Unexpected end of the navigation file."
    ):
        nav_object._skip_header()


def test_skip_header(nav_v2_object):
    nav_v2_object._skip_header()
    line = next(nav_v2_object.stream)
    assert line == '''\
 1 16  1  1  0 15  0.0-0.147201120853D-03 0.000000000000D+00 0.300000000000D+02
'''


def test_nav_v2_iter(nav_v2_object):
    # slot, epoch, freq_num
    std = [
        (1, datetime(2016, 1, 1, 0, 15), 1),
        (2, datetime(2016, 1, 1, 0, 15), -4),
        (3, datetime(2016, 1, 1, 0, 15), 5),
        (3, datetime(2016, 1, 1, 0, 15, 2), 5),
        (3, datetime(2016, 1, 1, 2, 15), 6),
    ]
    for i, test in enumerate(nav_v2_object):
        assert test == std[i]


def test_nav_v3_parse_date(nav_v3_object):
    # R01 2017 12 31 00 15 00
    std = datetime(2017, 12, 31, 0, 15, 0)
    line = '''\
R01 2017 12 31 00 15 00 2.002064138651e-05 0.000000000000e+00 0.000000000000e+00
'''
    test = nav_v3_object._parse_date(line)
    assert test == std


def test_nav_v3_iter(nav_v3_object):
    # slot, epoch, freq_num
    std = (
        (1, datetime(2017, 12, 31, 0, 15), 1),
        (6, datetime(2017, 12, 31, 13, 45), -4),
    )
    for i, test in enumerate(nav_v3_object):
        assert test == std[i]


@mark.parametrize(
    "nav_stream,expected_ver,expected_type",
    [
        ('nav_v2_stream', 2.01, 'G'),
        ('nav_v3_stream', 3.03, 'N'),
    ],
    indirect=['nav_stream'],
)
def test_read_version_type(nav_stream, expected_ver, expected_type):
    test_ver, test_type = _read_version_type(nav_stream)
    assert expected_ver == test_ver
    assert expected_type == test_type


def test_read_version_type_error():
    with raises(NavMessageFileError):
        _read_version_type(StringIO('hello'))


@mark.parametrize(
    "nav_stream,nav_class",
    [
        ('nav_v2_stream', NavMessageFileV2),
        ('nav_v3_stream', NavMessageFileV3),
    ],
    indirect=['nav_stream'],
)
def test_nav(nav_stream, nav_class):
    test_nav_obj = nav(nav_stream)
    assert isinstance(test_nav_obj, nav_class)


def test_nav_unknown_ver():
    unknown_version = """\
     7.00           NAVIGATION DATA     M (Mixed)           RINEX VERSION / TYPE
BCEmerge            congo               20180101 012902 GMT PGM / RUN BY / DATE 
    18                                                      LEAP SECONDS        
                                                            END OF HEADER       
"""
    with raises(NavMessageFileError, match='Unsupported version:'):
        nav(StringIO(unknown_version))
