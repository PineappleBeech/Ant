import struct


STRING = 0
INT = 1
BOOL = 2
FLOAT = 3
TUPLE = 4


def prepend_size(data):
    return struct.pack(">I", len(data)) + data


def read_size(data):
    return struct.unpack(">I", data[:4])[0]


def read_string(data):
    size = read_size(data)
    return data[4:4+size].decode("utf-8"), data[4+size:]


def read_int(data):
    return struct.unpack(">i", data[:4])[0], data[4:]


def read_bool(data):
    return bool(struct.unpack(">i", data[:4])[0]), data[4:]


def read_float(data):
    return struct.unpack(">f", data[:4])[0], data[4:]


def read_tuple(data):
    size, data = read_int(data)
    result = []
    for i in range(size):
        value, data = read(data)
        result.append(value)
    return tuple(result), data


def read(data):
    type = struct.unpack(">i", data[:4])[0]
    data = data[4:]
    if type == STRING:
        return read_string(data)
    elif type == INT:
        return read_int(data)
    elif type == BOOL:
        return read_bool(data)
    elif type == FLOAT:
        return read_float(data)
    elif type == TUPLE:
        return read_tuple(data)
    else:
        raise Exception("Unknown type %d" % type)


def read_packet(data, skipsize=False):
    if not skipsize:
        size = read_size(data)
        data = data[4:]
    name, data = read_string(data)
    data, left = read(data)
    assert len(left) == 0
    return name, data


def write_string(data):
    return prepend_size(data.encode("utf-8"))


def write_int(data):
    return struct.pack(">i", data)


def write_bool(data):
    return struct.pack(">i", int(data))


def write_float(data):
    return struct.pack(">f", data)


def write_tuple(data):
    buffer = b""
    count = len(data)
    for item in data:
        buffer += write(item)

    return write_int(count) + buffer


def write(data):
    if isinstance(data, str):
        return struct.pack(">i", STRING) + write_string(data)

    if isinstance(data, int):
        return struct.pack(">i", INT) + write_int(data)

    if isinstance(data, bool):
        return struct.pack(">i", BOOL) + write_bool(data)

    if isinstance(data, float):
        return struct.pack(">i", FLOAT) + write_float(data)

    if isinstance(data, tuple):
        return struct.pack(">i", TUPLE) + write_tuple(data)

    raise Exception("Unknown type %s" % type(data))


def write_packet(name, data):
    return prepend_size(write_string(name) + write(data))