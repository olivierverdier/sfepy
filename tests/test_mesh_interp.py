import os.path as op

from sfepy.base.base import *
from sfepy.base.conf import transform_variables, transform_fields
from sfepy.base.testing import TestCommon

variables = {
    'u'       : ('unknown field', 'f', 0),
    'v'       : ('test field',    'f', 'u'),
}

def in_dir(adir):
    return lambda x: op.join(adir, x)

def do_interpolation(m2, m1, data, field_name):
    """Interpolate data from m1 to m2. """
    from sfepy.fem import Domain, Field, Variables

    fields = {
        'scalar_si' : ((1,1), 'Omega', 2),
        'vector_si' : ((3,1), 'Omega', 2),
        'scalar_tp' : ((1,1), 'Omega', 1),
        'vector_tp' : ((3,1), 'Omega', 1),
    }

    d1 = Domain('d1', m1)

    omega1 = d1.create_region('Omega', 'all')

    f = fields[field_name]

    field1 = Field('f', nm.float64, f[0], d1.regions[f[1]], approx_order=f[2])
    ff = {field1.name : field1}

    vv = Variables.from_conf(transform_variables(variables), ff)
    u1 = vv['u']
    u1.set_from_mesh_vertices(data)

    d2 = Domain('d2', m2)
    omega2 = d2.create_region('Omega', 'all')

    field2 = Field('f', nm.float64, f[0], d2.regions[f[1]], approx_order=f[2])
    ff2 = {field2.name : field2}

    vv2 = Variables.from_conf(transform_variables(variables), ff2)
    u2 = vv2['u']

    # Performs interpolation, if other field differs from self.field
    # or, in particular, is defined on a different mesh.
    u2.set_from_other(u1, strategy='interpolation', close_limit=0.5)

    return u1, u2
 
class Test(TestCommon):

    @staticmethod
    def from_conf(conf, options):
        test = Test(conf=conf, options=options)
        return test

    def test_interpolation(self):
        from sfepy import data_dir
        from sfepy.fem import Mesh
        from sfepy.linalg import make_axis_rotation_matrix

        fname = in_dir(self.options.out_dir)

        meshes = {
            'tp' : Mesh('original mesh', data_dir + '/meshes/3d/block.mesh'),
            'si' : Mesh('original mesh', data_dir + '/meshes/3d/cylinder.mesh'),
        }

        datas = {}

        for key, mesh in meshes.iteritems():
            bbox = mesh.get_bounding_box()
            nx = bbox[1,0] - bbox[0,0]
            centre = 0.5 * bbox.sum(axis=0)
            mesh.coors -= centre
            
            data = nm.sin(4.0 * nm.pi * mesh.coors[:,0:1] / nx)
            datas['scalar_' + key] = data

            data = nm.zeros_like(mesh.coors)
            data[:,0] = 0.05 * nx * nm.sin(4.0 * nm.pi * mesh.coors[:,0] / nx)
            data[:,2] = 0.05 * nx * nm.cos(4.0 * nm.pi * mesh.coors[:,0] / nx)
            datas['vector_' + key] = data

        for field_name in ['scalar_si', 'vector_si', 'scalar_tp', 'vector_tp']:
            m1 = meshes[field_name[-2:]]

            for ia, angle in enumerate(nm.linspace(0.0, nm.pi, 11)):
                self.report('%s: %d. angle: %f' % (field_name, ia, angle))
                shift = [0.0, 0.0, 0.0]
                mtx = make_axis_rotation_matrix([0, 1, 0], angle)

                m2 = m1.copy('rotated mesh')
                m2.transform_coors(mtx)

                data = datas[field_name]
                u1, u2 = do_interpolation(m2, m1, data, field_name)

                if ia == 0:
                    u1.save_as_mesh(fname('test_mesh_interp_%s_u1.vtk'
                                          % field_name))

                u2.save_as_mesh(fname('test_mesh_interp_%s_u2.%03d.vtk'
                                      % (field_name, ia)))
       
        return True

    def test_interpolation_two_meshes(self):
        from sfepy import data_dir
        from sfepy.fem import Mesh, Domain, Field, Variables

        m1 = Mesh('source mesh', data_dir + '/meshes/3d/block.mesh')

        m2 = Mesh('target mesh', data_dir + '/meshes/3d/cube_medium_tetra.mesh')
        m2.coors *= 2.0

        bbox = m1.get_bounding_box()
        dd = bbox[1,:] - bbox[0,:]
        data = nm.sin(4.0 * nm.pi * m1.coors[:,0:1] / dd[0]) \
               * nm.cos(4.0 * nm.pi * m1.coors[:,1:2] / dd[1])

        variables1 = {
            'u'       : ('unknown field', 'scalar_tp', 0),
            'v'       : ('test field',    'scalar_tp', 'u'),
        }

        variables2 = {
            'u'       : ('unknown field', 'scalar_si', 0),
            'v'       : ('test field',    'scalar_si', 'u'),
        }

        d1 = Domain('d1', m1)
        omega1 = d1.create_region('Omega', 'all')
        field1 = Field('scalar_tp', nm.float64, (1,1), omega1, approx_order=1)
        ff1 = {field1.name : field1}

        d2 = Domain('d2', m2)
        omega2 = d2.create_region('Omega', 'all')
        field2 = Field('scalar_si', nm.float64, (1,1), omega2, approx_order=0)
        ff2 = {field2.name : field2}

        vv1 = Variables.from_conf(transform_variables(variables1), ff1)
        u1 = vv1['u']
        u1.set_from_mesh_vertices(data)

        vv2 = Variables.from_conf(transform_variables(variables2), ff2)
        u2 = vv2['u']

        # Performs interpolation, if other field differs from self.field
        # or, in particular, is defined on a different mesh.
        u2.set_from_other(u1, strategy='interpolation', close_limit=0.1)

        fname = in_dir(self.options.out_dir)
        u1.save_as_mesh(fname('test_mesh_interp_block_scalar.vtk'))
        u2.save_as_mesh(fname('test_mesh_interp_cube_scalar.vtk'))

        return True
