# coding=utf8
"""Classes to read RINEX files."""
import math
import warnings
from collections import namedtuple, defaultdict
from datetime import timedelta

from .dtutils import validate_epoch, get_microsec
from .glo import fetch_slot_freq_num, FetchSlotFreqNumError
from .gnss import *
from .tec import Tec


class ObsFile(object):
    """Create an object to iterate over the records of RINEX observation
    file. The ObsFileV2 object returns Tec instance on each iteration.

    Parameters
    ----------
    file : file-like object
        RINEX v2.n file.
    priority : dict, optional
        {'S': ((1, 2), (1, 5)), ...}, where 'S' it's a satellite system
        (e.g. 'G' for GPS), and the TEC values will be calculated according to
        the sequence of bands ((1, 2), (1, 5)). For GPS, for example, we will
        try to find 'L1' and 'L2' observation values and if it fails, try
        to find 'L1' and 'L5' values.
    glo_freq_nums : dict, optional
        { slot: { datetime.datetime: freq_number, ... }, ... }
        In order to calculate total electron content for the GLONASS data,
        we have to get frequency numbers for each slot in the constellation.
    """

    def __init__(
            self,
            file,
            version=None,
            band_priority=BAND_PRIORITY,
            pr_obs_priority=None,
            glo_freq_nums=None,
    ):
        """"""
        self.fh = file

        if version:
            self.version = version

        self.band_priority = band_priority

        if pr_obs_priority is None:
            # TODO: add fallback to default
            self.pr_obs_priority = {
                system: (('P', 'P'), ('C', 'C'), ('C', 'P'))
                for system in (GPS, GLO, GAL, SBAS, BDS, QZSS, IRNSS)
            }
        else:
            self.pr_obs_priority = pr_obs_priority

        if glo_freq_nums is None:
            self.glo_freq_nums = {}
        else:
            self.glo_freq_nums = glo_freq_nums

        self.obs_types = self.retrieve_obs_types()

        self.time_system = self.retrieve_time_system()
        self.skip_header()

    def skip_header(self):
        """Seek to the line right after 'END OF HEADER' record."""
        try:
            for row in self.fh:
                header_label = self._get_header_label(row)
                if header_label == 'END OF HEADER':
                    break
        except StopIteration:
            warnings.warn("{program}: Couldn't find 'END OF HEADER'")
            raise StopIteration

    def retrieve_obs_types(self):
        pass

    def retrieve_time_system(self):
        """Return a time system value from the header."""
        time_system = None

        try:
            while time_system is None:
                row = next(self.fh)
                header_label = self._get_header_label(row)
                if header_label == 'TIME OF FIRST OBS':
                    time_system = row[48:51]
        except StopIteration:
            warnings.warn("ObsFile: Couldn't find 'TIME OF FIRST OBS'")
            raise StopIteration

        self.fh.seek(0)
        return time_system

    def handle_event(self, epoch_flag, n_of_sats):
        while n_of_sats:
            next(self.fh)
            n_of_sats -= 1

    @staticmethod
    def _get_num_value(obs_set):
        """Return tuple which consists of observation value,
        LLI value and signal strength value."""
        value, lli, sig_strength = obs_set

        value = float(value) if not value.isspace() else 0.0
        lli = int(lli) if not lli.isspace() else 0
        sig_strength = int(sig_strength) if not sig_strength.isspace() else 0

        return value, lli, sig_strength

    @staticmethod
    def _get_header_label(h_row):
        """Return RINEX header label."""
        return h_row[60:].rstrip().upper()


class ObsFileV2(ObsFile):
    """Create an object to iterate over the records of RINEX observation file
    v.2.n. The ObsFileV2 object yields Tec instance on each iteration.
    """

    def __init__(
            self,
            file,
            version=None,
            band_priority=BAND_PRIORITY,
            pr_obs_priority=None,
            glo_freq_nums=None,
    ):
        super(ObsFileV2, self).__init__(
            file,
            version=version,
            band_priority=band_priority,
            pr_obs_priority=pr_obs_priority,
            glo_freq_nums=glo_freq_nums,
        )
        self._obs_types = set(self.obs_types)

    @staticmethod
    def _rfill(line):
        """Return a copy of the line right filled with white spaces to make
        a line of length 80 chars."""
        line = line.rstrip()
        return line + ' ' * (80 - len(line))

    @staticmethod
    def _get_obs_indices(obs_types, band_priority, obs_priority):
        """Return indices from obs_types list according to band_priority
         and obs_priority.

        Parameters
        ----------
        obs_types : list
            List of observation types in a observation file. For example,
            ['L1', 'L2', 'L5', 'C1', 'C2', 'C5', 'P1', 'P2', 'S1', 'S2', 'S5'].
        band_priority : list of lists
            Pairs of the bands, e.g. [[1, 2], [1, 5], ...].
        obs_priority : list of lists
            Pairs of the observation types, e.g. [['P', 'P'], ['C', 'C'], ...]

        Returns
        -------
        indices : tuple of tuples
            Pairs of the indices according to obs_types and band_priority
            lists.
        """
        indices = []

        obs_band_pair = []
        for band in band_priority:
            for obs in obs_priority:
                obs_band_pair.append(zip(band, obs))

        for pair in obs_band_pair:
            combination = []
            for band, obs in pair:
                combination.append('{}{}'.format(obs, band))
            try:
                indices.append(
                    tuple(obs_types.index(o) for o in combination)
                )
            except ValueError:
                continue

        if not indices:
            msg = "Can't find observable."
            raise ValueError(msg)

        return tuple(indices)

    def _parse_epoch_record(self):
        """Parse epoch record

        Returns
        -------
        timestamp : datetime
        epoch_flag : int
        n_of_sats : int
        list_of_sats : list
        """
        row = next(self.fh)

        err_msg = "Can't parse epoch record."

        epoch_flag, n_of_sats = None, None
        try:
            epoch_flag = int(row[26:29])
            n_of_sats = int(row[29:32])
        except ValueError:
            raise ValueError(err_msg)

        if epoch_flag > 1:
            return None, epoch_flag, n_of_sats, None

        timestamp = None
        try:
            sec = float(row[15:26])
            microsec = get_microsec(sec)

            timestamp = [int(row[i:i + 3]) for i in range(0, 13, 3)] + \
                        [int(i) for i in (sec, microsec)]

        except ValueError:
            raise ValueError(err_msg)

        timestamp = validate_epoch(timestamp)

        list_of_sats = row[32:68].rstrip()
        rows_to_read = math.ceil(n_of_sats / 12.) - 1
        if rows_to_read > 0:
            while rows_to_read > 0:
                row = next(self.fh)
                list_of_sats += row[32:68].rstrip()
                rows_to_read -= 1

        list_of_sats = [list_of_sats[i:i + 3] for i in
                        range(0, len(list_of_sats), 3)]

        msg = "Epoch's num of sats != actual num of sats"
        assert len(list_of_sats) == n_of_sats, msg

        return timestamp, epoch_flag, n_of_sats, list_of_sats

    def _split_observations_row(self, observations):
        """Return a list of observations."""
        observations = [observations[i:i + 16] for i in
                        range(0, len(observations), 16)]
        observations = [(o[:14], o[14], o[15]) for o in
                        observations[:len(self.obs_types)]]
        return observations

    def retrieve_obs_types(self):
        """Returns a list which contains types of observations
        from the header."""
        obs_types = None
        num_of_types = 0
        try:
            while not obs_types:
                row = next(self.fh)
                header_label = self._get_header_label(row)
                if header_label == '# / TYPES OF OBSERV':
                    num_of_types = int(row[:6].lstrip())
                    obs_types = row[6:60]
                    if num_of_types > 9:
                        rows_to_read = math.ceil(num_of_types / 9) - 1
                        while rows_to_read > 0:
                            row = next(self.fh)
                            obs_types += row[6:60]
                            rows_to_read -= 1
                    obs_types = obs_types.split()

        except StopIteration:
            warn_msg = ("tec: Can't find '# / TYPES OF OBSERV'; "
                        "unexpected end of the file.")
            warnings.warn(warn_msg)
            raise StopIteration
        except ValueError:
            msg = "tec: Can't extract '# / TYPES OF OBSERV'"
            raise ValueError(msg)

        msg = "Some obs types are missing."
        assert num_of_types == len(obs_types), msg

        self.fh.seek(0)
        return obs_types

    def next_tec(self):
        """Yields Tec object."""
        while 1:
            (timestamp,
             epoch_flag,
             n_of_sats,
             list_of_sats) = self._parse_epoch_record()

            if epoch_flag > 1:
                self.handle_event(epoch_flag, n_of_sats)
                continue

            phase_obs_code = dict()
            phase_obs_index = dict()
            pr_obs_code = dict()
            pr_obs_index = dict()

            for satellite in list_of_sats:
                if satellite[0] == ' ':
                    satellite = 'G{}'.format(satellite[1:])

                sat_sys = satellite[0].upper()

                observations_row = self._rfill(next(self.fh))
                rows_to_read = math.ceil(len(self.obs_types) / 5.) - 1

                while rows_to_read > 0:
                    observations_row += self._rfill(next(self.fh))
                    rows_to_read -= 1

                observations = self._split_observations_row(observations_row)

                freq_num = None
                try:
                    if sat_sys == GLO:
                        slot = int(satellite[1:])
                        freq_num = fetch_slot_freq_num(
                            timestamp,
                            slot,
                            self.glo_freq_nums,
                        )
                except FetchSlotFreqNumError as err:
                    warnings.warn(str(err))
                    continue

                # TODO: обернуть в одну ф-цию
                try:
                    if sat_sys not in phase_obs_index:
                        indices = self._get_obs_indices(
                            self.obs_types,
                            self.band_priority[sat_sys],
                            (('L', 'L'),),
                        )
                        phase_obs_index[sat_sys] = dict(
                            zip([1, 2], indices[0])
                        )

                    if sat_sys not in phase_obs_code:
                        phase_obs_code[sat_sys] = {
                            1: self.obs_types[phase_obs_index[sat_sys][1]],
                            2: self.obs_types[phase_obs_index[sat_sys][2]],
                        }

                    if sat_sys not in pr_obs_index:
                        indices = self._get_obs_indices(
                            self.obs_types,
                            self.band_priority[sat_sys],
                            self.pr_obs_priority[sat_sys],
                        )
                        pr_obs_index[sat_sys] = dict(
                            zip([1, 2], indices[0])
                        )

                    if sat_sys not in pr_obs_code:
                        pr_obs_code[sat_sys] = {
                            1: self.obs_types[pr_obs_index[sat_sys][1]],
                            2: self.obs_types[pr_obs_index[sat_sys][2]]
                        }
                except ValueError:
                    msg = ("Can't find observable to calculate TEC "
                           "using '{}' system.")
                    msg = msg.format(sat_sys)
                    warnings.warn(msg)
                    continue

                tec = Tec(
                    timestamp,
                    self.time_system,
                    satellite,
                    freq_num,
                )

                tec.phase_code = phase_obs_code[sat_sys]
                tec.p_range_code = pr_obs_code[sat_sys]

                sig_strength = {1: None, 2: None}
                for b in 1, 2:
                    obs = observations[phase_obs_index[sat_sys][b]]
                    obs = self._get_num_value(obs)
                    tec.phase[b] = obs[0]
                    tec.lli[b] = obs[1] & 1  # bit 0 only
                    sig_strength[b] = obs[2]

                tec.signal_strength = sig_strength[1]

                for b in 1, 2:
                    obs = observations[pr_obs_index[sat_sys][b]]
                    obs = self._get_num_value(obs)
                    tec.p_range[b] = obs[0]

                yield tec

    def __iter__(self):
        return self.next_tec()


class ObsFileV3(ObsFile):
    """Create an object to iterate over the records of RINEX observation
    file. Yields Tec object on each iteration."""

    phase_code = 'L'
    prange_code = 'C'

    bands = {
        GPS: (1, 2, 5),
        GLO: (1, 2, 3),
        GAL: (1, 5, 6, 7, 8),
        BDS: (2, 6, 7),
        SBAS: (1, 5),
        QZSS: (1, 2, 5, 6),
        IRNSS: (5, 9),
    }

    channels = {
        GPS: {
            1: 'CSLXPWYMN',
            2: 'CDSLXPWYMN',
            5: 'IQX',
        },
        GLO: {
            1: 'CP',
            2: 'CP',
            3: 'IQX',
        },
        GAL: {
            1: 'ABCXZ',
            5: 'IQX',
            6: 'ABCXZ',
            7: 'IQX',
            8: 'IQX',
        },
        BDS: {
            2: 'IQX',
            6: 'IQX',
            7: 'IQX',
        },
        SBAS: {
            1: 'C',
            5: 'IQX',
        },
        QZSS: {
            1: 'CSLXZ',
            2: 'SLX',
            5: 'IQX',
            6: 'SLX',
        },
        IRNSS: {
            5: 'ABCX',
            9: 'ABCX',
        }
    }

    def __init__(
            self,
            file,
            version=None,
            band_priority=BAND_PRIORITY,
            pr_obs_priority=None,
            glo_freq_nums=None,
    ):
        super(ObsFileV3, self).__init__(
            file,
            version=version,
            band_priority=band_priority,
            pr_obs_priority=pr_obs_priority,
            glo_freq_nums=glo_freq_nums,
        )
        self.obs_rec_indices = self._obs_slice_indices()

        self.phase_obs_codes = None
        self.prange_obs_codes = None

        self._generate_obs_codes()

        self._observation = namedtuple(
            'observation',
            ['code', 'value', 'lli', 'signal_strength']
        )
        self._observation_records = namedtuple(
            'observation_records',
            ['satellite', 'records']
        )
        self._obsrevation_indices = namedtuple(
            'observation_indices',
            ['phase', 'pseudo_range'],
        )

    def _generate_obs_codes(self):
        """Generate observation codes for the satellite systems."""
        self.phase_obs_codes = defaultdict(dict)
        self.prange_obs_codes = defaultdict(dict)

        v3_sat_systems = GPS, GLO, GAL, BDS, SBAS, QZSS, IRNSS
        obs_code_fmt = '{code}{band}{channel}'

        for sat_system in v3_sat_systems:
            for band in ObsFileV3.bands[sat_system]:
                phase_obs_codes = list()
                prange_obs_codes = list()

                for channel in ObsFileV3.channels[sat_system][band]:
                    phase_obs_codes.append(
                        obs_code_fmt.format(
                            code=ObsFileV3.phase_code,
                            band=band,
                            channel=channel,
                        )
                    )

                    prange_obs_codes.append(
                        obs_code_fmt.format(
                            code=ObsFileV3.prange_code,
                            band=band,
                            channel=channel,
                        )
                    )

                self.phase_obs_codes[sat_system][band] = \
                    tuple(phase_obs_codes)

                self.prange_obs_codes[sat_system][band] = \
                    tuple(prange_obs_codes)

    def __iter__(self):
        return self.next_tec()

    def _obs_slice_indices(self):
        """Return indices to slice observation record into single observations.

        Returns
        -------
        indices : tuple
        """
        obs_amount = [len(self.obs_types[d]) for d in self.obs_types]
        max_obs_num = max(obs_amount)

        rec_len = 16

        start = 3
        stop = max_obs_num * rec_len
        indices = [[i, i + rec_len] for i in range(start, stop, rec_len)]

        return tuple(indices)

    @staticmethod
    def _is_epoch_record(row):
        return True if row[0] == '>' else False

    @staticmethod
    def _parse_epoch_record(row):
        """Parse epoch record"""

        # month, day, hour, min
        epoch = [row[i:i + 3] for i in range(6, 17, 3)]
        # year + ...
        epoch = [row[1:6]] + epoch
        sec = row[18:29]

        try:
            sec = float(sec)
            micro_sec = get_microsec(sec)

            epoch += [sec, micro_sec]
            epoch = list(map(int, epoch))

            epoch = validate_epoch(epoch)
        except ValueError:
            epoch = None

        epoch_flag = int(row[31])
        num_of_sat = int(row[32:35])

        try:
            sec = float(row[42:])
            micro_sec = get_microsec(sec)
            clock_offset = timedelta(0, int(sec), int(micro_sec))
        except ValueError:
            clock_offset = timedelta(0)

        return epoch, epoch_flag, num_of_sat, clock_offset

    def _parse_obs_record(self, row):
        """Parse observation record

        Parameters
        ----------
        row : str

        Returns
        -------
        sat : str
            satellite
        obs_values : tuple
            (obs_values_1, ..., obs_values_n)
            with obs_values_x = (obs_value, lli_value, sig_strength_value)
        """

        sat = row[0:3]
        sat = sat.replace(' ', '0')
        sat_system = sat[0]

        if sat_system not in self.obs_types:
            msg = ('There is no such satellite system definition '
                   'in the header: {ss}.')
            raise ValueError(msg.format(ss=sat_system))

        records = []
        obs_num = len(self.obs_types[sat_system])

        for n in range(obs_num):
            s, e = self.obs_rec_indices[n]
            chunk = row[s:e]
            code = self.obs_types[sat_system][n]

            if not chunk or chunk.isspace():
                records.append(self._observation(code, 0, 0, 0))
                continue

            val = chunk[:14]
            try:
                if not val or val.isspace():
                    val = 0.0
                else:
                    val = float(val)
            except ValueError:
                val = 0.0

            feature = []
            for i in 14, 15:
                try:
                    v = chunk[i]
                    if v.isspace():
                        v = 0
                    else:
                        v = int(v)
                except (IndexError, ValueError):
                    v = 0
                feature.append(v)

            obs = self._observation(
                code,
                val,
                feature[0],
                feature[1],
            )
            records.append(obs)

        return self._observation_records(sat, tuple(records))

    def retrieve_obs_types(self):
        """Return types of observations."""
        obs_types_rows = ''
        try:
            header_label = ''
            while header_label != 'END OF HEADER':
                row = next(self.fh)
                header_label = self._get_header_label(row)
                if header_label == 'SYS / # / OBS TYPES':
                    obs_types_rows += row

        except StopIteration:
            warn_msg = (
                "tec: Can't find 'SYS / # / OBS TYPES'; "
                "unexpected end of the file."
            )
            warnings.warn(warn_msg)
            raise StopIteration

        obs_types_records = []
        for line in obs_types_rows.split('\n'):
            if not line or line.isspace():
                continue

            if line[0:6].isspace():
                obs_types_records[-1] += line[7:60]
            else:
                obs_types_records.append(line[:60])

        del obs_types_rows

        obs_types = {}
        try:
            for record in obs_types_records:
                record = record.split()

                sat_sys = record[0]
                num_of_obs = int(record[1])
                sys_obs_types = tuple(record[2:])

                # misunderstanding with band #1 in Compass/BeiDou
                # see RINEX v3.n format for the details
                if self.version >= 3.02 and sat_sys == BDS:
                    corrected_obs_types = list(sys_obs_types)
                    for i, t in enumerate(corrected_obs_types):
                        if t[1] == '1':
                            t = t.replace('1', '2')
                            corrected_obs_types[i] = t
                    sys_obs_types = tuple(corrected_obs_types)

                warn_msg = (
                    'ObsFileV3: '
                    'Wrong number of observations {ot} (expected {n}).'
                )
                assert len(sys_obs_types) == num_of_obs, \
                    warn_msg.format(ot=len(sys_obs_types), n=num_of_obs)

                obs_types[sat_sys] = sys_obs_types

        except ValueError as err:
            print(err)
            raise err

        del obs_types_records

        self.fh.seek(0)
        return obs_types

    def indices_according_priority(self, sat_system):
        """Return obs_types indices according band priority."""

        def code(current_codes, all_codes):
            union = set(current_codes) & set(all_codes)
            return [all_codes.index(c) for c in union]

        def indices(b_priority, ot_indices):
            for first_band, second_band in b_priority:
                if ot_indices[first_band] and ot_indices[second_band]:
                    return {
                        1: ot_indices[first_band][0],
                        2: ot_indices[second_band][0],
                    }
            msg = "Can't find any observations to calculate TEC."
            raise ValueError(msg)

        obs_types = self.obs_types[sat_system]

        bands = self.bands[sat_system]
        band_priority = self.band_priority[sat_system]

        phase_obs_codes = self.phase_obs_codes[sat_system]
        pr_obs_codes = self.prange_obs_codes[sat_system]

        phase_ot_indices = dict(
            zip(bands, (None,) * 3)
        )
        pr_ot_indices = dict(
            zip(bands, (None,) * 3)
        )

        for b in bands:
            phase_ot_indices[b] = code(phase_obs_codes[b], obs_types)
            pr_ot_indices[b] = code(pr_obs_codes[b], obs_types)

        phase_indices = indices(band_priority, phase_ot_indices)
        pr_indices = indices(band_priority, pr_ot_indices)

        return self._obsrevation_indices(phase_indices, pr_indices)

    def next_tec(self):
        """Yields Tec object."""
        obs_indices = {}

        while True:
            row = next(self.fh)

            if not self._is_epoch_record(row):
                msg = 'Unexpected format of the record: {row}'
                raise ValueError(msg.format(row=row))

            (timestamp,
             epoch_flag,
             num_of_sat,
             clock_offset) = self._parse_epoch_record(row)

            if epoch_flag > 1:
                self.handle_event(epoch_flag, num_of_sat)
                continue

            while num_of_sat:
                num_of_sat -= 1
                row = next(self.fh)

                observations = self._parse_obs_record(row)
                sat_sys = observations.satellite[0]

                freq_num = None
                if sat_sys == GLO:
                    try:
                        freq_num = fetch_slot_freq_num(
                            timestamp,
                            int(observations.satellite[1:]),
                            self.glo_freq_nums,
                        )
                    except FetchSlotFreqNumError as err:
                        warnings.warn(str(err))
                        continue

                tec = Tec(
                    timestamp,
                    self.time_system,
                    satellite=observations.satellite,
                    glo_freq_num=freq_num,
                )

                try:
                    if sat_sys not in obs_indices:
                        obs_indices[sat_sys] = (
                            self.indices_according_priority(sat_sys)
                        )
                except ValueError as err:
                    # TODO: add logger (info)
                    continue

                for b in 1, 2:
                    obs = observations.records[obs_indices[sat_sys].phase[b]]
                    tec.phase_code[b] = obs.code
                    tec.phase[b] = obs.value
                    tec.lli[b] = obs.lli & 1

                    obs = observations.records[
                        obs_indices[sat_sys].pseudo_range[b]]
                    tec.p_range_code[b] = obs.code
                    tec.p_range[b] = obs.value

                yield tec
