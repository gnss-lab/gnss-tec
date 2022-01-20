# coding=utf8
"""Class to compute total electron content."""
from .gnss import *


class TecError(Exception):
    """Class for Tec related errors."""
    pass


class Tec(object):
    """Total electron content object.

    Attributes
    ----------
    timestamp : datetime.datetime instance
        date and time of the observations.
    time_system : str
        time system of the observations.
    satellite : str
        Current satellite, e.g. 'G01'
    glo_freq_num : int
        GLONASS frequency number for the satellite.
    phase : dict
        Phase observation values, {1: 0., 2: 0.}
    phase_code : dict
        Phase observation types, {1: 'C', 2: 'C'}, where 'C' could be something
          like 'L1'.
    signal_strength : int
        Signal strength on the main (e.g. L1) frequency.
    p_range : dict
        pseudorange observations: {1: 0., 2: 0.}
    p_range_code : dict
        pseudorange observation types, {1: 'C', 2: 'C'}, where 'C'
        could be something like 'P1'.
    lli : dict
        Value of the bit 0 of loss of lock indicator (LLI) for the phase
        observation on the band, eg, {1: 1, 2: 0}
    validity : int
        Validity index.
        Bit 0: reserved
        Bit 1: reserved
        Bit 2 set: lli[2] != 0
        Bit 3 set: lli[1] != 0
        Bit 4 set: p_range[2] != 0
        Bit 5 set: p_range[1] != 0
        Bit 6 set: phase[2] != 0
        Bit 7 set: phase[1] != 0
    phase_tec : float
        Phase total electron content value calculated using self.phase data.
        Value will be None if some observations are missing.
    p_range_tec : float
        Pseudorange total electron content value calculated using self.pr data.
        Value will be None if some observations are missing.
    """

    frequency = FREQUENCY

    def __init__(
            self,
            timestamp,
            time_system,
            satellite,
            glo_freq_num=None,
    ):
        """Create a total electron content object.

        Parameters
        ----------
        timestamp : datetime.datetime
            timestamp of observations.
        time_system : str
            Time system used to make obserations, like 'GPS'.
        satellite : str
            Satellite e.g. 'G01'.
        glo_freq_num : int, optional
            Frequency number for the GLONASS slot number in the constellation.
        """
        if satellite[0].upper() == 'R':
            if glo_freq_num is None:
                msg = ('GLO frequency number must be provided'
                       ' to compute TEC values.')
                raise TecError(msg)

        self.timestamp = timestamp
        self.time_system = time_system

        self.satellite = satellite
        self.glo_freq_num = glo_freq_num

        self.phase = {1: 0., 2: 0.}
        self.phase_code = {1: None, 2: None}
        self.signal_strength = 0

        self.p_range = {1: 0., 2: 0.}
        self.p_range_code = {1: None, 2: None}

        self.lli = {1: 0, 2: 0}

    @staticmethod
    def factor(f1, f2):
        """Returns TEC factor."""
        return (1 / 40.308 *
                (f1 ** 2 * f2 ** 2) / (f1 ** 2 - f2 ** 2) * 1.0e-16)

    def get_freq(self, obs_code):
        """Return frequencies regarding to satellite system."""
        sat_sys = self.satellite[0].upper()
        # sat_num = self.satellite[1:]

        if sat_sys not in self.frequency:
            msg = "Unknown satellite system: '{}'"
            msg = msg.format(sat_sys)
            raise TecError(msg)

        freq = {}
        if sat_sys == 'R':
            k = self.glo_freq_num
            for b in 1, 2:
                band = int(obs_code[b][1])
                if band == 3:
                    freq[b] = self.frequency[sat_sys][band]
                else:
                    freq[b] = self.frequency[sat_sys][band](k)
        else:
            for b in 1, 2:
                band = int(obs_code[b][1])
                freq[b] = self.frequency[sat_sys][band]

        return freq

    @property
    def phase_tec(self):
        """Return phase TEC value."""
        speed_of_light = 299792458

        for b in 1, 2:
            if self.phase[b] == 0:
                return None

        freq = self.get_freq(self.phase_code)

        tec_value = (speed_of_light / freq[1] * self.phase[1] -
                     speed_of_light / freq[2] * self.phase[2])

        return self.factor(freq[1], freq[2]) * tec_value

    @property
    def p_range_tec(self):
        """Return pseudorange TEC value."""
        for b in 1, 2:
            if self.p_range[b] == 0:
                return None

        freq = self.get_freq(self.p_range_code)
        return self.factor(freq[1], freq[2]) * (self.p_range[2] -
                                                self.p_range[1])

    @property
    def validity(self):
        validity = 0

        pattern = {
            0: 0,  # reserved
            1: 0,  # reserved
            2: 2 ** 2 if self.lli[2] else 0,  # L/2 LLI (bit 0)
            3: 2 ** 3 if self.lli[1] else 0,  # L/1 LLI (bit 0)
            4: 2 ** 4 if not self.p_range[2] else 0,  # P/2
            5: 2 ** 5 if not self.p_range[1] else 0,  # P/1
            6: 2 ** 6 if not self.phase[2] else 0,  # L/2
            7: 2 ** 7 if not self.phase[1] else 0,  # L/1
        }

        for pos in pattern:
            validity += pattern[pos]

        return validity

    def __str__(self):
        msg = '{} {}: phase TEC: {}, PR TEC: {}'
        msg = msg.format(
            self.timestamp,
            self.satellite,
            self.phase_tec, self.p_range_tec)
        return msg
