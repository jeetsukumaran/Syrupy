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
    'command'
]

PS_FIELD_HELP = [
    ["PID",
    """
    Process IDentifier -- a number used by some operating system
    kernels (such as that of UNIX, Mac OS X or Windows NT) to
    uniquely identify a process."""
    ],
    ["DATE",
    """
    The calender date, given as YEAR-MONTH-DAY, that the process was
    polled."""
    ],
    ["TIME",
    """
    The actual time, given as HOUR:MINUTE:SECOND.MICROSECONDS that the
    process was polled."""
    ],
    ["ELAPSED",
    """
    The total time of the process had been running when it was polled.
    """
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
       
def poll_process(pid=None,
     debug=0):
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
    ps_invocation = "ps %s" % (" ".join(ps_args))
    
    if debug > 2:
        sys.stderr.write("\n" + ps_invocation + "\n")
    
    ps = subprocess.Popen(ps_invocation,
        shell=True,
        stdout=subprocess.PIPE)
    poll_time = datetime.datetime.now()        
    stdout = ps.communicate()[0] 
    
    records = []
    for row in stdout.split("\n"):
        if row:
            fields = re.split("\s+", row.strip(), non_command_cols)
            if (pid is None or int(fields[0]) == pid):
                pinfo = {}
                for idx, field in enumerate(fields):
                    pinfo[ps_fields[idx]] = field
                pinfo['poll_datetime'] = poll_time.isoformat(' ')
                pinfo['poll_date'] = poll_time.strftime("%Y-%m-%d")
                pinfo['poll_time'] = poll_time.strftime("%H:%M:%S.") + str(poll_time.microsecond)
                records.append(pinfo)
    return records
    
    
def profile_command(command,
    command_stdout,
    command_stderr,
    output,
    poll_interval=1,
    output_separator=" ",
    align=False,    
    headers=True,
    debug=0):
    """
    Executes command `command`, redirecting its output stream to `command_stdout`
    and error stream to `command_stderr`. Polls the resulting process every
    `poll_interval` seconds, and writes the memory/cpu usage information to
    `output`. 
    """
    
    NORM_COL_WIDTH = 10
    WIDE_COL_WIDTH = 15
    
    if align:
        ncolw = 8
        wcolw = 15
        right_align = "%d" % ncolw
        right_align_wide = "%d" % wcolw
        left_align = "-%d" % ncolw
        left_align_wide = "-%d" % wcolw
    else:   
        ncolw = 0
        wcolw = 0    
        right_align = ""
        right_align_wide = ""
        left_align = ""
        left_align_wide = ""
    
    result_fields = [
        "%%(poll_date)%ss" % left_align_wide,
        "%%(poll_time)%ss" % left_align_wide,        
        "%%(etime)%ss" % right_align,
        "%%(%%cpu)%ss" % right_align,
        "%%(%%mem)%ss" % right_align,
        "%%(rss)%ss" % right_align,
        "%%(vsz)%ss" % right_align,
    ]    
    
    if debug > 0:
        result_fields.insert(0, "%%(pid)%ss" % right_align)
        
    if debug > 1:
        result_fields.insert(0, "%%(ppid)%ss" % right_align)     
    
    col_headers = [
        "DATE".ljust(wcolw),
        "TIME".ljust(wcolw),
        "ELAPSED".rjust(ncolw),
        "CPU".rjust(ncolw),
        "MEM".rjust(ncolw),
        "RSS".rjust(ncolw),
        "VSIZE".rjust(ncolw)
    ]
    
    if debug > 0:
        col_headers.insert(0, "PID".rjust(ncolw))
        
    if debug > 1:
        col_headers.insert(0, "PPID".rjust(ncolw))        
        
    header_field_template = "%%%ss" % left_align
    col_headers = [header_field_template % col_head for col_head in col_headers]

    if headers:
        output.write(output_separator.join(col_headers) + "\n")
   
    try:
        start_time = datetime.datetime.now()            
        proc = subprocess.Popen(command,
            shell=False,
            stdout=command_stdout,
            stderr=command_stderr,
            env=os.environ)           
        while proc.poll() is None:
            pinfoset = poll_process(pid=proc.pid, debug=debug)
            for pinfo in pinfoset:
                result = output_separator.join(result_fields) % pinfo
                output.write(result + "\n")
            time.sleep(poll_interval)    
        end_time = datetime.datetime.now() 
    except OSError, oserror:
        if oserror.errno == 2:
            sys.stderr.write("Failed to execute command: %s\n" % command)
            sys.exit(1)
    
    return start_time, end_time
    
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
_program_usage = '%prog [options] COMMAND'
_program_version = '%s Version 1.0.0' % _program_name
_program_description = """\
System resource usage profiler: executes "COMMAND", logging the CPU and
memory usage of the resulting process at pre-specified intervals. All
dash-prefixed options following the first non-dash prefixed argument is assumed
to be part of COMMAND and will be ignored by Syrupy. That is, only options
before COMMAND will be parsed by Syrupy; everything else will be passed to 
COMMAND.
"""
_program_author = 'Jeet Sukumaran'
_program_copyright = 'Copyright (C) 2008 Jeet Sukumaran.'

def main():
    """
    Main CLI handler.
    """

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
                
    polling_opts = OptionGroup(parser, 'Polling Regime')
    parser.add_option_group(polling_opts)
    
    polling_opts.add_option('-i', '--interval',
        action='store',
        dest='poll_interval',
        default=1,
        metavar='#.##',
        type=float,
        help='polling interval in seconds(default=%default)')   
               
    soutput_opts = OptionGroup(parser, 'Syrupy Output Destination')
    parser.add_option_group(soutput_opts)    
    
    soutput_opts.add_option('-o', '--output',
        action='store',
        dest='outputfile',
        default=None,
        metavar="FILEPATH",
        help='write resource usage data to FILEPATH instead of ' \
            + 'standard output')     
        
    soutput_opts.add_option('-l', '--log',
        action='store',
        dest='logfile',
        default=None,
        metavar="FILEPATH",
        help='save miscellaneous run information to this file')       
        
    coutput_opts = OptionGroup(parser, 
        'Command Output Destination',
        """\
By default the output and error streams of COMMAND is redirected to the
system null device, because that is the way I want it most often; you
can use these option to redirect either or both these
streams to somewhere more useful. Note that if you choose to direct any of
COMMAND's streams to the standard output (by specifying "^1" for the options
below, you really hould then ask Syrupy to write its own output elsewhere
using the "--output" and "--log" options, otherwise things can 
get a little confusing.
"""
    )
    parser.add_option_group(coutput_opts)           
        
    coutput_opts.add_option('--stdout',
        action='store',
        dest='stdout',
        default=os.path.devnull,
        metavar="FILEPATH",
        help="""\
path to file to direct standard output of COMMAND
(default="%default"; use "^1" to specify current standard output
or "^2" to specify current standard error)"""
        )
            
    coutput_opts.add_option('--stderr',
        action='store',
        dest='stderr',
        default=os.path.devnull,
        metavar="FILEPATH",
        help="""\
path to file to direct standard output of COMMAND
(default="%default"; use "^1" to specify current standard output
or "^2" to specify current standard error)"""
        )
                    
    formatting_opts = OptionGroup(parser, 'Output Formatting')
    parser.add_option_group(formatting_opts)   
    
    formatting_opts.add_option('--separator',
        action='store',
        dest='separator',
        default=" ",
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
    
    if len(args) == 0:
        sys.stderr.write("Please supply a command to be executed.\n")
        sys.exit(1)
        
    command = args             
    command_stdout = open_file(opts.stdout, 'w', replace=opts.replace)
    command_stderr = open_file(opts.stderr, 'w', replace=opts.replace)
    if opts.outputfile is not None:
        output = open_file(opts.outputfile, 'w', replace=opts.replace)
    else:
        output = sys.stdout
    if opts.logfile is not None:
        logfile = open_file(opts.logfile, 'w', replace=opts.replace)
    else:
        logfile = None        
          
    start_time, end_time = profile_command(command=command,
        command_stdout=command_stdout,
        command_stderr=command_stderr,
        output=output,
        poll_interval=opts.poll_interval,
        output_separator=opts.separator,
        align=opts.align,
        headers=opts.headers,
        debug=opts.debug)
        
    final_run_report = []            
    final_run_report.append(" Command: %s" % (" ".join(command))) 
    final_run_report.append("Began at: %s." % (start_time.isoformat(' ')))
    final_run_report.append("Ended at: %s." % (end_time.isoformat(' ')))
    hours, mins, secs = str(end_time-start_time).split(":")
    run_time = "Run time: %s hour(s), %s minute(s), %s second(s)." % (hours, mins, secs)    
    final_run_report.append(run_time)

    report = "\n".join(final_run_report) + "\n"
    if not opts.quiet:
        sys.stderr.write("---\n")
        sys.stderr.write(report)
        sys.stderr.write("---\n")        
    if logfile is not None:
        logfile.write(report)
    
if __name__ == '__main__':
    main()

    



