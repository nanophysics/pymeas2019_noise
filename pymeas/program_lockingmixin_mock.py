class LockingMixinMock:
    TO_BE_SET = "TO_BE_SET"

    def _lock(self):
        pass

    def _freeze(self):
        pass

    def unlock(self):
        pass
