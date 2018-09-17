from decorator import Decorator

@Decorator('ping_event')
def ping():
    print '>>>>>>>>>>>>>>>>>>> PING?'

@Decorator('ping_event')
def ping_pong():
    print '>>>>>>>>>>>>>>>>>>> PONG!'


@Decorator('openflow_event')
def of_seila():
    print '>>>>>> OPEN FLOW'
