
Introduction
============

Syrupy is a Python script to dynamically profile the resource (especially memory) usage of any program or process that can be invoked from the command line.

Syrupy works by executing a command (which can be any arbitrarily-complex combination of programs and arguments that can be invoked in a terminal), and then monitoring the resource usage of the resulting process through repeated calls to the system command "`ps <http://en.wikipedia.org/wiki/Ps_(Unix)>`_".


Prerequisites
=============

Given that Syrupy is nothing more than a glorifed wrapper and parser of "`ps <http://en.wikipedia.org/wiki/Ps_(Unix)>`_", naturally the most important precondition for Syrupy to work on your system is to have the "`ps <http://en.wikipedia.org/wiki/Ps_(Unix)>`_" command available. This is almost certainly found in all POSIX or mostly POSIX-compliant systems, including various flavors of UNIX, Linux's, Apple Mac OS X's etc. 

Unless they happen to have a POSIX-compliant subsystem installed, such as Cygwin, Microsoft Windows users are out of luck. Though that is hardly news.

Apart from requiring "`ps <http://en.wikipedia.org/wiki/Ps_(Unix)>`_" or something similar on your system (and, of course, Python), Syrupy has no other dependencies whatsoever: it is a single self-contained pure Python script and uses nothing but the standard Python libraries.


Downloading
===========

The entire Syrupy package can be downloaded as a single archive here:

    http://www.jeetworks.org/files/downloads/Syrupy-1.0.0.tar.gz

If you have Git installed on your system, you can clone your own copy of the repository by entering::

    git clone http://jeetworks.org/files/repositories/syrupy.git
    
    
Installing
==========

As mentioned above, Syrupy is a self-contained single-module (single-file) executable script. So you do not even really need to "install" it as such: you can simply unpack the archive and use the script from wherever you end up saving it. Or you can copy it on the system path to be invoked globally. In fact, all the installation procedure does is automate the latter for you, and this can be carried out by entering::

    $ sudo python install
    
Usage
=====

Basic Invocation
----------------

Syrupy is invoked via the following syntax::

    $ syrupy.py [OPTIONS] COMMAND [COMMAND OPTIONS] [COMMAND ARGS]
    
In this context, "COMMAND [COMMAND OPTIONS] [COMMAND ARGS]" can be anything that you would normally invoke from a terminal, such as a program, executable, or interpretable script, with or without options and/or arguments::

    $ syrupy.py /usr/local/bin/program
    $ syrupy.py program.sh -o1 --opt2=foo -opt3="foo foo" /path/to/foo foo
    $ syrupy.py find . -name "*.csv" 
    $ syrupy.py python script.py -o1 -o2 foo "something pithy"
    
As usual, full help and information on all options is readily available by entering::

    $ syrupy.py --help
    
Basic Output
------------
    
Given commands like the above, Syrupy will (if all is well) respond with writing something like the following to the standard output::

     PID DATE        TIME             ELAPSED  CPU   MEM    RSS     SZ      VSZ
   14634 2008-10-10  20:45:25.459525    00:00  0.0   0.0   2996   1670     6680
   14634 2008-10-10  20:45:26.489843    00:01  105   0.2   7804   3148    12592
   14634 2008-10-10  20:45:27.521555    00:02  103   0.2   8996   3444    13776
   14634 2008-10-10  20:45:28.553634    00:03  103   0.2  10468   3837    15348
   14634 2008-10-10  20:45:29.585121    00:04  103   0.3  11412   4099    16396
   14634 2008-10-10  20:45:30.663359    00:05  104   0.3  12492   4361    17444
   ...
   etc.

Each row represents an instantaneous snapshot taken at regular intervals of the CPU and memory usage of the process initiated by COMMAND. 
Thus, over time Syrupy builds up a system resource usage profile of a particular program (hence the name: **SYRUPY** = **SY**\ stem **R**\ esource **U**\ sage **P**\ rofile ...um, **Y**\ eah).

The meaning of the various fields are given by entering the following::

    $ syrupy.py --explain
    
Which will tell you that::

    PID       Process IDentifier -- a number used by the operating system
              kernel to uniquely identify a running program or process.
    DATE      The calender date, given as YEAR-MONTH-DAY, that the process
              was polled.
    TIME      The actual time, given as HOUR:MINUTE:SECOND.MICROSECONDS
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
              
Syrupy will continue taking and logging snapshots of the resource usage of the process until the processes terminates. When this happens, so does Syrupy, usually with a final report like::

    ---
     Command: sumtrees.py ansonia_combo.aligned.fasta.trees
    Began at: 2008-10-10 20:45:25.453861.
    Ended at: 2008-10-10 21:33:52.629728.
    Run time: 0 hour(s), 48 minute(s), 27.175867 second(s).
    ---

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

Controlling and Redirecting Output
----------------------------------
 
By default, Syrupy will redirect both the output and and error streams of COMMAND to the system null device (typically, "``/dev/null``"), while writing its own results to the standard output stream (with miscellaneous information to the standard error stream). 
This is simply the way I tend to want it to work when I am using it: I am usually running a program under it to assess the resource usage of the program, rather than being interested in the output of the program per se.
Of course, the standard error of the program or command may actually be useful to see, especially if the program is not bug-free. 
Also, sometimes the COMMAND may actually be a chained pipeline of scripts or programs, where the output of one is fed as the input of the other.
In cases like these, it might be useful to actually have the output stream of COMMAND go to the standard output, and/or the error stream of COMMAND go to the standard error.
This can be achieved by the following options::

    $ syrupy.py --stdout=^1 --stderr=^2 /bin/program
    
"``^1``" and "``^2``" are special symbols that are interpreted by Syrupy to mean the standard output and standard error respectively.     

If you do send the output stream of COMMAND to the standard output, you will probably find that this channel gets cluttered very quickly, as that is where, by default Syrupy writes *its* output. So you probably want to instruct Syrupy to write its own output elsewhere, using the "``--output``" option::

    $ syrupy.py --output="program.run" --stdout=^1 /bin/program

Similarly, you can redirect the standard error stream of Syrupy using::

    $ syrupy.py --log="syrupy.log" --stderr-^2 /bin/program
    
Of course, you can request Syrupy to redirect its streams to files without redirecting the streams of COMMAND anywhere in particular as well::

    $ syrupy.py --output="program.run" --log="syrupy.log" /bin/program
    
You may also want to save the output and error stream of COMMAND, but not actually want to see them on the standard output. Then, instead of using the special symbols "``^1``" or "``^2``", you would simply supply proper file paths::

    $ syrupy.py --stdout=cmd.out --stderr=cmd.err /bin/program
    
As a matter of convenience, you can use the "``--debug-command``" flag to have the error of COMMAND sent to the standard error::

    $ syrupy.py --debug-command /bin/program
    
This is exactly the same as::

    $ syrupy.py --stderr=^2 /bin/program
        
Formatting Output
-----------------
Syrupy's default output makes for easy visual inspection on a terminal or in a text editor.
However, you might want to bring the results into a program like R for analysis.
Some of these analysis programs are very picky about how fields are separated, requiring specific characters or strings to delimit columns.
You can use the "``--separator``" flag to specify some other string or character to separate the fields, such as tabs or commas.
Furthermore, by default Syrupy pads out each column with extra spaces so that they are all the same widht, thus getting them to line up on the screen or when viewed in a (monospace-font rendering) text-editor.
These extra spaces may confuse some other programs, and, if so, you can turn off the flushing or alignment of fields using the "``--no-align``" flag.
Thus, for example, to produce plain-vanilla/no-frills comma-separated value (CSV) output you would enter::

        $ syrupy --separator=, --no-align /bin/program

which would result in something like::

    DATE,TIME,ELAPSED,CPU,MEM,RSS,VSIZE
    2008-10-11,00:39:04.733761,00:00,0.0,0.1,1688,601580
    2008-10-11,00:39:05.758148,00:01,98.1,0.2,7544,82752
    2008-10-11,00:39:06.775282,00:02,98.1,0.3,9872,85056
    2008-10-11,00:39:07.791840,00:03,100.0,0.4,12324,87392
    2008-10-11,00:39:08.807924,00:04,100.0,0.4,13472,87904
    2008-10-11,00:39:09.824843,00:05,98.4,0.5,15480,89952
    2008-10-11,00:39:10.841040,00:06,99.0,0.6,17612,92176
    2008-10-11,00:39:11.853790,00:07,97.5,0.6,20192,94560
    2008-10-11,00:39:12.874014,00:08,99.7,0.6,19632,94048
    2008-10-11,00:39:13.891240,00:09,99.4,0.6,19788,94088

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
