# -*- coding: utf8 -*-


def generate_tests(**targets):
    u"""
    Generates independent parametrized tests.
    Supply a dictionary from method names to an array of tuple of parameters.
    It will generate one test per tuple.

    :param targets:
    :return:
    """
    def decorator(cls):
        for method, args_list in targets.items():
            for i, args in enumerate(args_list):
                def fn(self, method_=method, args_=args):
                    getattr(self, method_)(*args_)
                fn.__doc__ = u'Run method "{}" with arguments: {}'.format(method, repr(args))
                # Name starts with test_ to be detected:
                fn.__name__ = bytes(u'test__{}__{}'.format(method, i))
                setattr(cls, fn.__name__, fn)
        return cls
    return decorator
