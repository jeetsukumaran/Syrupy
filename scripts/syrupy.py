#! /usr/bin/env python

############################################################################
##  syrupy.py
##
##  Copyright 2008 Jeet Sukumaran.
##
##  This program is free software; you can redistribute it and/or modify
##  it under the terms of the GNU General Public License as published by
##  the Free Software Foundation; either version 3 of the License, or
##  (at your option) any later version.
##
##  This program is distributed in the hope that it will be useful,
##  but WITHOUT ANY WARRANTY; without even the implied warranty of
##  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##  GNU General Public License for more details.
##
##  You should have received a copy of the GNU General Public License along
##  with this program. If not, see <http://www.gnu.org/licenses/>.
##
############################################################################

"""
Profile the memory and CPU usage of a command.
"""

from optparse import OptionGroup
from optparse import OptionParser
import subprocess
import re
import time
import sys
import os
import datetime
import textwrap

PS_FIELDS = [
    'pid',
    'ppid',
    'etime',
    '%cpu',
    '%mem',
    'rss',
    'vsz',
]

RSS_COL = PS_FIELDS.index('rss')
VSZ_COL = PS_FIELDS.index('vsz')

PS_FIELD_HELP = [
    ["PID",
    """
    Process IDentifier -- a number used by the operating system
    kernel to uniquely identify a running program or process."""
    ],
    ["DATE",
    """
    The calender date, given as YEAR-MONTH-DAY, that the process was
    polled."""
    ],
    ["TIME",
    """
    The actual time, given as HOUR:MINUTE:SECONDS that the
    process was polled."""
    ],
    ["ELAPSED",
    """
    The total time that the process had been running up to the time it
    was polled."""
    ],
    ["CPU",
    """
    The CPU utilization of the process: CPU time used divided by the
    time the process has been running (cputime/realtime ratio),
    expressed as a percentage."""
    ],
    ["MEM",
    """
    The memory utilization of the process: ratio of the process's
    resident set size to the physical memory on the machine, expressed
    as a percentage."""
    ],
    ["RSS",
    """
    Resident Set Size -- the non-swapped physical memory (RAM) that a
    process is occupying (in kiloBytes). The rest of the process memory
    usage is in swap. If the computer has not used swap, this number
    will be equal to VSIZE."""
    ],
    ["VSIZE",
    """
    Virtual memory Size -- the total amount of memory the
    process is currently using (in kiloBytes). This includes the amount
    in RAM (the resident set size) as well as the amount in swap."""
    ],

]

def column_help(keyword_width=10, total_width=70):
    help = []
    for entry in PS_FIELD_HELP:
        desc = textwrap.dedent(re.sub("\s+", " ", entry[1]))
        desc = textwrap.fill(desc,
            width=total_width-keyword_width,
            initial_indent='',
            subsequent_indent=(' ' * keyword_width))
        help.append("%s%s" % \
            (entry[0].ljust(keyword_width),
            desc))
    return '\n'.join(help)

def pretty_timestamp(t=None, style=0):
    if t is None:
        t = time.localtime()
    if style == 0:
        return time.strftime("%Y-%m-%d", t)
    else:
        return time.strftime("%Y%m%d%H%M%S", t)

def poll_process(pid=None,
        command_pattern=None,
        ignore_self=True,
        raw_ps_log=None,
        debug_level=0):
    """
    Calls ps, and extracts rows where command matches given command
    filter. If no filter is given, all rows are extracted.
    """

    # count up all the fields so far
    # we are relying on all these fields NOT to contain
    # any space; we'll use this fact to parse out columns
    non_command_cols = len(PS_FIELDS)

    # add the command fields = command + args
    # this field will probably have spaces: we'll take this
    # into account
    ps_fields = PS_FIELDS + ["command"]

    ps_args = [ '-o %s=""' % s for s in ps_fields]
    ps_invocation = "ps -A %s" % (" ".join(ps_args))

    if debug_level >= 3:
        sys.stderr.write("\n" + ps_invocation + "\n")

    ps = subprocess.Popen(ps_invocation,
        shell=True,
        stdout=subprocess.PIPE)
    poll_time = datetime.datetime.now()
    stdout = ps.communicate()[0]

    if debug_level >= 9:
        sys.stderr.write(stdout + "\n")

    if raw_ps_log is not None:
        raw_ps_log.write(stdout + "\n")

    records = []
    for row in stdout.split("\n"):
        if not row:
            continue
        fields = re.split("\s+", row.strip(), non_command_cols)
        if debug_level >= 5:
            sys.stderr.write(str(fields) + "\n")
        if len(fields) != 8:
            #raise ValueError("Expecting 8 columns in output, but found %d: %s" % (len(fields), fields))
            sys.stderr.write("SYRUPY: Skipping sample: found only %d columns: %s" % (len(fields), fields))
            continue
        if (not ignore_self or int(fields[0]) != os.getpid())  \
                and (pid is None or int(fields[0]) == int(pid)) \
                and (command_pattern is None or re.search(command_pattern, fields[-1])):
            pinfo = {}
            for idx, field in enumerate(fields):
                pinfo[ps_fields[idx]] = field
            pinfo['poll_datetime'] = poll_time.isoformat(' ')
            pinfo['poll_date'] = poll_time.strftime("%Y-%m-%d")
            pinfo['poll_time'] = poll_time.strftime("%H:%M:%S")
            records.append(pinfo)
            if debug_level >= 4:
                sys.stderr.write(str(pinfo) + "\n")
    return records

def profile_process(pid=None,
        command_pattern=None,
        syrupy_output=None,
        raw_ps_log=None,
        poll_interval=1,
        quit_poll_func=None,
        quit_if_none=False,
        quit_at_time=None,
        show_command=False,
        output_separator="  ",
        align=False,
        headers=True,
        flush_output=False,
        debug_level=0):
    """
    Will poll process with PID `pid` or with COMMAND matching
    `command_pattern` every `poll_interval` seconds, writing system
    resource usage to `syrupy_output`. Will quit if `quit_poll_func` is not
    None and when called ("quit_poll_func()") returns True. I f process
    with PID does not exist, will quit waiting if `quit_if_none` is
    True, otherwise will continue until time given by `quit_at_time` if
    `quit_at_time` is not None. If `quit_at_time` is None and the PID
    does not exist and if `quit_if_none` is False, then will poll
    continuously until interupted by user.
    """

    if pid is None and command_pattern is None:
        raise Exception("Must provide either PID or command pattern")

    if align:
        ncolw = 5
        mcolw = 8
        wcolw = 11
        right_align_narrow = "%d" % ncolw
        right_align = "%d" % mcolw
        right_align_wide = "%d" % wcolw
        left_align_narrow = "-%d" % ncolw
        left_align = "-%d" % mcolw
        left_align_wide = "-%d" % wcolw
    else:
        ncolw = 0
        mcolw = 0
        wcolw = 0
        right_align_narrow = ""
        right_align = ""
        right_align_wide = ""
        left_align_narrow = ""
        left_align = ""
        left_align_wide = ""

    result_fields = [
        "%%(pid)%ss" % right_align,
        "%%(poll_date)%ss" % right_align_wide,
        "%%(poll_time)%ss" % right_align,
        "%%(etime)%ss" % right_align_wide,
        "%%(%%cpu)%ss" % right_align_narrow,
        "%%(%%mem)%ss" % right_align_narrow,
        "%%(rss)%ss" % right_align,
        "%%(vsz)%ss" % right_align,
    ]

    if debug_level >= 1:
        result_fields.insert(0, "%%(ppid)%ss" % right_align)

    if show_command:
        result_fields.append("%(command)s")

    col_headers = [
        "PID".rjust(mcolw),
        "DATE".rjust(wcolw),
        "TIME".rjust(mcolw),
        "ELAPSED".rjust(wcolw),
        "CPU".rjust(ncolw),
        "MEM".rjust(ncolw),
        "RSS".rjust(mcolw),
        "VSIZE".rjust(mcolw)
    ]

    if debug_level >=1:
        col_headers.insert(0, "PPID".rjust(mcolw))

    if show_command:
        col_headers.append("COMMAND")

    if headers:
        if syrupy_output is not None:
            syrupy_output.write(output_separator.join(col_headers) + "\n")
            if flush_output:
                syrupy_output.flush()

    quit = False
    while not quit:
        pinfoset = poll_process(pid=pid,
                                command_pattern=command_pattern,
                                raw_ps_log=raw_ps_log,
                                debug_level=debug_level)
        if debug_level > 4:
            sys.stderr.write(str(pinfoset) + "\n")
        if raw_ps_log is not None and flush_output:
            raw_ps_log.flush()
        for pinfo in pinfoset:
            result = output_separator.join(result_fields) % pinfo
            if syrupy_output is not None:
                syrupy_output.write(result + "\n")
                if flush_output:
                    syrupy_output.flush()
        if quit_poll_func is not None and quit_poll_func():
            quit = True
        elif len(pinfoset) == 0 and quit_if_none:
            quit = True
        else:
            time.sleep(poll_interval)

def profile_command(command,
        command_stdout,
        command_stderr,
        syrupy_output,
        raw_ps_log=None,
        poll_interval=1,
        output_separator=" ",
        show_command=False,
        align=False,
        headers=True,
        flush_output=False,
        debug_level=0):
    """
    Executes command `command`, redirecting its output stream to `command_stdout`
    and error stream to `command_stderr`. Polls the resulting process every
    `poll_interval` seconds, and writes the memory/cpu usage information to
    `syrupy_output`.
    """
    try:
        start_time = datetime.datetime.now()
        proc = subprocess.Popen(command,
                shell=False,
                stdout=command_stdout,
                stderr=command_stderr,
                env=os.environ)
        profile_process(pid=proc.pid,
                syrupy_output=syrupy_output,
                raw_ps_log=raw_ps_log,
                poll_interval=poll_interval,
                quit_poll_func=proc.poll,
                quit_if_none=True,
                quit_at_time=None,
                show_command=show_command,
                output_separator=output_separator,
                align=align,
                headers=headers,
                flush_output=flush_output,
                debug_level=debug_level)
        end_time = datetime.datetime.now()
        return start_time, end_time
    except Exception, e:
        sys.stderr.write("Failed to execute command: %s\n" % command)
        raise e
        sys.exit(1)

def open_file(fpath, mode='r', replace=False, exit_on_fail=True):
    """
    Does idiot-checked file opening.
    """
    if fpath is None:
        return None
    elif fpath == "^1":
        return sys.stdout
    elif fpath == "^2":
        return sys.stderr
    else:
        full_fpath = os.path.expanduser(os.path.expandvars(fpath))
        if mode.count('r'):
            if not os.path.exists(full_fpath):
                sys.stderr.write('File not found: %s\n' % full_fpath)
                if exit_on_fail:
                    sys.exit(1)
                else:
                    return None
            else:
                return open(full_fpath, mode)
        else:
            if os.path.exists(full_fpath):
                if mode.count('a') or replace or full_fpath == os.path.devnull:
                    return open(full_fpath, mode)
                else:
                    sys.stderr.write('File already exists: %s\n' % full_fpath)
                    sys.stderr.write('Overwrite (y/N)? ')
                    ok = raw_input()
                    if ok.lower().startswith('y'):
                        return open(full_fpath, mode)
                    else:
                        if exit_on_fail:
                            sys.exit(1)
                        else:
                            return None
            else:
                return open(full_fpath, mode)

_program_name = "Syrupy"
_program_usage = '%prog [SYRUPY-OPTIONS] [COMMAND [COMMAND-OPTIONS] [COMMAND-ARGS]]'
_program_version = '%s Version 1.4' % _program_name
_program_description = """\
System resource usage profiler: executes "COMMAND" with given
options/arguments and tracks resulting process, or tracks other running
processes based on criteria specified in SYRUPY-OPTIONS. In either case,
the CPU and memory usage of the tracked processes are sampled and logged
at pre-specified intervals. Note that, if COMMAND is given, then all
dash-prefixed options following the first non-dash prefixed argument are
assumed to be part of COMMAND and will be ignored by Syrupy. That is,
only options before COMMAND will be parsed by Syrupy; everything else
will be passed to COMMAND.
"""
_program_author = 'Jeet Sukumaran'
_program_copyright = 'Copyright (C) 2009 Jeet Sukumaran.'

def main():
    """
    Main CLI handler.
    """

    default_title = "syrupy_" + pretty_timestamp(style=1)

    parser = OptionParser(usage=_program_usage,
            add_help_option=True,
            version=_program_version,
            description=_program_description)

    parser.add_option('-q', '--quiet',
            action='store_true',
            dest='quiet',
            default=False,
            help='do not report miscellaneous run information to stderr')

    parser.add_option('-r', '--replace',
            action='store_true',
            dest='replace',
            default=False,
            help='replace output file(s) without asking if already exists')

    parser.add_option('-t', '--title',
            action='store',
            dest='title',
            metavar="PROCESS-TITLE",
            default=default_title,
            help="name for this run (will be used as prefix for all output files); defaults to 'syrupy_<TIMESTAMP>'")

    parser.add_option('-v', '--debug-level',
            action='store',
            type='int',
            dest='debug',
            metavar="#",
            default=0,
            help='debugging information level (0, 1, 2, 3; default=%default)')

    parser.add_option('--explain',
            action='store_true',
            dest='explain',
            default=False,
            help='show detailed information on the meaning of each of the columns, ' \
                +'and then exit')

    process_opts = OptionGroup(parser, 'Process Selection', """\
By default, Syrupy tracks the process resulting from executing
COMMAND. You can also instruct Syrupy to track external
processes by using the following options, each of which specify
a criteria that a particular process must meet so as to be
monitored. Syrupy will report the resource usage of any and all
processes that meet the specified criteria, and will exit when
no processes matching all the criteria are found. If no
processes matching all the criteria are actually already running
when Syrupy starts, then Syrupy exits immediately. Note that an
instance of Syrupy automatically excludes its own process from
being tracked by itself.
        """
        )
    parser.add_option_group(process_opts)

    process_opts.add_option('-p', '--poll-pid', '--pid',
            action='store',
            dest='poll_pid',
            default=None,
            metavar='PID',
            type=int,
            help='ignore COMMAND if given, and poll external process with ' \
                +'specified PID')

    process_opts.add_option('-c', '--poll-command',
            action='store',
            dest='poll_command',
            default=None,
            metavar='REG-EXP',
            help='ignore COMMAND if given, and poll external process with ' \
                +'command matching specified regular expression pattern')

    polling_opts = OptionGroup(parser, 'Polling Regime')
    parser.add_option_group(polling_opts)

    polling_opts.add_option('-i', '--interval',
            action='store',
            dest='poll_interval',
            default=1,
            metavar='#.##',
            type=float,
            help='polling interval in seconds (default=%default)')

    run_output_opts = OptionGroup(parser, 'Output Modes', """\
By default, Syrupy redirects the standard output and standard error of COMMAND, as well
as its own output, to log files. The following options allow you to change this behavior, either
having Syrupy write to standard output and standard error ('-S'), COMMAND write to
standard output and standard error ('-C'), or suppress all COMMAND output altogether ('-N').
        """
        )
    parser.add_option_group(run_output_opts)

    run_output_opts.add_option('-S', '--syrupy-in-front',
            action='store_true',
            dest='syrupy_in_front',
            default=False,
            help='redirect Syrupy output and miscellaneous information to ' \
                +'standard output and standard error instead of logging to files')

    run_output_opts.add_option('-C', '--command-in-front',
            action='store_true',
            dest='command_in_front',
            default=False,
            help='run COMMAND in foreground: send output and error stream of' \
                +' COMMAND to standard output and standard error, respectively')

    run_output_opts.add_option('-N', '--no-command-output',
            action='store_true',
            dest='suppress_command_output',
            default=False,
            help='suppress all output from COMMAND')

    run_output_opts.add_option('--flush-output',
            action='store_true',
            dest='flush_output',
            default=False,
            help='force flushing of stream buffers after every write')

    run_output_opts.add_option('--no-raw-process-log',
            action='store_true',
            dest='suppress_raw_process_log',
            default=False,
            help='suppress writing of raw results from process sampling')

    formatting_opts = OptionGroup(parser, 'Output Formatting')
    parser.add_option_group(formatting_opts)

    formatting_opts.add_option('--show-command',
            action='store_true',
            dest='show_command',
            default=False,
            help='show command column in output' )

    formatting_opts.add_option('--separator',
            action='store',
            dest='separator',
            default="  ",
            metavar="SEPARATOR",
            help='character(s) to used to separate columns in results' )

    formatting_opts.add_option('--no-align',
            action='store_false',
            dest='align',
            default=True,
            help='do not align/justify columns' )

    formatting_opts.add_option('--no-headers',
            action='store_false',
            dest='headers',
            default=True,
            help='do not output column headers' )

    # we need to do this to prevent options meant for COMMAND
    # being consumed by Syrupy
    parser.disable_interspersed_args()
    (opts, args) = parser.parse_args()

    if opts.explain:
        sys.stdout.write(column_help())
        sys.stdout.write("\n")
        sys.exit(0)

    if len(args) == 0 \
        and opts.poll_pid is None \
        and opts.poll_command is None:
        parser.print_usage()
        sys.exit(1)

    if opts.title is None and len(args) > 0:
        base_title = os.path.splitext(os.path.basename(args[0]))[0]
    else:
        base_title = opts.title

    if opts.syrupy_in_front:
        syrupy_output = sys.stdout
    else:
        fname = base_title + ".ps.log"
        if not opts.quiet:
            sys.stderr.write("SYRUPY: Writing process resource usage samples to '%s'\n" % fname)
        syrupy_output = open_file(fname, "w", replace=opts.replace)

    if opts.suppress_raw_process_log:
        raw_ps_log = None
    else:
        fname = base_title + ".ps.raw"
        if not opts.quiet:
            sys.stderr.write("SYRUPY: Writing raw process resource usage logs to '%s'\n" % fname)
        raw_ps_log = open_file(base_title + ".ps.raw", "w", replace=opts.replace)

    if opts.poll_pid is not None or opts.poll_command is not None:
        if not opts.quiet:
            if opts.poll_pid is not None:
                sys.stderr.write("SYRUPY: sampling process %d\n" % opts.poll_pid)
            else:
                sys.stderr.write("SYRUPY: sampling process with command pattern '%s'\n" % opts.poll_command)
        profile_process(pid=opts.poll_pid,
                command_pattern=opts.poll_command,
                syrupy_output=syrupy_output,
                raw_ps_log=raw_ps_log,
                poll_interval=opts.poll_interval,
                quit_poll_func=None,
                quit_if_none=True,
                quit_at_time=None,
                show_command=opts.show_command,
                output_separator=opts.separator,
                align=opts.align,
                headers=opts.headers,
                flush_output=opts.flush_output,
                debug_level=opts.debug)
    else:
        command = args
        if not opts.quiet:
            sys.stderr.write("SYRUPY: Executing command '%s'\n" % (" ".join(command)))
        if opts.suppress_command_output:
            command_stdout = open(os.devnull, "w")
            command_stderr = open(os.devnull, "w")
            if not opts.quiet:
                sys.stderr.write("SYRUPY: Suppressing output of command\n")
        elif opts.command_in_front:
            command_stdout = sys.stdout
            command_stderr = sys.stderr
        else:
            cout = base_title + ".out.log"
            cerr = base_title + ".err.log"
            if not opts.quiet:
                sys.stderr.write("SYRUPY: Redirecting command output stream to '%s'\n" % cout)
            command_stdout = open_file(cout, 'w', replace=opts.replace)
            if not opts.quiet:
                sys.stderr.write("SYRUPY: Redirecting command error stream to '%s'\n" % cerr)
            command_stderr = open_file(cerr, 'w', replace=opts.replace)
        start_time, end_time = profile_command(command=command,
                command_stdout=command_stdout,
                command_stderr=command_stderr,
                syrupy_output=syrupy_output,
                raw_ps_log=raw_ps_log,
                poll_interval=opts.poll_interval,
                show_command=opts.show_command,
                output_separator=opts.separator,
                align=opts.align,
                headers=opts.headers,
                flush_output=opts.flush_output,
                debug_level=opts.debug)

        if not opts.quiet:
                final_run_report = []
                final_run_report.append("SYRUPY: Completed running: %s" % (" ".join(command)))
                final_run_report.append("SYRUPY: Started at %s" % (start_time.isoformat(' ')))
                final_run_report.append("SYRUPY: Ended at %s" % (end_time.isoformat(' ')))
                hours, mins, secs = str(end_time-start_time).split(":")
                run_time = "SYRUPY: Total run time: %s hour(s), %s minute(s), %s second(s)" % (hours, mins, secs)
                final_run_report.append(run_time)
                report = "\n".join(final_run_report) + "\n"
                sys.stderr.write(report)

if __name__ == '__main__':
    main()





