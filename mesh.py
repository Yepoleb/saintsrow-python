from common import VBase, VFile, VBinIO
from matlib import MaterialMap, Material


def cstring_at(data, offset):
    return data[offset:data.find(b"\x00", offset)]


class StaticMesh(VBase):
    def read(self, stream):
        self.vfile = VFile(stream)

        self.signature = stream.read_uint32()
        self.version = stream.read_int16()
        self.mesh_flags = stream.read_int16()

        self.num_navpoints = stream.read_int16()
        self.num_rig_bones = stream.read_int16()
        self.num_materials = stream.read_int16()
        self.num_material_maps = stream.read_int16()
        self.num_lods_per_submesh = stream.read_int16()
        self.num_submesh_vids = stream.read_int16()
        stream.skip(4)

        self.navpoints_p = stream.read_ptr()
        self.rig_bone_indices_p = stream.read_ptr()
        self.bounding_center = stream.read_vec3()
        self.bounding_radius = stream.read_float()
        self.num_cspheres = stream.read_int16()
        self.num_ccylinders = stream.read_int16()
        stream.skip(4)

        self.cspheres_p = stream.read_ptr()
        self.ccylinders_p = stream.read_ptr()
        self.mesh_p = stream.read_ptr()
        self.material_maps_pp = stream.read_ptr()
        self.materal_map_name_crcs_p = stream.read_ptr()
        self.materials_pp = stream.read_ptr()
        self.num_logical_submeshes = stream.read_uint32()
        stream.skip(4)

        self.submesh_vids_p = stream.read_ptr()
        self.submesh_lod_info = stream.read_ptr()

        self.texture_name_size = stream.read_int32()
        stream.align(16)
        stream.skip(1)
        texture_name_data = stream.read(self.texture_name_size)

        stream.align(16)
        self.navpoints = [StaticMeshNavpoint(stream) for i in range(self.num_navpoints)]
        stream.align(16)
        self.cspheres = [CMeshSphere(stream) for i in range(self.num_cspheres)]
        stream.align(16)
        self.ccylinders = [CMeshCylinder(stream) for i in range(self.num_ccylinders)]
        stream.align(16)
        self.rig_bones = [stream.read_uint32() for i in range(self.num_rig_bones)]

        stream.align(8)
        mesh_start = stream.tell()
        self.mesh_version = stream.read_uint16()
        stream.skip(2)
        self.mesh_gpu_data_crc = stream.read_uint32()
        self.mesh_cpu_data_size = stream.read_uint32()
        self.mesh_gpu_data_size = stream.read_uint32()
        self.mesh = RlMesh(stream)
        stream.seek(mesh_start + self.mesh_cpu_data_size)

        stream.align(8)
        self.material_maps_p = [stream.read_ptr() for i in range(self.num_material_maps)]
        self.material_map_name_crcs = [stream.read_uint32() for i in range(self.num_material_maps)]
        self.materials_p = [stream.read_ptr() for i in range(self.num_materials)]
        stream.align(16)
        self.materials = [Material(stream) for i in range(self.num_materials)]
        stream.align(16)
        self.material_maps = [MaterialMap(stream) for i in range(self.num_material_maps)]
        self.submesh_vids = [stream.read_uint32() for i in range(self.num_submesh_vids)]
        stream.align(8)
        self.submesh_lod_info = [stream.read_int16() for i in
            range(self.num_logical_submeshes * self.num_lods_per_submesh)]

        for mat in self.materials:
            for tex in mat.textures:
                tex.name = cstring_at(texture_name_data, tex.texture_handle)

    def read_gpu(self, stream):
        self.gpu_crc = stream.read_uint32()
        stream.seek(16)
        if self.mesh.index_buffer.index_size == 2:
            self.mesh.index_buffer.indices = [stream.read_uint16() for i in range(
                self.mesh.index_buffer.num_indices)]
        else:
            self.mesh.index_buffer.indices = [stream.read_uint32() for i in range(
                self.mesh.index_buffer.num_indices)]
        stream.align(16)
        for vertex_buf in self.mesh.vertex_buffers:
            vertex_buf.verts = [Vertex(stream) for i in range(vertex_buf.num_verts)]
        self.gpu_crc2 = stream.read_uint32()


class StaticMeshNavpoint(VBase):
    def read(self, stream):
        self.name = stream.read(64).rstrip("\x00")
        self.vid = stream.read_uint32()
        self.pos = stream.read_vec3()
        self.orient = stream.read_vec4()

class CMeshSphere(VBase):
    def read(self, stream):
        self.body_part_id = stream.read_uint32()
        self.parent_index = stream.read_int32()
        self.pos = stream.read_vec3()
        self.radius = stream.read_float()

class CMeshCylinder(VBase):
    def read(self, stream):
        self.body_part_id = stream.read_uint32()
        self.parent_index = stream.read_int32()
        self.axis = stream.read_vec3()
        self.pos = stream.read_vec3()
        self.radius = stream.read_float()
        self.height = stream.read_float()

class RlMesh(VBase):
    def read(self, stream):
        mesh_start = stream.tell() - 16
        self.mesh_flags = stream.read_uint32()
        self.num_sub_meshes = stream.read_int32()
        self.sub_meshes_p = stream.read_ptr()
        self.num_vertex_buffers = stream.read_uint32()
        stream.skip(4)
        self.vertex_buffers_p = stream.read_ptr()
        self.index_buffer = IndexBuffer(stream)
        self.bone_map = BoneMap(stream)
        self.position_scale = stream.read_vec3()
        self.position_offset = stream.read_vec3()

        stream.seek(mesh_start + self.vertex_buffers_p)
        self.vertex_buffers = [VertexBuffer(stream) for i in range(self.num_vertex_buffers)]
        self.bone_map.mapped_bone_list = [stream.read_uint8() for i in range(self.bone_map.num_mapped_bones)]
        self.bone_map.bone_groups = [BoneGroup(stream) for i in range(self.bone_map.num_bone_groups)]
        stream.seek(mesh_start + self.sub_meshes_p)
        self.sub_meshes = [SubmeshData(stream) for i in range(self.num_sub_meshes)]
        for sub_mesh in self.sub_meshes:
            sub_mesh.render_blocks = [RenderBlock(stream) for i in range(sub_mesh.num_render_blocks)]
        for sub_mesh in self.sub_meshes:
            sub_mesh.render_block_bone_groups_p = [
                stream.read_ptr() for i in range(sub_mesh.num_render_blocks)]
        self.crc = stream.read_uint32()


class IndexBuffer(VBase):
    def read(self, stream):
        self.num_indices = stream.read_uint32()
        stream.skip(4)
        self.indices_p = stream.read_ptr()
        self.index_size = stream.read_uint8()
        self.prim_type = stream.read_uint8()
        self.num_blocks = stream.read_uint16()
        stream.skip(4)

class BoneGroup(VBase):
    def read(self, stream):
        self.num_group_bones = stream.read_uint8()
        self.group_bone_offset = stream.read_uint8()

class BoneMap(VBase):
    def read(self, stream):
        self.num_mapped_bones = stream.read_uint16()
        stream.skip(6)
        self.mapped_bone_list_p = stream.read_ptr()
        self.num_bone_groups = stream.read_uint16()
        stream.skip(6)
        self.bone_group_list_p = stream.read_ptr()

class VertexBuffer(VBase):
    def read(self, stream):
        self.num_verts = stream.read_int32()
        self.vert_stride_0 = stream.read_uint8()
        self.vertex_format = stream.read_uint8()
        self.num_uv_channels = stream.read_uint8()
        self.vert_stride_1 = stream.read_uint8()
        self.render_data_p = stream.read_ptr()
        self.verts_p = stream.read_ptr()

class SubmeshData(VBase):
    def read(self, stream):
        self.num_render_blocks = stream.read_int32()
        self.bmin = stream.read_vec3()
        self.bmax = stream.read_vec3()
        stream.skip(4)
        self.render_blocks_p = stream.read_ptr()
        self.render_blocks_bone_groups_pp = stream.read_ptr()

class RenderBlock(VBase):
    def read(self, stream):
        self.material_map_idx = stream.read_uint16()
        self.vertex_buffer_idx = stream.read_uint16()
        self.start_index = stream.read_uint32()
        self.num_indices = stream.read_uint32()
        self.minimum_index = stream.read_uint32()
        self.maximum_index = stream.read_uint32()

class Vertex(VBase):
    def read(self, stream):
        self.pos = stream.read_vec3()
        self.normal = stream.read_comp_vec4()
        self.tangent = stream.read_comp_vec4()
        self.blendweights = stream.read_ucvec_4()
        self.blendindices = stream.read_scvec_4()
        self.u = stream.read_uint16() / 1023.0
        self.v = stream.read_uint16() / 1023.0


if __name__ == "__main__":
    stream = VBinIO(open("examples/SMG_Pistol_A.ccmesh_pc", "rb"), endian="<")
    stream_gpu = VBinIO(open("examples/SMG_Pistol_A.gcmesh_pc", "rb"), endian="<")
    mesh = StaticMesh(stream)
    mesh.read_gpu(stream_gpu)
    print(repr(mesh))
