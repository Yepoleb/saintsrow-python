from binio import BinIO


class VBase:
    def __init__(self, stream=None):
        if stream is not None:
            self.read(stream)

    def read(self, stream):
        raise NotImplementedError()

    def __repr__(self):
        return repr(self.__dict__)

class VFile(VBase):
    def read(self, stream):
        self.signature = stream.read_uint16()
        self.version = stream.read_uint16()
        self.reference_data_size = stream.read_uint32()
        self.reference_data_start = stream.read_uint32()
        self.reference_count = stream.read_uint32()
        self.initialized = stream.read_uint8()
        stream.skip(15)
        self.references = [stream.read_cstring() for i in range(self.reference_count)]
        stream.align(16)

class VBinIO(BinIO):
    def read_ptr(self):
        ptr_val = self.read_uint32()
        self.skip(4)
        return ptr_val

    def read_vec3(self):
        return self.unpack("3f")

    def read_vec4(self):
        return self.unpack("4f")

    def read_comp_vec4(self):
        values = self.unpack("4B")
        return tuple((x - 127) / 128.0 for x in values)

    def read_ucvec_4(self):
        return self.unpack("4B")

    def read_scvec_4(self):
        return self.unpack("4b")
