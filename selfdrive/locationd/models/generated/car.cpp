#include "car.h"

namespace {
#define DIM 9
#define EDIM 9
#define MEDIM 9
typedef void (*Hfun)(double *, double *, double *);

double mass;

void set_mass(double x){ mass = x;}

double rotational_inertia;

void set_rotational_inertia(double x){ rotational_inertia = x;}

double center_to_front;

void set_center_to_front(double x){ center_to_front = x;}

double center_to_rear;

void set_center_to_rear(double x){ center_to_rear = x;}

double stiffness_front;

void set_stiffness_front(double x){ stiffness_front = x;}

double stiffness_rear;

void set_stiffness_rear(double x){ stiffness_rear = x;}
const static double MAHA_THRESH_25 = 3.8414588206941227;
const static double MAHA_THRESH_24 = 5.991464547107981;
const static double MAHA_THRESH_30 = 3.8414588206941227;
const static double MAHA_THRESH_26 = 3.8414588206941227;
const static double MAHA_THRESH_27 = 3.8414588206941227;
const static double MAHA_THRESH_29 = 3.8414588206941227;
const static double MAHA_THRESH_28 = 3.8414588206941227;
const static double MAHA_THRESH_31 = 3.8414588206941227;

/******************************************************************************
 *                      Code generated with SymPy 1.14.0                      *
 *                                                                            *
 *              See http://www.sympy.org/ for more information.               *
 *                                                                            *
 *                         This file is part of 'ekf'                         *
 ******************************************************************************/
void err_fun(double *nom_x, double *delta_x, double *out_6350667449765540099) {
   out_6350667449765540099[0] = delta_x[0] + nom_x[0];
   out_6350667449765540099[1] = delta_x[1] + nom_x[1];
   out_6350667449765540099[2] = delta_x[2] + nom_x[2];
   out_6350667449765540099[3] = delta_x[3] + nom_x[3];
   out_6350667449765540099[4] = delta_x[4] + nom_x[4];
   out_6350667449765540099[5] = delta_x[5] + nom_x[5];
   out_6350667449765540099[6] = delta_x[6] + nom_x[6];
   out_6350667449765540099[7] = delta_x[7] + nom_x[7];
   out_6350667449765540099[8] = delta_x[8] + nom_x[8];
}
void inv_err_fun(double *nom_x, double *true_x, double *out_7446146129217267588) {
   out_7446146129217267588[0] = -nom_x[0] + true_x[0];
   out_7446146129217267588[1] = -nom_x[1] + true_x[1];
   out_7446146129217267588[2] = -nom_x[2] + true_x[2];
   out_7446146129217267588[3] = -nom_x[3] + true_x[3];
   out_7446146129217267588[4] = -nom_x[4] + true_x[4];
   out_7446146129217267588[5] = -nom_x[5] + true_x[5];
   out_7446146129217267588[6] = -nom_x[6] + true_x[6];
   out_7446146129217267588[7] = -nom_x[7] + true_x[7];
   out_7446146129217267588[8] = -nom_x[8] + true_x[8];
}
void H_mod_fun(double *state, double *out_1654058053598813317) {
   out_1654058053598813317[0] = 1.0;
   out_1654058053598813317[1] = 0.0;
   out_1654058053598813317[2] = 0.0;
   out_1654058053598813317[3] = 0.0;
   out_1654058053598813317[4] = 0.0;
   out_1654058053598813317[5] = 0.0;
   out_1654058053598813317[6] = 0.0;
   out_1654058053598813317[7] = 0.0;
   out_1654058053598813317[8] = 0.0;
   out_1654058053598813317[9] = 0.0;
   out_1654058053598813317[10] = 1.0;
   out_1654058053598813317[11] = 0.0;
   out_1654058053598813317[12] = 0.0;
   out_1654058053598813317[13] = 0.0;
   out_1654058053598813317[14] = 0.0;
   out_1654058053598813317[15] = 0.0;
   out_1654058053598813317[16] = 0.0;
   out_1654058053598813317[17] = 0.0;
   out_1654058053598813317[18] = 0.0;
   out_1654058053598813317[19] = 0.0;
   out_1654058053598813317[20] = 1.0;
   out_1654058053598813317[21] = 0.0;
   out_1654058053598813317[22] = 0.0;
   out_1654058053598813317[23] = 0.0;
   out_1654058053598813317[24] = 0.0;
   out_1654058053598813317[25] = 0.0;
   out_1654058053598813317[26] = 0.0;
   out_1654058053598813317[27] = 0.0;
   out_1654058053598813317[28] = 0.0;
   out_1654058053598813317[29] = 0.0;
   out_1654058053598813317[30] = 1.0;
   out_1654058053598813317[31] = 0.0;
   out_1654058053598813317[32] = 0.0;
   out_1654058053598813317[33] = 0.0;
   out_1654058053598813317[34] = 0.0;
   out_1654058053598813317[35] = 0.0;
   out_1654058053598813317[36] = 0.0;
   out_1654058053598813317[37] = 0.0;
   out_1654058053598813317[38] = 0.0;
   out_1654058053598813317[39] = 0.0;
   out_1654058053598813317[40] = 1.0;
   out_1654058053598813317[41] = 0.0;
   out_1654058053598813317[42] = 0.0;
   out_1654058053598813317[43] = 0.0;
   out_1654058053598813317[44] = 0.0;
   out_1654058053598813317[45] = 0.0;
   out_1654058053598813317[46] = 0.0;
   out_1654058053598813317[47] = 0.0;
   out_1654058053598813317[48] = 0.0;
   out_1654058053598813317[49] = 0.0;
   out_1654058053598813317[50] = 1.0;
   out_1654058053598813317[51] = 0.0;
   out_1654058053598813317[52] = 0.0;
   out_1654058053598813317[53] = 0.0;
   out_1654058053598813317[54] = 0.0;
   out_1654058053598813317[55] = 0.0;
   out_1654058053598813317[56] = 0.0;
   out_1654058053598813317[57] = 0.0;
   out_1654058053598813317[58] = 0.0;
   out_1654058053598813317[59] = 0.0;
   out_1654058053598813317[60] = 1.0;
   out_1654058053598813317[61] = 0.0;
   out_1654058053598813317[62] = 0.0;
   out_1654058053598813317[63] = 0.0;
   out_1654058053598813317[64] = 0.0;
   out_1654058053598813317[65] = 0.0;
   out_1654058053598813317[66] = 0.0;
   out_1654058053598813317[67] = 0.0;
   out_1654058053598813317[68] = 0.0;
   out_1654058053598813317[69] = 0.0;
   out_1654058053598813317[70] = 1.0;
   out_1654058053598813317[71] = 0.0;
   out_1654058053598813317[72] = 0.0;
   out_1654058053598813317[73] = 0.0;
   out_1654058053598813317[74] = 0.0;
   out_1654058053598813317[75] = 0.0;
   out_1654058053598813317[76] = 0.0;
   out_1654058053598813317[77] = 0.0;
   out_1654058053598813317[78] = 0.0;
   out_1654058053598813317[79] = 0.0;
   out_1654058053598813317[80] = 1.0;
}
void f_fun(double *state, double dt, double *out_5983655230060451393) {
   out_5983655230060451393[0] = state[0];
   out_5983655230060451393[1] = state[1];
   out_5983655230060451393[2] = state[2];
   out_5983655230060451393[3] = state[3];
   out_5983655230060451393[4] = state[4];
   out_5983655230060451393[5] = dt*((-state[4] + (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(mass*state[4]))*state[6] - 9.8100000000000005*state[8] + stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(mass*state[1]) + (-stiffness_front*state[0] - stiffness_rear*state[0])*state[5]/(mass*state[4])) + state[5];
   out_5983655230060451393[6] = dt*(center_to_front*stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(rotational_inertia*state[1]) + (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])*state[5]/(rotational_inertia*state[4]) + (-pow(center_to_front, 2)*stiffness_front*state[0] - pow(center_to_rear, 2)*stiffness_rear*state[0])*state[6]/(rotational_inertia*state[4])) + state[6];
   out_5983655230060451393[7] = state[7];
   out_5983655230060451393[8] = state[8];
}
void F_fun(double *state, double dt, double *out_5804942899831410446) {
   out_5804942899831410446[0] = 1;
   out_5804942899831410446[1] = 0;
   out_5804942899831410446[2] = 0;
   out_5804942899831410446[3] = 0;
   out_5804942899831410446[4] = 0;
   out_5804942899831410446[5] = 0;
   out_5804942899831410446[6] = 0;
   out_5804942899831410446[7] = 0;
   out_5804942899831410446[8] = 0;
   out_5804942899831410446[9] = 0;
   out_5804942899831410446[10] = 1;
   out_5804942899831410446[11] = 0;
   out_5804942899831410446[12] = 0;
   out_5804942899831410446[13] = 0;
   out_5804942899831410446[14] = 0;
   out_5804942899831410446[15] = 0;
   out_5804942899831410446[16] = 0;
   out_5804942899831410446[17] = 0;
   out_5804942899831410446[18] = 0;
   out_5804942899831410446[19] = 0;
   out_5804942899831410446[20] = 1;
   out_5804942899831410446[21] = 0;
   out_5804942899831410446[22] = 0;
   out_5804942899831410446[23] = 0;
   out_5804942899831410446[24] = 0;
   out_5804942899831410446[25] = 0;
   out_5804942899831410446[26] = 0;
   out_5804942899831410446[27] = 0;
   out_5804942899831410446[28] = 0;
   out_5804942899831410446[29] = 0;
   out_5804942899831410446[30] = 1;
   out_5804942899831410446[31] = 0;
   out_5804942899831410446[32] = 0;
   out_5804942899831410446[33] = 0;
   out_5804942899831410446[34] = 0;
   out_5804942899831410446[35] = 0;
   out_5804942899831410446[36] = 0;
   out_5804942899831410446[37] = 0;
   out_5804942899831410446[38] = 0;
   out_5804942899831410446[39] = 0;
   out_5804942899831410446[40] = 1;
   out_5804942899831410446[41] = 0;
   out_5804942899831410446[42] = 0;
   out_5804942899831410446[43] = 0;
   out_5804942899831410446[44] = 0;
   out_5804942899831410446[45] = dt*(stiffness_front*(-state[2] - state[3] + state[7])/(mass*state[1]) + (-stiffness_front - stiffness_rear)*state[5]/(mass*state[4]) + (-center_to_front*stiffness_front + center_to_rear*stiffness_rear)*state[6]/(mass*state[4]));
   out_5804942899831410446[46] = -dt*stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(mass*pow(state[1], 2));
   out_5804942899831410446[47] = -dt*stiffness_front*state[0]/(mass*state[1]);
   out_5804942899831410446[48] = -dt*stiffness_front*state[0]/(mass*state[1]);
   out_5804942899831410446[49] = dt*((-1 - (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(mass*pow(state[4], 2)))*state[6] - (-stiffness_front*state[0] - stiffness_rear*state[0])*state[5]/(mass*pow(state[4], 2)));
   out_5804942899831410446[50] = dt*(-stiffness_front*state[0] - stiffness_rear*state[0])/(mass*state[4]) + 1;
   out_5804942899831410446[51] = dt*(-state[4] + (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(mass*state[4]));
   out_5804942899831410446[52] = dt*stiffness_front*state[0]/(mass*state[1]);
   out_5804942899831410446[53] = -9.8100000000000005*dt;
   out_5804942899831410446[54] = dt*(center_to_front*stiffness_front*(-state[2] - state[3] + state[7])/(rotational_inertia*state[1]) + (-center_to_front*stiffness_front + center_to_rear*stiffness_rear)*state[5]/(rotational_inertia*state[4]) + (-pow(center_to_front, 2)*stiffness_front - pow(center_to_rear, 2)*stiffness_rear)*state[6]/(rotational_inertia*state[4]));
   out_5804942899831410446[55] = -center_to_front*dt*stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(rotational_inertia*pow(state[1], 2));
   out_5804942899831410446[56] = -center_to_front*dt*stiffness_front*state[0]/(rotational_inertia*state[1]);
   out_5804942899831410446[57] = -center_to_front*dt*stiffness_front*state[0]/(rotational_inertia*state[1]);
   out_5804942899831410446[58] = dt*(-(-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])*state[5]/(rotational_inertia*pow(state[4], 2)) - (-pow(center_to_front, 2)*stiffness_front*state[0] - pow(center_to_rear, 2)*stiffness_rear*state[0])*state[6]/(rotational_inertia*pow(state[4], 2)));
   out_5804942899831410446[59] = dt*(-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(rotational_inertia*state[4]);
   out_5804942899831410446[60] = dt*(-pow(center_to_front, 2)*stiffness_front*state[0] - pow(center_to_rear, 2)*stiffness_rear*state[0])/(rotational_inertia*state[4]) + 1;
   out_5804942899831410446[61] = center_to_front*dt*stiffness_front*state[0]/(rotational_inertia*state[1]);
   out_5804942899831410446[62] = 0;
   out_5804942899831410446[63] = 0;
   out_5804942899831410446[64] = 0;
   out_5804942899831410446[65] = 0;
   out_5804942899831410446[66] = 0;
   out_5804942899831410446[67] = 0;
   out_5804942899831410446[68] = 0;
   out_5804942899831410446[69] = 0;
   out_5804942899831410446[70] = 1;
   out_5804942899831410446[71] = 0;
   out_5804942899831410446[72] = 0;
   out_5804942899831410446[73] = 0;
   out_5804942899831410446[74] = 0;
   out_5804942899831410446[75] = 0;
   out_5804942899831410446[76] = 0;
   out_5804942899831410446[77] = 0;
   out_5804942899831410446[78] = 0;
   out_5804942899831410446[79] = 0;
   out_5804942899831410446[80] = 1;
}
void h_25(double *state, double *unused, double *out_1034218770023834114) {
   out_1034218770023834114[0] = state[6];
}
void H_25(double *state, double *unused, double *out_7539130172313423920) {
   out_7539130172313423920[0] = 0;
   out_7539130172313423920[1] = 0;
   out_7539130172313423920[2] = 0;
   out_7539130172313423920[3] = 0;
   out_7539130172313423920[4] = 0;
   out_7539130172313423920[5] = 0;
   out_7539130172313423920[6] = 1;
   out_7539130172313423920[7] = 0;
   out_7539130172313423920[8] = 0;
}
void h_24(double *state, double *unused, double *out_3223690919535887602) {
   out_3223690919535887602[0] = state[4];
   out_3223690919535887602[1] = state[5];
}
void H_24(double *state, double *unused, double *out_6161104574429618662) {
   out_6161104574429618662[0] = 0;
   out_6161104574429618662[1] = 0;
   out_6161104574429618662[2] = 0;
   out_6161104574429618662[3] = 0;
   out_6161104574429618662[4] = 1;
   out_6161104574429618662[5] = 0;
   out_6161104574429618662[6] = 0;
   out_6161104574429618662[7] = 0;
   out_6161104574429618662[8] = 0;
   out_6161104574429618662[9] = 0;
   out_6161104574429618662[10] = 0;
   out_6161104574429618662[11] = 0;
   out_6161104574429618662[12] = 0;
   out_6161104574429618662[13] = 0;
   out_6161104574429618662[14] = 1;
   out_6161104574429618662[15] = 0;
   out_6161104574429618662[16] = 0;
   out_6161104574429618662[17] = 0;
}
void h_30(double *state, double *unused, double *out_1492420132182395776) {
   out_1492420132182395776[0] = state[4];
}
void H_30(double *state, double *unused, double *out_622439830821807165) {
   out_622439830821807165[0] = 0;
   out_622439830821807165[1] = 0;
   out_622439830821807165[2] = 0;
   out_622439830821807165[3] = 0;
   out_622439830821807165[4] = 1;
   out_622439830821807165[5] = 0;
   out_622439830821807165[6] = 0;
   out_622439830821807165[7] = 0;
   out_622439830821807165[8] = 0;
}
void h_26(double *state, double *unused, double *out_6637310195298043313) {
   out_6637310195298043313[0] = state[7];
}
void H_26(double *state, double *unused, double *out_163753180431744809) {
   out_163753180431744809[0] = 0;
   out_163753180431744809[1] = 0;
   out_163753180431744809[2] = 0;
   out_163753180431744809[3] = 0;
   out_163753180431744809[4] = 0;
   out_163753180431744809[5] = 0;
   out_163753180431744809[6] = 0;
   out_163753180431744809[7] = 1;
   out_163753180431744809[8] = 0;
}
void h_27(double *state, double *unused, double *out_4191688445811490833) {
   out_4191688445811490833[0] = state[3];
}
void H_27(double *state, double *unused, double *out_2797203142622232076) {
   out_2797203142622232076[0] = 0;
   out_2797203142622232076[1] = 0;
   out_2797203142622232076[2] = 0;
   out_2797203142622232076[3] = 1;
   out_2797203142622232076[4] = 0;
   out_2797203142622232076[5] = 0;
   out_2797203142622232076[6] = 0;
   out_2797203142622232076[7] = 0;
   out_2797203142622232076[8] = 0;
}
void h_29(double *state, double *unused, double *out_7829137974065513183) {
   out_7829137974065513183[0] = state[1];
}
void H_29(double *state, double *unused, double *out_112208486507414981) {
   out_112208486507414981[0] = 0;
   out_112208486507414981[1] = 1;
   out_112208486507414981[2] = 0;
   out_112208486507414981[3] = 0;
   out_112208486507414981[4] = 0;
   out_112208486507414981[5] = 0;
   out_112208486507414981[6] = 0;
   out_112208486507414981[7] = 0;
   out_112208486507414981[8] = 0;
}
void h_28(double *state, double *unused, double *out_8589640527093119845) {
   out_8589640527093119845[0] = state[0];
}
void H_28(double *state, double *unused, double *out_5194607503576945555) {
   out_5194607503576945555[0] = 1;
   out_5194607503576945555[1] = 0;
   out_5194607503576945555[2] = 0;
   out_5194607503576945555[3] = 0;
   out_5194607503576945555[4] = 0;
   out_5194607503576945555[5] = 0;
   out_5194607503576945555[6] = 0;
   out_5194607503576945555[7] = 0;
   out_5194607503576945555[8] = 0;
}
void h_31(double *state, double *unused, double *out_6729046486796838327) {
   out_6729046486796838327[0] = state[8];
}
void H_31(double *state, double *unused, double *out_462454921801606667) {
   out_462454921801606667[0] = 0;
   out_462454921801606667[1] = 0;
   out_462454921801606667[2] = 0;
   out_462454921801606667[3] = 0;
   out_462454921801606667[4] = 0;
   out_462454921801606667[5] = 0;
   out_462454921801606667[6] = 0;
   out_462454921801606667[7] = 0;
   out_462454921801606667[8] = 1;
}
#include <eigen3/Eigen/Dense>
#include <iostream>

typedef Eigen::Matrix<double, DIM, DIM, Eigen::RowMajor> DDM;
typedef Eigen::Matrix<double, EDIM, EDIM, Eigen::RowMajor> EEM;
typedef Eigen::Matrix<double, DIM, EDIM, Eigen::RowMajor> DEM;

void predict(double *in_x, double *in_P, double *in_Q, double dt) {
  typedef Eigen::Matrix<double, MEDIM, MEDIM, Eigen::RowMajor> RRM;

  double nx[DIM] = {0};
  double in_F[EDIM*EDIM] = {0};

  // functions from sympy
  f_fun(in_x, dt, nx);
  F_fun(in_x, dt, in_F);


  EEM F(in_F);
  EEM P(in_P);
  EEM Q(in_Q);

  RRM F_main = F.topLeftCorner(MEDIM, MEDIM);
  P.topLeftCorner(MEDIM, MEDIM) = (F_main * P.topLeftCorner(MEDIM, MEDIM)) * F_main.transpose();
  P.topRightCorner(MEDIM, EDIM - MEDIM) = F_main * P.topRightCorner(MEDIM, EDIM - MEDIM);
  P.bottomLeftCorner(EDIM - MEDIM, MEDIM) = P.bottomLeftCorner(EDIM - MEDIM, MEDIM) * F_main.transpose();

  P = P + dt*Q;

  // copy out state
  memcpy(in_x, nx, DIM * sizeof(double));
  memcpy(in_P, P.data(), EDIM * EDIM * sizeof(double));
}

// note: extra_args dim only correct when null space projecting
// otherwise 1
template <int ZDIM, int EADIM, bool MAHA_TEST>
void update(double *in_x, double *in_P, Hfun h_fun, Hfun H_fun, Hfun Hea_fun, double *in_z, double *in_R, double *in_ea, double MAHA_THRESHOLD) {
  typedef Eigen::Matrix<double, ZDIM, ZDIM, Eigen::RowMajor> ZZM;
  typedef Eigen::Matrix<double, ZDIM, DIM, Eigen::RowMajor> ZDM;
  typedef Eigen::Matrix<double, Eigen::Dynamic, EDIM, Eigen::RowMajor> XEM;
  //typedef Eigen::Matrix<double, EDIM, ZDIM, Eigen::RowMajor> EZM;
  typedef Eigen::Matrix<double, Eigen::Dynamic, 1> X1M;
  typedef Eigen::Matrix<double, Eigen::Dynamic, Eigen::Dynamic, Eigen::RowMajor> XXM;

  double in_hx[ZDIM] = {0};
  double in_H[ZDIM * DIM] = {0};
  double in_H_mod[EDIM * DIM] = {0};
  double delta_x[EDIM] = {0};
  double x_new[DIM] = {0};


  // state x, P
  Eigen::Matrix<double, ZDIM, 1> z(in_z);
  EEM P(in_P);
  ZZM pre_R(in_R);

  // functions from sympy
  h_fun(in_x, in_ea, in_hx);
  H_fun(in_x, in_ea, in_H);
  ZDM pre_H(in_H);

  // get y (y = z - hx)
  Eigen::Matrix<double, ZDIM, 1> pre_y(in_hx); pre_y = z - pre_y;
  X1M y; XXM H; XXM R;
  if (Hea_fun){
    typedef Eigen::Matrix<double, ZDIM, EADIM, Eigen::RowMajor> ZAM;
    double in_Hea[ZDIM * EADIM] = {0};
    Hea_fun(in_x, in_ea, in_Hea);
    ZAM Hea(in_Hea);
    XXM A = Hea.transpose().fullPivLu().kernel();


    y = A.transpose() * pre_y;
    H = A.transpose() * pre_H;
    R = A.transpose() * pre_R * A;
  } else {
    y = pre_y;
    H = pre_H;
    R = pre_R;
  }
  // get modified H
  H_mod_fun(in_x, in_H_mod);
  DEM H_mod(in_H_mod);
  XEM H_err = H * H_mod;

  // Do mahalobis distance test
  if (MAHA_TEST){
    XXM a = (H_err * P * H_err.transpose() + R).inverse();
    double maha_dist = y.transpose() * a * y;
    if (maha_dist > MAHA_THRESHOLD){
      R = 1.0e16 * R;
    }
  }

  // Outlier resilient weighting
  double weight = 1;//(1.5)/(1 + y.squaredNorm()/R.sum());

  // kalman gains and I_KH
  XXM S = ((H_err * P) * H_err.transpose()) + R/weight;
  XEM KT = S.fullPivLu().solve(H_err * P.transpose());
  //EZM K = KT.transpose(); TODO: WHY DOES THIS NOT COMPILE?
  //EZM K = S.fullPivLu().solve(H_err * P.transpose()).transpose();
  //std::cout << "Here is the matrix rot:\n" << K << std::endl;
  EEM I_KH = Eigen::Matrix<double, EDIM, EDIM>::Identity() - (KT.transpose() * H_err);

  // update state by injecting dx
  Eigen::Matrix<double, EDIM, 1> dx(delta_x);
  dx  = (KT.transpose() * y);
  memcpy(delta_x, dx.data(), EDIM * sizeof(double));
  err_fun(in_x, delta_x, x_new);
  Eigen::Matrix<double, DIM, 1> x(x_new);

  // update cov
  P = ((I_KH * P) * I_KH.transpose()) + ((KT.transpose() * R) * KT);

  // copy out state
  memcpy(in_x, x.data(), DIM * sizeof(double));
  memcpy(in_P, P.data(), EDIM * EDIM * sizeof(double));
  memcpy(in_z, y.data(), y.rows() * sizeof(double));
}




}
extern "C" {

void car_update_25(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<1, 3, 0>(in_x, in_P, h_25, H_25, NULL, in_z, in_R, in_ea, MAHA_THRESH_25);
}
void car_update_24(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<2, 3, 0>(in_x, in_P, h_24, H_24, NULL, in_z, in_R, in_ea, MAHA_THRESH_24);
}
void car_update_30(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<1, 3, 0>(in_x, in_P, h_30, H_30, NULL, in_z, in_R, in_ea, MAHA_THRESH_30);
}
void car_update_26(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<1, 3, 0>(in_x, in_P, h_26, H_26, NULL, in_z, in_R, in_ea, MAHA_THRESH_26);
}
void car_update_27(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<1, 3, 0>(in_x, in_P, h_27, H_27, NULL, in_z, in_R, in_ea, MAHA_THRESH_27);
}
void car_update_29(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<1, 3, 0>(in_x, in_P, h_29, H_29, NULL, in_z, in_R, in_ea, MAHA_THRESH_29);
}
void car_update_28(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<1, 3, 0>(in_x, in_P, h_28, H_28, NULL, in_z, in_R, in_ea, MAHA_THRESH_28);
}
void car_update_31(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<1, 3, 0>(in_x, in_P, h_31, H_31, NULL, in_z, in_R, in_ea, MAHA_THRESH_31);
}
void car_err_fun(double *nom_x, double *delta_x, double *out_6350667449765540099) {
  err_fun(nom_x, delta_x, out_6350667449765540099);
}
void car_inv_err_fun(double *nom_x, double *true_x, double *out_7446146129217267588) {
  inv_err_fun(nom_x, true_x, out_7446146129217267588);
}
void car_H_mod_fun(double *state, double *out_1654058053598813317) {
  H_mod_fun(state, out_1654058053598813317);
}
void car_f_fun(double *state, double dt, double *out_5983655230060451393) {
  f_fun(state,  dt, out_5983655230060451393);
}
void car_F_fun(double *state, double dt, double *out_5804942899831410446) {
  F_fun(state,  dt, out_5804942899831410446);
}
void car_h_25(double *state, double *unused, double *out_1034218770023834114) {
  h_25(state, unused, out_1034218770023834114);
}
void car_H_25(double *state, double *unused, double *out_7539130172313423920) {
  H_25(state, unused, out_7539130172313423920);
}
void car_h_24(double *state, double *unused, double *out_3223690919535887602) {
  h_24(state, unused, out_3223690919535887602);
}
void car_H_24(double *state, double *unused, double *out_6161104574429618662) {
  H_24(state, unused, out_6161104574429618662);
}
void car_h_30(double *state, double *unused, double *out_1492420132182395776) {
  h_30(state, unused, out_1492420132182395776);
}
void car_H_30(double *state, double *unused, double *out_622439830821807165) {
  H_30(state, unused, out_622439830821807165);
}
void car_h_26(double *state, double *unused, double *out_6637310195298043313) {
  h_26(state, unused, out_6637310195298043313);
}
void car_H_26(double *state, double *unused, double *out_163753180431744809) {
  H_26(state, unused, out_163753180431744809);
}
void car_h_27(double *state, double *unused, double *out_4191688445811490833) {
  h_27(state, unused, out_4191688445811490833);
}
void car_H_27(double *state, double *unused, double *out_2797203142622232076) {
  H_27(state, unused, out_2797203142622232076);
}
void car_h_29(double *state, double *unused, double *out_7829137974065513183) {
  h_29(state, unused, out_7829137974065513183);
}
void car_H_29(double *state, double *unused, double *out_112208486507414981) {
  H_29(state, unused, out_112208486507414981);
}
void car_h_28(double *state, double *unused, double *out_8589640527093119845) {
  h_28(state, unused, out_8589640527093119845);
}
void car_H_28(double *state, double *unused, double *out_5194607503576945555) {
  H_28(state, unused, out_5194607503576945555);
}
void car_h_31(double *state, double *unused, double *out_6729046486796838327) {
  h_31(state, unused, out_6729046486796838327);
}
void car_H_31(double *state, double *unused, double *out_462454921801606667) {
  H_31(state, unused, out_462454921801606667);
}
void car_predict(double *in_x, double *in_P, double *in_Q, double dt) {
  predict(in_x, in_P, in_Q, dt);
}
void car_set_mass(double x) {
  set_mass(x);
}
void car_set_rotational_inertia(double x) {
  set_rotational_inertia(x);
}
void car_set_center_to_front(double x) {
  set_center_to_front(x);
}
void car_set_center_to_rear(double x) {
  set_center_to_rear(x);
}
void car_set_stiffness_front(double x) {
  set_stiffness_front(x);
}
void car_set_stiffness_rear(double x) {
  set_stiffness_rear(x);
}
}

const EKF car = {
  .name = "car",
  .kinds = { 25, 24, 30, 26, 27, 29, 28, 31 },
  .feature_kinds = {  },
  .f_fun = car_f_fun,
  .F_fun = car_F_fun,
  .err_fun = car_err_fun,
  .inv_err_fun = car_inv_err_fun,
  .H_mod_fun = car_H_mod_fun,
  .predict = car_predict,
  .hs = {
    { 25, car_h_25 },
    { 24, car_h_24 },
    { 30, car_h_30 },
    { 26, car_h_26 },
    { 27, car_h_27 },
    { 29, car_h_29 },
    { 28, car_h_28 },
    { 31, car_h_31 },
  },
  .Hs = {
    { 25, car_H_25 },
    { 24, car_H_24 },
    { 30, car_H_30 },
    { 26, car_H_26 },
    { 27, car_H_27 },
    { 29, car_H_29 },
    { 28, car_H_28 },
    { 31, car_H_31 },
  },
  .updates = {
    { 25, car_update_25 },
    { 24, car_update_24 },
    { 30, car_update_30 },
    { 26, car_update_26 },
    { 27, car_update_27 },
    { 29, car_update_29 },
    { 28, car_update_28 },
    { 31, car_update_31 },
  },
  .Hes = {
  },
  .sets = {
    { "mass", car_set_mass },
    { "rotational_inertia", car_set_rotational_inertia },
    { "center_to_front", car_set_center_to_front },
    { "center_to_rear", car_set_center_to_rear },
    { "stiffness_front", car_set_stiffness_front },
    { "stiffness_rear", car_set_stiffness_rear },
  },
  .extra_routines = {
  },
};

ekf_lib_init(car)
