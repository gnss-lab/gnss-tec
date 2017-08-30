"""Various utils to work with date/time."""
import datetime


def get_microsec(sec):
    """Return microsecond value from fractional part of the sec."""
    microsec = (sec - int(sec)) * 1e+6
    microsec = float("%.5f" % microsec)
    return microsec


def validate_epoch(epoch):
    """Return datetime.datetime object using values from epoch list.

    Do some checks:
    - sometimes the seconds or minutes value >= 60, to return datetime.datetime
      we need to check this;
    - converts YY to YYYY (datetime.datetime treats 92 and 1992 in different
      ways.

    Parameters
    ----------
    epoch : list
        epoch = [year, month, day, hour, min, sec, microsec]

    Returns
    -------
    datetime : datetime.datetime
    """
    epoch = epoch[:]

    # YY -> YYYY
    if epoch[0] < 100:
        if epoch[0] >= 89:
            epoch[0] += 1900
        elif epoch[0] < 89:
            epoch[0] += 2000

    delta = datetime.timedelta(0)

    # epoch[-2] - seconds; epoch[-3] - minutes
    # we do all calculation in seconds so we use multiplier
    for i, ier in [(-2, 1), (-3, 60)]:
        if 60 <= epoch[i] <= 120:
            sec = (epoch[i] - 59) * ier
            delta += datetime.timedelta(seconds=sec)
            epoch[i] = 59

    epoch = datetime.datetime(*epoch) + delta

    return epoch
