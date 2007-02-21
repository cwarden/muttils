# $Id$

import os, sys, time, util

connstat = '''tell application "Internet Connect"
    set visible of window 1 to false
    return seconds connected of status of current configuration
end tell'''

connect = '''tell application "Internet Connect"
    set visible of window 1 to false
    connect
    return name of current configuration
end tell'''

disconnect = '''tell application "Internet Connect"
    set visible of window 1 to false
    disconnect
end tell'''


def appleconnect():
    '''Connects Mac to internet using AppleScript.'''
    applescript = ['osascript', '-l', 'AppleScript', '-e']

    def cstat():
        '''Returns connection status.'''
        f0, f1 = os.popen2(applescript + [connstat])
        try:
            return int(f1.read()[:-1])
        except ValueError, inst:
            raise util.DeadMan('failed to connect: %s' % inst)

    stat = cstat()
    if stat > 0:
        return

    f0, f1 = os.popen2(applescript + [connect])
    conname = f1.read()[:-1]
    sys.stdout.write('connecting via %s ' % conname)
    try:
        while stat < 1:
            sys.stdout.write('.')
            sys.stdout.flush()
            time.sleep(1)
            stat = cstat()
    except KeyboardInterrupt:
        pass
    if stat > 0:
        sys.stdout.write('\nconnected via %s\n' % conname)
        os.spawnlp(os.P_WAIT, '/etc/ppp/ip-up')
    else:
        os.spawnvp(os.P_WAIT, 'osascript', applescript + [disconnect])
        sys.exit('\nconnection via %s failed' % conname)
