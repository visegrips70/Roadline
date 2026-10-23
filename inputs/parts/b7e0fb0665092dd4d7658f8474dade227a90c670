#pragma once
#include "rednose/helpers/ekf.h"
extern "C" {
void car_update_25(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void car_update_24(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void car_update_30(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void car_update_26(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void car_update_27(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void car_update_29(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void car_update_28(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void car_update_31(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void car_err_fun(double *nom_x, double *delta_x, double *out_6350667449765540099);
void car_inv_err_fun(double *nom_x, double *true_x, double *out_7446146129217267588);
void car_H_mod_fun(double *state, double *out_1654058053598813317);
void car_f_fun(double *state, double dt, double *out_5983655230060451393);
void car_F_fun(double *state, double dt, double *out_5804942899831410446);
void car_h_25(double *state, double *unused, double *out_1034218770023834114);
void car_H_25(double *state, double *unused, double *out_7539130172313423920);
void car_h_24(double *state, double *unused, double *out_3223690919535887602);
void car_H_24(double *state, double *unused, double *out_6161104574429618662);
void car_h_30(double *state, double *unused, double *out_1492420132182395776);
void car_H_30(double *state, double *unused, double *out_622439830821807165);
void car_h_26(double *state, double *unused, double *out_6637310195298043313);
void car_H_26(double *state, double *unused, double *out_163753180431744809);
void car_h_27(double *state, double *unused, double *out_4191688445811490833);
void car_H_27(double *state, double *unused, double *out_2797203142622232076);
void car_h_29(double *state, double *unused, double *out_7829137974065513183);
void car_H_29(double *state, double *unused, double *out_112208486507414981);
void car_h_28(double *state, double *unused, double *out_8589640527093119845);
void car_H_28(double *state, double *unused, double *out_5194607503576945555);
void car_h_31(double *state, double *unused, double *out_6729046486796838327);
void car_H_31(double *state, double *unused, double *out_462454921801606667);
void car_predict(double *in_x, double *in_P, double *in_Q, double dt);
void car_set_mass(double x);
void car_set_rotational_inertia(double x);
void car_set_center_to_front(double x);
void car_set_center_to_rear(double x);
void car_set_stiffness_front(double x);
void car_set_stiffness_rear(double x);
}