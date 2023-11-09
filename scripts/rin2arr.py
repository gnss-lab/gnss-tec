import sys
import argparse
import pathlib
import matplotlib.pyplot as plt
import time

sys.path.append('../')

from gnss_tec import rnx
from gnss_tec.handler import RinexForSpace
from gnss_tec.glo import collect_freq_nums


if __name__ == '__main__':
    formatter = argparse.ArgumentDefaultsHelpFormatter
    parser = argparse.ArgumentParser(prog='rin2arr', formatter_class=formatter)
    parser.add_argument('--rinex_path', type=pathlib.Path, help='RINEX Path')
    parser.add_argument('--nav_path', type=pathlib.Path, help='NAV Path')
    args = vars(parser.parse_args())
    obs_file = str(args['rinex_path'])
    nav_file = str(args['nav_path'])
    glo_freq_nums = collect_freq_nums(nav_file)
    with open(obs_file) as f:
        reader = rnx(f, glo_freq_nums=glo_freq_nums)    
        for tec in reader:
            pass
    hand = RinexForSpace.rnx_to_handler(reader)
    hand._convert_to_dataframes()

    hand.calc_tec_pd({'C': [('C2I', 'C6I')]})
    hand.calc_tec_pd({'C': [('L2I', 'L6I')]})
    hand.define_best_combination()