
Introduction
============

Syrupy is a Python script that regularly takes snapshots of the memory and CPU load of one or more running processes, so as to dynamically build up a profile
of their usage of system resources.

Syrupy works by one of two modes.
In the first (default) mode, it monitors the resource usage of a process resulting from the execution of a user-specified command (which can be any arbitrarily-complex combination of programs and arguments that can be invoked from a shell terminal).
In the second mode, Syrupy monitors the resource usage of external running processes that meet user-specified criteria: a PID (Process IDentifier) number or a command string matching a regular expression pattern.

In either case, the monitoring of the system resource usage is based on repeated calls to the system command "`ps <http://en.wikipedia.org/wiki/Ps_(Unix)>`_".

Prerequisites
=============

Given that Syrupy is ultimately nothing more than a glorifed wrapper and parser of "`ps <http://en.wikipedia.org/wiki/Ps_(Unix)>`_" output, naturally the second-most important precondition for Syrupy to work on your system is to have the "`ps <http://en.wikipedia.org/wiki/Ps_(Unix)>`_" command available (the first-most important is to have Python available). This is almost certainly true all POSIX or mostly POSIX-compliant systems, including various flavors of UNIX, Linux's, Apple Mac OS X's etc.

Unless they happen to have a POSIX-compliant subsystem (such as Cygwin) installed, however, Microsoft Windows users are out of luck. Though that is hardly news.

Apart from requiring "`ps <http://en.wikipedia.org/wiki/Ps_(Unix)>`_" or something similar on your system (and, of course, Python), Syrupy has no other dependencies whatsoever: it is a single self-contained pure Python script and uses nothing but the standard Python libraries.


Downloading
===========

The entire Syrupy package can be downloaded as a single archive from the SourceForge site:

    https://sourceforge.net/project/platformdownload.php?group_id=242033

If you have Git installed on your system, you can clone your own copy of the repository by entering::

    git clone https://github.com/jeetsukumaran/Syrupy


Installing
==========

As mentioned above, Syrupy is a self-contained single-module (single-file) executable script. So you do not even really need to "install" it as such: you can simply unpack the archive and use the script from wherever you end up saving it. Or you can copy it on the system path to be invoked globally. In fact, all the installation procedure does is automate the latter for you, and this can be carried out by entering the unpacked archive directory and typing::

    $ sudo python install

Usage
=====

The discussion that follows highlights some of the main features of Syrupy, but full help and information on all options is readily available by entering::

    $ syrupy.py --help

Basic Invocation (Default Mode)
-------------------------------

In its default mode, Syrupy is invoked via the following syntax::

    $ syrupy.py [SYRUPY OPTIONS] COMMAND [COMMAND OPTIONS/ARGS]

In this context, "COMMAND [COMMAND OPTION/ARGS]" can be anything that you would normally invoke from a terminal, such as a program, executable, or interpretable script, with or without options and/or arguments::

    $ syrupy.py /usr/local/bin/program
    $ syrupy.py program.sh -o1 --opt2=foo -opt3="foo foo" /path/to/foo foo
    $ syrupy.py find . -name "*.csv"
    $ syrupy.py python script.py -o1 -o2 foo "something pithy"

Basic Invocation (External Process Mode)
----------------------------------------

In this mode, Syrupy will monitor one or more processes that are already running on the system based in user-specified criteria.
This mode is invoked by supplying values for one or more of the following options:

* "``-p``" or "``--poll-pid``"
* "``-c``" or "``--poll-command``"

The first option takes an integer value representing the PID (Process IDentifier) number of the process to be monitored.
The second option takes a string value representing a regular expression or grep pattern matching the command string that invoked the process or processes to be monitored.
For example::

    $ syrupy.py -p 20912
    $ syrupy.py --poll-pid=30011
    $ syrupy.py -c '[P|p]ython'
    $ syrupy.py --poll-command='.*java'

Note that you should protect the regular expression by quotes so as to avoid confusing the shell.

If both options are given, then only processes that meet both the PID condition and the command regular expression will be monitored (obviously, as the PID condition will match at most one process, then specifying both options is at best redundant, and at worst will get you nothing).

As long as processes are found that meet the specified conditions, then Syrupy will continue to run, monitoring the selected processes.
When no processes are found meeting the conditions specified, then Syrupy will terminate.
Note that if Syrupy starts up and does not find any processes matching the specified criteria, it will exit immediately.
Thus it is important that the processes to be monitored (or, to be more precise, matching the specified criteria) be already running before invoking Syrupy.
Each Syrupy instance automatically excludes itself when searching for processes matching a particular ID or command pattern: you cannot use an instance of Syrupy to monitor itself!
However, you can use an instance of Syrupy to monitor another instance of the same program.

Basic Output
------------

Given commands like the above, Syrupy will (if all is well) respond with writing something like the following to its log file (or standard output if the '-S' flag is used)::

     PID DATE        TIME     ELAPSED  CPU   MEM    RSS   VSIZE
   14634 2008-10-10  20:45:25   00:00  0.0   0.0   2996    6680
   14634 2008-10-10  20:45:26   00:01  105   0.2   7804   12592
   14634 2008-10-10  20:45:27   00:02  103   0.2   8996   13776
   14634 2008-10-10  20:45:28   00:03  103   0.2  10468   15348
   14634 2008-10-10  20:45:29   00:04  103   0.3  11412   16396
   14634 2008-10-10  20:45:30   00:05  104   0.3  12492   17444
   ...
   etc.

Each row represents an instantaneous snapshot taken at regular intervals of the CPU and memory usage of the process or processes being monitored by Syrupy. In the case of the default mode, this is the process resulting from the user-specified COMMAND invoked by Syrupy, while in the second mode, this is any number of external processes that match the specified criteria.

Thus, over time Syrupy builds up a system resource usage profile of a particular program or programs (hence the name: **SYRUPY** = **SY**\ stem **R**\ esource **U**\ sage **P**\ rofile ...um, **Y**\ eah).

The meaning of the various fields are given by entering the following::

    $ syrupy.py --explain

Which will tell you that::

    PID       Process IDentifier -- a number used by the operating system
              kernel to uniquely identify a running program or process.
    DATE      The calender date, given as YEAR-MONTH-DAY, that the process
              was polled.
    TIME      The actual time, given as HOUR:MINUTE:SECOND
              that the process was polled.
    ELAPSED   The total time that the process had been running up to the
              time it was polled.
    CPU       The CPU utilization of the process: CPU time used divided by
              the time the process has been running
              (cputime/realtime ratio), expressed as a
              percentage.
    MEM       The memory utilization of the process: ratio of the
              process's resident set size to the physical memory
              on the machine, expressed as a percentage.
    RSS       Resident Set Size -- the non-swapped physical memory (RAM)
              that a process is occupying (in kiloBytes). The
              rest of the process memory usage is in swap. If
              the computer has not used swap, this number will
              be equal to VSIZE.
    VSIZE     Virtual memory Size -- the total amount of memory the
              process is currently using (in kiloBytes). This
              includes the amount in RAM (the resident set size)
              as well as the amount in swap.

If you specify the "``show-command``" flag, then a final column will appear that presents the entire command string corresponding to the particular process.

Syrupy will continue taking and logging snapshots of the resource usage of the process or processes that it is monitoring until they terminate.

Specifying Options to Syrupy: Position Counts!
----------------------------------------------

Various options to Syrupy control, customize or change its default behavior. It is important to note that *all* options for Syrupy must be specified *before* the COMMAND and its options/arguments. Any and all arguments and options following the COMMAND will be passed directly to COMMAND and ignored by Syrupy.

That is::

    $ syrupy.py --syrupy-opt1 --syrupy-opt2 /usr/local/bin/program

is correct, while::

    $ syrupy.py --syrupy-opt1 /usr/local/bin/program --syrupy-opt2

is wrong. In the second case, "``--syrupy-opt2``" will be passed to "``program``", which will result in unintended and probably undesirable behavior.

Controlling the Polling Regime
------------------------------

Since the polling regime is pretty simple, there is only one option to control: the polling interval. By default this is one second, but it can be set to anything you want using the "``-i``" or "``--polling-interval``" option::

    $ syrupy.py -i 0.001 /bin/program
    $ syrupy.py --polling-interval=0.001 /bin/program
    $ syrupy.py -i 60 /bin/program
    $ syrupy.py --polling-interval=60 /bin/program
    etc.

Units are always in seconds, and thus the first two examples will sample the resource usage of "``/bin/program``" every 100th of a second, while the second two examples will sample the resource usage of "``/bin/program``" every minute.

Formatting Output
-----------------
Syrupy's default output makes for easy visual inspection on a terminal or in a text editor.
However, you might want to bring the results into a program like R for analysis.
Some of these analysis programs are very picky about how fields are separated, requiring specific characters or strings to delimit columns.
You can use the "``--separator``" flag to specify some other string or character to separate the fields, such as tabs or commas.
Furthermore, by default Syrupy pads out each column with extra spaces so that they are all the same width, thus getting them to line up on the screen or when viewed in a (monospace-font rendering) text-editor.
These extra spaces may confuse some other programs, and, if so, you can turn off the flushing or alignment of fields using the "``--no-align``" flag.
Thus, for example, to produce plain-vanilla/no-frills comma-separated value (CSV) output you would enter::

        $ syrupy --separator=, --no-align /bin/program

which would result in something like::

    DATE,TIME,ELAPSED,CPU,MEM,RSS,VSIZE
    2008-10-11,00:39:04,00:00,0.0,0.1,1688,601580
    2008-10-11,00:39:05,00:01,98.1,0.2,7544,82752
    2008-10-11,00:39:06,00:02,98.1,0.3,9872,85056
    2008-10-11,00:39:07,00:03,100.0,0.4,12324,87392
    2008-10-11,00:39:08,00:04,100.0,0.4,13472,87904
    2008-10-11,00:39:09,00:05,98.4,0.5,15480,89952
    2008-10-11,00:39:10,00:06,99.0,0.6,17612,92176
    2008-10-11,00:39:11,00:07,97.5,0.6,20192,94560
    2008-10-11,00:39:12,00:08,99.7,0.6,19632,94048
    2008-10-11,00:39:13,00:09,99.4,0.6,19788,94088

You can also suppress the first row, i.e. the column headers, using the "``--no-headers``" option.

Bugs, Suggestions, Comments, etc.
=================================
If you have questions, bug reports, criticisms, suggestion, comments or any other message to send me, you can contact me jeet@ku.edu.

Copyright, License and Warranty
===============================

Copyright 2008 Jeet Sukumaran.

This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation; either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program. If not, see <http://www.gnu.org/licenses/>.
