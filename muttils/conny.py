# $Id$

import subprocess, sys, time, util

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
        p = subprocess.Popen(applescript + [connstat], close_fds=True,
                stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        out = p.stdout.read()[:-1]
        try:
            return int(out)
        except ValueError:
            raise util.DeadMan(
                    'AppleScript cannot handle this configuration\nresult: %s'
                    % out)

    stat = cstat()
    if stat > 0:
        return

    p = subprocess.Popen(applescript + [connect], close_fds=True,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    conname = p.stdout.read()[:-1]
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
        prog = '/etc/ppp/ip-up'
        sys.stdout.write('\nconnected via %s\n' % conname)
        ret = subprocess.call([prog])
    else:
        prog = 'osascript'
        ret = subprocess.call(applescript + [disconnect])
        if ret:
            raise util.DeadMan(
                    '\nerror connecting %s: %s returned %i'
                    % (conname, prog, ret))
