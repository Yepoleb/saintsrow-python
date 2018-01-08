import io
from binio import BinIO


class MatlibIO(BinIO):
    def read_ptr(self):
        ptr_val = self.read_uint32()
        self.skip(4)
        return ptr_val

class VBase:
    def __init__(self, stream=None):
        if stream is not None:
            self.read(stream)
    
    def read(self, stream):
        raise NotImplementedError()
    
    def __repr__(self):
        return repr(self.__dict__)

class Matlib(VBase):
    def read(self, stream):
        self.vfile = VFile(stream)
        
        matlib_base_pos = stream.tell()
        self.signature = stream.read_uint32()
        self.version = stream.read_uint32()
        self.material_map_p = stream.read_ptr()
        self.materials_pp = stream.read_ptr()
        self.num_materials = stream.read_uint32()
        stream.skip(4)
        self.texture_names_p = stream.read_ptr()
        
        stream.seek(matlib_base_pos + self.material_map_p)
        self.material_map = MaterialMap(stream)
        
        stream.seek(matlib_base_pos + self.materials_pp)
        self.materials_p = [stream.read_ptr() for i in range(self.num_materials)]
        self.materials = []
        for material_p in self.materials_p:
            stream.seek(matlib_base_pos + material_p)
            self.materials.append(Material(stream))
        
        stream.seek(matlib_base_pos + self.texture_names_p)
        for mat in self.materials:
            for tex in mat.textures:
                stream.seek(matlib_base_pos + self.texture_names_p + tex.texture_handle)
                tex.name = stream.read_cstring()
        

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

class Material(VBase):
    def read(self, stream):        
        self.size = stream.read_uint64()
        self.shader_handle = stream.read_uint32()
        self.name_checksum = stream.read_uint32()
        self.mat_flags = stream.read_uint32()
        self.num_textures = stream.read_uint16()
        self.num_constants = stream.read_uint8()
        self.max_constants = stream.read_uint8()
        self.textures_p = stream.read_ptr()
        self.constant_name_checksum_p = stream.read_ptr()
        self.constant_block_p = stream.read_ptr()
        self.alpha_shader_handle = stream.read_uint32()
        stream.skip(4)
        
        self.textures = [MaterialTexture(stream) for i in range(self.num_textures)]
        self.constant_name_checksum_size = stream.read_uint32()
        self.constant_name_checksum = [stream.read_uint32() for i in range(self.num_constants)]
        self.constant_block = []
        for i in range(self.num_constants):
            self.constant_block.append([stream.read_float() for j in range(4)])

class MaterialTexture(VBase):
    def read(self, stream):        
        self.texture_handle = stream.read_int32()
        self.name_checksum = stream.read_uint32()
        self.texture_stage = stream.read_uint16()
        self.texture_flags = stream.read_uint16()
        self.name = None

class MaterialMap(VBase):
    def read(self, stream):        
        self.materials_p = stream.read_ptr()
        self.num_materials = stream.read_uint32()
        stream.skip(4)

fstream = open("joshbirk_body_high.matlib_pc", "rb")
binstream = MatlibIO(fstream)
mlib = Matlib(binstream)
print(repr(mlib))
