// Exercise the actual firmware-only forwarding path with an in-memory CAN sink.
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>

#define STM32H7
#define ALLOW_DEBUG
uint32_t microsecond_timer_get(void) { return 0U; }
#include "opendbc/safety/can.h"
#include "opendbc/safety/safety.h"

static CANPacket_t wheel_packet;
static unsigned int wheel_count;

void can_set_checksum(CANPacket_t *packet) { (void)packet; }
void can_send(CANPacket_t *packet, uint8_t bus, bool skip_tx_hook) {
  assert(bus == 1U);
  assert(skip_tx_hook);
  if (packet->addr == 0x169U) {
    wheel_packet = *packet;
    wheel_count++;
  }
}

int main(void) {
  (void)tesla_preap_init(PREAP_FLAG_RADAR_EMULATION);
  for (unsigned int raw = 0U; raw < 4096U; raw++) {
    for (unsigned int counter = 0U; counter < 16U; counter++) {
      CANPacket_t input = {.addr = 0x118U, .bus = 0U, .data_len_code = 6U};
      input.data[2] = (uint8_t)(raw & 0xFFU);
      input.data[3] = (uint8_t)(0xF0U | (raw >> 8U));
      input.data[4] = (uint8_t)counter;
      input.data[7] = 0xFFU; // high bit also exercises unsigned byte assembly
      wheel_count = 0U;
      tesla_preap_gtw_emulation(&input);
      assert(wheel_count == 1U);

      int mph_x100 = ((int)raw * 5) - 2500;
      int kph_x100 = (mph_x100 * 1609) / 1000;
      uint64_t expected = raw == 4095U ? 8191U : (uint64_t)(kph_x100 < 0 ? 0 : kph_x100 / 4);
      expected &= 8191U;
      uint64_t word = 0U;
      unsigned int checksum = 0x76U;
      for (unsigned int byte = 0U; byte < 7U; byte++) {
        word |= (uint64_t)wheel_packet.data[byte] << (byte * 8U);
        checksum += wheel_packet.data[byte];
      }
      for (unsigned int wheel = 0U; wheel < 4U; wheel++) {
        assert(((word >> (wheel * 13U)) & 8191U) == expected);
      }
      assert(((word >> 52U) & 15U) == counter);
      assert(wheel_packet.data[7] == (checksum & 255U));
    }
  }
  puts("65536 radar speed/counter combinations passed with undefined-behavior checks");
  return 0;
}
