import sys
import argparse
import pathlib

sys.path.append('../')

from gnss_tec import rnx
from gnss_tec.handler import RinexForSpace

if __name__ == '__main__':
    formatter = argparse.ArgumentDefaultsHelpFormatter
    parser = argparse.ArgumentParser(prog='rin2arr', formatter_class=formatter)
    parser.add_argument('--rinex_path', type=pathlib.Path, help='RINEX Path')
    args = vars(parser.parse_args())
    obs_file = args['rinex_path']
    with open(obs_file) as f:
        reader = rnx(f)
        for tec in reader:
            pass
    
    codes = reader.obs_types
    print(codes)
    features = reader.features
    times = reader.timestamps
    observations = reader.rinex_as_array
    ts = [k for k in times]
    freqs = reader.rinex_freqs
    hand = RinexForSpace(observations, codes, features, ts, freqs)
    #hand.calc_phase_tec(('L1C', 'L2L'), s='G')
    hand.define_best_combination()