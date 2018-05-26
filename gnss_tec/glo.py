"""Module contains utils to extract GLONASS frequency numbers from navigation
files."""
import warnings
from collections import defaultdict

from .dtutils import validate_epoch, get_microsec

__all__ = [
    'collect_freq_nums',
    'fetch_slot_freq_num',
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


def _skip_header(file):
    while 1:
        try:
            line = next(file)
            if line[60:].rstrip() == 'END OF HEADER':
                break
        except StopIteration:
            msg = "{p}: Unexpected end of the file: {}."
            msg = msg.format('_skip_header', str(file))
            warnings.warn(msg)


def _next_nav_mgs(file):
    """Iterate over lines of the file and yield slot, epoch and frequency
    number for each navigation message.

    Parameters
    ----------
    file : file-like object

    Returns
    -------
    generator iterator which yields tuple (slot, epoch, frequency_number),
    where

    slot : int
        GLONASS slot number

    epoch : datetime.datetime object
        epoch of the navigation message

    frequency_number : float
        GLONASS slot's frequency number
    """
    while 1:
        try:
            prn_epoch_sv_clk = next(file)

            slot_num = int(prn_epoch_sv_clk[:2])

            sec = float(prn_epoch_sv_clk[17:22])
            microsec = get_microsec(sec)

            timestamp = [
                int(prn_epoch_sv_clk[i:i + 3])
                for i in range(2, 17, 3)
            ]
            timestamp += [int(i) for i in (sec, microsec)]

            epoch = validate_epoch(timestamp)

            orbits = ''
            rows_to_read = 3
            while rows_to_read > 0:
                rows_to_read -= 1
                line = next(file)
                line = line[3:].rstrip()
                orbits += line

            data = [orbits[i:i + 19].lower() for i in range(0, 228, 19)]
            data = [val.replace('d', 'e') for val in data]

            yield slot_num, epoch, float(data[7])

        except StopIteration:
            break


def _read_version_type(file_handler):
    file_handler.seek(0)
    line = file_handler.readline()

    try:
        rnx_ver, rnx_type = float(line[0:10]), line[20]
    except (IndexError, ValueError) as err:
        msg = "Can't read navigation file: {error}".format(error=err)
        raise NavigationFileError(msg)

    return rnx_ver, rnx_type


def collect_freq_nums(file):
    """Collect GLONASS frequency numbers from a navigation file.

    Parameters
    ----------
    file : str or file-like object
        filename, file, or generator to read.

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
    f_own = False
    if _is_string_like(file):
        f_own = True
        file_handler = open(file)
    else:
        file_handler = file

    try:
        rnx_version, rnx_type = _read_version_type(file_handler)

        if rnx_version > 2.11:
            msg = ("Can't read the file: "
                   "version {version} is unsupported.").format(
                version=rnx_version,
            )
            raise NavigationFileError(msg)

        if rnx_type != 'G':
            msg = ("Can't read the file: "
                   "type {type} is unsupported.").format(
                type=rnx_type,
            )
            raise NavigationFileError(msg)

        _skip_header(file_handler)

        freq_num_timestamps = defaultdict(dict)
        for slot, epoch, f_num in _next_nav_mgs(file_handler):
            if f_num in freq_num_timestamps[slot]:
                continue
            freq_num_timestamps[slot][f_num] = epoch

    finally:
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
