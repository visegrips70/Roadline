#include "pose.h"

namespace {
#define DIM 18
#define EDIM 18
#define MEDIM 18
typedef void (*Hfun)(double *, double *, double *);
const static double MAHA_THRESH_4 = 7.814727903251177;
const static double MAHA_THRESH_10 = 7.814727903251177;
const static double MAHA_THRESH_13 = 7.814727903251177;
const static double MAHA_THRESH_14 = 7.814727903251177;

/******************************************************************************
 *                      Code generated with SymPy 1.14.0                      *
 *                                                                            *
 *              See http://www.sympy.org/ for more information.               *
 *                                                                            *
 *                         This file is part of 'ekf'                         *
 ******************************************************************************/
void err_fun(double *nom_x, double *delta_x, double *out_8639454197913824489) {
   out_8639454197913824489[0] = delta_x[0] + nom_x[0];
   out_8639454197913824489[1] = delta_x[1] + nom_x[1];
   out_8639454197913824489[2] = delta_x[2] + nom_x[2];
   out_8639454197913824489[3] = delta_x[3] + nom_x[3];
   out_8639454197913824489[4] = delta_x[4] + nom_x[4];
   out_8639454197913824489[5] = delta_x[5] + nom_x[5];
   out_8639454197913824489[6] = delta_x[6] + nom_x[6];
   out_8639454197913824489[7] = delta_x[7] + nom_x[7];
   out_8639454197913824489[8] = delta_x[8] + nom_x[8];
   out_8639454197913824489[9] = delta_x[9] + nom_x[9];
   out_8639454197913824489[10] = delta_x[10] + nom_x[10];
   out_8639454197913824489[11] = delta_x[11] + nom_x[11];
   out_8639454197913824489[12] = delta_x[12] + nom_x[12];
   out_8639454197913824489[13] = delta_x[13] + nom_x[13];
   out_8639454197913824489[14] = delta_x[14] + nom_x[14];
   out_8639454197913824489[15] = delta_x[15] + nom_x[15];
   out_8639454197913824489[16] = delta_x[16] + nom_x[16];
   out_8639454197913824489[17] = delta_x[17] + nom_x[17];
}
void inv_err_fun(double *nom_x, double *true_x, double *out_4523294178166863030) {
   out_4523294178166863030[0] = -nom_x[0] + true_x[0];
   out_4523294178166863030[1] = -nom_x[1] + true_x[1];
   out_4523294178166863030[2] = -nom_x[2] + true_x[2];
   out_4523294178166863030[3] = -nom_x[3] + true_x[3];
   out_4523294178166863030[4] = -nom_x[4] + true_x[4];
   out_4523294178166863030[5] = -nom_x[5] + true_x[5];
   out_4523294178166863030[6] = -nom_x[6] + true_x[6];
   out_4523294178166863030[7] = -nom_x[7] + true_x[7];
   out_4523294178166863030[8] = -nom_x[8] + true_x[8];
   out_4523294178166863030[9] = -nom_x[9] + true_x[9];
   out_4523294178166863030[10] = -nom_x[10] + true_x[10];
   out_4523294178166863030[11] = -nom_x[11] + true_x[11];
   out_4523294178166863030[12] = -nom_x[12] + true_x[12];
   out_4523294178166863030[13] = -nom_x[13] + true_x[13];
   out_4523294178166863030[14] = -nom_x[14] + true_x[14];
   out_4523294178166863030[15] = -nom_x[15] + true_x[15];
   out_4523294178166863030[16] = -nom_x[16] + true_x[16];
   out_4523294178166863030[17] = -nom_x[17] + true_x[17];
}
void H_mod_fun(double *state, double *out_2824299669774444771) {
   out_2824299669774444771[0] = 1.0;
   out_2824299669774444771[1] = 0.0;
   out_2824299669774444771[2] = 0.0;
   out_2824299669774444771[3] = 0.0;
   out_2824299669774444771[4] = 0.0;
   out_2824299669774444771[5] = 0.0;
   out_2824299669774444771[6] = 0.0;
   out_2824299669774444771[7] = 0.0;
   out_2824299669774444771[8] = 0.0;
   out_2824299669774444771[9] = 0.0;
   out_2824299669774444771[10] = 0.0;
   out_2824299669774444771[11] = 0.0;
   out_2824299669774444771[12] = 0.0;
   out_2824299669774444771[13] = 0.0;
   out_2824299669774444771[14] = 0.0;
   out_2824299669774444771[15] = 0.0;
   out_2824299669774444771[16] = 0.0;
   out_2824299669774444771[17] = 0.0;
   out_2824299669774444771[18] = 0.0;
   out_2824299669774444771[19] = 1.0;
   out_2824299669774444771[20] = 0.0;
   out_2824299669774444771[21] = 0.0;
   out_2824299669774444771[22] = 0.0;
   out_2824299669774444771[23] = 0.0;
   out_2824299669774444771[24] = 0.0;
   out_2824299669774444771[25] = 0.0;
   out_2824299669774444771[26] = 0.0;
   out_2824299669774444771[27] = 0.0;
   out_2824299669774444771[28] = 0.0;
   out_2824299669774444771[29] = 0.0;
   out_2824299669774444771[30] = 0.0;
   out_2824299669774444771[31] = 0.0;
   out_2824299669774444771[32] = 0.0;
   out_2824299669774444771[33] = 0.0;
   out_2824299669774444771[34] = 0.0;
   out_2824299669774444771[35] = 0.0;
   out_2824299669774444771[36] = 0.0;
   out_2824299669774444771[37] = 0.0;
   out_2824299669774444771[38] = 1.0;
   out_2824299669774444771[39] = 0.0;
   out_2824299669774444771[40] = 0.0;
   out_2824299669774444771[41] = 0.0;
   out_2824299669774444771[42] = 0.0;
   out_2824299669774444771[43] = 0.0;
   out_2824299669774444771[44] = 0.0;
   out_2824299669774444771[45] = 0.0;
   out_2824299669774444771[46] = 0.0;
   out_2824299669774444771[47] = 0.0;
   out_2824299669774444771[48] = 0.0;
   out_2824299669774444771[49] = 0.0;
   out_2824299669774444771[50] = 0.0;
   out_2824299669774444771[51] = 0.0;
   out_2824299669774444771[52] = 0.0;
   out_2824299669774444771[53] = 0.0;
   out_2824299669774444771[54] = 0.0;
   out_2824299669774444771[55] = 0.0;
   out_2824299669774444771[56] = 0.0;
   out_2824299669774444771[57] = 1.0;
   out_2824299669774444771[58] = 0.0;
   out_2824299669774444771[59] = 0.0;
   out_2824299669774444771[60] = 0.0;
   out_2824299669774444771[61] = 0.0;
   out_2824299669774444771[62] = 0.0;
   out_2824299669774444771[63] = 0.0;
   out_2824299669774444771[64] = 0.0;
   out_2824299669774444771[65] = 0.0;
   out_2824299669774444771[66] = 0.0;
   out_2824299669774444771[67] = 0.0;
   out_2824299669774444771[68] = 0.0;
   out_2824299669774444771[69] = 0.0;
   out_2824299669774444771[70] = 0.0;
   out_2824299669774444771[71] = 0.0;
   out_2824299669774444771[72] = 0.0;
   out_2824299669774444771[73] = 0.0;
   out_2824299669774444771[74] = 0.0;
   out_2824299669774444771[75] = 0.0;
   out_2824299669774444771[76] = 1.0;
   out_2824299669774444771[77] = 0.0;
   out_2824299669774444771[78] = 0.0;
   out_2824299669774444771[79] = 0.0;
   out_2824299669774444771[80] = 0.0;
   out_2824299669774444771[81] = 0.0;
   out_2824299669774444771[82] = 0.0;
   out_2824299669774444771[83] = 0.0;
   out_2824299669774444771[84] = 0.0;
   out_2824299669774444771[85] = 0.0;
   out_2824299669774444771[86] = 0.0;
   out_2824299669774444771[87] = 0.0;
   out_2824299669774444771[88] = 0.0;
   out_2824299669774444771[89] = 0.0;
   out_2824299669774444771[90] = 0.0;
   out_2824299669774444771[91] = 0.0;
   out_2824299669774444771[92] = 0.0;
   out_2824299669774444771[93] = 0.0;
   out_2824299669774444771[94] = 0.0;
   out_2824299669774444771[95] = 1.0;
   out_2824299669774444771[96] = 0.0;
   out_2824299669774444771[97] = 0.0;
   out_2824299669774444771[98] = 0.0;
   out_2824299669774444771[99] = 0.0;
   out_2824299669774444771[100] = 0.0;
   out_2824299669774444771[101] = 0.0;
   out_2824299669774444771[102] = 0.0;
   out_2824299669774444771[103] = 0.0;
   out_2824299669774444771[104] = 0.0;
   out_2824299669774444771[105] = 0.0;
   out_2824299669774444771[106] = 0.0;
   out_2824299669774444771[107] = 0.0;
   out_2824299669774444771[108] = 0.0;
   out_2824299669774444771[109] = 0.0;
   out_2824299669774444771[110] = 0.0;
   out_2824299669774444771[111] = 0.0;
   out_2824299669774444771[112] = 0.0;
   out_2824299669774444771[113] = 0.0;
   out_2824299669774444771[114] = 1.0;
   out_2824299669774444771[115] = 0.0;
   out_2824299669774444771[116] = 0.0;
   out_2824299669774444771[117] = 0.0;
   out_2824299669774444771[118] = 0.0;
   out_2824299669774444771[119] = 0.0;
   out_2824299669774444771[120] = 0.0;
   out_2824299669774444771[121] = 0.0;
   out_2824299669774444771[122] = 0.0;
   out_2824299669774444771[123] = 0.0;
   out_2824299669774444771[124] = 0.0;
   out_2824299669774444771[125] = 0.0;
   out_2824299669774444771[126] = 0.0;
   out_2824299669774444771[127] = 0.0;
   out_2824299669774444771[128] = 0.0;
   out_2824299669774444771[129] = 0.0;
   out_2824299669774444771[130] = 0.0;
   out_2824299669774444771[131] = 0.0;
   out_2824299669774444771[132] = 0.0;
   out_2824299669774444771[133] = 1.0;
   out_2824299669774444771[134] = 0.0;
   out_2824299669774444771[135] = 0.0;
   out_2824299669774444771[136] = 0.0;
   out_2824299669774444771[137] = 0.0;
   out_2824299669774444771[138] = 0.0;
   out_2824299669774444771[139] = 0.0;
   out_2824299669774444771[140] = 0.0;
   out_2824299669774444771[141] = 0.0;
   out_2824299669774444771[142] = 0.0;
   out_2824299669774444771[143] = 0.0;
   out_2824299669774444771[144] = 0.0;
   out_2824299669774444771[145] = 0.0;
   out_2824299669774444771[146] = 0.0;
   out_2824299669774444771[147] = 0.0;
   out_2824299669774444771[148] = 0.0;
   out_2824299669774444771[149] = 0.0;
   out_2824299669774444771[150] = 0.0;
   out_2824299669774444771[151] = 0.0;
   out_2824299669774444771[152] = 1.0;
   out_2824299669774444771[153] = 0.0;
   out_2824299669774444771[154] = 0.0;
   out_2824299669774444771[155] = 0.0;
   out_2824299669774444771[156] = 0.0;
   out_2824299669774444771[157] = 0.0;
   out_2824299669774444771[158] = 0.0;
   out_2824299669774444771[159] = 0.0;
   out_2824299669774444771[160] = 0.0;
   out_2824299669774444771[161] = 0.0;
   out_2824299669774444771[162] = 0.0;
   out_2824299669774444771[163] = 0.0;
   out_2824299669774444771[164] = 0.0;
   out_2824299669774444771[165] = 0.0;
   out_2824299669774444771[166] = 0.0;
   out_2824299669774444771[167] = 0.0;
   out_2824299669774444771[168] = 0.0;
   out_2824299669774444771[169] = 0.0;
   out_2824299669774444771[170] = 0.0;
   out_2824299669774444771[171] = 1.0;
   out_2824299669774444771[172] = 0.0;
   out_2824299669774444771[173] = 0.0;
   out_2824299669774444771[174] = 0.0;
   out_2824299669774444771[175] = 0.0;
   out_2824299669774444771[176] = 0.0;
   out_2824299669774444771[177] = 0.0;
   out_2824299669774444771[178] = 0.0;
   out_2824299669774444771[179] = 0.0;
   out_2824299669774444771[180] = 0.0;
   out_2824299669774444771[181] = 0.0;
   out_2824299669774444771[182] = 0.0;
   out_2824299669774444771[183] = 0.0;
   out_2824299669774444771[184] = 0.0;
   out_2824299669774444771[185] = 0.0;
   out_2824299669774444771[186] = 0.0;
   out_2824299669774444771[187] = 0.0;
   out_2824299669774444771[188] = 0.0;
   out_2824299669774444771[189] = 0.0;
   out_2824299669774444771[190] = 1.0;
   out_2824299669774444771[191] = 0.0;
   out_2824299669774444771[192] = 0.0;
   out_2824299669774444771[193] = 0.0;
   out_2824299669774444771[194] = 0.0;
   out_2824299669774444771[195] = 0.0;
   out_2824299669774444771[196] = 0.0;
   out_2824299669774444771[197] = 0.0;
   out_2824299669774444771[198] = 0.0;
   out_2824299669774444771[199] = 0.0;
   out_2824299669774444771[200] = 0.0;
   out_2824299669774444771[201] = 0.0;
   out_2824299669774444771[202] = 0.0;
   out_2824299669774444771[203] = 0.0;
   out_2824299669774444771[204] = 0.0;
   out_2824299669774444771[205] = 0.0;
   out_2824299669774444771[206] = 0.0;
   out_2824299669774444771[207] = 0.0;
   out_2824299669774444771[208] = 0.0;
   out_2824299669774444771[209] = 1.0;
   out_2824299669774444771[210] = 0.0;
   out_2824299669774444771[211] = 0.0;
   out_2824299669774444771[212] = 0.0;
   out_2824299669774444771[213] = 0.0;
   out_2824299669774444771[214] = 0.0;
   out_2824299669774444771[215] = 0.0;
   out_2824299669774444771[216] = 0.0;
   out_2824299669774444771[217] = 0.0;
   out_2824299669774444771[218] = 0.0;
   out_2824299669774444771[219] = 0.0;
   out_2824299669774444771[220] = 0.0;
   out_2824299669774444771[221] = 0.0;
   out_2824299669774444771[222] = 0.0;
   out_2824299669774444771[223] = 0.0;
   out_2824299669774444771[224] = 0.0;
   out_2824299669774444771[225] = 0.0;
   out_2824299669774444771[226] = 0.0;
   out_2824299669774444771[227] = 0.0;
   out_2824299669774444771[228] = 1.0;
   out_2824299669774444771[229] = 0.0;
   out_2824299669774444771[230] = 0.0;
   out_2824299669774444771[231] = 0.0;
   out_2824299669774444771[232] = 0.0;
   out_2824299669774444771[233] = 0.0;
   out_2824299669774444771[234] = 0.0;
   out_2824299669774444771[235] = 0.0;
   out_2824299669774444771[236] = 0.0;
   out_2824299669774444771[237] = 0.0;
   out_2824299669774444771[238] = 0.0;
   out_2824299669774444771[239] = 0.0;
   out_2824299669774444771[240] = 0.0;
   out_2824299669774444771[241] = 0.0;
   out_2824299669774444771[242] = 0.0;
   out_2824299669774444771[243] = 0.0;
   out_2824299669774444771[244] = 0.0;
   out_2824299669774444771[245] = 0.0;
   out_2824299669774444771[246] = 0.0;
   out_2824299669774444771[247] = 1.0;
   out_2824299669774444771[248] = 0.0;
   out_2824299669774444771[249] = 0.0;
   out_2824299669774444771[250] = 0.0;
   out_2824299669774444771[251] = 0.0;
   out_2824299669774444771[252] = 0.0;
   out_2824299669774444771[253] = 0.0;
   out_2824299669774444771[254] = 0.0;
   out_2824299669774444771[255] = 0.0;
   out_2824299669774444771[256] = 0.0;
   out_2824299669774444771[257] = 0.0;
   out_2824299669774444771[258] = 0.0;
   out_2824299669774444771[259] = 0.0;
   out_2824299669774444771[260] = 0.0;
   out_2824299669774444771[261] = 0.0;
   out_2824299669774444771[262] = 0.0;
   out_2824299669774444771[263] = 0.0;
   out_2824299669774444771[264] = 0.0;
   out_2824299669774444771[265] = 0.0;
   out_2824299669774444771[266] = 1.0;
   out_2824299669774444771[267] = 0.0;
   out_2824299669774444771[268] = 0.0;
   out_2824299669774444771[269] = 0.0;
   out_2824299669774444771[270] = 0.0;
   out_2824299669774444771[271] = 0.0;
   out_2824299669774444771[272] = 0.0;
   out_2824299669774444771[273] = 0.0;
   out_2824299669774444771[274] = 0.0;
   out_2824299669774444771[275] = 0.0;
   out_2824299669774444771[276] = 0.0;
   out_2824299669774444771[277] = 0.0;
   out_2824299669774444771[278] = 0.0;
   out_2824299669774444771[279] = 0.0;
   out_2824299669774444771[280] = 0.0;
   out_2824299669774444771[281] = 0.0;
   out_2824299669774444771[282] = 0.0;
   out_2824299669774444771[283] = 0.0;
   out_2824299669774444771[284] = 0.0;
   out_2824299669774444771[285] = 1.0;
   out_2824299669774444771[286] = 0.0;
   out_2824299669774444771[287] = 0.0;
   out_2824299669774444771[288] = 0.0;
   out_2824299669774444771[289] = 0.0;
   out_2824299669774444771[290] = 0.0;
   out_2824299669774444771[291] = 0.0;
   out_2824299669774444771[292] = 0.0;
   out_2824299669774444771[293] = 0.0;
   out_2824299669774444771[294] = 0.0;
   out_2824299669774444771[295] = 0.0;
   out_2824299669774444771[296] = 0.0;
   out_2824299669774444771[297] = 0.0;
   out_2824299669774444771[298] = 0.0;
   out_2824299669774444771[299] = 0.0;
   out_2824299669774444771[300] = 0.0;
   out_2824299669774444771[301] = 0.0;
   out_2824299669774444771[302] = 0.0;
   out_2824299669774444771[303] = 0.0;
   out_2824299669774444771[304] = 1.0;
   out_2824299669774444771[305] = 0.0;
   out_2824299669774444771[306] = 0.0;
   out_2824299669774444771[307] = 0.0;
   out_2824299669774444771[308] = 0.0;
   out_2824299669774444771[309] = 0.0;
   out_2824299669774444771[310] = 0.0;
   out_2824299669774444771[311] = 0.0;
   out_2824299669774444771[312] = 0.0;
   out_2824299669774444771[313] = 0.0;
   out_2824299669774444771[314] = 0.0;
   out_2824299669774444771[315] = 0.0;
   out_2824299669774444771[316] = 0.0;
   out_2824299669774444771[317] = 0.0;
   out_2824299669774444771[318] = 0.0;
   out_2824299669774444771[319] = 0.0;
   out_2824299669774444771[320] = 0.0;
   out_2824299669774444771[321] = 0.0;
   out_2824299669774444771[322] = 0.0;
   out_2824299669774444771[323] = 1.0;
}
void f_fun(double *state, double dt, double *out_7206685078178042626) {
   out_7206685078178042626[0] = atan2((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), -(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]));
   out_7206685078178042626[1] = asin(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]));
   out_7206685078178042626[2] = atan2(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), -(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]));
   out_7206685078178042626[3] = dt*state[12] + state[3];
   out_7206685078178042626[4] = dt*state[13] + state[4];
   out_7206685078178042626[5] = dt*state[14] + state[5];
   out_7206685078178042626[6] = state[6];
   out_7206685078178042626[7] = state[7];
   out_7206685078178042626[8] = state[8];
   out_7206685078178042626[9] = state[9];
   out_7206685078178042626[10] = state[10];
   out_7206685078178042626[11] = state[11];
   out_7206685078178042626[12] = state[12];
   out_7206685078178042626[13] = state[13];
   out_7206685078178042626[14] = state[14];
   out_7206685078178042626[15] = state[15];
   out_7206685078178042626[16] = state[16];
   out_7206685078178042626[17] = state[17];
}
void F_fun(double *state, double dt, double *out_503941297957831173) {
   out_503941297957831173[0] = ((-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*cos(state[0])*cos(state[1]) - sin(state[0])*cos(dt*state[6])*cos(dt*state[7])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + ((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*cos(state[0])*cos(state[1]) - sin(dt*state[6])*sin(state[0])*cos(dt*state[7])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_503941297957831173[1] = ((-sin(dt*state[6])*sin(dt*state[8]) - sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*cos(state[1]) - (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*sin(state[1]) - sin(state[1])*cos(dt*state[6])*cos(dt*state[7])*cos(state[0]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*sin(state[1]) + (-sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) + sin(dt*state[8])*cos(dt*state[6]))*cos(state[1]) - sin(dt*state[6])*sin(state[1])*cos(dt*state[7])*cos(state[0]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_503941297957831173[2] = 0;
   out_503941297957831173[3] = 0;
   out_503941297957831173[4] = 0;
   out_503941297957831173[5] = 0;
   out_503941297957831173[6] = (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(dt*cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*sin(dt*state[8]) - dt*sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-dt*sin(dt*state[6])*cos(dt*state[8]) + dt*sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) - dt*cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (dt*sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_503941297957831173[7] = (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[6])*sin(dt*state[7])*cos(state[0])*cos(state[1]) + dt*sin(dt*state[6])*sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) - dt*sin(dt*state[6])*sin(state[1])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[7])*cos(dt*state[6])*cos(state[0])*cos(state[1]) + dt*sin(dt*state[8])*sin(state[0])*cos(dt*state[6])*cos(dt*state[7])*cos(state[1]) - dt*sin(state[1])*cos(dt*state[6])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_503941297957831173[8] = ((dt*sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + dt*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (dt*sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + ((dt*sin(dt*state[6])*sin(dt*state[8]) + dt*sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*cos(dt*state[8]) + dt*sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_503941297957831173[9] = 0;
   out_503941297957831173[10] = 0;
   out_503941297957831173[11] = 0;
   out_503941297957831173[12] = 0;
   out_503941297957831173[13] = 0;
   out_503941297957831173[14] = 0;
   out_503941297957831173[15] = 0;
   out_503941297957831173[16] = 0;
   out_503941297957831173[17] = 0;
   out_503941297957831173[18] = (-sin(dt*state[7])*sin(state[0])*cos(state[1]) - sin(dt*state[8])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_503941297957831173[19] = (-sin(dt*state[7])*sin(state[1])*cos(state[0]) + sin(dt*state[8])*sin(state[0])*sin(state[1])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_503941297957831173[20] = 0;
   out_503941297957831173[21] = 0;
   out_503941297957831173[22] = 0;
   out_503941297957831173[23] = 0;
   out_503941297957831173[24] = 0;
   out_503941297957831173[25] = (dt*sin(dt*state[7])*sin(dt*state[8])*sin(state[0])*cos(state[1]) - dt*sin(dt*state[7])*sin(state[1])*cos(dt*state[8]) + dt*cos(dt*state[7])*cos(state[0])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_503941297957831173[26] = (-dt*sin(dt*state[8])*sin(state[1])*cos(dt*state[7]) - dt*sin(state[0])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_503941297957831173[27] = 0;
   out_503941297957831173[28] = 0;
   out_503941297957831173[29] = 0;
   out_503941297957831173[30] = 0;
   out_503941297957831173[31] = 0;
   out_503941297957831173[32] = 0;
   out_503941297957831173[33] = 0;
   out_503941297957831173[34] = 0;
   out_503941297957831173[35] = 0;
   out_503941297957831173[36] = ((sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[7]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[7]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_503941297957831173[37] = (-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(-sin(dt*state[7])*sin(state[2])*cos(state[0])*cos(state[1]) + sin(dt*state[8])*sin(state[0])*sin(state[2])*cos(dt*state[7])*cos(state[1]) - sin(state[1])*sin(state[2])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*(-sin(dt*state[7])*cos(state[0])*cos(state[1])*cos(state[2]) + sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1])*cos(state[2]) - sin(state[1])*cos(dt*state[7])*cos(dt*state[8])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_503941297957831173[38] = ((-sin(state[0])*sin(state[2]) - sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (-sin(state[0])*sin(state[1])*sin(state[2]) - cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_503941297957831173[39] = 0;
   out_503941297957831173[40] = 0;
   out_503941297957831173[41] = 0;
   out_503941297957831173[42] = 0;
   out_503941297957831173[43] = (-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(dt*(sin(state[0])*cos(state[2]) - sin(state[1])*sin(state[2])*cos(state[0]))*cos(dt*state[7]) - dt*(sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[7])*sin(dt*state[8]) - dt*sin(dt*state[7])*sin(state[2])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*(dt*(-sin(state[0])*sin(state[2]) - sin(state[1])*cos(state[0])*cos(state[2]))*cos(dt*state[7]) - dt*(sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[7])*sin(dt*state[8]) - dt*sin(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_503941297957831173[44] = (dt*(sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*cos(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*sin(state[2])*cos(dt*state[7])*cos(state[1]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + (dt*(sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*cos(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[7])*cos(state[1])*cos(state[2]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_503941297957831173[45] = 0;
   out_503941297957831173[46] = 0;
   out_503941297957831173[47] = 0;
   out_503941297957831173[48] = 0;
   out_503941297957831173[49] = 0;
   out_503941297957831173[50] = 0;
   out_503941297957831173[51] = 0;
   out_503941297957831173[52] = 0;
   out_503941297957831173[53] = 0;
   out_503941297957831173[54] = 0;
   out_503941297957831173[55] = 0;
   out_503941297957831173[56] = 0;
   out_503941297957831173[57] = 1;
   out_503941297957831173[58] = 0;
   out_503941297957831173[59] = 0;
   out_503941297957831173[60] = 0;
   out_503941297957831173[61] = 0;
   out_503941297957831173[62] = 0;
   out_503941297957831173[63] = 0;
   out_503941297957831173[64] = 0;
   out_503941297957831173[65] = 0;
   out_503941297957831173[66] = dt;
   out_503941297957831173[67] = 0;
   out_503941297957831173[68] = 0;
   out_503941297957831173[69] = 0;
   out_503941297957831173[70] = 0;
   out_503941297957831173[71] = 0;
   out_503941297957831173[72] = 0;
   out_503941297957831173[73] = 0;
   out_503941297957831173[74] = 0;
   out_503941297957831173[75] = 0;
   out_503941297957831173[76] = 1;
   out_503941297957831173[77] = 0;
   out_503941297957831173[78] = 0;
   out_503941297957831173[79] = 0;
   out_503941297957831173[80] = 0;
   out_503941297957831173[81] = 0;
   out_503941297957831173[82] = 0;
   out_503941297957831173[83] = 0;
   out_503941297957831173[84] = 0;
   out_503941297957831173[85] = dt;
   out_503941297957831173[86] = 0;
   out_503941297957831173[87] = 0;
   out_503941297957831173[88] = 0;
   out_503941297957831173[89] = 0;
   out_503941297957831173[90] = 0;
   out_503941297957831173[91] = 0;
   out_503941297957831173[92] = 0;
   out_503941297957831173[93] = 0;
   out_503941297957831173[94] = 0;
   out_503941297957831173[95] = 1;
   out_503941297957831173[96] = 0;
   out_503941297957831173[97] = 0;
   out_503941297957831173[98] = 0;
   out_503941297957831173[99] = 0;
   out_503941297957831173[100] = 0;
   out_503941297957831173[101] = 0;
   out_503941297957831173[102] = 0;
   out_503941297957831173[103] = 0;
   out_503941297957831173[104] = dt;
   out_503941297957831173[105] = 0;
   out_503941297957831173[106] = 0;
   out_503941297957831173[107] = 0;
   out_503941297957831173[108] = 0;
   out_503941297957831173[109] = 0;
   out_503941297957831173[110] = 0;
   out_503941297957831173[111] = 0;
   out_503941297957831173[112] = 0;
   out_503941297957831173[113] = 0;
   out_503941297957831173[114] = 1;
   out_503941297957831173[115] = 0;
   out_503941297957831173[116] = 0;
   out_503941297957831173[117] = 0;
   out_503941297957831173[118] = 0;
   out_503941297957831173[119] = 0;
   out_503941297957831173[120] = 0;
   out_503941297957831173[121] = 0;
   out_503941297957831173[122] = 0;
   out_503941297957831173[123] = 0;
   out_503941297957831173[124] = 0;
   out_503941297957831173[125] = 0;
   out_503941297957831173[126] = 0;
   out_503941297957831173[127] = 0;
   out_503941297957831173[128] = 0;
   out_503941297957831173[129] = 0;
   out_503941297957831173[130] = 0;
   out_503941297957831173[131] = 0;
   out_503941297957831173[132] = 0;
   out_503941297957831173[133] = 1;
   out_503941297957831173[134] = 0;
   out_503941297957831173[135] = 0;
   out_503941297957831173[136] = 0;
   out_503941297957831173[137] = 0;
   out_503941297957831173[138] = 0;
   out_503941297957831173[139] = 0;
   out_503941297957831173[140] = 0;
   out_503941297957831173[141] = 0;
   out_503941297957831173[142] = 0;
   out_503941297957831173[143] = 0;
   out_503941297957831173[144] = 0;
   out_503941297957831173[145] = 0;
   out_503941297957831173[146] = 0;
   out_503941297957831173[147] = 0;
   out_503941297957831173[148] = 0;
   out_503941297957831173[149] = 0;
   out_503941297957831173[150] = 0;
   out_503941297957831173[151] = 0;
   out_503941297957831173[152] = 1;
   out_503941297957831173[153] = 0;
   out_503941297957831173[154] = 0;
   out_503941297957831173[155] = 0;
   out_503941297957831173[156] = 0;
   out_503941297957831173[157] = 0;
   out_503941297957831173[158] = 0;
   out_503941297957831173[159] = 0;
   out_503941297957831173[160] = 0;
   out_503941297957831173[161] = 0;
   out_503941297957831173[162] = 0;
   out_503941297957831173[163] = 0;
   out_503941297957831173[164] = 0;
   out_503941297957831173[165] = 0;
   out_503941297957831173[166] = 0;
   out_503941297957831173[167] = 0;
   out_503941297957831173[168] = 0;
   out_503941297957831173[169] = 0;
   out_503941297957831173[170] = 0;
   out_503941297957831173[171] = 1;
   out_503941297957831173[172] = 0;
   out_503941297957831173[173] = 0;
   out_503941297957831173[174] = 0;
   out_503941297957831173[175] = 0;
   out_503941297957831173[176] = 0;
   out_503941297957831173[177] = 0;
   out_503941297957831173[178] = 0;
   out_503941297957831173[179] = 0;
   out_503941297957831173[180] = 0;
   out_503941297957831173[181] = 0;
   out_503941297957831173[182] = 0;
   out_503941297957831173[183] = 0;
   out_503941297957831173[184] = 0;
   out_503941297957831173[185] = 0;
   out_503941297957831173[186] = 0;
   out_503941297957831173[187] = 0;
   out_503941297957831173[188] = 0;
   out_503941297957831173[189] = 0;
   out_503941297957831173[190] = 1;
   out_503941297957831173[191] = 0;
   out_503941297957831173[192] = 0;
   out_503941297957831173[193] = 0;
   out_503941297957831173[194] = 0;
   out_503941297957831173[195] = 0;
   out_503941297957831173[196] = 0;
   out_503941297957831173[197] = 0;
   out_503941297957831173[198] = 0;
   out_503941297957831173[199] = 0;
   out_503941297957831173[200] = 0;
   out_503941297957831173[201] = 0;
   out_503941297957831173[202] = 0;
   out_503941297957831173[203] = 0;
   out_503941297957831173[204] = 0;
   out_503941297957831173[205] = 0;
   out_503941297957831173[206] = 0;
   out_503941297957831173[207] = 0;
   out_503941297957831173[208] = 0;
   out_503941297957831173[209] = 1;
   out_503941297957831173[210] = 0;
   out_503941297957831173[211] = 0;
   out_503941297957831173[212] = 0;
   out_503941297957831173[213] = 0;
   out_503941297957831173[214] = 0;
   out_503941297957831173[215] = 0;
   out_503941297957831173[216] = 0;
   out_503941297957831173[217] = 0;
   out_503941297957831173[218] = 0;
   out_503941297957831173[219] = 0;
   out_503941297957831173[220] = 0;
   out_503941297957831173[221] = 0;
   out_503941297957831173[222] = 0;
   out_503941297957831173[223] = 0;
   out_503941297957831173[224] = 0;
   out_503941297957831173[225] = 0;
   out_503941297957831173[226] = 0;
   out_503941297957831173[227] = 0;
   out_503941297957831173[228] = 1;
   out_503941297957831173[229] = 0;
   out_503941297957831173[230] = 0;
   out_503941297957831173[231] = 0;
   out_503941297957831173[232] = 0;
   out_503941297957831173[233] = 0;
   out_503941297957831173[234] = 0;
   out_503941297957831173[235] = 0;
   out_503941297957831173[236] = 0;
   out_503941297957831173[237] = 0;
   out_503941297957831173[238] = 0;
   out_503941297957831173[239] = 0;
   out_503941297957831173[240] = 0;
   out_503941297957831173[241] = 0;
   out_503941297957831173[242] = 0;
   out_503941297957831173[243] = 0;
   out_503941297957831173[244] = 0;
   out_503941297957831173[245] = 0;
   out_503941297957831173[246] = 0;
   out_503941297957831173[247] = 1;
   out_503941297957831173[248] = 0;
   out_503941297957831173[249] = 0;
   out_503941297957831173[250] = 0;
   out_503941297957831173[251] = 0;
   out_503941297957831173[252] = 0;
   out_503941297957831173[253] = 0;
   out_503941297957831173[254] = 0;
   out_503941297957831173[255] = 0;
   out_503941297957831173[256] = 0;
   out_503941297957831173[257] = 0;
   out_503941297957831173[258] = 0;
   out_503941297957831173[259] = 0;
   out_503941297957831173[260] = 0;
   out_503941297957831173[261] = 0;
   out_503941297957831173[262] = 0;
   out_503941297957831173[263] = 0;
   out_503941297957831173[264] = 0;
   out_503941297957831173[265] = 0;
   out_503941297957831173[266] = 1;
   out_503941297957831173[267] = 0;
   out_503941297957831173[268] = 0;
   out_503941297957831173[269] = 0;
   out_503941297957831173[270] = 0;
   out_503941297957831173[271] = 0;
   out_503941297957831173[272] = 0;
   out_503941297957831173[273] = 0;
   out_503941297957831173[274] = 0;
   out_503941297957831173[275] = 0;
   out_503941297957831173[276] = 0;
   out_503941297957831173[277] = 0;
   out_503941297957831173[278] = 0;
   out_503941297957831173[279] = 0;
   out_503941297957831173[280] = 0;
   out_503941297957831173[281] = 0;
   out_503941297957831173[282] = 0;
   out_503941297957831173[283] = 0;
   out_503941297957831173[284] = 0;
   out_503941297957831173[285] = 1;
   out_503941297957831173[286] = 0;
   out_503941297957831173[287] = 0;
   out_503941297957831173[288] = 0;
   out_503941297957831173[289] = 0;
   out_503941297957831173[290] = 0;
   out_503941297957831173[291] = 0;
   out_503941297957831173[292] = 0;
   out_503941297957831173[293] = 0;
   out_503941297957831173[294] = 0;
   out_503941297957831173[295] = 0;
   out_503941297957831173[296] = 0;
   out_503941297957831173[297] = 0;
   out_503941297957831173[298] = 0;
   out_503941297957831173[299] = 0;
   out_503941297957831173[300] = 0;
   out_503941297957831173[301] = 0;
   out_503941297957831173[302] = 0;
   out_503941297957831173[303] = 0;
   out_503941297957831173[304] = 1;
   out_503941297957831173[305] = 0;
   out_503941297957831173[306] = 0;
   out_503941297957831173[307] = 0;
   out_503941297957831173[308] = 0;
   out_503941297957831173[309] = 0;
   out_503941297957831173[310] = 0;
   out_503941297957831173[311] = 0;
   out_503941297957831173[312] = 0;
   out_503941297957831173[313] = 0;
   out_503941297957831173[314] = 0;
   out_503941297957831173[315] = 0;
   out_503941297957831173[316] = 0;
   out_503941297957831173[317] = 0;
   out_503941297957831173[318] = 0;
   out_503941297957831173[319] = 0;
   out_503941297957831173[320] = 0;
   out_503941297957831173[321] = 0;
   out_503941297957831173[322] = 0;
   out_503941297957831173[323] = 1;
}
void h_4(double *state, double *unused, double *out_4034886323950789465) {
   out_4034886323950789465[0] = state[6] + state[9];
   out_4034886323950789465[1] = state[7] + state[10];
   out_4034886323950789465[2] = state[8] + state[11];
}
void H_4(double *state, double *unused, double *out_7438926706703761135) {
   out_7438926706703761135[0] = 0;
   out_7438926706703761135[1] = 0;
   out_7438926706703761135[2] = 0;
   out_7438926706703761135[3] = 0;
   out_7438926706703761135[4] = 0;
   out_7438926706703761135[5] = 0;
   out_7438926706703761135[6] = 1;
   out_7438926706703761135[7] = 0;
   out_7438926706703761135[8] = 0;
   out_7438926706703761135[9] = 1;
   out_7438926706703761135[10] = 0;
   out_7438926706703761135[11] = 0;
   out_7438926706703761135[12] = 0;
   out_7438926706703761135[13] = 0;
   out_7438926706703761135[14] = 0;
   out_7438926706703761135[15] = 0;
   out_7438926706703761135[16] = 0;
   out_7438926706703761135[17] = 0;
   out_7438926706703761135[18] = 0;
   out_7438926706703761135[19] = 0;
   out_7438926706703761135[20] = 0;
   out_7438926706703761135[21] = 0;
   out_7438926706703761135[22] = 0;
   out_7438926706703761135[23] = 0;
   out_7438926706703761135[24] = 0;
   out_7438926706703761135[25] = 1;
   out_7438926706703761135[26] = 0;
   out_7438926706703761135[27] = 0;
   out_7438926706703761135[28] = 1;
   out_7438926706703761135[29] = 0;
   out_7438926706703761135[30] = 0;
   out_7438926706703761135[31] = 0;
   out_7438926706703761135[32] = 0;
   out_7438926706703761135[33] = 0;
   out_7438926706703761135[34] = 0;
   out_7438926706703761135[35] = 0;
   out_7438926706703761135[36] = 0;
   out_7438926706703761135[37] = 0;
   out_7438926706703761135[38] = 0;
   out_7438926706703761135[39] = 0;
   out_7438926706703761135[40] = 0;
   out_7438926706703761135[41] = 0;
   out_7438926706703761135[42] = 0;
   out_7438926706703761135[43] = 0;
   out_7438926706703761135[44] = 1;
   out_7438926706703761135[45] = 0;
   out_7438926706703761135[46] = 0;
   out_7438926706703761135[47] = 1;
   out_7438926706703761135[48] = 0;
   out_7438926706703761135[49] = 0;
   out_7438926706703761135[50] = 0;
   out_7438926706703761135[51] = 0;
   out_7438926706703761135[52] = 0;
   out_7438926706703761135[53] = 0;
}
void h_10(double *state, double *unused, double *out_4450943621918908199) {
   out_4450943621918908199[0] = 9.8100000000000005*sin(state[1]) - state[4]*state[8] + state[5]*state[7] + state[12] + state[15];
   out_4450943621918908199[1] = -9.8100000000000005*sin(state[0])*cos(state[1]) + state[3]*state[8] - state[5]*state[6] + state[13] + state[16];
   out_4450943621918908199[2] = -9.8100000000000005*cos(state[0])*cos(state[1]) - state[3]*state[7] + state[4]*state[6] + state[14] + state[17];
}
void H_10(double *state, double *unused, double *out_8909781275043755673) {
   out_8909781275043755673[0] = 0;
   out_8909781275043755673[1] = 9.8100000000000005*cos(state[1]);
   out_8909781275043755673[2] = 0;
   out_8909781275043755673[3] = 0;
   out_8909781275043755673[4] = -state[8];
   out_8909781275043755673[5] = state[7];
   out_8909781275043755673[6] = 0;
   out_8909781275043755673[7] = state[5];
   out_8909781275043755673[8] = -state[4];
   out_8909781275043755673[9] = 0;
   out_8909781275043755673[10] = 0;
   out_8909781275043755673[11] = 0;
   out_8909781275043755673[12] = 1;
   out_8909781275043755673[13] = 0;
   out_8909781275043755673[14] = 0;
   out_8909781275043755673[15] = 1;
   out_8909781275043755673[16] = 0;
   out_8909781275043755673[17] = 0;
   out_8909781275043755673[18] = -9.8100000000000005*cos(state[0])*cos(state[1]);
   out_8909781275043755673[19] = 9.8100000000000005*sin(state[0])*sin(state[1]);
   out_8909781275043755673[20] = 0;
   out_8909781275043755673[21] = state[8];
   out_8909781275043755673[22] = 0;
   out_8909781275043755673[23] = -state[6];
   out_8909781275043755673[24] = -state[5];
   out_8909781275043755673[25] = 0;
   out_8909781275043755673[26] = state[3];
   out_8909781275043755673[27] = 0;
   out_8909781275043755673[28] = 0;
   out_8909781275043755673[29] = 0;
   out_8909781275043755673[30] = 0;
   out_8909781275043755673[31] = 1;
   out_8909781275043755673[32] = 0;
   out_8909781275043755673[33] = 0;
   out_8909781275043755673[34] = 1;
   out_8909781275043755673[35] = 0;
   out_8909781275043755673[36] = 9.8100000000000005*sin(state[0])*cos(state[1]);
   out_8909781275043755673[37] = 9.8100000000000005*sin(state[1])*cos(state[0]);
   out_8909781275043755673[38] = 0;
   out_8909781275043755673[39] = -state[7];
   out_8909781275043755673[40] = state[6];
   out_8909781275043755673[41] = 0;
   out_8909781275043755673[42] = state[4];
   out_8909781275043755673[43] = -state[3];
   out_8909781275043755673[44] = 0;
   out_8909781275043755673[45] = 0;
   out_8909781275043755673[46] = 0;
   out_8909781275043755673[47] = 0;
   out_8909781275043755673[48] = 0;
   out_8909781275043755673[49] = 0;
   out_8909781275043755673[50] = 1;
   out_8909781275043755673[51] = 0;
   out_8909781275043755673[52] = 0;
   out_8909781275043755673[53] = 1;
}
void h_13(double *state, double *unused, double *out_7684661552775223725) {
   out_7684661552775223725[0] = state[3];
   out_7684661552775223725[1] = state[4];
   out_7684661552775223725[2] = state[5];
}
void H_13(double *state, double *unused, double *out_3397186158689089552) {
   out_3397186158689089552[0] = 0;
   out_3397186158689089552[1] = 0;
   out_3397186158689089552[2] = 0;
   out_3397186158689089552[3] = 1;
   out_3397186158689089552[4] = 0;
   out_3397186158689089552[5] = 0;
   out_3397186158689089552[6] = 0;
   out_3397186158689089552[7] = 0;
   out_3397186158689089552[8] = 0;
   out_3397186158689089552[9] = 0;
   out_3397186158689089552[10] = 0;
   out_3397186158689089552[11] = 0;
   out_3397186158689089552[12] = 0;
   out_3397186158689089552[13] = 0;
   out_3397186158689089552[14] = 0;
   out_3397186158689089552[15] = 0;
   out_3397186158689089552[16] = 0;
   out_3397186158689089552[17] = 0;
   out_3397186158689089552[18] = 0;
   out_3397186158689089552[19] = 0;
   out_3397186158689089552[20] = 0;
   out_3397186158689089552[21] = 0;
   out_3397186158689089552[22] = 1;
   out_3397186158689089552[23] = 0;
   out_3397186158689089552[24] = 0;
   out_3397186158689089552[25] = 0;
   out_3397186158689089552[26] = 0;
   out_3397186158689089552[27] = 0;
   out_3397186158689089552[28] = 0;
   out_3397186158689089552[29] = 0;
   out_3397186158689089552[30] = 0;
   out_3397186158689089552[31] = 0;
   out_3397186158689089552[32] = 0;
   out_3397186158689089552[33] = 0;
   out_3397186158689089552[34] = 0;
   out_3397186158689089552[35] = 0;
   out_3397186158689089552[36] = 0;
   out_3397186158689089552[37] = 0;
   out_3397186158689089552[38] = 0;
   out_3397186158689089552[39] = 0;
   out_3397186158689089552[40] = 0;
   out_3397186158689089552[41] = 1;
   out_3397186158689089552[42] = 0;
   out_3397186158689089552[43] = 0;
   out_3397186158689089552[44] = 0;
   out_3397186158689089552[45] = 0;
   out_3397186158689089552[46] = 0;
   out_3397186158689089552[47] = 0;
   out_3397186158689089552[48] = 0;
   out_3397186158689089552[49] = 0;
   out_3397186158689089552[50] = 0;
   out_3397186158689089552[51] = 0;
   out_3397186158689089552[52] = 0;
   out_3397186158689089552[53] = 0;
}
void h_14(double *state, double *unused, double *out_1124588162973463748) {
   out_1124588162973463748[0] = state[6];
   out_1124588162973463748[1] = state[7];
   out_1124588162973463748[2] = state[8];
}
void H_14(double *state, double *unused, double *out_7044576510666305952) {
   out_7044576510666305952[0] = 0;
   out_7044576510666305952[1] = 0;
   out_7044576510666305952[2] = 0;
   out_7044576510666305952[3] = 0;
   out_7044576510666305952[4] = 0;
   out_7044576510666305952[5] = 0;
   out_7044576510666305952[6] = 1;
   out_7044576510666305952[7] = 0;
   out_7044576510666305952[8] = 0;
   out_7044576510666305952[9] = 0;
   out_7044576510666305952[10] = 0;
   out_7044576510666305952[11] = 0;
   out_7044576510666305952[12] = 0;
   out_7044576510666305952[13] = 0;
   out_7044576510666305952[14] = 0;
   out_7044576510666305952[15] = 0;
   out_7044576510666305952[16] = 0;
   out_7044576510666305952[17] = 0;
   out_7044576510666305952[18] = 0;
   out_7044576510666305952[19] = 0;
   out_7044576510666305952[20] = 0;
   out_7044576510666305952[21] = 0;
   out_7044576510666305952[22] = 0;
   out_7044576510666305952[23] = 0;
   out_7044576510666305952[24] = 0;
   out_7044576510666305952[25] = 1;
   out_7044576510666305952[26] = 0;
   out_7044576510666305952[27] = 0;
   out_7044576510666305952[28] = 0;
   out_7044576510666305952[29] = 0;
   out_7044576510666305952[30] = 0;
   out_7044576510666305952[31] = 0;
   out_7044576510666305952[32] = 0;
   out_7044576510666305952[33] = 0;
   out_7044576510666305952[34] = 0;
   out_7044576510666305952[35] = 0;
   out_7044576510666305952[36] = 0;
   out_7044576510666305952[37] = 0;
   out_7044576510666305952[38] = 0;
   out_7044576510666305952[39] = 0;
   out_7044576510666305952[40] = 0;
   out_7044576510666305952[41] = 0;
   out_7044576510666305952[42] = 0;
   out_7044576510666305952[43] = 0;
   out_7044576510666305952[44] = 1;
   out_7044576510666305952[45] = 0;
   out_7044576510666305952[46] = 0;
   out_7044576510666305952[47] = 0;
   out_7044576510666305952[48] = 0;
   out_7044576510666305952[49] = 0;
   out_7044576510666305952[50] = 0;
   out_7044576510666305952[51] = 0;
   out_7044576510666305952[52] = 0;
   out_7044576510666305952[53] = 0;
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

void pose_update_4(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<3, 3, 0>(in_x, in_P, h_4, H_4, NULL, in_z, in_R, in_ea, MAHA_THRESH_4);
}
void pose_update_10(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<3, 3, 0>(in_x, in_P, h_10, H_10, NULL, in_z, in_R, in_ea, MAHA_THRESH_10);
}
void pose_update_13(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<3, 3, 0>(in_x, in_P, h_13, H_13, NULL, in_z, in_R, in_ea, MAHA_THRESH_13);
}
void pose_update_14(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<3, 3, 0>(in_x, in_P, h_14, H_14, NULL, in_z, in_R, in_ea, MAHA_THRESH_14);
}
void pose_err_fun(double *nom_x, double *delta_x, double *out_8639454197913824489) {
  err_fun(nom_x, delta_x, out_8639454197913824489);
}
void pose_inv_err_fun(double *nom_x, double *true_x, double *out_4523294178166863030) {
  inv_err_fun(nom_x, true_x, out_4523294178166863030);
}
void pose_H_mod_fun(double *state, double *out_2824299669774444771) {
  H_mod_fun(state, out_2824299669774444771);
}
void pose_f_fun(double *state, double dt, double *out_7206685078178042626) {
  f_fun(state,  dt, out_7206685078178042626);
}
void pose_F_fun(double *state, double dt, double *out_503941297957831173) {
  F_fun(state,  dt, out_503941297957831173);
}
void pose_h_4(double *state, double *unused, double *out_4034886323950789465) {
  h_4(state, unused, out_4034886323950789465);
}
void pose_H_4(double *state, double *unused, double *out_7438926706703761135) {
  H_4(state, unused, out_7438926706703761135);
}
void pose_h_10(double *state, double *unused, double *out_4450943621918908199) {
  h_10(state, unused, out_4450943621918908199);
}
void pose_H_10(double *state, double *unused, double *out_8909781275043755673) {
  H_10(state, unused, out_8909781275043755673);
}
void pose_h_13(double *state, double *unused, double *out_7684661552775223725) {
  h_13(state, unused, out_7684661552775223725);
}
void pose_H_13(double *state, double *unused, double *out_3397186158689089552) {
  H_13(state, unused, out_3397186158689089552);
}
void pose_h_14(double *state, double *unused, double *out_1124588162973463748) {
  h_14(state, unused, out_1124588162973463748);
}
void pose_H_14(double *state, double *unused, double *out_7044576510666305952) {
  H_14(state, unused, out_7044576510666305952);
}
void pose_predict(double *in_x, double *in_P, double *in_Q, double dt) {
  predict(in_x, in_P, in_Q, dt);
}
}

const EKF pose = {
  .name = "pose",
  .kinds = { 4, 10, 13, 14 },
  .feature_kinds = {  },
  .f_fun = pose_f_fun,
  .F_fun = pose_F_fun,
  .err_fun = pose_err_fun,
  .inv_err_fun = pose_inv_err_fun,
  .H_mod_fun = pose_H_mod_fun,
  .predict = pose_predict,
  .hs = {
    { 4, pose_h_4 },
    { 10, pose_h_10 },
    { 13, pose_h_13 },
    { 14, pose_h_14 },
  },
  .Hs = {
    { 4, pose_H_4 },
    { 10, pose_H_10 },
    { 13, pose_H_13 },
    { 14, pose_H_14 },
  },
  .updates = {
    { 4, pose_update_4 },
    { 10, pose_update_10 },
    { 13, pose_update_13 },
    { 14, pose_update_14 },
  },
  .Hes = {
  },
  .sets = {
  },
  .extra_routines = {
  },
};

ekf_lib_init(pose)
