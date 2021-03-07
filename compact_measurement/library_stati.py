import time
import logging
import pathlib
from dataclasses import dataclass

logger = logging.getLogger('logger')

TAG_COMMIT = 'stati: COMMMIT'
TAG_RUN    = 'stati:    RUN'
TAG_SKIP   = 'stati:   SKIP'

@dataclass
class Stati:
    context: 'MeasurementContext'
    filename: pathlib.Path
    _depends: 'Stati' = None
    _feeds: 'Stati' = None

    def dependson(self, stati: 'Stati'):
        assert self._depends is None
        self._depends = stati

    def feeds(self, stati: 'Stati'):
        assert self._feeds is None
        self._feeds = stati

    def __enter__(self):
        return self

    def __exit__(self, _type, _value, _tb):
        if _type:
            # There was an exception
            self.reset()
            return
        # self.commit()

    @property
    def requires_to_run(self):
        '''
            We require to run, if our stati file does NOT exist.
            Or if our 'depends' was processed after than we.
        '''
        def log(f, tag):
            f(f'{tag} {self.filename.relative_to(self.context.dir_measurements)}')
        _requires_to_run = self.__requires_to_run
        if _requires_to_run:
            log(logger.info, TAG_RUN)
        else:
            log(logger.debug, TAG_SKIP)
        if _requires_to_run:
            self.reset()
        return _requires_to_run

    @property
    def __requires_to_run(self):
        if not self.filename.exists():
            return True
        if self._depends is not None:
            return self._time_done_s < self._depends._time_done_s
        return False

    def commit(self):
        '''
            We processed successfully and commit by writing a 'stati_xx' file.
        '''
        # logger.info(f'    commit(): {self.filename.relative_to(self.topdir)}')
        logger.debug(f'{TAG_COMMIT} {self.filename.relative_to(self.context.dir_measurements)}')
        self.filename.parent.mkdir(parents=True, exist_ok=True)
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
        if self._feeds is not None:
            self._feeds.reset()
