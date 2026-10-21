"""Exercise the real NAP interface/settings path without CAN I/O."""
import importlib

import pytest

from openpilot.common.params import Params
from opendbc.car import structs
from opendbc.car.tesla.interface import CarInterface
from opendbc.car.tesla.values import CAR


@pytest.mark.parametrize('pedal', [False, True])
@pytest.mark.parametrize('radar', [False, True])
@pytest.mark.parametrize('behind_nosecone', [False, True])
def test_nap_settings_select_preap_safety_without_rewriting_calibration(mocker, pedal, radar, behind_nosecone):
  params = Params()
  conf = importlib.import_module('opendbc.car.tesla.preap.nap_conf')
  mocker.patch.object(conf, '_params', params)
  mocker.patch.object(conf, '_PARAMS_AVAILABLE', True)
  booleans = {'NAPPedalEnabled': pedal, 'NAPRadarEnabled': radar, 'NAPRadarBehindNosecone': behind_nosecone}
  calibration = {'NAPPedalCalibMin': -2.0, 'NAPPedalCalibMax': 97.0,
                 'NAPPedalCalibZero': 1.0, 'NAPPedalCalibFactor': 1.1, 'NAPPedalCanBus': 2}
  for key, value in booleans.items():
    params.put_bool(key, value)
  for key, value in calibration.items():
    params.put(key, value)
  cp = CarInterface.get_params(CAR.TESLA_MODEL_S_PREAP, {i: {} for i in range(4)}, [],
                               alpha_long=False, is_release=False, docs=False)
  assert cp.carFingerprint == CAR.TESLA_MODEL_S_PREAP
  assert cp.safetyConfigs[0].safetyModel == structs.CarParams.SafetyModel.teslaPreap
  assert cp.safetyConfigs[0].safetyParam == int(pedal) + 2 * int(radar) + 4 * int(behind_nosecone)
  assert cp.steerControlType == structs.CarParams.SteerControlType.angle
  assert cp.openpilotLongitudinalControl == pedal
  assert cp.pcmCruise == (not pedal)
  assert cp.radarUnavailable == (not radar)
  for key, value in calibration.items():
    assert params.get(key) == value
