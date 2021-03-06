from sfepy.base.base import *
from sfepy.fem.mesh import Mesh
from sfepy.fem.meshio import MeshIO
from sfepy.solvers.ts import TimeStepper
from sfepy.base.ioutils import get_trunk, write_dict_hdf5

def dump_to_vtk(filename, output_filename_trunk=None, step0=0, steps=None):
    """Dump a multi-time-step results file into a sequence of VTK files."""
    output('dumping to VTK...')
    
    io = MeshIO.any_from_filename(filename)
    mesh = Mesh.from_file(filename, io=io)

    if output_filename_trunk is None:
        output_filename_trunk = get_trunk(filename)

    try:
        ts = TimeStepper(*io.read_time_stepper())

    except:
        output('no time stepping info found, assuming single step')

        out = io.read_data(0)
        if out is not None:
            mesh.write(output_filename_trunk + '.vtk', io='auto', out=out)

        ret = None

    else:
        if steps is None:
            iterator = ts.iter_from(step0)

        else:
            iterator = [(step, ts.times[step]) for step in steps]

        for step, time in iterator:
            output(ts.format % (step, ts.n_step - 1))
            out = io.read_data(step)
            if out is None: break
            mesh.write('.'.join((output_filename_trunk,
                                 ts.suffix % step, 'vtk')),
                       io='auto', out=out)

        ret = ts.suffix

    output('...done')
    return ret

def extract_time_history(filename, extract, verbose=True):
    """Extract time history of a variable from a multi-time-step results file.

    Parameters
    ----------
    filename : str
        The name of file to extract from.
    extract : str
        The description of what to extract in a string of comma-separated
        description items. A description item consists of: name of the variable
        to extract, mode ('e' for elements, 'n' for nodes), ids of the nodes or
        elements (given by the mode). Example: 'u n 10 15, p e 0' means
        variable 'u' in nodes 10, 15 and variable 'p' in element 0.
    verbose : bool
        Verbosity control.

    Returns
    -------
    ths : dict
        The time histories in a dict with variable names as keys. If a
        nodal variable is requested in elements, its value is a dict of histories
        in the element nodes.
    ts : TimeStepper instance
        The time stepping information.
    """
    output('extracting selected data...', verbose=verbose)

    output('selection:', extract, verbose=verbose)

    ##
    # Parse extractions.
    pes = OneTypeList(Struct)
    for chunk in extract.split(','):
        aux = chunk.strip().split()
        pes.append(Struct(var = aux[0],
                          mode = aux[1],
                          indx = map(int, aux[2:]),
                          igs = None))

    ##
    # Verify array limits, set igs for element data, shift indx.
    mesh = Mesh.from_file(filename)
    n_el, n_els, offs = mesh.n_el, mesh.n_els, mesh.el_offsets
    for pe in pes:
        if pe.mode == 'n':
            for ii in pe.indx:
                if (ii < 0) or (ii >= mesh.n_nod):
                    raise ValueError('node index 0 <= %d < %d!'
                                     % (ii, mesh.n_nod))

        if pe.mode == 'e':
            pe.igs = []
            for ii, ie in enumerate(pe.indx[:]):
                if (ie < 0) or (ie >= n_el):
                    raise ValueError('element index 0 <= %d < %d!'
                                     % (ie, n_el))
                ig = (ie < n_els).argmax()
                pe.igs.append(ig)
                pe.indx[ii] = ie - offs[ig]

##     print pes

    ##
    # Extract data.
    # Assumes only one element group (ignores igs)!
    io = MeshIO.any_from_filename(filename)
    ths = {}
    for pe in pes:
        mode, nname = io.read_data_header(pe.var)
        output(mode, nname, verbose=verbose)

        if ((pe.mode == 'n' and mode == 'vertex') or
            (pe.mode == 'e' and mode == 'cell')):
            th = io.read_time_history(nname, pe.indx)

        elif pe.mode == 'e' and mode == 'vertex':
            conn = mesh.conns[0]
            th = {}
            for iel in pe.indx:
                ips = conn[iel]
                th[iel] = io.read_time_history(nname, ips)
        else:
            raise ValueError('cannot extract cell data %s in nodes!' % pe.var)
            
        ths[pe.var] = th

    output('...done', verbose=verbose)

    ts = TimeStepper(*io.read_time_stepper())

    return ths, ts

def average_vertex_var_in_cells(ths_in):
    """Average histories in the element nodes for each nodal variable
        originally requested in elements."""
    ths = dict.fromkeys(ths_in.keys())
    for var, th in ths_in.iteritems():
        aux = dict.fromkeys(th.keys())
        for ir, data in th.iteritems():
            if isinstance(data, dict):
                for ic, ndata in data.iteritems():
                    if aux[ir] is None:
                        aux[ir] = ndata
                    else:
                        aux[ir] += ndata
                aux[ir] /= float(len(data))
            else:
                aux[ir] = data
        ths[var] = aux

    return ths

def save_time_history(ths, ts, filename_out):
    """Save time history and time-stepping information in a HDF5 file."""
    ths.update({'times' : ts.times, 'dt' : ts.dt})
    write_dict_hdf5(filename_out, ths)
