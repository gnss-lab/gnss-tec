import numpy as np
import pandas as pd
import warnings
from collections import defaultdict
from .gnss import FREQUENCY, BAND_PRIORITY
from .tec import Tec
from .glo import collect_freq_nums
from .rinex import ObsFileV3

class RinexHandlerError(Exception):
    pass

class RinexHandlerObservableCodes(Exception):
    pass

class RinexHandlerReaderNotSupport(Exception):
    pass

class RinexHandlerCouldNotAddFiled(Exception):
    pass


class RinexForSpace(object):
    
    def __init__(self, observations, codes, features, times, glofreqnums, **kwargs):
        """Wrapper for rinex as a pandas dataframes

        Parameters
        ----------
        observations : dict
        Keys are letter for system see gnss.py. Values are dicts where keys
        are sat names and values are numpy array with shape (ntimes, ncodes)
        
        codes : dict
        Keys are letter for system see gnss.py. Values are list of codes
        observed
        
        features : dict
        Keys are letter for system see gnss.py. Values are dicts where keys
        are sat names and values are numpy array with shape (ntimes, ncodes, 2)
        
        times : list
        List of times of observations (first dimension of observation is the 
        same as len(times)
        """
        self.observations = observations
        self.codes = codes
        self.features = features
        self.times = times
        self.glofreqnums = glofreqnums
        self.dataframes = dict()
        self.calculations = []
        if kwargs.get('convert_to_pd', False):
            self._convert_to_dataframes()
            
    @staticmethod
    def rnx_to_handler(reader):
        if not type(reader) is ObsFileV3:
            raise RinexHandlerReaderNotSupport()
        codes = reader.obs_types
        features = reader.features
        times = reader.timestamps
        observations = reader.rinex_as_array
        glofn = reader.rinex_glofreqnum
        ts = [k for k in times]
        hand = RinexForSpace(observations, codes, features, ts, glofn)
        return hand

    def _convert_to_dataframes(self):
        dataframes = defaultdict(dict)
        for s in self.observations:
            for sat in self.observations[s]:
                obs_shape = self.observations[s][sat].shape[0]
                time_shape = len(self.times)
                if self.observations[s][sat].shape[0] != len(self.times):
                    msg = f'For {sat}  observations and times differs in ' \
                        f'shape {obs_shape} and {time_shape}'
                    raise RinexHandlerError(msg)
                d = {'system': [], 
                     'sat': [], 
                     'time': [],
                     'glofreqnum': []}
                d['system'] = [s] * len(self.times)
                d['sat'] = [sat] * len(self.times)
                d['time'] = self.times[:]
                d['glofreqnum'] = self.glofreqnums[s][sat][:]
                for icode, code in enumerate(self.codes[s]):
                    d.update({code: [], 'fe1'+code: [], 'fe2'+code: []})
                    d[code]= self.observations[s][sat][:, icode]
                    d['fe1'+code] = self.features[s][sat][:, icode,0]
                    d['fe2'+code] = self.features[s][sat][:, icode,1]
                    dataframes[s][sat] = pd.DataFrame(d)
            dfs = [df for df in dataframes[s].values()]
            if len(dfs) == 0:
                warnings.warn(f'For system {s} there are no data')
            else:
                self.dataframes[s] = pd.concat(dfs)

    def calc_phase_tec(self, combination, sat=None, s=None):
        """
        combination : tuple
        pair of codes to calculate phase TECc_phase_tec
        """
        if sat is None and s is None:
            raise RinexHandlerError('Define sat or system')
        if sat:
            sats = [sat]
            s = sat[0].upper()
        else:
            sats = [k for k in self.observations[s]]
        for s in self.observations:
            if not combination[0] in self.codes[s] or not combination[1] in self.codes[s]:
                continue

            icode1 = self.codes[s].index(combination[0])
            icode2 = self.codes[s].index(combination[1])
            for iter_sat in self.observations[s]:
                p1 = self.observations[s][iter_sat][:, icode1]
                p2 = self.observations[s][iter_sat][:, icode2]
                glof = self.glofreqnums[s][iter_sat]
                
                tec = Tec.calc_phase_tec(p1, p2, 
                                         combination[0], combination[1], 
                                         iter_sat, glof)
    
    
    def define_best_combination(self):
        sats = {s: list(d.keys()) for s, d in self.observations.items()}
        phase_codes = {'c': {}, 'n': {}}
        prange_codes = {'c': {}, 'n': {}}
        avails = {'p': {}, 'r': {}}
        all_comb = {'p': {}, 'r': {}}
        for s in sats:
            sats[s].sort()
            phase_codes['n'][s] = {c: 0 for c in self.codes[s] if c[0] == 'L'}
            prange_codes['n'][s] = {c: 0 for c in self.codes[s] if c[0] == 'C'}
            phase_codes['c'][s] = [c for c in self.codes[s] if c[0] == 'L']
            prange_codes['c'][s] = [c for c in self.codes[s] if c[0] == 'C']
            for o, _codes in zip(['p', 'r'], [phase_codes, prange_codes]):
                avails[o][s] = {}
                all_comb[o][s] = []
                for i, c in enumerate(_codes['c'][s]):
                    for _c in _codes['c'][s][i+1:]:
                        all_comb[o][s].append((c, _c))
                for sat in sats[s]:
                    for code in _codes['c'][s]:
                        ic = self.codes[s].index(code)
                        data = self.observations[s][sat][:, ic]
                        _codes['n'][s][code] = np.count_nonzero(data)
                        avails[o][s]
                    avail = {b:[] for b in BAND_PRIORITY[s]}
                    avails[o][s][sat] = avail
                    for comb in all_comb[o][s]:
                        b = (int(comb[0][1]), int(comb[1][1]))
                        if not b in avail:
                            continue
                        c1, c2  = comb
                        n = (_codes['n'][s][c1], _codes['n'][s][c2])
                        avail[b].append((comb, min(n)))
                    if o == 'r':
                        print(sat)
                        for _o in ['p', 'r']:
                            for b in avails[_o][s][sat]:
                                print(b, avails[_o][s][sat][b])
                    #for code in prange_codes[s]:
                    #    ic = self.codes[s].index(code)
                    #    data = self.observations[s][sat][:, ic]
                    #   prange_codes[s][code] = np.count_nonzero(data)
                    

    def add_column(self, sat, data, col_name):
        """
        Parameters
        ----------
        sat : String
        Three symbol sat name
        
        data : dict
        Keys are datetimes and values are number (float or int)
        
        col_name : String
        Name of column to be added
        """
        if not self.dataframes:
            raise RinexHandlerCouldNotAddFiled('Calculate dataframes first')
        s = sat[0].upper()
        if not s in self.dataframes:
            raise RinexHandlerCouldNotAddFiled(f'Unknow system {s}')
        if not sat in set(self.dataframes[s]['sat']):
            raise RinexHandlerCouldNotAddFiled(f'{sat} not in dataframe')
        if not col_name in self.dataframes[s]:
            self.dataframes[s][col_name] = 0
        sdf = self.dataframes[s]
        sdf.loc[sdf['sat'] == sat, col_name] = \
            sdf.loc[sdf['sat'] == sat]['time'].map(data)
        
    def get_times(self, sat):
        if not self.dataframes:
            raise RinexHandlerCouldNotAddFiled('Calculate dataframes first')
        s = sat[0].upper()
        if not s in self.dataframes:
            raise RinexHandlerCouldNotAddFiled(f'Unknow system {s}')
        if not sat in set(self.dataframes[s]['sat']):
            return []
        sdf = self.dataframes[s]
        ts = [d.to_pydatetime() for d in sdf.loc[sdf['sat'] == sat]['time']]
        return ts

    def get_sats(self):
        sats = dict()
        for s in self.dataframes:
            sats[s] = list(set(self.dataframes[s]['sat']))
        return sats


    def calc_tec_pd(self, combinations):
        """Calculates phase tec 

        Parameters
        ----------
        combination : dict of list of tuples
        Keys are system letter. Values are list each element of which is 
        a pair of codes.
        
        Example: {G: [(L1, L2), (L2, L5)], C: [(L2I, L7I)]}
        """
        tec_type = defaultdict(list)
        calculated = defaultdict(dict)
        for s, comb in combinations.items():
            for c in comb:
                if len(c) != 2:
                    msg = f'Need exact 2 codes, {c} given for {s}'
                    raise RinexHandlerObservableCodes(msg)
                comb_type = c[0][0] + c[1][0]
                phase_range_codes = [ObsFileV3.phase_code, ObsFileV3.prange_code]
                if c[0][0] != c[1][0] and not c[0][0] in phase_range_codes:
                    msg = f'Calculation for obs {comb_type} is not defined. '
                    msg += f'Only {phase_range_codes} are defined'
                    raise RinexHandlerObservableCodes(msg)
                if c[0][0] == ObsFileV3.phase_code:
                    tec_type[s].append('phase')
                if c[0][0] == ObsFileV3.prange_code:
                    tec_type[s].append('range')
        for s in self.dataframes:
            if not s in combinations:
                continue
            sdf = self.dataframes[s]
            codes = combinations[s]
            sats  = list(set(list(self.dataframes[s]['sat'])))
            for ipair, pair in enumerate(codes):
                if not (pair[0] in self.dataframes[s] and 
                        pair[1] in self.dataframes[s]):
                    calculated[s][pair] = [None for sat in sats]
                    warnings.warn(f'Could not calculate {pair}, check codes.')
                    continue
                tec_code = 'tec'+pair[0]+pair[1]
                if tec_type[s][ipair] == 'phase':
                    calc_tec = Tec.calc_phase_tec
                else:
                    calc_tec = Tec.calc_p_range_tec
                self.dataframes[s][tec_code] = 0
                sats_calculated = []
                for sat in sats:
                    obs1 = sdf.loc[sdf['sat'] == sat][pair[0]]
                    obs2 = sdf.loc[sdf['sat'] == sat][pair[1]]
                    glofn = sdf.loc[sdf['sat'] == sat]['glofreqnum']
                    tecs =  calc_tec(obs1, obs2, 
                                     pair[0], pair[1], 
                                     sat, glofn)
                    sdf.loc[sdf['sat'] == sat, tec_code] = tecs
                    sats_calculated.append(sat)
                calculated[s][pair] = sats_calculated
        self.calculations.append(calculated)