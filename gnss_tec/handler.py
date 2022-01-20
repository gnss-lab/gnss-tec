import numpy as np
import pandas as pd
import itertools
from collections import defaultdict
from .gnss import FREQUENCY, BAND_PRIORITY
from .tec import Tec

class RinexHandlerError(Exception):

    pass

class RinexForSpace(object):
    
    def __init__(self, observations, codes, features, times, frequencies, **kwargs):
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
        self.frequencies = frequencies
        self.dataframe = None
        self.dataframes = None
        if kwargs.get('convert_to_pd', False):
            self.dataframes = self._convert_to_dataframes()


    def _convert_to_dataframes(self, make_one=False):
        dataframes = defaultdict(dict)
        for s in self.observations:
            for sat in self.observations[s]:
                if self.observations[s][sat].shape[0] != len(self.times):
                    msg = f'For {sat}  observations and times differs in shape'
                    raise RinexHandlerError(msg)
                for icode, code in enumerate(self.codes[s]):
                    d = {'system': [], 
                        'sat': [], 
                        'time': [],
                        'code': [], 
                        'observable':[], 
                        'feature1': [], 
                        'feature2': [],
                        'frequency': []}
                    d['system'] = [s] * len(self.times)
                    d['sat'] = [sat] * len(self.times)
                    d['code'] = [code] * len(self.times)
                    d['time'] = self.times[:]
                    d['observable']= self.observations[s][sat][:, icode]
                    d['feature1'] = self.features[s][sat][:, icode,0]
                    d['feature2'] = self.features[s][sat][:, icode,1]
                    d['frequency'] = self.frequencies[s][sat][:]
                    dataframes[s][sat] = pd.DataFrame(d)
        if make_one:
            self.dataframe = pd.concat(dataframes)
        return dataframes


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
                glof = self.frequencies[s][iter_sat]
                print(glof.shape, p2.shape)
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
                    

    def calc_phase_tec_pd(self, combination):
        pass
