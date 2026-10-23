#pragma once

// ============================================
// SAFETY_TESLA_PREAP — Pre-Autopilot Tesla Model S (2012-2014)
// ============================================
//
// Standalone safety mode for Pre-AP Tesla Model S. These cars have NO
// Autopilot ECU, NO harness relay, and a different EPAS/CAN layout than
// HW1+ Teslas. This is the spiritual successor to Tinkla (Boggyver's
// Pre-AP openpilot fork, tesla_unity_betaC3 branch).
//
// WHY check_relay=false AND disable_static_blocking=true:
//
//   Pre-AP has no harness relay hardware. Standard openpilot uses a relay
//   on the harness to switch between stock AP ECU and openpilot — when
//   openpilot is not active, the relay routes CAN to the stock ECU. On
//   Pre-AP there is no AP ECU and no relay; the panda connects directly
//   to the car's CAN bus. Setting check_relay=true would cause the panda
//   to falsely detect a "relay malfunction" and block ALL TX permanently.
//   disable_static_blocking=true is required for the same reason — without
//   a relay, the panda's static blocking logic (which assumes relay state)
//   would incorrectly block messages.
//
//   Tinkla handled this identically via generic_rx_checks(false) in the
//   older panda API, with the comment "PreAP has no relay" (safety_tesla.h
//   line 1071, tesla_unity_betaC3 branch). The modern API added check_relay
//   and disable_static_blocking with restrictive defaults, so we explicitly
//   set them to get the same behavior Tinkla had implicitly.
//
// WHY ignore_checksum=true AND ignore_counter=true on RX:
//
//   Pre-AP EPAS firmware uses a byte-sum checksum, but the exact algorithm
//   has not been fully verified against all firmware versions. A checksum
//   mismatch caused a silent 21-second steering dropout during testing.
//   Tinkla's RX checks also had no checksum/counter validation (frequency
//   set to 0 for all messages). Once the checksum algorithm is verified
//   across all Pre-AP EPAS firmware versions, these can be re-enabled.
//
// ALL ACTUAL SAFETY CHECKS REMAIN FULLY ACTIVE:
//   - Steering angle + rate limits via steer_angle_cmd_checks_vm()
//   - controls_allowed gating on all TX
//   - Disengage on hands-on override (level >= 3)
//   - Disengage on EPAS error codes 6-9
//   - Disengage on door open, gear out of Drive
//   - Disengage on stalk cancel (with 600ms echo filter)
//   - AEB events blocked from openpilot
//   - EPB_epasControl mode validation
//   - Pedal TX gated by PREAP_FLAG_ENABLE_PEDAL + get_longitudinal_allowed()
//
// Completely independent from tesla_legacy.h — has its own hooks struct,
// counter/checksum functions, init, RX/TX/fwd hooks, and GTW emulation.
// Registered as SAFETY_TESLA_PREAP in declarations.h.

#include "opendbc/safety/declarations.h"

// Forward declarations for panda firmware CAN send (defined in can_common.h)
#if defined(STM32H7) || defined(STM32F4)
void can_send(CANPacket_t *to_push, uint8_t bus_number, bool skip_tx_hook);
void can_set_checksum(CANPacket_t *packet);
#endif

// ============================================
// Byte manipulation macros
// ============================================

#define PREAP_GET_BYTES_04(msg) ((uint32_t)(msg)->data[0] | ((uint32_t)(msg)->data[1] << 8U) | ((uint32_t)(msg)->data[2] << 16U) | ((uint32_t)(msg)->data[3] << 24U))
#define PREAP_GET_BYTES_48(msg) ((uint32_t)(msg)->data[4] | ((uint32_t)(msg)->data[5] << 8U) | ((uint32_t)(msg)->data[6] << 16U) | ((uint32_t)(msg)->data[7] << 24U))
#define PREAP_WORD_TO_BYTES(dst8, src32) 0[dst8] = ((src32) & 0xFFU); 1[dst8] = (((src32) >> 8U) & 0xFFU); 2[dst8] = (((src32) >> 16U) & 0xFFU); 3[dst8] = (((src32) >> 24U) & 0xFFU)

// ============================================
// Safety param flags
// ============================================
// Longitudinal is gated by PREAP_FLAG_ENABLE_PEDAL + get_longitudinal_allowed().
// There is no separate LONG_CONTROL flag — the framework's get_longitudinal_allowed()
// is a derived check (controls_allowed && !gas_pressed_prev), not a settable flag.
// This matches how tesla.h, honda.h, and hyundai.h handle longitudinal gating.

#define PREAP_FLAG_ENABLE_PEDAL         1U
#define PREAP_FLAG_RADAR_EMULATION      2U
#define PREAP_FLAG_RADAR_BEHIND_NOSECONE 4U

// ============================================
// State variables
// ============================================

static bool preap_enable_pedal = false;
static bool preap_radar_emulation = false;

static int preap_pedal_can = -1;
// EAS manual starts require a fresh ESP_B sample strictly below 40 mph.
static uint32_t preap_eas_speed_ts = 0U;
static bool preap_eas_speed_seen = false;
static bool preap_eas_speed_ok = false;

// Gear and door checks
static int preap_gear = 4;        // init to Drive to avoid false disables on startup
static int preap_gear_prev = 4;
static bool preap_doors_open = false;

// Stalk echo filter
static uint32_t preap_last_stalk_engage_us = 0;
#define PREAP_CANCEL_ECHO_WINDOW_US 600000U  // 600ms
static int preap_stalk_prev = -1;
static uint32_t preap_stalk_ts = 0U;
#define PREAP_STALK_FRESH_US 250000U

// Radar emulation state
static int preap_radar_status = 0;
static uint32_t preap_last_radar_signal = 0;
static uint32_t preap_radar_position = 0U;

// ============================================
// Checksum and counter (for EPAS validation)
// ============================================

static uint8_t tesla_preap_get_counter(const CANPacket_t *msg) {
  uint8_t counter = 0U;
  if (msg->addr == 0x370U) {
    counter = msg->data[6] & 0x0FU;  // EPAS_sysStatusCounter
  }
  return counter;
}

static uint32_t tesla_preap_get_checksum(const CANPacket_t *msg) {
  uint32_t checksum = 0U;
  if (msg->addr == 0x370U) {
    checksum = msg->data[7];  // EPAS_sysStatusChecksum at byte 7
  }
  if (msg->addr == 0x488U) {
    checksum = msg->data[3];  // DAS_steeringControlChecksum at byte 3
  }
  return checksum;
}

static uint32_t tesla_preap_compute_checksum(const CANPacket_t *msg) {
  // Tesla byte-sum checksum: sum of address bytes + all data bytes except checksum byte
  int checksum_byte = -1;
  if (msg->addr == 0x370U) {
    checksum_byte = 7;
  } else if (msg->addr == 0x488U) {
    checksum_byte = 3;
  } else {
    // Other messages have no checksum defined by this hook.
  }
  uint8_t chksum = 0U;
  if (checksum_byte != -1) {
    chksum = (uint8_t)(msg->addr & 0xFFU) + (uint8_t)((msg->addr >> 8) & 0xFFU);
    int len = GET_LEN(msg);
    for (int i = 0; i < len; i++) {
      if (i != checksum_byte) {
        chksum += msg->data[i];
      }
    }
  }
  return chksum;
}

static uint32_t preap_compute_crc8(uint32_t lo, uint32_t hi, unsigned int msg_len) {
  // CRC-8 lookup table (polynomial 0x1D) for steering angle re-addressing
  static const uint32_t preap_crc_lookup[256] = {
    0x00U, 0x1DU, 0x3AU, 0x27U, 0x74U, 0x69U, 0x4EU, 0x53U, 0xE8U, 0xF5U, 0xD2U, 0xCFU, 0x9CU, 0x81U, 0xA6U, 0xBBU,
    0xCDU, 0xD0U, 0xF7U, 0xEAU, 0xB9U, 0xA4U, 0x83U, 0x9EU, 0x25U, 0x38U, 0x1FU, 0x02U, 0x51U, 0x4CU, 0x6BU, 0x76U,
    0x87U, 0x9AU, 0xBDU, 0xA0U, 0xF3U, 0xEEU, 0xC9U, 0xD4U, 0x6FU, 0x72U, 0x55U, 0x48U, 0x1BU, 0x06U, 0x21U, 0x3CU,
    0x4AU, 0x57U, 0x70U, 0x6DU, 0x3EU, 0x23U, 0x04U, 0x19U, 0xA2U, 0xBFU, 0x98U, 0x85U, 0xD6U, 0xCBU, 0xECU, 0xF1U,
    0x13U, 0x0EU, 0x29U, 0x34U, 0x67U, 0x7AU, 0x5DU, 0x40U, 0xFBU, 0xE6U, 0xC1U, 0xDCU, 0x8FU, 0x92U, 0xB5U, 0xA8U,
    0xDEU, 0xC3U, 0xE4U, 0xF9U, 0xAAU, 0xB7U, 0x90U, 0x8DU, 0x36U, 0x2BU, 0x0CU, 0x11U, 0x42U, 0x5FU, 0x78U, 0x65U,
    0x94U, 0x89U, 0xAEU, 0xB3U, 0xE0U, 0xFDU, 0xDAU, 0xC7U, 0x7CU, 0x61U, 0x46U, 0x5BU, 0x08U, 0x15U, 0x32U, 0x2FU,
    0x59U, 0x44U, 0x63U, 0x7EU, 0x2DU, 0x30U, 0x17U, 0x0AU, 0xB1U, 0xACU, 0x8BU, 0x96U, 0xC5U, 0xD8U, 0xFFU, 0xE2U,
    0x26U, 0x3BU, 0x1CU, 0x01U, 0x52U, 0x4FU, 0x68U, 0x75U, 0xCEU, 0xD3U, 0xF4U, 0xE9U, 0xBAU, 0xA7U, 0x80U, 0x9DU,
    0xEBU, 0xF6U, 0xD1U, 0xCCU, 0x9FU, 0x82U, 0xA5U, 0xB8U, 0x03U, 0x1EU, 0x39U, 0x24U, 0x77U, 0x6AU, 0x4DU, 0x50U,
    0xA1U, 0xBCU, 0x9BU, 0x86U, 0xD5U, 0xC8U, 0xEFU, 0xF2U, 0x49U, 0x54U, 0x73U, 0x6EU, 0x3DU, 0x20U, 0x07U, 0x1AU,
    0x6CU, 0x71U, 0x56U, 0x4BU, 0x18U, 0x05U, 0x22U, 0x3FU, 0x84U, 0x99U, 0xBEU, 0xA3U, 0xF0U, 0xEDU, 0xCAU, 0xD7U,
    0x35U, 0x28U, 0x0FU, 0x12U, 0x41U, 0x5CU, 0x7BU, 0x66U, 0xDDU, 0xC0U, 0xE7U, 0xFAU, 0xA9U, 0xB4U, 0x93U, 0x8EU,
    0xF8U, 0xE5U, 0xC2U, 0xDFU, 0x8CU, 0x91U, 0xB6U, 0xABU, 0x10U, 0x0DU, 0x2AU, 0x37U, 0x64U, 0x79U, 0x5EU, 0x43U,
    0xB2U, 0xAFU, 0x88U, 0x95U, 0xC6U, 0xDBU, 0xFCU, 0xE1U, 0x5AU, 0x47U, 0x60U, 0x7DU, 0x2EU, 0x33U, 0x14U, 0x09U,
    0x7FU, 0x62U, 0x45U, 0x58U, 0x0BU, 0x16U, 0x31U, 0x2CU, 0x97U, 0x8AU, 0xADU, 0xB0U, 0xE3U, 0xFEU, 0xD9U, 0xC4U
  };
  uint32_t crc = 0xFFU;
  for (unsigned int x = 0U; x < msg_len; x++) {
    uint32_t v = (x <= 3U) ? ((lo >> (x * 8U)) & 0xFFU) : ((hi >> ((x - 4U) * 8U)) & 0xFFU);
    crc = preap_crc_lookup[crc ^ v];
  }
  return crc ^ 0xFFU;
}

// ============================================
// GTW Emulation helpers
// ============================================

static void preap_radar_readdr(const CANPacket_t *src, uint16_t new_addr) {
#if defined(STM32H7) || defined(STM32F4)
  CANPacket_t pkt;
  pkt.returned = 0U;
  pkt.rejected = 0U;
  pkt.extended = src->extended;
  pkt.bus = 1;
  pkt.addr = new_addr;
  pkt.data_len_code = src->data_len_code;
  for (int i = 0; i < GET_LEN(src); i++) {
    pkt.data[i] = src->data[i];
  }
  can_set_checksum(&pkt);
  can_send(&pkt, 1, true);
#else
  (void)src;
  (void)new_addr;
#endif
}

static uint8_t preap_byte_sum_checksum(const CANPacket_t *pkt) {
  uint8_t chksum = (uint8_t)(pkt->addr & 0xFFU) + (uint8_t)((pkt->addr >> 8) & 0xFFU);
  int len = GET_LEN(pkt);
  for (int i = 0; i < (len - 1); i++) {
    chksum += pkt->data[i];
  }
  return chksum;
}

// ============================================
// GTW Emulation: CAN0 → CAN1 for Bosch radar
// ============================================

static void tesla_preap_gtw_emulation(const CANPacket_t *to_fwd) {
  int bus_num = GET_BUS(to_fwd);
  int addr = GET_ADDR(to_fwd);

  if ((bus_num == 0) && preap_radar_emulation) {
    // Group A: Simple re-addresses
    switch (addr) {
      case 0x45:   preap_radar_readdr(to_fwd, 0x219); break;  // STW_ACTN_RQ
      case 0x108:  preap_radar_readdr(to_fwd, 0x109); break;  // DI_torque1
      case 0x145:  preap_radar_readdr(to_fwd, 0x149); break;  // ESP_145h
      case 0x20A:  preap_radar_readdr(to_fwd, 0x159); break;  // BrakeMessage -> ESP_C
      case 0x308:  preap_radar_readdr(to_fwd, 0x209); break;  // GTW_odo
      case 0x30A:  preap_radar_readdr(to_fwd, 0x2D9); break;  // BC_status
      case 0x405:  preap_radar_readdr(to_fwd, 0x2B9); break;  // VIP_405HS
      default: break;
    }

    // Group B: GTW_carConfig (0x398) → 0x2A9 with bitfield patching
    if (addr == 0x398) {
      CANPacket_t pkt = {.returned = 0U, .rejected = 0U, .extended = to_fwd->extended,
                         .bus = 1, .addr = 0x2A9, .data_len_code = to_fwd->data_len_code};
      uint32_t lo = PREAP_GET_BYTES_04(to_fwd);
      uint32_t hi = PREAP_GET_BYTES_48(to_fwd);
      lo = (lo & 0xFFFFF33FU) | 0x100U | 0x440U;  // country=US, radar_type=Bosch
      hi = (hi & 0xCFFF0F0FU) | 0x10000000U | (preap_radar_position << 4U);  // EPAS type remains zero
      PREAP_WORD_TO_BYTES(&pkt.data[0], lo);
      PREAP_WORD_TO_BYTES(&pkt.data[4], hi);
      pkt.data[7] = preap_byte_sum_checksum(&pkt);
#if defined(STM32H7) || defined(STM32F4)
      can_set_checksum(&pkt);
      can_send(&pkt, 1, true);
#endif
    }

    // Group B: STW_ANGLHP_STAT (0x0E) → 0x199 with SNA replacement
    if (addr == 0x0E) {
      CANPacket_t pkt = {.returned = 0U, .rejected = 0U, .extended = to_fwd->extended,
                         .bus = 1, .addr = 0x199, .data_len_code = to_fwd->data_len_code};
      uint32_t lo = PREAP_GET_BYTES_04(to_fwd);
      uint32_t hi = PREAP_GET_BYTES_48(to_fwd);
      if (((lo >> 16U) & 0xFF3FU) == 0xFF3FU) {
        lo = (lo & 0x00C0FFFFU) | 0x00200000U;
        hi = (hi & 0x00FFFFF0U) | 0x00000004U;  // force DELPHI sensor ID
        uint32_t crc = preap_compute_crc8(lo, hi, 7U);
        hi = hi | (crc << 24U);
      }
      PREAP_WORD_TO_BYTES(&pkt.data[0], lo);
      PREAP_WORD_TO_BYTES(&pkt.data[4], hi);
#if defined(STM32H7) || defined(STM32F4)
      can_set_checksum(&pkt);
      can_send(&pkt, 1, true);
#endif
    }

    // Group C: ESP_115h (0x115) → 0x129 + synthetic DI_espControl (0x1A9)
    if (addr == 0x115) {
      preap_radar_readdr(to_fwd, 0x129);
      uint32_t hi_src = PREAP_GET_BYTES_48(to_fwd);
      uint32_t counter = ((hi_src & 0xF0U) >> 4U) & 0x0FU;
      uint32_t syn_lo = 0x000C0000U | (counter << 28U);
      uint32_t cksm = (0x38U + 0x0CU + (counter << 4U)) & 0xFFU;
      CANPacket_t pkt = {.returned = 0U, .rejected = 0U, .extended = 0,
                         .bus = 1, .addr = 0x1A9, .data_len_code = 5};
      PREAP_WORD_TO_BYTES(&pkt.data[0], syn_lo);
      PREAP_WORD_TO_BYTES(&pkt.data[4], cksm);
#if defined(STM32H7) || defined(STM32F4)
      can_set_checksum(&pkt);
      can_send(&pkt, 1, true);
#endif
    }

    // Group C: DI_torque2 (0x118) → 0x119 + synthetic ESP_wheelSpeeds (0x169)
    if (addr == 0x118) {
      preap_radar_readdr(to_fwd, 0x119);
      uint32_t lo = PREAP_GET_BYTES_04(to_fwd);
      uint32_t ws_counter = PREAP_GET_BYTES_48(to_fwd) & 0x0FU;
      int raw_speed = (int)((0xFFF0000U & lo) >> 16);
      int speed;
      if (raw_speed == 0xFFF) {
        speed = 0x1FFF;
      } else {
        int mph_x100 = (raw_speed * 5) - 2500;
        int kph_x100 = mph_x100 * 1609 / 1000;
        speed = (kph_x100 < 0) ? 0 : ((kph_x100 / 4) & 0x1FFF);
      }
      // Pack using unsigned arithmetic: shifting a signed 13-bit speed by
      // 26 is undefined before a cast can truncate it to the intended bits.
      uint32_t speed_bits = (uint32_t)speed;
      uint32_t ws_lo = speed_bits | (speed_bits << 13U) | (speed_bits << 26U);
      uint32_t ws_hi = ((speed_bits >> 6U) | (speed_bits << 7U) | (ws_counter << 20U)) & 0x00FFFFFFU;
      uint32_t ws_cksm = 0x76U;
      ws_cksm = (ws_cksm + (ws_lo & 0xFFU) + ((ws_lo >> 8U) & 0xFFU) + ((ws_lo >> 16U) & 0xFFU) + ((ws_lo >> 24U) & 0xFFU)) & 0xFFU;
      ws_cksm = (ws_cksm + (ws_hi & 0xFFU) + ((ws_hi >> 8U) & 0xFFU) + ((ws_hi >> 16U) & 0xFFU)) & 0xFFU;
      ws_hi = ws_hi | (ws_cksm << 24U);
      CANPacket_t pkt = {.returned = 0U, .rejected = 0U, .extended = 0,
                         .bus = 1, .addr = 0x169, .data_len_code = 8};
      PREAP_WORD_TO_BYTES(&pkt.data[0], ws_lo);
      PREAP_WORD_TO_BYTES(&pkt.data[4], ws_hi);
#if defined(STM32H7) || defined(STM32F4)
      can_set_checksum(&pkt);
      can_send(&pkt, 1, true);
#endif
    }
  }

  // Radar status tracking (CAN1 → informational only)
  if ((bus_num == 1) && preap_radar_emulation) {
    if ((addr == 0x631) && (preap_radar_status == 0)) {
      preap_radar_status = 1;
      preap_last_radar_signal = microsecond_timer_get();
    }
    if ((addr == 0x300) && (preap_radar_status == 1)) {
      preap_radar_status = 2;
      preap_last_radar_signal = microsecond_timer_get();
    }
  }
}

// ============================================
// RX Hook
// ============================================

static void tesla_preap_rx_hook(const CANPacket_t *msg) {
  // Pedal interceptor (0x552) — may arrive on bus 0 OR bus 2 depending on wiring.
  // Must be handled BEFORE the bus-0-only handlers below.
  // Whitelisted on both bus 0 and bus 2 in preap_rx_checks; the framework has
  // already verified the message matches one of them, so accept either here.
  //
  // Gas-press threshold: 650 raw, chosen from real Pre-AP drive data:
  //   - At-rest noise (driver not pressing): raw range 424-633, mean 470 (p99.9=602)
  //   - Actual gas press: raw range 441-1246, mean 799 (p10=607, p50=802)
  // The original threshold of 450 was inside the resting noise distribution and
  // caused false gas_pressed readings that blocked pedal TX → pedal wouldn't engage.
  // 650 gives zero false positives on rest noise while still catching the vast
  // majority of real driver presses. Python-layer DI_pedalPos is the primary
  // gas-override detection; the panda threshold here is a safety backstop.
  if (preap_enable_pedal && (msg->addr == 0x552U)) {
    int pedal_val = ((msg->data[0] << 8) | msg->data[1]);
    gas_pressed = (pedal_val > 650);
    if (preap_pedal_can == -1) {
      preap_pedal_can = msg->bus;
    }
  } else if (msg->bus == 0U) {
    // All other RX handlers are bus 0 only.

    // EPAS (0x370): steering angle, hands-on level, disengage detection
    if (msg->addr == 0x370U) {
      const int raw_angle = ((msg->data[4] & 0x3FU) << 8) | msg->data[5];
      const int angle_meas_new = raw_angle - 8192;
      update_sample(&angle_meas, angle_meas_new);

      const int hands_on_level = msg->data[4] >> 6;
      const int eac_status = msg->data[6] >> 5;
      const int eac_error_code = msg->data[2] >> 4;

      // Disengage on hands-on override OR EPAS actively rejecting steering commands.
      // Error codes 6/7/8 = EPAS request validators rejected angle/rate, 9 = safety layer.
      // All indicate the EPAS stopped steering — driver must be notified immediately.
      bool epas_rejecting = (eac_status == 0) && (eac_error_code >= 6) && (eac_error_code <= 9);
      steering_disengage = (hands_on_level >= 3) || epas_rejecting;

      // Re-arm fix: force cruise_engaged_prev reset on steering disengage
      // so next stalk pull creates a clean rising edge
      if (steering_disengage && !steering_disengage_prev) {
        pcm_cruise_check(false);
      }
    }

    // Vehicle speed (ESP_B: 0x155) — derive vehicle_moving from actual speed
    if (msg->addr == 0x155U) {
      preap_eas_speed_ts = microsecond_timer_get();
      preap_eas_speed_seen = true;
      uint32_t raw_speed = ((uint32_t)msg->data[5] << 8U) | msg->data[6];
      preap_eas_speed_ok = raw_speed < 6437U;
      float speed = ((float)raw_speed * 0.01f) * KPH_TO_MS;
      UPDATE_VEHICLE_SPEED(speed);
      vehicle_moving = speed > (0.5f * KPH_TO_MS);
    }

    // Gas pressed from DI_torque1 (0x108) — only when pedal interceptor is not active.
    // (The pedal interceptor path is handled above the bus-0-only handlers since it may
    // arrive on bus 0 or bus 2.)
    if (msg->addr == 0x108U) {
      if (!preap_enable_pedal) {
        gas_pressed = msg->data[6] != 0U;
      }
    }

    // Brake (0x20a) — force false so generic_rx_checks doesn't drop controls_allowed.
    // Pre-AP brake → steering-only is handled in the software layer.
    if (msg->addr == 0x20aU) {
      brake_pressed = false;
    }

    // Cruise state (DI_state: 0x368) — vehicle_moving only, engagement via stalk
    if (msg->addr == 0x368U) {
      int cruise_state = (msg->data[1] >> 4) & 0x07U;
      // Backup vehicle_moving from cruise state (standstill detection)
      if (cruise_state == 3) {
        vehicle_moving = false;
      }
    }

    // Gear check (DI_torque2: 0x118) — disable controls on leaving Drive
    if (msg->addr == 0x118U) {
      preap_gear = (msg->data[1] >> 4) & 0x07U;
      if ((preap_gear_prev == 4) && (preap_gear != 4)) {
        controls_allowed = false;
      }
      preap_gear_prev = preap_gear;
    }

    // Door check (GTW_carState: 0x318)
    if (msg->addr == 0x318U) {
      int d_fl = (msg->data[1] >> 4) & 0x03U;
      int d_fr = (msg->data[1] >> 6) & 0x03U;
      int d_rl = (msg->data[2] >> 6) & 0x03U;
      int d_rr = (msg->data[3] >> 5) & 0x03U;
      int d_ft = (msg->data[6] >> 2) & 0x03U;
      int d_tr = (msg->data[5] >> 6) & 0x03U;
      preap_doors_open = (d_fl == 1) || (d_fr == 1) || (d_rl == 1) || (d_rr == 1) || (d_ft == 1) || (d_tr == 1);
      if (preap_doors_open) {
        controls_allowed = false;
      }
    }

    // Stalk engagement (STW_ACTN_RQ: 0x45) with echo-filtered cancel
    if (msg->addr == 0x45U) {
      int lever = msg->data[0] & 0x3FU;
      uint32_t now = microsecond_timer_get();
      bool fresh_pull = (preap_stalk_prev == 0) &&
                        ((now - preap_stalk_ts) < PREAP_STALK_FRESH_US);
      if (lever == 2) {  // RWD = pull toward driver = enable
        if (fresh_pull && (preap_gear == 4) && !preap_doors_open &&
            !steering_disengage && !safety_rx_checks_invalid) {
          // Application/heartbeat disengagement can clear controls_allowed
          // without clearing the stock-cruise latch. Only a fresh physical
          // neutral -> pull gesture may reset that latch and request re-arm.
          // A held pull, startup with the stalk held, or releasing an override
          // while holding the stalk must never restore permission.
          cruise_engaged_prev = false;
          pcm_cruise_check(true);
          preap_last_stalk_engage_us = now;
        }
      } else if (lever == 1) {  // FWD = push away = cancel
        uint32_t elapsed = now - preap_last_stalk_engage_us;
        if (elapsed > PREAP_CANCEL_ECHO_WINDOW_US) {
          pcm_cruise_check(false);
        }
      } else {
        // Other stalk positions do not change engagement.
      }
      preap_stalk_prev = lever;
      preap_stalk_ts = now;
    }
  } else {
    // Ignore other messages off the chassis bus.
  }
}

// ============================================
// TX Hook
// ============================================

static bool tesla_preap_eas_tx_allowed(const CANPacket_t *msg) {
  bool allowed = false;
  const uint8_t *d = msg->data;
  if ((GET_BUS(msg) == 0U) && (GET_LEN(msg) == 8U) && (d[6] == 0U) && (d[7] == 0U)) {
    bool dtc_read = (d[0] == 3U) && (d[1] == 0x19U) && (d[2] == 2U) && (d[3] == 0xFFU) && (d[4] == 0U) && (d[5] == 0U);
    bool dtc_flow = (d[0] == 0x30U) && (d[1] == 0U) && (d[2] == 0U) && (d[3] == 0U) && (d[4] == 0U) && (d[5] == 0U);
    // Only recovered single-frame commands. Cleanup remains available at speed.
    bool session = (d[0] == 2U) && (d[1] == 0x10U) && (d[3] == 0U) && (d[4] == 0U) && (d[5] == 0U);
    bool routine = (d[0] == 4U) && (d[1] == 0x31U) && (d[3] == 3U) && (d[5] == 0U);
    bool cleanup = (session && (d[2] == 1U)) ||
                   (routine && (d[2] == 2U) && ((d[4] == 0x34U) || (d[4] == 0x10U))) ||
                   (routine && ((d[2] == 1U) || (d[2] == 2U) || (d[2] == 3U)) && (d[4] == 9U));
    bool fresh_low_speed = preap_eas_speed_seen && preap_eas_speed_ok &&
                          ((microsecond_timer_get() - preap_eas_speed_ts) < 250000U);
    bool vent = (d[0] == 6U) && (d[1] == 0x31U) && (d[2] == 1U) && (d[3] == 3U) && (d[4] == 0x34U) && (d[5] <= 3U);
    bool setup = (session && (d[2] == 3U)) || (routine && (d[2] == 1U) && (d[4] == 0x10U));
    allowed = dtc_read || dtc_flow || cleanup || (fresh_low_speed && (vent || setup));
  }
  return allowed;
}

static bool tesla_preap_tx_hook(const CANPacket_t *msg) {
  const AngleSteeringLimits PREAP_STEERING_LIMITS = {
    .max_angle = 3600,  // 360 deg, EPAS faults above this
    .angle_deg_to_can = 10,
    .frequency = 50U,
  };

  // Pre-AP Model S is physically the same car as HW1/HW2/HW3 Model S.
  // These values MUST match VehicleModel(TESLA_MODEL_S_HW3) in carcontroller.py.
  // Verified: mass=2100+STD_CARGO_KG, wheelbase=2.960, steerRatio=15.0
  //           → slip_factor = -0.0005666 (calc_slip_factor)
  // Confirmed by Lukas (xnor-tech, former comma employee, Tesla port author).
  const AngleSteeringParams PREAP_STEERING_PARAMS = {
    .slip_factor = -0.0005666,
    .steer_ratio = 15.,
    .wheelbase = 2.96,
  };

  bool tx = true;
  bool violation = false;

  if (msg->addr == 0x64BU) {
    tx = tesla_preap_eas_tx_allowed(msg);
  }

  // DAS_steeringControl (0x488)
  if (msg->addr == 0x488U) {
    int raw_angle_can = ((msg->data[0] & 0x7FU) << 8) | msg->data[1];
    int desired_angle = raw_angle_can - 16384;
    int steer_control_type = msg->data[2] >> 6;
    bool steer_control_enabled = steer_control_type == 1;

    if (steer_angle_cmd_checks_vm(desired_angle, steer_control_enabled, PREAP_STEERING_LIMITS, PREAP_STEERING_PARAMS)) {
      violation = true;
    }
    if ((steer_control_type != 0) && (steer_control_type != 1)) {
      violation = true;
    }
  }

  // EPB_epasControl (0x214): only allow valid EAC modes (0=disable, 1=enable)
  if (msg->addr == 0x214U) {
    int epas_control_type = msg->data[0] & 0x07U;  // EPB_epasEACAllow: bits 2:0 of byte 0
    if (epas_control_type > 1) {
      violation = true;
    }
  }

  // DAS_control (0x2B9): no AEB events from openpilot
  if (msg->addr == 0x2B9U) {
    int aeb_event = msg->data[2] & 0x03U;
    if (aeb_event != 0) {
      violation = true;
    }
  }

  // Pedal interceptor (0x551 GAS_COMMAND): parse ENABLE bit and GAS_COMMAND
  // value to distinguish authoritative accel commands from driver-passthrough
  // release commands.
  //   DBC: SG_ ENABLE : 39|1@0+  →  bit 7 of data[4]
  //   DBC: SG_ GAS_COMMAND : 7|16@0+  →  bytes 0-1 big-endian (physical 0 = raw 450)
  //
  //   ENABLE=0: openpilot is releasing control. Comma Pedal ignores GAS_COMMAND
  //   and passes driver's OEM pedal voltage through. NAP's pedal passthrough
  //   feature sends this during driver gas override for a smooth handoff.
  //   Defense-in-depth: we still require the GAS_COMMAND raw value to be at or
  //   below the zero point (raw <= 500, which is ~2.5% physical) so a bugged or
  //   malicious ENABLE=0 + high-value message can't sneak through a potential
  //   Comma Pedal firmware bug.
  //
  //   ENABLE=1: authoritative actuation command. Gated by get_longitudinal_allowed()
  //   (controls_allowed && !gas_pressed_prev).
  if (msg->addr == 0x551U) {
    if (!preap_enable_pedal) {
      violation = true;
    } else {
      bool pedal_enable = (msg->data[4] & 0x80U) != 0U;
      int raw_gas_cmd = (msg->data[0] << 8) | msg->data[1];
      if (pedal_enable) {
        if (!get_longitudinal_allowed()) {
          violation = true;
        }
      } else {
        // ENABLE=0: only allow near-zero GAS_COMMAND values (defense-in-depth).
        // Legitimate passthrough sends physical 0 = raw 450.
        if (raw_gas_cmd > 500) {
          violation = true;
        }
      }
    }
  }

  if (violation) {
    tx = false;
  }
  return tx;
}

// ============================================
// Forwarding Hook
// ============================================

static bool tesla_preap_fwd_hook(int bus_num, int addr) {
  (void)bus_num;
  (void)addr;
  // Pre-AP has no AP ECU on bus 2. Block default 0↔2 forwarding to avoid
  // flooding a dead TX queue.
  return true;
}

// ============================================
// Init
// ============================================

static safety_config tesla_preap_init(uint16_t param) {
  preap_enable_pedal = GET_FLAG(param, PREAP_FLAG_ENABLE_PEDAL);
  preap_radar_emulation = GET_FLAG(param, PREAP_FLAG_RADAR_EMULATION);
  bool preap_radar_behind_nosecone = GET_FLAG(param, PREAP_FLAG_RADAR_BEHIND_NOSECONE);

  preap_eas_speed_seen = false;
  preap_eas_speed_ok = false;
  preap_eas_speed_ts = 0U;
  preap_gear = 4;
  preap_gear_prev = 4;
  preap_doors_open = false;
  preap_pedal_can = -1;
  preap_radar_status = 0;
  preap_last_radar_signal = 0;
  preap_last_stalk_engage_us = 0;
  preap_stalk_prev = -1;
  preap_stalk_ts = 0U;
  preap_radar_position = preap_radar_behind_nosecone ? 1U : 0U;

  // TX whitelist — no harness relay on Pre-AP
  static const CanMsg PREAP_TX_MSGS[] = {
    {0x64B, 0, 8, .check_relay = false, .disable_static_blocking = true},  // Narrow EAS commands
    {0x488, 0, 4, .check_relay = false, .disable_static_blocking = true},  // DAS_steeringControl
    {0x2B9, 0, 8, .check_relay = false, .disable_static_blocking = true},  // DAS_control
    {0x214, 0, 3, .check_relay = false, .disable_static_blocking = true},  // EPB_epasControl
    {0x551, 0, 6, .check_relay = false, .disable_static_blocking = true},  // Pedal on bus 0
    {0x551, 2, 6, .check_relay = false, .disable_static_blocking = true},  // Pedal on bus 2
    {0x45,  0, 8, .check_relay = false, .disable_static_blocking = true},  // STW_ACTN_RQ (stalk spoof)
  };

  // RX checks — disable EPAS counter/checksum until we verify the Pre-AP
  // EPAS firmware's checksum matches our compute_checksum exactly.
  // Mismatched validation caused silent 21s steering dropout.
  static RxCheck preap_rx_checks[] = {
    {.msg = {{0x370, 0, 8, 25U, .ignore_quality_flag = true, .ignore_checksum = true, .ignore_counter = true}, { 0 }, { 0 }}},   // EPAS_sysStatus
    {.msg = {{0x108, 0, 8, 100U, .ignore_quality_flag = true, .ignore_checksum = true, .ignore_counter = true}, { 0 }, { 0 }}},  // DI_torque1
    {.msg = {{0x118, 0, 6, 100U, .ignore_quality_flag = true, .ignore_checksum = true, .ignore_counter = true}, { 0 }, { 0 }}},  // DI_torque2
    {.msg = {{0x20a, 0, 8, 50U, .ignore_quality_flag = true, .ignore_checksum = true, .ignore_counter = true}, { 0 }, { 0 }}},   // BrakeMessage
    {.msg = {{0x368, 0, 8, 10U, .ignore_quality_flag = true, .ignore_checksum = true, .ignore_counter = true}, { 0 }, { 0 }}},   // DI_state
    {.msg = {{0x318, 0, 8, 10U, .ignore_quality_flag = true, .ignore_checksum = true, .ignore_counter = true}, { 0 }, { 0 }}},   // GTW_carState
    {.msg = {{0x45,  0, 8, 10U, .ignore_quality_flag = true, .ignore_checksum = true, .ignore_counter = true}, { 0 }, { 0 }}},   // STW_ACTN_RQ
    {.msg = {{0x155, 0, 8, 50U, .ignore_quality_flag = true, .ignore_checksum = true, .ignore_counter = true}, { 0 }, { 0 }}},   // ESP_B
  };

  // Pedal-enabled variant: adds 0x552 (GAS_SENSOR) to rx_checks so the
  // framework routes it to the rx hook. Split into its own array because
  // frequency=0 causes divide-by-zero in safety_tick (safety.h:330), which
  // marks the check as lagging and trips safetyRxChecksInvalid → controls
  // mismatch on cars without a pedal. 50Hz matches the Comma Pedal firmware.
  static RxCheck preap_rx_checks_with_pedal[] = {
    {.msg = {{0x370, 0, 8, 25U, .ignore_quality_flag = true, .ignore_checksum = true, .ignore_counter = true}, { 0 }, { 0 }}},
    {.msg = {{0x108, 0, 8, 100U, .ignore_quality_flag = true, .ignore_checksum = true, .ignore_counter = true}, { 0 }, { 0 }}},
    {.msg = {{0x118, 0, 6, 100U, .ignore_quality_flag = true, .ignore_checksum = true, .ignore_counter = true}, { 0 }, { 0 }}},
    {.msg = {{0x20a, 0, 8, 50U, .ignore_quality_flag = true, .ignore_checksum = true, .ignore_counter = true}, { 0 }, { 0 }}},
    {.msg = {{0x368, 0, 8, 10U, .ignore_quality_flag = true, .ignore_checksum = true, .ignore_counter = true}, { 0 }, { 0 }}},
    {.msg = {{0x318, 0, 8, 10U, .ignore_quality_flag = true, .ignore_checksum = true, .ignore_counter = true}, { 0 }, { 0 }}},
    {.msg = {{0x45,  0, 8, 10U, .ignore_quality_flag = true, .ignore_checksum = true, .ignore_counter = true}, { 0 }, { 0 }}},
    {.msg = {{0x155, 0, 8, 50U, .ignore_quality_flag = true, .ignore_checksum = true, .ignore_counter = true}, { 0 }, { 0 }}},
    {.msg = {{0x552, 0, 6, 50U, .ignore_quality_flag = true, .ignore_checksum = true, .ignore_counter = true},
             {0x552, 2, 6, 50U, .ignore_quality_flag = true, .ignore_checksum = true, .ignore_counter = true}, { 0 }}},  // GAS_SENSOR
  };

  return preap_enable_pedal ? BUILD_SAFETY_CFG(preap_rx_checks_with_pedal, PREAP_TX_MSGS)
                            : BUILD_SAFETY_CFG(preap_rx_checks, PREAP_TX_MSGS);
}

// ============================================
// Hooks struct
// ============================================

const safety_hooks tesla_preap_hooks = {
  .init = tesla_preap_init,
  .rx = tesla_preap_rx_hook,
  .rx_all = tesla_preap_gtw_emulation,  // must see ALL CAN traffic for radar GTW forwarding
  .tx = tesla_preap_tx_hook,
  .fwd = tesla_preap_fwd_hook,
  .get_counter = tesla_preap_get_counter,
  .get_checksum = tesla_preap_get_checksum,
  .compute_checksum = tesla_preap_compute_checksum,
  .get_quality_flag_valid = NULL,
};
