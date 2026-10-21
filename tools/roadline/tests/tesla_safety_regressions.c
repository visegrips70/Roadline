// In-memory firmware checks: no CAN devices, settings, or vehicle connections.
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#define STM32H7
#define ALLOW_DEBUG
static uint32_t now;
uint32_t microsecond_timer_get(void) { return now; }
#include "opendbc/safety/can.h"
#include "opendbc/safety/safety.h"

static CANPacket_t sent;
static unsigned int sends;
void can_set_checksum(CANPacket_t *packet) { (void)packet; }
void can_send(CANPacket_t *packet, uint8_t bus, bool skip_tx_hook) {
  assert(bus == packet->bus);
  assert(skip_tx_hook);
  sent = *packet;
  sends++;
}

// A bitwise CRC oracle, independent of the production lookup table.
static uint8_t crc8(const uint8_t *data, unsigned int len) {
  uint8_t crc = 0xFFU;
  for (unsigned int i = 0U; i < len; i++) {
    crc ^= data[i];
    for (unsigned int bit = 0U; bit < 8U; bit++) {
      crc = (uint8_t)((crc << 1U) ^ ((crc & 0x80U) ? 0x1DU : 0U));
    }
  }
  return crc ^ 0xFFU;
}

static void check_radar_crc(void) {
  (void)tesla_preap_init(PREAP_FLAG_RADAR_EMULATION);
  for (unsigned int byte = 0U; byte < 8U; byte++) {
    for (unsigned int value = 0U; value < 256U; value++) {
      CANPacket_t input = {.addr = 0xEU, .bus = 0U, .data_len_code = 8U,
                           .data = {0x80, 0xFF, 0xFF, 0xFF, 0xFF, 0xAA, 0x55, 0xFF}};
      input.data[byte] = (uint8_t)value;
      uint32_t lo = PREAP_GET_BYTES_04(&input);
      uint32_t hi = PREAP_GET_BYTES_48(&input);
      assert(preap_compute_crc8(lo, hi, 7U) == crc8(input.data, 7U));
      sends = 0U;
      tesla_preap_gtw_emulation(&input);
      assert(sends == 1U && sent.addr == 0x199U && sent.bus == 1U);
      bool unavailable = ((input.data[2] & 0x3FU) == 0x3FU) && (input.data[3] == 0xFFU);
      if (unavailable) {
        uint8_t expected[8];
        memcpy(expected, input.data, sizeof(expected));
        expected[2] = (expected[2] & 0xC0U) | 0x20U;
        expected[3] = 0U;
        expected[4] = (expected[4] & 0xF0U) | 4U;
        expected[7] = crc8(expected, 7U);
        assert(memcmp(sent.data, expected, sizeof(expected)) == 0);
      } else {
        assert(memcmp(sent.data, input.data, 8U) == 0);
      }
    }
  }
}

static void check_legacy_forwarding(void) {
  for (uint16_t flags = 0U; flags < 32U; flags += 2U) {
    (void)tesla_legacy_init(flags);
    for (unsigned int bus = 0U; bus < 3U; bus++) {
      for (unsigned int addr = 0U; addr < 2048U; addr++) {
        CANPacket_t input = {.addr = addr, .bus = bus, .data_len_code = 8U,
                             .data = {0x80, 0xAB, 0xCD, 0xFF, 0x81, 0x98, 0x76, 0xFE}};
        sends = 0U;
        tesla_legacy_handle_forwarding(&input);
        bool blocked = (addr == 0x27DU) && ((flags & (2U | 4U)) == 0U);
        bool expected = (bus == 2U) && !blocked;
        assert(sends == (expected ? 1U : 0U));
        if (expected) {
          assert(sent.addr == addr && sent.bus == 0U && sent.data_len_code == 8U);
          assert(memcmp(sent.data, input.data, 8U) == 0);
        }
      }
    }
  }
}

static void check_eas_allowlist(void) {
  // First eight are status/cleanup; the remaining six require fresh low speed.
  const uint8_t commands[][8] = {
    {3, 0x19, 2, 0xFF, 0, 0, 0, 0}, {0x30, 0, 0, 0, 0, 0, 0, 0},
    {2, 0x10, 1, 0, 0, 0, 0, 0}, {4, 0x31, 2, 3, 0x34, 0, 0, 0},
    {4, 0x31, 2, 3, 0x10, 0, 0, 0}, {4, 0x31, 1, 3, 9, 0, 0, 0},
    {4, 0x31, 2, 3, 9, 0, 0, 0}, {4, 0x31, 3, 3, 9, 0, 0, 0},
    {2, 0x10, 3, 0, 0, 0, 0, 0}, {4, 0x31, 1, 3, 0x10, 0, 0, 0},
    {6, 0x31, 1, 3, 0x34, 0, 0, 0}, {6, 0x31, 1, 3, 0x34, 1, 0, 0},
    {6, 0x31, 1, 3, 0x34, 2, 0, 0}, {6, 0x31, 1, 3, 0x34, 3, 0, 0},
  };
  const unsigned int count = sizeof(commands) / sizeof(commands[0]);
  // Exercise missing samples, speed boundary, freshness boundary, and timer wrap.
  const struct { bool seen; unsigned int speed; uint32_t start; uint32_t age; bool manual; } states[] = {
    {false, 0, 0, 0, false}, {true, 6436, 1000000, 0, true},
    {true, 6437, 1000000, 0, false}, {true, 6436, 1000000, 249999, true},
    {true, 6436, 1000000, 250000, false}, {true, 6436, UINT32_MAX - 100U, 200, true},
  };
  for (unsigned int state = 0U; state < sizeof(states) / sizeof(states[0]); state++) {
    (void)tesla_preap_init(0U);
    now = states[state].start;
    if (states[state].seen) {
      CANPacket_t speed = {.addr = 0x155U, .bus = 0U, .data_len_code = 8U};
      speed.data[5] = (uint8_t)(states[state].speed >> 8U);
      speed.data[6] = (uint8_t)states[state].speed;
      tesla_preap_rx_hook(&speed);
    }
    now += states[state].age;
    for (unsigned int command = 0U; command < count; command++) {
      for (unsigned int byte = 0U; byte < 8U; byte++) {
        for (unsigned int value = 0U; value < 256U; value++) {
          CANPacket_t input = {.addr = 0x64BU, .bus = 0U, .data_len_code = 8U};
          memcpy(input.data, commands[command], 8U);
          input.data[byte] = (uint8_t)value;
          bool allowed = false;
          for (unsigned int match = 0U; match < count; match++) {
            if (memcmp(input.data, commands[match], 8U) == 0) {
              allowed = (match < 8U) || states[state].manual;
            }
          }
          assert(tesla_preap_tx_hook(&input) == allowed);
          input.bus = 1U;
          assert(!tesla_preap_tx_hook(&input));
          input.bus = 0U;
          input.data_len_code = 7U;
          assert(!tesla_preap_tx_hook(&input));
        }
      }
    }
  }
}

int main(void) {
  check_radar_crc();
  check_legacy_forwarding();
  check_eas_allowlist();
  puts("Tesla CRC, firmware forwarding, and EAS boundary/mutation checks passed");
  return 0;
}
