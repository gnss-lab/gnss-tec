# coding=utf8
"""
GNSS codes and frequencies.
"""
from types import MappingProxyType

GPS = 'G'
GLO = 'R'
GAL = 'E'
QZSS = 'J'
BDS = 'C'
SBAS = 'S'
IRNSS = 'I'

NNSS = 'T'
MIX = 'M'

# Hz
FREQUENCY = MappingProxyType({
    GPS: {
        1: 1575.42e+06,
        2: 1227.60e+06,
        5: 1176.45e+06,
    },

    GLO: {
        1: lambda k: 1602e+06 + k * 562.5e+03,
        2: lambda k: 1246e+06 + k * 437.5e+03,
        3: 1202.025e+06,
    },

    GAL: {
        1: 1575.420e+06,
        5: 1176.450e+06,
        7: 1207.140e+06,
        8: 1191.795e+06,
        6: 1278.750e+06,
    },

    SBAS: {
        1: 1575.42e+06,
        5: 1176.45e+06,
    },

    QZSS: {
        1: 1575.42e+06,
        2: 1227.60e+06,
        5: 1176.45e+06,
        6: 1278.75e+06,
    },

    BDS: {
        2: 1561.098e+06,
        7: 1207.14e+06,
        6: 1268.52e+06,
    },

    IRNSS: {
        5: 1176.45e+06,
        9: 2492.028e+06,
    },
})

BAND_PRIORITY = MappingProxyType({
    GPS: ((1, 2), (1, 5)),
    GLO: ((1, 2), (1, 3)),
    GAL: ((1, 5), (1, 7), (1, 8), (1, 6)),
    SBAS: ((1, 5),),
    QZSS: ((1, 2), (1, 5), (1, 6)),
    BDS: ((2, 7), (2, 6)),
    IRNSS: ((5, 9),),
})
