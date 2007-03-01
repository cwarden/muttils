# $Id$

import sys, time, util

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


def appleconnect(ui):
    '''Connects Mac to internet using AppleScript.'''
    applescript = ['osascript', '-l', 'AppleScript', '-e']

    def cstat():
        '''Returns connection status.'''
        st = util.pipeline(applescript + [connstat])[:-1]
        try:
            return int(st)
        except ValueError:
            raise util.DeadMan(
                    'AppleScript cannot handle this configuration\nresult: %s'
                    % st)

    stat = cstat()
    if stat > 0:
        return

    conname = util.pipeline(applescript + [connect])[:-1]
    ui.write('connecting via %s ' % conname)
    try:
        while stat < 1:
            ui.write('.')
            ui.flush()
            time.sleep(1)
            stat = cstat()
    except KeyboardInterrupt:
        pass
    if stat > 0:
        cs = ['/etc/ppp/ip-up']
        ui.write('\nconnected via %s\n' % conname)
    else:
        cs = applescript + [disconnect]
    util.systemcall(cs)

def goonline(ui):
    '''Connects to internet if not yet connected.
    Note: only MacOS supported atm.'''
    if ui.configitem('net', 'connect').lower() != 'true':
        return
    plat = sys.platform
    if plat == 'darwin':
        appleconnect(ui)
    else:
        ui.warn('automatic connection not supported for %s\n' % plat)
