from terms import *

## expr = """
## e = 1/2 * (grad( vec( u ) ) + grad( vec( u ) ).T)
## D = map( D_sym )
## s = D * e
## div( s )
## """

## """
## e[i,j] = 1/2 * (der[j]( u[i] ) + der[i]( u[j] ))
## map =
## D[i,j,k,l]
## s[i,j] = D[i,j,k,l] * e[k,l]
## """

##
# c: 02.08.2006
class LinearElasticTerm( Term ):
    r""":description: General linear elasticity term, with $D_{ijkl}$ given in
    the usual matrix form exploiting symmetry: in 3D it is $6\times6$ with the
    indices ordered as $[11, 22, 33, 12, 13, 23]$, in 2D it is $3\times3$ with
    the indices ordered as $[11, 22, 12]$.
    :definition: $\int_{\Omega}  D_{ijkl}\ e_{ij}(\ul{v}) e_{kl}(\ul{u})$
    """
    name = 'dw_lin_elastic'
    argTypes = ('material', 'virtual', 'state')
    geometry = [(Volume, 'virtual')]
    useCaches = {'cauchy_strain' : [['state', {'strain' : (1,1)}]]}
##     symbolic = {'expression': expr,
##                 'map' : {'u' : 'state', 'D_sym' : 'material'}}

    def __init__( self, region, name = name, sign = 1 ):
        Term.__init__( self, region, name, sign, terms.dw_lin_elastic )

    ##
    # c: 21.03.2008, r: 25.03.2008
    def getShape( self, diffVar, chunkSize, apr, apc = None ):
        self.dataShape = apr.getVDataShape( self.integralName )
        nEl, nQP, dim, nEP = self.dataShape
        
        if diffVar is None:
            return (chunkSize, 1, dim * nEP, 1), 0
        elif diffVar == self.getArgName( 'state' ):
            return (chunkSize, 1, dim * nEP, dim * nEP), 1
        else:
            raise StopIteration

    ##
    # c: 25.03.2008, r: 25.03.2008
    def buildCFunArgs( self, mat, state, ap, vg ):
        matQP = mat[nm.newaxis,:,:].repeat( self.dataShape[1], 0 )
        cache = self.getCache( 'cauchy_strain', 0 )
        strain = cache( 'strain', self.getCurrentGroup(), 0, state = state )
        return 1.0, strain, matQP, vg

    ##
    # c: 07.03.2006, r: 21.03.2008
    def __call__( self, diffVar = None, chunkSize = None, **kwargs ):
        material, virtual, state = self.getArgs( **kwargs )
        ap, vg = virtual.getApproximation( self.getCurrentGroup(), 'Volume' )

        shape, mode = self.getShape( diffVar, chunkSize, ap )
        fargs = self.buildCFunArgs( material, state, ap, vg )
        
        for out, chunk in self.charFun( chunkSize, shape ):
            status = self.function( out, *fargs + (chunk, mode) )
            yield out, chunk, status

##
# 01.03.2007, c
class  LinearElasticIntegratedTerm( Term ):
    r""":description: Integrated general linear elasticity term.
    :definition: $\int_{\Omega} D_{ijkl}\ e_{ij}(\ul{b}) e_{kl}(\ul{w})$
    """
    name = 'd_lin_elastic'
    argTypes = ('material', 'parameter_1', 'parameter_2')
    geometry = [(Volume, 'parameter_1'), (Volume, 'parameter_2')]
    useCaches = {'cauchy_strain' : [['parameter_1'], ['parameter_2']]}

    def __init__( self, region, name = name, sign = 1 ):
        Term.__init__( self, region, name, sign, terms.d_lin_elastic )

    ##
    # c: 01.03.2007, r: 15.01.2008
    def __call__( self, diffVar = None, chunkSize = None, **kwargs ):
        mat, par1, par2 = self.getArgs( **kwargs )
        ap, vg = par1.getApproximation( self.getCurrentGroup(), 'Volume' )
        nEl, nQP, dim, nEP = ap.getVDataShape( self.integralName )
        shape = (chunkSize, 1, 1, 1)

        matQP = mat[nm.newaxis,:,:].repeat( nQP, 0 )
#        print matQP

        cache = self.getCache( 'cauchy_strain', 0 )
        strain1 = cache( 'strain', self.getCurrentGroup(), 0, state = par1 )
        cache = self.getCache( 'cauchy_strain', 1 )
        strain2 = cache( 'strain', self.getCurrentGroup(), 0, state = par2 )

        for out, chunk in self.charFun( chunkSize, shape ):
            status = self.function( out, 1.0, strain1, strain2, matQP,
                                    vg, chunk )
            out1 = nm.sum( nm.squeeze( out ) )
            yield out1, chunk, status

##
# 07.03.2006, c
class LinearElasticIsotropicTerm( LinearElasticTerm ):
    r""":description: Isotropic linear elasticity term.
    :definition: $\int_{\Omega}  D_{ijkl}\ e_{ij}(\ul{v}) e_{kl}(\ul{u})$
    with $D_{ijkl} = \mu (\delta_{ik} \delta_{jl}+\delta_{il} \delta_{jk}) +
    \lambda \ \delta_{ij} \delta_{kl}$ 
    """
    name = 'dw_lin_elastic_iso'
    argTypes = ('material', 'virtual', 'state')
    geometry = [(Volume, 'virtual'), (Volume, 'state')]

    ##
    # c: 07.03.2006, r: 21.03.2008
    def __init__( self, region, name = name, sign = 1 ):
        Term.__init__( self, region, name, sign, terms.dw_lin_elastic_iso )

    ##
    # c: 21.03.2008, r: 21.03.2008
    def buildCFunArgs( self, mat, state, ap, vg ):
        vec, indx = state()
        lam, mu = map( nm.float64, [mat[ii] for ii in ['lambda', 'mu']] )
        return vec, indx.start, lam, mu, vg, ap.econn

##
# 01.08.2006, c
class LinearViscousTerm( LinearElasticTerm ):
    r""":description: General linear viscosity term, with $D_{ijkl}$ given in
    the usual matrix form exploiting symmetry: in 3D it is $6\times6$ with the
    indices ordered as $[11, 22, 33, 12, 13, 23]$, in 2D it is $3\times3$ with
    the indices ordered as $[11, 22, 12]$.
    :definition: $\int_{\Omega}  D_{ijkl}\ e_{ij}(\ul{v})
    \frac{e_{kl}(\ul{u}) - e_{kl}(\ul{u}_0)}{\dt}$
    :arguments: ts.dt : $\dt$, material : $D_{ijkl}$, virtual : $\ul{v}$,
    state : $\ul{u}$ (displacements of current time step), parameter : $\ul{u}_0$
    (known displacements of previous time step)
    """
    name = 'dw_lin_viscous'
    argTypes = ('ts', 'material', 'virtual', 'state', 'parameter')
    geometry = [(Volume, 'virtual')]
    useCaches = {'cauchy_strain' : [['state', {'strain' : (2,2),
                                               'dstrain' : (1,1)}]]}

    ##
    # c: 25.03.2008, r: 25.03.2008
    def buildCFunArgs( self, dt, mat, state, ap, vg ):
        matQP = mat[nm.newaxis,:,:].repeat( self.dataShape[1], 0 )
        cache = self.getCache( 'cauchy_strain', 0 )
        dstrain = cache( 'dstrain', self.getCurrentGroup(), 0, state = state )
        return 1.0 / dt, dstrain, matQP, vg

    ##
    # c: 03.08.2006, r: 25.03.2008
    def __call__( self, diffVar = None, chunkSize = None, **kwargs ):
        ts, mat, virtual, state, state0 = self.getArgs( **kwargs )
        ap, vg = virtual.getApproximation( self.getCurrentGroup(), 'Volume' )

        shape, mode = self.getShape( diffVar, chunkSize, ap )
        fargs = self.buildCFunArgs( ts.dt, material, state, ap, vg )
        
        for out, chunk in self.charFun( chunkSize, shape ):
            status = self.function( out, *fargs + (chunk, mode) )
            yield out, chunk, status

##
# 14.09.2006, c
class LinearViscousTHTerm( LinearElasticTerm ):
    r""":definition: $\int_{\Omega} \left [\int_0^t
    \Hcal_{ijkl}(t-\tau)\,\tdiff{e_{kl}(\ul{u}(\tau))}{\tau}
    \difd{\tau} \right]\,e_{ij}(\ul{v})$"""
    name = 'dw_lin_viscous_th'
    argTypes = ('ts', 'material', 'virtual', 'state', 'parameter')
    geometry = [(Volume, 'virtual')]
    useCaches = {'cauchy_strain' : [['state', {'strain' : (2,2),
                                               'dstrain' : (-1,-1)}]]}

    ##
    # c: 14.09.2006, r: 18.06.2008
    def __call__( self, diffVar = None, chunkSize = None, **kwargs ):
        """history for now is just state_0, it is not used anyway, as the
        history is held in the dstrain cache"""
        ts, mats, virtual, state, history = self.getArgs( **kwargs )
        ap, vg = virtual.getApproximation( self.getCurrentGroup(), 'Volume' )

        shape, mode = self.getShape( diffVar, chunkSize, ap )
        nEl, nQP, dim, nEP = self.dataShape

        if (ts.step == 0) and (mode == 0):
            raise StopIteration

        if mode == 1:
            matQP = mats[0][nm.newaxis,:,:].repeat( nQP, 0 )
            for out, chunk in self.charFun( chunkSize, shape ):
                status = self.function( out, 1.0, nm.empty( 0 ),
                                        matQP, vg, chunk, 1 )
                yield out, chunk, status
        else:
            cache = self.getCache( 'cauchy_strain', 0 )
            for out, chunk in self.charFun( chunkSize, shape, zero = True ):
                out1 = nm.empty_like( out )
##                 ttt = 0.0
##                 itt = time.clock()
                for ii, mat in enumerate( mats ):
                    matQP = mat[nm.newaxis,:,:].repeat( nQP, 0 )
                    dstrain = cache( 'dstrain', self.getCurrentGroup(), ii,
                                     state = state, history = history )
##                     tt = time.clock()
                    status = self.function( out1, 1.0, dstrain,
                                            matQP, vg, chunk, 0 )
##                     ttt += time.clock() - tt
                    out += out1
##                 itt = time.clock() - itt
##                 print ttt, itt
                yield out, chunk, status

##
# 21.09.2006, c
class CauchyStrainTerm( Term ):
    r""":description: Cauchy strain tensor averaged in elements.
    :definition: vector of $\forall K \in \Tcal_h: \int_{T_K} \ull{e}(\ul{w}) /
    \int_{T_K} 1$
    """
    name = 'de_cauchy_strain'
    argTypes = ('parameter',)
    geometry = [(Volume, 'parameter')]

    ##
    # 05.10.2007
    def __init__( self, region, name = name, sign = 1 ):
        Term.__init__( self, region, name, sign, terms.de_cauchy_strain )

    ##
    # c: 25.03.2008, r: 25.03.2008
    def getShape( self, diffVar, chunkSize, apr, apc = None ):
        self.dataShape = apr.getVDataShape( self.integralName )
        nEl, nQP, dim, nEP = self.dataShape
        
        if diffVar is None:
            return chunkSize, 1, dim * (dim + 1) / 2, 1
        else:
            raise StopIteration

    ##
    # c: 25.03.2008, r: 25.03.2008
    def buildCFunArgs( self, state, ap, vg, **kwargs ):
        vec, indx = state()
        return vec, indx.start, vg, ap.econn
        
    ##
    # c: 21.09.2006, r: 06.05.2008
    def __call__( self, diffVar = None, chunkSize = None, **kwargs ):
        parameter, = self.getArgs( ['parameter'], **kwargs )
        ap, vg = parameter.getApproximation( self.getCurrentGroup(), 'Volume' )

        shape = self.getShape( diffVar, chunkSize, ap )
        fargs = self.buildCFunArgs( parameter, ap, vg, **kwargs )
        
        for out, chunk in self.charFun( chunkSize, shape ):
            status = self.function( out, *fargs + (chunk,) )
            out1 = out / vg.variable( 2 )
            yield out1, chunk, status

##
# c: 25.03.2008
class CauchyStressTerm( CauchyStrainTerm ):
    r""":description: Cauchy stress tensor averaged in elements.
    :definition: vector of $\forall K \in \Tcal_h:
    \int_{T_K} D_{ijkl} e_kl(\ul{w}) / \int_{T_K} 1$
    """
    name = 'de_cauchy_stress'
    argTypes = ('material', 'parameter')
    geometry = [(Volume, 'parameter')]
    useCaches = {'cauchy_strain' : [['parameter']]}

    ##
    # c: 25.03.2008, r: 25.03.2008
    def __init__( self, region, name = name, sign = 1 ):
        Term.__init__( self, region, name, sign, terms.de_cauchy_stress )

    ##
    # c: 25.03.2008, r: 31.03.2008
    def buildCFunArgs( self, state, ap, vg, **kwargs ):
        mat, = self.getArgs( ['material'], **kwargs )
        matQP = mat[nm.newaxis,:,:].repeat( self.dataShape[1], 0 )
        cache = self.getCache( 'cauchy_strain', 0 )
        strain = cache( 'strain', self.getCurrentGroup(), 0, state = state )
        return strain, matQP, vg