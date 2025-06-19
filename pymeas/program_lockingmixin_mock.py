from __future__ import annotations

import dataclasses

TO_BE_SET: str = "TO_BE_SET"

@dataclasses.dataclass(slots=True)
class LockingMixinMock:
    def _lock(self):
        pass

    def _freeze(self):
        pass

    def unlock(self):
        pass


    def dump(self, logger, indent="") -> None:
        logger.error("to be implemented!")
        return
        for name, value in sorted(self.__dict__.items()):
            if name.startswith("_"):
                continue
            if isinstance(value, (list, tuple)):
                logger.info(f"{indent}{name} = {[v.info for v in value]}")
                continue
            if isinstance(value, (float, int, bool, str, type(None))):
                logger.info(f"{indent}{name} = {value}")
                continue
            if isinstance(value, (LockingMixinMock,)):
                value.dump(logger, indent=f"{indent}{name}.")
                continue
            logger.info(f"{indent}{name} = type({value.__class__.__name__}):{value}")
