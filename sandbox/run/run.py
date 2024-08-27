# Add project folder to path
import sys
from os.path import dirname
sys.path.append(dirname(dirname(dirname(__file__))))

from pysbs.core.step import BuildStep
from pysbs.core.build import build
import time

class TestStep(BuildStep):

    def __init__(self, name : str, vs : str = 'not done') -> None:
        super().__init__()
        self.name = name
        self.vs = vs

    @property
    def step_id(self):
        return self.name

    @property
    def input_version(self) -> str:
        return self.vs # '' is HACK-ed version returned by last_time_input_version

    def run(self):
        for i in range(5):
            self.print(f'Doing step `{self.name}`...')
            time.sleep(0.5)
        self.print('Done!')

        if self.name == 'Fail':
            raise RuntimeError('Failing!')


a = TestStep('StepA')
b = TestStep('StepB')
done = TestStep('Step which is done', '')

c = TestStep('StepC')


c.dependencies.append(a)
c.dependencies.append(b)

failer = TestStep('Fail')
failer.dependencies.append(c)

build(failer)
