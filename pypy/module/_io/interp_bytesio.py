from pypy.interpreter.typedef import (
    TypeDef, generic_new_descr, GetSetProperty)
from pypy.interpreter.gateway import interp2app, unwrap_spec
from pypy.interpreter.error import OperationError, operationerrfmt
from pypy.interpreter.buffer import RWBuffer
from rpython.rlib.rStringIO import RStringIO
from rpython.rlib.rarithmetic import r_longlong
from pypy.module._io.interp_bufferedio import W_BufferedIOBase
from pypy.module._io.interp_iobase import convert_size
import sys


class BytesIOBuffer(RWBuffer):
    def __init__(self, w_bytesio):
        self.w_bytesio = w_bytesio
        self.format = 'B'
        self.itemsize = 1

    def getlength(self):
        return int(self.w_bytesio.getsize())

    def as_str(self):
        return self.w_bytesio.getvalue()

    def getitem(self, index):
        # XXX: move this & setitem into rStringIO or some kind of
        # rStringIOBufferView
        w_bytesio = self.w_bytesio
        tell = w_bytesio.tell()
        try:
            w_bytesio.seek(index)
            item = w_bytesio.read(1)
            # cast to char
            assert len(item) == 1
            return item[0]
        finally:
            w_bytesio.seek(tell)

    def setitem(self, index, char):
        w_bytesio = self.w_bytesio
        tell = w_bytesio.tell()
        try:
            w_bytesio.seek(index)
            w_bytesio.write(char)
        finally:
            w_bytesio.seek(tell)


class W_BytesIO(RStringIO, W_BufferedIOBase):
    def __init__(self, space):
        W_BufferedIOBase.__init__(self, space)
        self.init()

    def descr_new(space, w_subtype, __args__):
        self = space.allocate_instance(W_BytesIO, w_subtype)
        W_BytesIO.__init__(self, space)
        return space.wrap(self)

    def descr_init(self, space, w_initial_bytes=None):
        self.init()
        if not space.is_none(w_initial_bytes):
            self.write_w(space, w_initial_bytes)
            self.seek(0)

    def _check_closed(self, space, message=None):
        if self.is_closed():
            if message is None:
                message = "I/O operation on closed file"
            raise OperationError(space.w_ValueError, space.wrap(message))

    def read_w(self, space, w_size=None):
        self._check_closed(space)
        size = convert_size(space, w_size)
        return space.wrapbytes(self.read(size))

    def readline_w(self, space, w_limit=None):
        self._check_closed(space)
        limit = convert_size(space, w_limit)
        return space.wrapbytes(self.readline(limit))

    def read1_w(self, space, w_size):
        return self.read_w(space, w_size)

    def readinto_w(self, space, w_buffer):
        self._check_closed(space)
        rwbuffer = space.rwbuffer_w(w_buffer)
        size = rwbuffer.getlength()

        output = self.read(size)
        rwbuffer.setslice(0, output)
        return space.wrap(len(output))

    def write_w(self, space, w_data):
        self._check_closed(space)
        if space.isinstance_w(w_data, space.w_unicode):
            raise OperationError(space.w_TypeError, space.wrap(
                "bytes string of buffer expected"))
        buf = space.bufferstr_w(w_data)
        length = len(buf)
        if length <= 0:
            return space.wrap(0)
        self.write(buf)
        return space.wrap(length)

    def truncate_w(self, space, w_size=None):
        self._check_closed(space)

        pos = self.tell()
        if space.is_none(w_size):
            size = pos
        else:
            size = space.r_longlong_w(w_size)

        if size < 0:
            raise OperationError(space.w_ValueError, space.wrap(
                "negative size value"))

        self.truncate(size)
        if size == pos:
            self.seek(0, 2)
        else:
            self.seek(pos)
        return space.wrap(size)

    def getbuffer_w(self, space):
        return space.wrap(BytesIOBuffer(self))

    def getvalue_w(self, space):
        self._check_closed(space)
        return space.wrapbytes(self.getvalue())

    def tell_w(self, space):
        self._check_closed(space)
        return space.wrap(self.tell())

    @unwrap_spec(pos=r_longlong, whence=int)
    def seek_w(self, space, pos, whence=0):
        self._check_closed(space)

        if whence == 0:
            if pos < 0:
                raise OperationError(space.w_ValueError, space.wrap(
                    "negative seek value"))
        elif whence == 1:
            if pos > sys.maxint - self.tell():
                raise OperationError(space.w_OverflowError, space.wrap(
                    "new position too large"))
        elif whence == 2:
            if pos > sys.maxint - self.getsize():
                raise OperationError(space.w_OverflowError, space.wrap(
                    "new position too large"))
        else:
            raise operationerrfmt(space.w_ValueError,
                "whence must be between 0 and 2, not %d", whence)

        self.seek(pos, whence)
        return space.wrap(self.tell())

    def readable_w(self, space):
        return space.w_True

    def writable_w(self, space):
        return space.w_True

    def seekable_w(self, space):
        return space.w_True

    def close_w(self, space):
        self.close()

    def closed_get_w(self, space):
        return space.wrap(self.is_closed())

    def getstate_w(self, space):
        self._check_closed(space)
        return space.newtuple([
            space.wrapbytes(self.getvalue()),
            space.wrap(self.tell()),
            self.getdict(space)])

    def setstate_w(self, space, w_state):
        self._check_closed(space)

        if space.len_w(w_state) != 3:
            raise operationerrfmt(space.w_TypeError,
                "%T.__setstate__ argument should be 3-tuple, got %T",
                self, w_state)
        w_content, w_pos, w_dict = space.unpackiterable(w_state, 3)
        self.truncate(0)
        self.write_w(space, w_content)
        pos = space.int_w(w_pos)
        if pos < 0:
            raise OperationError(space.w_ValueError, space.wrap(
                "position value cannot be negative"))
        self.seek(pos)
        if not space.is_w(w_dict, space.w_None):
            space.call_method(self.getdict(space), "update", w_dict)

W_BytesIO.typedef = TypeDef(
    'BytesIO', W_BufferedIOBase.typedef,
    __module__ = "_io",
    __new__  = interp2app(W_BytesIO.descr_new.im_func),
    __init__  = interp2app(W_BytesIO.descr_init),

    read = interp2app(W_BytesIO.read_w),
    read1 = interp2app(W_BytesIO.read1_w),
    readline = interp2app(W_BytesIO.readline_w),
    readinto = interp2app(W_BytesIO.readinto_w),
    write = interp2app(W_BytesIO.write_w),
    truncate = interp2app(W_BytesIO.truncate_w),
    getbuffer = interp2app(W_BytesIO.getbuffer_w),
    getvalue = interp2app(W_BytesIO.getvalue_w),
    seek = interp2app(W_BytesIO.seek_w),
    tell = interp2app(W_BytesIO.tell_w),
    readable = interp2app(W_BytesIO.readable_w),
    writable = interp2app(W_BytesIO.writable_w),
    seekable = interp2app(W_BytesIO.seekable_w),
    close = interp2app(W_BytesIO.close_w),
    closed = GetSetProperty(W_BytesIO.closed_get_w),
    __getstate__ = interp2app(W_BytesIO.getstate_w),
    __setstate__ = interp2app(W_BytesIO.setstate_w),
    )
