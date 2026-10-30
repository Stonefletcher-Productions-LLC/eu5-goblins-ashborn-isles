"""LZAV data format 3 (github.com/avaneev/lzav), as used by EU5 1.4 terrain tiles.

decompress() handles any format-3 stream. compress() writes a valid stream that
holds the input as one final literal block: no matching, so tiles stay roughly
raw-sized, but every LZAV decoder accepts it.
"""


def _varint(data, i, value, shift=7):
    # Up to three continuation bytes after the first length byte.
    for _ in range(4):
        byte = data[i]; i += 1
        value += (byte & 0x7F) << shift
        if not byte & 0x80 or shift == 7 + 21:
            break
        shift += 7
    return value, i


def decompress(data, size):
    data = bytes(data)
    if len(data) < 11 or data[0] >> 4 != 3:
        raise ValueError('not an LZAV format-3 stream')
    mref1 = (data[0] & 15) - 1
    out = bytearray()
    i = 1
    cv = 0; csh = 0
    end = len(data)
    while i < end:
        bh = data[i]; i += 1
        bt = (bh >> 4) & 3
        if bt == 0:
            cv |= (bh >> 6) << csh; csh += 2
            cc = bh & 15
            if cc == 0:
                b = data[i]; i += 1
                cc = (b & 0x7F) + 16
                if b & 0x80:
                    cc, i = _varint(data, i, cc)
            out += data[i:i + cc]; i += cc
            continue
        bv = int.from_bytes(data[i:i + 4].ljust(4, b'\0'), 'little')
        om = (0, 0x3FF, 0x7FFF, 0x1FFFFF)[bt]
        ncsh = (0, 0, 3, 5)[bt]
        d = (((bv << 2) | (bh >> 6)) & om) << csh | cv
        cv = (data[i + bt - 1] << ncsh) >> 8
        csh = ncsh
        i += bt
        cc = bh & 15
        if cc:
            n = mref1 + cc
        else:
            b = data[i]; i += 1
            n = b & 0x7F
            if b & 0x80:
                n, i = _varint(data, i, n)
            n += mref1 + 16
        if d == 0 or d > len(out):
            raise ValueError('LZAV reference out of bounds')
        start = len(out) - d
        for k in range(n):
            out.append(out[start + k])
    if len(out) != size:
        raise ValueError(f'LZAV length {len(out)} != {size}')
    return bytes(out)


def compress(raw):
    raw = bytes(raw)
    if len(raw) < 16:
        raise ValueError('tile too small for a single final literal block')
    head = bytearray([0x35, 0])
    n = len(raw) - 16
    while n > 127:
        head.append(0x80 | (n & 0x7F)); n >>= 7
    head.append(n)
    return bytes(head) + raw
