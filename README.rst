========
gnss-tec
========

gnss-tec is a Python package to reconstruct slant total electron content in the
ionosphere using data provided by global navigation satellite systems (GPS,
GLONASS, etc.). The module uses carrier phase and pseudo-range measurements
from RINEX observation files as input.

********
Features
********

* phase & pseudo-range TEC reconstruction
* RINEX v2.n & 3.n support

*****
Usage
*****

A short usage example::

    from gnss_tec import rnx
    from gnss_tec.glo import collect_freq_nums

    glo_freq_nums = collect_freq_nums('site0390.17g')

    with open('site0390.17o') as obs_file:
        reader = rnx(obs_file, glo_freq_nums=glo_freq_nums)
        for tec in reader:
            print(
                '{} {}: {} {}'.format(
                    tec.timestamp,
                    tec.satellite,
                    tec.phase_tec,
                    tec.p_range_tec,
                )
            )

************
Installation
************

$ pip install gnss-tec

*******
License
*******

Distributed under the terms of the
`MIT <https://github.com/gnss-lab/gnss-tec/blob/master/LICENSE.txt>`_
license, gnss-tec is free and open source software.

Copyright Ilya Zhivetiev, 2019.
