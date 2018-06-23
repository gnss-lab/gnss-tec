"""Classes dealing with navigation messages file."""

from gnss_tec.dtutils import get_microsec, validate_epoch


class NavMessageFileError(Exception):
    pass


class NavMessageFileV2:
    """Iterate over lines of the file and yield slot, epoch and frequency
    number for each navigation message.

    Parameters
    ----------
    stream : file-like object

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

    def __init__(self, stream):
        self.stream = stream

    def _skip_header(self):
        while 1:
            try:
                line = next(self.stream)
                if line[60:].rstrip() == 'END OF HEADER':
                    return
            except StopIteration:
                raise NavMessageFileError(
                    "Unexpected end of the navigation file."
                )

    def __iter__(self):
        self._skip_header()
        while 1:
            try:
                prn_epoch_sv_clk = next(self.stream)

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
                    line = next(self.stream)
                    line = line[3:].rstrip()
                    orbits += line

                data = [orbits[i:i + 19].lower() for i in range(0, 228, 19)]
                data = [val.replace('d', 'e') for val in data]

                yield slot_num, epoch, float(data[7])
            except StopIteration:
                return


class NavMessageFileV3(NavMessageFileV2):
    def __iter__(self):
        self._skip_header()
        while 1:
            try:
                line = next(self.stream)
                if not line[0] in 'rR':
                    continue

                slot = int(line[1:3])
                epoch = self._parse_date(line)

                next(self.stream)

                line = next(self.stream).lower()
                freq_num = float(line[61:].replace('d', 'e'))

                yield slot, epoch, freq_num
            except StopIteration:
                return

    @staticmethod
    def _parse_date(line):
        # year + month day hour min sec
        epoch = [int(line[4:8])]
        epoch += [int(line[i:i + 3]) for i in range(8, 21, 3)]
        # add microsec needed for validate_epoch
        epoch.append(0)
        return validate_epoch(epoch)


def _read_version_type(file):
    file.seek(0)
    line = file.readline()
    try:
        rnx_ver, rnx_type = float(line[0:10]), line[20]
    except (IndexError, ValueError) as err:
        msg = "Can't read navigation file: {error}".format(error=err)
        raise NavMessageFileError(msg)
    return rnx_ver, rnx_type


def nav(file):
    """
    NavMessageFile factory. Return an instance of NavMessageFileV2 or
    NavMessageFileV3 depending on RINEX version in the ``file``.

    Parameters
    ----------
    file : file-like object

    Returns
    -------
    NavMessageFile instance

    """
    rnx_version, rnx_type = _read_version_type(file)

    if 2 <= rnx_version <= 2.11:
        if rnx_type != 'G':
            raise NavMessageFileError(
                "Can't read the file: type {type} is unsupported.".format(
                    type=rnx_type
                )
            )
        return NavMessageFileV2(file)

    elif 3 <= rnx_version <= 3.03:
        return NavMessageFileV3(file)

    else:
        raise NavMessageFileError(
            'Unsupported version: {}.'.format(rnx_version)
        )
