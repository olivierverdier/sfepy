import numpy as nm

try:
    import sympy as sm
except ImportError:
    sm = None

from sfepy.base.testing import TestCommon
from sfepy.base.base import ordered_iteritems

def get_poly(order, dim, is_simplex=False):
    """
    Construct a polynomial of given `order` in space dimension `dim`,
    and integrate it symbolically over a rectangular or simplex domain
    for coordinates in [0, 1].
    """
    try:
        xs = sm.symarray('x', dim)
    except:
        xs = sm.symarray(dim, 'x')

    opd = max(1, int((order + 1) / dim))

    poly = 1.0
    oo = 0
    for x in xs:
        if (oo + opd) > order:
            opd = order - oo
            
        poly *= (x**opd + 1)
        oo += opd

    limits = [[xs[ii], 0, 1] for ii in range(dim)]
    if is_simplex:
        for ii in range(1, dim):
            for ip in range(0, ii):
                limits[ii][2] -= xs[ip]

    integral = sm.integrate(poly, *reversed(limits))

    return xs, poly, limits, integral

class Test(TestCommon):

    @staticmethod
    def from_conf( conf, options ):

        test = Test(conf=conf, options=options)
        return test

    def test_weight_consistency(self):
        """
        Test if integral of 1 (= sum of weights) gives the domain volume.
        """
        from sfepy.fem.quadratures import quadrature_tables

        ok = True
        for geometry, qps in ordered_iteritems(quadrature_tables):
            self.report('geometry:', geometry)
            for order, qp in ordered_iteritems(qps):
                _ok = nm.allclose(qp.weights.sum(), qp.volume,
                                  rtol=0.0, atol=1e-15)
                self.report('order %d: %s' % (order, _ok))

                ok = ok and _ok

        return ok

    def test_quadratures(self):
        """
        Test if the quadratures have orders they claim to have, using
        symbolic integration by sympy.
        """
        from sfepy.fem.quadratures import quadrature_tables
        from sfepy.fem.integrals import Integral

        if sm is None:
            self.report('cannot import sympy, skipping')
            return True

        quad = Integral('test_integral')

        ok = True
        failed = []
        for geometry, qps in ordered_iteritems(quadrature_tables):
            self.report('geometry:', geometry)

            for order, qp in ordered_iteritems(qps):
                self.report('order:', order)

                dim = int(geometry[0])
                n_v = int(geometry[2])
                is_simplex = n_v == (dim + 1)

                xs, poly, limits, integral = get_poly(order, dim,
                                                      is_simplex=is_simplex)

                self.report('  polynomial:', poly)
                self.report('  limits:', limits)
                self.report('  integral:', integral)

                def fun(coors):
                    vals = nm.empty(coors.shape[0], dtype=nm.float64)

                    subs = {}
                    for ir, cc in enumerate(coors):
                        for ic, x in enumerate(xs):
                            subs[x] = coors[ir,ic]
                        vals[ir] = float(poly.subs(subs))

                    return vals
                    
                val = quad.integrate(fun, order=order, geometry=geometry)
                _ok = nm.allclose(val, float(integral), rtol=0.0, atol=1e-15)

                self.report('  sym. == num.: %f == %f -> %s' %
                            (float(integral), val, _ok))

                if not _ok:
                    failed.append((geometry, order, float(integral), val))

                ok = ok and _ok

        if not ok:
            self.report('failed:')
            for aux in failed:
                self.report(aux)

        return ok
