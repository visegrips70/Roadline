"""Exercise card's real startup methods with real CarParams and mocked I/O.

Only the selected methods are loaded, so these regressions run without msgq,
device services or CAN access. They do not establish hardware behavior.
"""
import ast
from pathlib import Path
from types import SimpleNamespace as N
from unittest.mock import Mock  # noqa: TID251 - only transport and persistence are mocked

import pytest

from opendbc.car import structs


class TestPassiveStartup:
  @pytest.fixture(autouse=True)
  def setUp(self):
    self.enabled = False
    self.saved = {}
    self.order = []
    self.params = Mock()
    self.params.get.return_value = None
    self.params.get_bool.side_effect = lambda key: self.enabled if key == 'OpenpilotEnabledToggle' else False
    self.params.put.side_effect = self.save
    self.params.put_bool.side_effect = self.save
    self.params.put_bool_nonblocking.side_effect = self.save
    self.events = []
    self.control = structs.CarControl.new_message()
    self.pm = Mock()
    self.pm.sock = {'sendcan': Mock()}

    # Compile the actual constructor and loop methods, preserving their bodies.
    source = Path(__file__).resolve().parents[3] / 'selfdrive/car/card.py'
    tree = ast.parse(source.read_text())
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'Car')
    methods = [n for n in cls.body if isinstance(n, ast.FunctionDef)
               and n.name in ('__init__', 'controls_update', 'step')]
    fixture_class = ast.ClassDef(name='Car', bases=[], keywords=[], body=methods, decorator_list=[])
    module = ast.Module(body=[ast.ImportFrom(module='__future__', names=[ast.alias(name='annotations')], level=0),
                             fixture_class], type_ignores=[])
    ast.fix_missing_locations(module)
    ns = dict(car=structs, structs=structs, REPLAY=False,
              EventName=N(selfdriveInitializing='initializing'),
              Params=lambda: self.params, os=N(path=N(exists=lambda _: False)),
              messaging=N(sub_sock=Mock(), SubMaster=lambda _: self.make_sm(), PubMaster=lambda _: self.pm),
              can_comm_callbacks=lambda *_: (Mock(), Mock()), VCruiseHelper=Mock(), Ratekeeper=Mock())
    exec(compile(module, str(source), 'exec'), ns)
    self.Car = ns['Car']

  def save(self, key, value):
    self.order.append(key)
    self.saved[key] = value

  def make_sm(self):
    outer = self

    class SubMaster(dict):
      seen = {'onroadEvents': True}

      def __getitem__(self, key):
        return outer.events if key == 'onroadEvents' else outer.control

      def all_alive(self, _):
        return False

    return SubMaster()

  def create(self, *, dashcam=False, controller=True):
    cp = structs.CarParams.new_message(brand='tesla', carFingerprint='TESLA_MODEL_S_PREAP',
                                      dashcamOnly=dashcam, safetyConfigs=[{'safetyModel': 'teslaPreap'}])
    self.ci = N(CP=cp, CC=object() if controller else None, init=Mock(), apply=Mock())
    self.ci.init.side_effect = lambda *_: self.order.append('CI.init')
    self.instance = self.Car(CI=self.ci, RI=Mock())
    self.instance.state_update = Mock(return_value=(structs.CarState.new_message(), None))
    self.instance.state_publish = Mock()
    return self.instance

  def assert_passive_ready(self):
    assert self.saved.get('ControlsReady') is True
    assert self.order.index('CarParams') < self.order.index('ControlsReady')
    with structs.CarParams.from_bytes(self.saved['CarParams']) as cp:
      assert cp.passive
      assert [str(c.safetyModel) for c in cp.safetyConfigs] == ['noOutput']
    self.ci.init.assert_not_called()
    self.ci.apply.assert_not_called()
    self.pm.send.assert_not_called()

  def test_disabled_startup_exits_diagnostics_without_actuator_initialization(self):
    instance = self.create()
    for _ in range(3):
      instance.step()
    self.assert_passive_ready()
    assert self.order.count('ControlsReady') == 1

  def test_passive_readiness_does_not_wait_for_models(self):
    self.events = [N(name='initializing')]
    self.create().step()
    self.assert_passive_ready()

  def test_dashcam_only_also_uses_no_output(self):
    self.enabled = True
    self.create(dashcam=True)
    self.assert_passive_ready()

  def test_missing_controller_also_uses_no_output(self):
    self.enabled = True
    self.create(controller=False)
    self.assert_passive_ready()

  def test_failed_carparams_write_cannot_signal_ready(self):
    self.params.put.side_effect = OSError('storage unavailable')
    with pytest.raises(OSError):
      self.create()
    assert 'ControlsReady' not in self.saved

  def test_active_startup_still_waits_for_interface_initialization(self):
    self.enabled = True
    instance = self.create()
    assert 'ControlsReady' not in self.saved
    self.events = [N(name='initializing')]
    instance.step()
    self.ci.init.assert_not_called()
    assert 'ControlsReady' not in self.saved
    self.events = []
    instance.step()
    assert self.saved.get('ControlsReady') is True
    assert self.order.index('CI.init') < self.order.index('ControlsReady')
    self.ci.init.assert_called_once()
    self.ci.apply.assert_not_called()

  def test_failed_active_interface_initialization_cannot_signal_ready(self):
    self.enabled = True
    instance = self.create()
    self.ci.init.side_effect = RuntimeError('ECU initialization failed')
    with pytest.raises(RuntimeError):
      instance.step()
    assert 'ControlsReady' not in self.saved
