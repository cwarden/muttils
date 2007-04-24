# $Id$

'''Word wraps text to given width.
Handles (email) quote chars.
Quotation lines (eg. email: |) can be excluded from wrapping.
Can be told to respect linebreaks and just wrap long lines.
Capability to hyphenate dash-compounded words.
'''

import wrap
import util
import version
import optparse
import sys

proginfo = 'Wrap - word wrap text to stdout'

def run():
    '''Command interface to the Wrap class.'''
    parser = optparse.OptionParser(usage='%prog [options] [files]',
            description=__doc__, version=version.version_(proginfo))
    parser.set_defaults(width=0, ipar=0, respect=0, hyph=False,
            tabwidth=8, excl='', quote='', qmail=False, email=False,
            _outfunc=False)

    parser.add_option('-w', '--width', type='int',
            help='wrap lines to width WIDTH')
    parser.add_option('-i', '--ipar', type='int',
            help='wrap to width IPAR '
                'with each indent change starting a paragraph')
    parser.add_option('-r', '--respect', type='int',
            help='wrap respecting linebreaks to width RESPECT')
    parser.add_option('-H', '--hyph', action='store_true',
            help='break hyphen-compounded words when wrapping')
    parser.add_option('-t', '--tabwidth', type='int',
            help='expand tabs to TABWIDTH spaces')
    parser.add_option('-e', '--excl',
            help='exclude lines matching regex EXCL, '
                'anchored at start of line, after quote removal')
    parser.add_option('-E', dest='excl',
            action='store_const', const='[\s>|%:\-]',
            help='exclude lines starting with space, ">", "|", "%", ":", "-"')
    parser.add_option('-q', '--quote',
            help='treat character(s) of string QUOTE as quote char(s)')
    parser.add_option('-m', '--email', action='store_true',
            help='treat input as email message: skip headers, unmangle >From')
    parser.add_option('-M', dest='qmail', action='store_true',
            help='treat input as email message and ">" '
                'as (additional) quote char')
    parser.add_option('-s', '--stream', dest='_outfunc', action='store_true',
            help='stream output immediately')

    options, args = parser.parse_args()

    try:
        w = wrap.wrap(inp=args, opts=options.__dict__)
        parser.destroy()
        w.formwrap()
        sys.stdout.writelines(w.olines)
    except (util.DeadMan, IOError, KeyboardInterrupt), inst:
        sys.exit(inst)
