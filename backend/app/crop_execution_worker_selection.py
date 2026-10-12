"""Select one explicitly configured crop consumer without starting it."""
from .deterministic_work import (
    DeterministicWorkerLoop, JointExecutionWorker, VentilationExecutionWorker, LoopHold,
)


def select_crop_execution_loop(model=None, *, joint_factory=None, ventilation_factory=None):
    try:
        if any(factory is not None and not callable(factory)
               for factory in (joint_factory, ventilation_factory)):
            raise ValueError
        if model is None:
            return None
        if type(model) is not str:
            raise ValueError
        choices = {
            'crop-climate-joint': (joint_factory, JointExecutionWorker,
                                   'joint-crop-climate-execution-input-v1'),
            'crop-greenhouse-ventilation': (ventilation_factory, VentilationExecutionWorker,
                                           'joint-ventilation-execution-input-v1'),
        }
        factory, worker_type, version = choices[model]
        if factory is None:
            raise ValueError
        loop = factory()
        if (type(loop) is not DeterministicWorkerLoop or type(loop.worker) is not worker_type
                or loop.discovery.input_versions != frozenset({version})):
            raise ValueError
        loop._binding()
        return loop
    except (Exception, SystemExit):
        raise LoopHold('crop_worker_selection_rejected') from None
