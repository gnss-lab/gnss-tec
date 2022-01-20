"""Module contains utils to extract GLONASS frequency numbers from navigation
files."""
from collections import defaultdict

from gnss_tec.nav import nav

__all__ = [
    'collect_freq_nums',
    'fetch_slot_freq_num',
    'FetchSlotFreqNumError',
]


class NavigationFileError(Exception):
    pass


class FetchSlotFreqNumError(Exception):
    pass


def _is_string_like(obj):
    """Check whether obj behaves like a string."""
    try:
        obj + ''
    except (TypeError, ValueError):
        return False
    return True


def collect_freq_nums(file):
    """Collect GLONASS frequency numbers from a navigation file.

    Parameters
    ----------
    file : str or file-like object
        filename, file, or iter to read.

    Returns
    -------
    freq_num_timestamps : dict
        {slot_num: {datetime: freq_num, ... }, ...}, where
        slot_num : int
            GLONASS slot number in the constellation.
        datetime : datetime.datetime object
            timestamp
        freq_num : float
            Frequency number of the slot.
    """
    freq_num_timestamps = defaultdict(dict)

    f_own = False
    if _is_string_like(file):
        f_own = True
        file_handler = open(file)
    else:
        file_handler = file

    for slot, epoch, f_num in nav(file_handler):
        if f_num in freq_num_timestamps[slot]:
            continue
        freq_num_timestamps[slot][f_num] = epoch

    if f_own:
        file_handler.close()

    frequency_numbers = defaultdict(dict)
    for slot in freq_num_timestamps:
        f_nums = list(freq_num_timestamps[slot].keys())
        t_stamps = list(freq_num_timestamps[slot].values())
        frequency_numbers[slot] = dict(zip(t_stamps, f_nums))

    del freq_num_timestamps

    # frequency_numbers[<unknown_key>] produces {} so
    # we convert defaultdict to dict to avoid possible errors
    return dict(frequency_numbers)


def fetch_slot_freq_num(timestamp, slot, freq_nums):
    """Find GLONASS frequency number in glo_freq_nums and return it.

    Parameters
    ----------
    timestamp : datetime.datetime
    slot : int
        GLONASS satellite number
    freq_nums : dict
        { slot_1: { datetime_1: freq-num, ... } }

    Returns
    -------
    freq_num : int

    Raises
    ------
    FetchSlotFreqNumError in case we can't find frequency number of the slot.
    """
    freq_num = None

    try:
        slot_freq_nums = freq_nums[slot]
    except KeyError:
        msg = "Can't find slot {} in the glo_freq_nums dict.".format(slot)
        raise FetchSlotFreqNumError(msg)

    dates_times = sorted(slot_freq_nums.keys())
    for ts in dates_times:
        if timestamp >= ts and timestamp.date() == ts.date():
            freq_num = slot_freq_nums[ts]

    if freq_num is not None:
        return freq_num

    timestamp_date = timestamp.date()
    first_date = dates_times[0].date()

    if timestamp_date == first_date:
        freq_num = slot_freq_nums[dates_times[0]]
        return freq_num
    else:
        msg = "Can't find GLONASS frequency number for {}.".format(slot)
        raise FetchSlotFreqNumError(msg)
