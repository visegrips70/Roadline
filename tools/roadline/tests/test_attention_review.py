from types import SimpleNamespace as N
from openpilot.tools.roadline.review_log import AttentionReview


def state(mask=0, events=(), **changes):
  fields = dict(faceDetected=True, isLowStd=True, isActiveMode=True, isDistracted=bool(mask), distractedType=mask, events=[N(name=name) for name in events])
  fields.update(changes)
  return N(**fields)


class TestAttentionReview:
  def test_empty_is_unavailable(self):
    assert AttentionReview().report()['sample_percentages']['phone'] is None

  def test_classifier_causes_and_episode_counts(self):
    review = AttentionReview()
    review.add(state())
    review.add(state(4, ['promptDriverDistracted']))
    review.add(state(4, ['promptDriverDistracted']))
    review.add(state(3, ['driverDistracted'], faceDetected=False, isLowStd=False))
    report = review.report()
    assert report['sample_percentages']['phone'] == 50
    assert report['sample_percentages']['eyes'] == 25
    assert report['observed_alert_starts'] == {'driverDistracted': 1, 'promptDriverDistracted': 1}
    assert 'location' not in report

  def test_invalid_packets_are_excluded(self):
    review = AttentionReview()
    review.add(state(7), valid=False)
    review.add(state())
    assert review.report()['valid_samples'] == 1
    assert review.report()['invalid_packets'] == 1
    assert review.report()['sample_percentages']['distracted'] == 0
