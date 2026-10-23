from dataclasses import replace
import types
import numpy as np
from opendbc.can import CANPacker
from opendbc.car import Bus
from opendbc.car.lateral import apply_steer_angle_limits_vm
from opendbc.car.interfaces import CarControllerBase
from opendbc.car.tesla.teslacan import TeslaCAN
from opendbc.car.tesla.teslacan_legacy import TeslaCANRaven
from opendbc.car.tesla.values import CarControllerParams, CANBUS, LEGACY_CARS, CAR
from opendbc.car.vehicle_model import VehicleModel
from opendbc.car.tesla.preap.carcontroller import PreAPLongController, init_preap_can
from opendbc.car.tesla.preap.stock_cc_spoofer import StockCCSpoofer
from opendbc.car.tesla.preap.parked_signal_test import ParkedSignalTest
from opendbc.car.tesla.preap.tap_lane_change import NavigationSignalController, TapController
from opendbc.car.tesla.preap.nap_params import NAPParamKeys
from opendbc.car.tesla.preap.steering_override import steering_takeover_requested
from opendbc.car.tesla.preap.turn_safety import TurnDirectionGuard

def get_safety_CP():
  from opendbc.car.tesla.interface import CarInterface
  return CarInterface.get_non_essential_params("TESLA_MODEL_Y")

class CarController(CarControllerBase):
  def __init__(self, dbc_names, CP):
    super().__init__(dbc_names, CP)
    self.apply_angle_last = 0
    self.packer = CANPacker(dbc_names[Bus.party])
    self.tesla_can = TeslaCAN(self.packer)

    self.VM = VehicleModel(get_safety_CP())

    if CP.carFingerprint in LEGACY_CARS:
      if CP.carFingerprint in (CAR.TESLA_MODEL_S_HW1, CAR.TESLA_MODEL_X_HW1, CAR.TESLA_MODEL_S_PREAP):
        CANBUS.powertrain = CANBUS.party
        CANBUS.autopilot_powertrain = CANBUS.autopilot_party

      self.packers = {CANBUS.party: CANPacker(dbc_names[Bus.party]), CANBUS.powertrain: CANPacker(dbc_names[Bus.pt])}

      if CP.carFingerprint == CAR.TESLA_MODEL_S_PREAP:
        self.preap_long = PreAPLongController()
        self.stock_cc = StockCCSpoofer()
        self.parked_signal_test = ParkedSignalTest()
        self.navigation_signal = NavigationSignalController()
        self.tap_lane_change = TapController()
        try:
          from openpilot.common.params import Params
          self.tap_params = Params()
        except ImportError:
          self.tap_params = None
        self.tesla_can = init_preap_can(dbc_names, self.packers)
      else:
        self.tesla_can = TeslaCANRaven(self.packers)

      from opendbc.car.tesla.interface import CarInterface
      self.VM = VehicleModel(CarInterface.get_non_essential_params("TESLA_MODEL_S_HW3"))

  def update(self, CC, CS, now_nanos):
    if self.CP.carFingerprint == CAR.TESLA_MODEL_S_PREAP:
      return self._update_preap(CC, CS)

    actuators = CC.actuators
    can_sends = []

    lat_active = CC.latActive and CS.hands_on_level < 3

    if self.frame % 2 == 0:
      try:
        auto_res = __import__("json").load(open("/data/nap_settings.json")).get("auto_resume", False)
      except:
        auto_res = False

      target_angle = CS.out.steeringAngleDeg if ((CS.out.steeringPressed or getattr(CS, "hands_on_level", 0) >= 3) and auto_res) else actuators.steeringAngleDeg
      self.apply_angle_last = apply_steer_angle_limits_vm(target_angle, self.apply_angle_last, CS.out.vEgoRaw, CS.out.steeringAngleDeg,
                                                          lat_active, CarControllerParams, self.VM)
      if self.CP.carFingerprint in LEGACY_CARS:
        cntr = (self.frame // 2) % 16
        can_sends.append(self.tesla_can.create_steering_control(cntr, self.apply_angle_last, lat_active))
      else:
        can_sends.append(self.tesla_can.create_steering_control(self.apply_angle_last, lat_active))

    if self.frame % 10 == 0:
      if self.CP.carFingerprint in LEGACY_CARS and self.CP.carFingerprint not in (CAR.TESLA_MODEL_S_HW1, CAR.TESLA_MODEL_X_HW1):
        cntr = (self.frame // 10) % 16
        can_sends.append(self.tesla_can.create_steering_allowed(cntr))
      elif self.CP.carFingerprint not in LEGACY_CARS:
        can_sends.append(self.tesla_can.create_steering_allowed())

    if self.CP.openpilotLongitudinalControl:
      if self.frame % 4 == 0:
        state = 13 if CC.cruiseControl.cancel else 4
        accel = float(np.clip(actuators.accel, CarControllerParams.ACCEL_MIN, CarControllerParams.ACCEL_MAX))
        cntr = (self.frame // 4) % 8
        can_sends.append(self.tesla_can.create_longitudinal_command(state, accel, cntr, CS.out.vEgo, CC.longActive))
    else:
      if CC.cruiseControl.cancel:
        cntr = (CS.das_control["DAS_controlCounter"] + 1) % 8
        can_sends.append(self.tesla_can.create_longitudinal_command(13, 0, cntr, CS.out.vEgo, False))

    new_actuators = actuators.as_builder()
    new_actuators.steeringAngleDeg = self.apply_angle_last

    self.frame += 1
    return new_actuators, can_sends

  def _update_preap(self, CC, CS):
    actuators = CC.actuators
    can_sends = []

    # Shared gate for low-speed steering rate and HSO sensitivity.
    speed_mph = CS.out.vEgo * 2.236936
    blinker_on = bool(CS.out.leftBlinker) != bool(CS.out.rightBlinker)

    low_speed_turn_profile = (
      speed_mph < 25.0
      and blinker_on
    )

    driver_pulling = (steering_takeover_requested(
      getattr(CS, "hands_on_level", 0), CS.out.steeringTorque, CS.out.vEgo,
      blinker_on, CS.out.steeringPressed) or getattr(CS.out, "steeringDisengage", False))

    # Takeover cancels both axes. Never reacquire merely because driver
    # effort, an indicator, or a timer expires. Observe full disengagement
    # before allowing the FSM's next fresh stalk engagement to take effect.
    if not hasattr(self, "steering_takeover_latched"):
      self.steering_takeover_latched = False
    if not CC.enabled and not CS.cruiseEnabled:
      self.steering_takeover_latched = False
    if driver_pulling:
      self.steering_takeover_latched = True

    if not hasattr(self, "turn_direction_guard"):
      self.turn_direction_guard = TurnDirectionGuard()
    # Independent final request check before packing steering or pedal CAN.
    turn_blocked = self.turn_direction_guard.update(
      CS.out, [actuators.curvature] if CC.latActive else [],
      enabled=CC.enabled, cruise_enabled=CS.cruiseEnabled)
    overriding = self.steering_takeover_latched or turn_blocked
    control_allowed = CC.enabled and CS.cruiseEnabled and not overriding
    if overriding:
      low_speed_turn_profile = False
    lat_active = control_allowed and CC.latActive

    if self.frame % 2 == 0:
      target_angle = CS.out.steeringAngleDeg if overriding else actuators.steeringAngleDeg
      if overriding:
        self.apply_angle_last = CS.out.steeringAngleDeg

      # ========================================================
      # BLINKER-GATED LOW-SPEED STEERING RATE
      #
      # Blinker OFF:
      #   stock Tesla steering rate
      #
      # Blinker ON + below 25 mph:
      #   <=5 mph : 9.00 deg / 20ms
      #    10 mph : 8.50 deg / 20ms
      #    15 mph : 8.00 deg / 20ms
      #    20 mph : 7.50 deg / 20ms
      #    25 mph : 7.00 deg / 20ms stock
      #
      # VM lateral accel/jerk limits remain active.
      # ========================================================
      params_to_use = CarControllerParams

      if not hasattr(self, 'params'):
        from openpilot.common.params import Params
        self.params = Params()
        self.low_speed_steering_rate_enabled = True

      if self.frame % 100 == 0:
        self.low_speed_steering_rate_enabled = self.params.get_bool("NAPLowSpeedSteeringRate")

      if not self.low_speed_steering_rate_enabled:
        low_speed_turn_profile = False

      if low_speed_turn_profile:
        speed_fraction = max(
          0.0,
          min(
            1.0,
            (speed_mph - 5.0) / 20.0,
          ),
        )

        low_speed_max_angle_rate = (
          9.0 - (2.0 * speed_fraction)
        )

        scaled_limits = replace(
          CarControllerParams.ANGLE_LIMITS,
          MAX_ANGLE_RATE=low_speed_max_angle_rate,
        )

        params_to_use = types.SimpleNamespace(
          ANGLE_LIMITS=scaled_limits,
          STEER_STEP=CarControllerParams.STEER_STEP,
        )

      self.apply_angle_last = apply_steer_angle_limits_vm(target_angle, self.apply_angle_last, CS.out.vEgoRaw, CS.out.steeringAngleDeg,
                                                          lat_active, params_to_use, self.VM)
      cntr = (self.frame // 2) % 16
      can_sends.append(self.tesla_can.create_steering_control(cntr, self.apply_angle_last, lat_active))
      can_sends.append(self.tesla_can.create_epas_control(cntr, 1)) # EPAS must stay powered to avoid shudder

    CS.pccEvent = None

    if self.CP.openpilotLongitudinalControl:
      can_sends.extend(self.preap_long.update(CC, CS, self.frame, self.tesla_can, CANBUS.party,
                                            control_allowed=control_allowed))

    can_sends.extend(self.stock_cc.update(CS, self.frame, self.tesla_can, CANBUS.party,
                                        cancel_override=overriding))
    if self.stock_cc.pcc_event:
      CS.pccEvent = self.stock_cc.pcc_event

    # Independent parked-only one-shot test; existing cruise transmissions win.
    can_sends.extend(self.parked_signal_test.update(CC, CS, can_sends))

    # Complete an in-progress lane-change tap before navigation uses the
    # synthetic signal slot. Physical stalk input wins in both controllers.
    tap_enabled = (self.tap_params is not None and self.tap_params.check_key(NAPParamKeys.TAP_LANE_CHANGE)
                   and self.tap_params.get_bool(NAPParamKeys.TAP_LANE_CHANGE))
    can_sends.extend(self.tap_lane_change.update(
      CS.tap_stalk, CS.out, enabled=tap_enabled,
      lateral_active=lat_active, overriding=overriding, existing=can_sends))

    can_sends.extend(self.navigation_signal.update(
      CS.tap_stalk, CS.out, lateral_active=lat_active,
      overriding=overriding, existing=can_sends))

    new_actuators = actuators.as_builder()
    new_actuators.steeringAngleDeg = self.apply_angle_last

    self.frame += 1
    return new_actuators, can_sends
