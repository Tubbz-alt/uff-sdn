
ping_functions = []
of_functions = []

class Decorator:

    def __init__(self, start_when):
        self._when = start_when
        print 'entrei init'
        self._start = True

    def __call__(self, function):
        if self._when == 'ping_event':
            ping_functions.append(function)

        elif self._when == 'openflow_event':
            of_functions.append(function)
