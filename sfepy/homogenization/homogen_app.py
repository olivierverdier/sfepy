import os.path as op
import shutil

from sfepy.base.base import *
from sfepy.homogenization.coefficients import Coefficients
from sfepy.homogenization.coefs_base import MiniAppBase
from sfepy.homogenization.engine import HomogenizationEngine
from sfepy.applications import SimpleApp

class Volume(MiniAppBase):

    def __call__(self, problem=None):
        problem = get_default(problem, self.problem)
        problem.select_variables(self.variables)

        volume = problem.evaluate(self.expression)

        return volume

class HomogenizationApp( HomogenizationEngine ):

    def process_options( options ):
        """Application options setup. Sets default values for missing
        non-compulsory options."""
        get = options.get_default_attr
        
        print_digits = get( 'print_digits', 3 )

        float_format = get( 'float_format', '%8.3e' )
        coef_save_name = get( 'coef_save_name', 'coefs' )
        tex_names = get( 'tex_names', None )
        
        coefs = get( 'coefs', None, 'missing "coefs" in options!' )
        requirements = get( 'requirements', None,
                            'missing "requirements" in options!' )
        volume = get( 'volume', None, 'missing "volume" in options!' )

        return Struct( **locals() )
    process_options = staticmethod( process_options )

    def __init__(self, conf, options, output_prefix, **kwargs):
        SimpleApp.__init__(self, conf, options, output_prefix,
                           init_equations=False)

        self.setup_options()
        self.cached_coefs = None

        output_dir = self.problem.output_dir

        if conf._filename is not None:
            shutil.copyfile(conf._filename,
                            op.join(output_dir, op.basename(conf._filename)))

    def setup_options( self ):
        SimpleApp.setup_options( self )
        po = HomogenizationApp.process_options
        self.app_options += po( self.conf.options )
    
    def call( self, ret_all = False ):
        opts = self.app_options

        if 'value' in opts.volume:
            volume = nm.float64( opts.options.volume['value'] )
        else:
            volume = Volume( 'volume', self.problem, opts.volume )()
        output( 'volume: %.2f' % volume )
        
        if hasattr(opts.options, 'return_all'):
            ret_all = opts.options.return_all

        he = HomogenizationEngine( self.problem, self.options, volume = volume )

        aux = he( ret_all = ret_all)
        if ret_all:
            coefs, dependencies = aux
        else:
            coefs = aux

        coefs = Coefficients( **coefs.to_dict() )
        coefs.volume = volume
        
        prec = nm.get_printoptions()[ 'precision']
        if hasattr( opts, 'print_digits' ):
            nm.set_printoptions( precision = opts.print_digits )
        print coefs
        nm.set_printoptions( precision = prec )
##        pause()

        coef_save_name = op.join( opts.output_dir, opts.coef_save_name )
        coefs.to_file_hdf5( coef_save_name + '.h5' )
        coefs.to_file_txt( coef_save_name + '.txt',
                           opts.tex_names,
                           opts.float_format )

        if ret_all:
            return coefs, dependencies
        else:
            return coefs
