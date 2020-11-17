'''
'LockingMixin' make sure that a configuration class is not manipulated anymore.

Use of 'LockingMixin'
---------------------

In the constructor of the class which inherits LockingMixing:
    Define all members.
    Assign default values to members or 'LockingMixin.TO_BE_SET' if they have to be set by the user.
    Call 'self._lock()'

This is how to use it:

#
# Construction: The class 'Configuration' prepares the members.
#
>>> config = Configuration()

#
# Configuring
#
>>> config.name = 'hello'
>>> config.size_x2 = 5
Traceback (most recent call last):
...
AttributeError: Property "size_x2" does not exit!

#
# validate the configuration and freeze the object
#
>>> config.validate()
Traceback (most recent call last):
...
Exception: These properties have not been set: ['size_y']!
>>> config.size_y = 6
>>> config.validate()

#
# The object is frozen. Values may not be written anymore
#
>>> config.size_y = 7
Traceback (most recent call last):
...
AttributeError: This object is frozen: "size_y" is not writeable!

>>> config.size_x
42
>>> config.size_y
6
'''

class LockingMixin: # pylint: disable=too-few-public-methods
    TO_BE_SET = 'TO_BE_SET'
    __IS_LOCKED = '_locked_members'
    __IS_FROZEN = '_frozen'

    def _lock(self):
        self.__dict__[LockingMixin.__IS_LOCKED] = True

    def _freeze(self):
        unset_properties = [name for name, value in self.__dict__.items() if value is LockingMixin.TO_BE_SET]
        if unset_properties:
            raise Exception(f'These properties have not been set: {unset_properties}!')
        self.__dict__[LockingMixin.__IS_FROZEN] = True

    @property
    def is_locked(self):
        return LockingMixin.__IS_LOCKED in self.__dict__

    @property
    def is_frozen(self):
        return LockingMixin.__IS_FROZEN in self.__dict__

    def __setattr__(self, name, value):
        if self.is_frozen:
            raise AttributeError(f'This object is frozen: "{name}" is not writeable!')

        if self.is_locked:
            if name not in self.__dict__:
                raise AttributeError(f'Property "{name}" does not exit!')

        self.__dict__[name] = value


class Configuration(LockingMixin): # pylint: disable=too-few-public-methods
    def __init__(self):
        self.size_x:int = 42
        self.size_y:int = LockingMixin.TO_BE_SET
        self.name:str = LockingMixin.TO_BE_SET
        self._lock()

    def validate(self):
        self._freeze()

if __name__ == '__main__':
    import doctest
    doctest.testmod()
