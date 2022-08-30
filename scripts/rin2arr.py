import sys
import argparse
import pathlib
import matplotlib.pyplot as plt

sys.path.append('../')

from gnss_tec import rnx
from gnss_tec.handler import RinexForSpace
from gnss_tec.glo import collect_freq_nums


if __name__ == '__main__':
    formatter = argparse.ArgumentDefaultsHelpFormatter
    parser = argparse.ArgumentParser(prog='rin2arr', formatter_class=formatter)
    parser.add_argument('--rinex_path', type=pathlib.Path, help='RINEX Path')
    args = vars(parser.parse_args())
    obs_file = args['rinex_path']
    nav_file = args['nav_path']
    glo_freq_nums = collect_freq_nums(nav_file)
    with open(obs_file) as f:
        reader = rnx(f, glo_freq_nums=glo_freq_nums)
        for tec in reader:
            pass
    
    codes = reader.obs_types
    print(codes)
    features = reader.features
    times = reader.timestamps
    observations = reader.rinex_as_array
    ts = [k for k in times]
    glofn = reader.rinex_glofreqnum
    hand = RinexForSpace(observations, codes, features, ts, glofn)
    hand._convert_to_dataframes()

    hand.calc_tec_pd({'C': [('C2I', 'C6I')]}, tec_type='range')
    hand.calc_tec_pd({'C': [('L2I', 'L6I')]}, tec_type='phase')
    hand.define_best_combination()