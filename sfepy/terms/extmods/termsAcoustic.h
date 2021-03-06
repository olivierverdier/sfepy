/*!
  @par Revision history:
  - 15.07.2008, c
*/
#ifndef _TERMSACOUSTIC_H_
#define _TERMSACOUSTIC_H_

#include "common.h"
BEGIN_C_DECLS

#include "fmfield.h"
#include "geometry.h"

int32 d_llaplace_p_sa( FMField *out,
		       FMField *stateU, FMField *stateV, FMField *stateW,
		       VolumeGeometry *vg,
		       int32 *conn, int32 nEl, int32 nEP,
		       int32 mode,
		       int32 *elList, int32 elList_nRow );

int32 d_llaplace_t_sa( FMField *out,
		       FMField *stateU, FMField *stateV, FMField *stateW,
		       VolumeGeometry *vg,
		       int32 *conn, int32 nEl, int32 nEP,
		       int32 mode,
		       int32 *elList, int32 elList_nRow );

int32 dw_llaplace( FMField *out, FMField *state,
		   FMField *coef, FMField *coef2, VolumeGeometry *vg,
		   int32 *conn, int32 nEl, int32 nEP,
		   int32 *elList, int32 elList_nRow,
		   int32 isDiff );

int32 d_llaplace( FMField *out, FMField *stateU, FMField *stateV,
		  FMField *coef, FMField *coef2, VolumeGeometry *vg,
		  int32 *conn, int32 nEl, int32 nEP,
		  int32 *elList, int32 elList_nRow );

int32 d_acoustic_surface( FMField *out, FMField *in,
			  FMField *coef, FMField *coef2, SurfaceGeometry *sg,
			  int32 *conn, int32 nEl, int32 nEP,
			  int32 *elList, int32 elList_nRow );

int32 dw_acoustic_integrate( FMField *out, FMField *coef, VolumeGeometry *vg,
			     int32 *conn, int32 nEl, int32 nEP,
			     int32 *elList, int32 elList_nRow,
			     int32 isDiff );

int32 d_acoustic_alpha( FMField *out, FMField *in,
			VolumeGeometry *vg,
			int32 *conn, int32 nEl, int32 nEP,
			int32 *elList, int32 elList_nRow );

END_C_DECLS

#endif /* Header */
