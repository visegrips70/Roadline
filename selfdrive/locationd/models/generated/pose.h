#pragma once
#include "rednose/helpers/ekf.h"
extern "C" {
void pose_update_4(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_10(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_13(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_14(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_err_fun(double *nom_x, double *delta_x, double *out_8639454197913824489);
void pose_inv_err_fun(double *nom_x, double *true_x, double *out_4523294178166863030);
void pose_H_mod_fun(double *state, double *out_2824299669774444771);
void pose_f_fun(double *state, double dt, double *out_7206685078178042626);
void pose_F_fun(double *state, double dt, double *out_503941297957831173);
void pose_h_4(double *state, double *unused, double *out_4034886323950789465);
void pose_H_4(double *state, double *unused, double *out_7438926706703761135);
void pose_h_10(double *state, double *unused, double *out_4450943621918908199);
void pose_H_10(double *state, double *unused, double *out_8909781275043755673);
void pose_h_13(double *state, double *unused, double *out_7684661552775223725);
void pose_H_13(double *state, double *unused, double *out_3397186158689089552);
void pose_h_14(double *state, double *unused, double *out_1124588162973463748);
void pose_H_14(double *state, double *unused, double *out_7044576510666305952);
void pose_predict(double *in_x, double *in_P, double *in_Q, double dt);
}