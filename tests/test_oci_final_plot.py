"""Regression test for plotting of the final BSM2 OCI metric."""

import numpy as np

from bsm2_python.bsm2_base import BSM2Base
from bsm2_python.evaluation import Evaluation


class StubBSM2(BSM2Base):
    """Exercise BSM2 evaluation without running the process model."""

    def __init__(self, filepath):
        self.simtime = np.array([0.0, 1.0, 2.0])
        self.evaltime = np.array([0.0, 2.0])
        self.iqi_all = np.array([1.0, 2.0, 3.0])
        self.eqi_all = np.array([4.0, 5.0, 6.0])
        self.oci_all = np.array([7.0, 8.0, 9.0])
        self.evaluator = Evaluation(str(filepath))

    def step(self, i):
        pass

    def get_final_performance(self):
        return (42.0,)


def test_final_oci_is_exported_but_not_plotted(tmp_path, monkeypatch):
    """Final OCI is a scalar, unlike the three plotted time series."""
    show_calls = []
    monkeypatch.setattr('bsm2_python.evaluation.plt.show', lambda: show_calls.append(None))

    output_file = tmp_path / 'evaluation.csv'
    model = StubBSM2(output_file)
    model.simulate(plot=True)

    final = model.evaluator.get_data('oci_final')
    assert model.oci_final == 42.0
    assert final.num_timestamps == 1
    assert final.get_values() == [[42.0]]
    assert final.plot is False
    assert final.export is True
    assert len(show_calls) == 3  # IQI, EQI, and time-resolved OCI only
    assert 'oci_final' in output_file.read_text(encoding='utf-8')
