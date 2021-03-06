import time
import pathlib
from dataclasses import dataclass

@dataclass
class Stati:
    topdir: pathlib.Path
    filename: pathlib.Path
    depends: 'Stati' = None
    feeds: 'Stati' = None

    @property
    def requires_to_run(self):
        '''
            We require to run, if our stati file does NOT exist.
            Or if our 'depends' was processed after than we.
        '''
        run = self.__requires_to_run
        if run:
            self.reset()

    @property
    def __requires_to_run(self):
        if not self.filename.exists():
            return True
        if self.depends is not None:
            return self._time_done_s < self.depends._time_done_s
        return False

    def commit(self):
        '''
            We processed successfully and commit by writing a 'stati_xx' file.
        '''
        # logger.info(f'    commit(): {self.filename.relative_to(self.topdir)}')
        self.filename.write_text(str(time.time()))

    @property
    def _time_done_s(self) -> float:
        '''
        returns the time.time() of the commit
        '''
        try:
            return float(self.filename.read_text())
        except FileNotFoundError:
            return -1.0

    def reset(self):
        '''
            Notify, that our stati has to be reset.
            Lets say, we and the ones we feed have to be executed again.
        '''
        if self.filename.exists():
            self.filename.unlink()
        if self.feeds is not None:
            self.feeds.reset()
