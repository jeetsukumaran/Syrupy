#! /usr/bin/env python

############################################################################
##  syrupy-peak.py
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
Reports maximum memory usage from Syrupy logs.
"""

import sys
import os
from optparse import OptionParser

_program_name = "Syrupy Memory Peak Reporter"
_program_usage = '%prog [options] <log> [<log> [<log> [...]]]'
_program_version = '%s Version 1.0' % _program_name
_program_description = """\
Analyzes one or more Syrupy logs and reports peak resource usage within and across
all logs."""
_program_author = 'Jeet Sukumaran'
_program_copyright = 'Copyright (C) 2010 Jeet Sukumaran.'

def format_dict_table(rows, column_names=None, max_column_width=None, border_style=2):
    """
    Returns a string representation of a tuple of dictionaries in a
    table format. This method can read the column names directly off the
    dictionary keys, but if a tuple of these keys is provided in the
    'column_names' variable, then the order of column_names will follow
    the order of the fields/keys in that variable.
    """
    if column_names or len(rows) > 0:
        lengths = {}
        rules = {}
        if column_names:
            column_list = column_names
        else:
            try:
                column_list = rows[0].keys()
            except:
                column_list = None
        if column_list:
            # characters that make up the table rules
            border_style = int(border_style)
            #border_style = 0
            if border_style >= 1:
                vertical_rule = ' | '
                horizontal_rule = '-'
                rule_junction = '-+-'
            else:
                vertical_rule = '  '
                horizontal_rule = ''
                rule_junction = ''
            if border_style >= 2:
                left_table_edge_rule = '| '
                right_table_edge_rule = ' |'
                left_table_edge_rule_junction = '+-'
                right_table_edge_rule_junction = '-+'
            else:
                left_table_edge_rule = ''
                right_table_edge_rule = ''
                left_table_edge_rule_junction = ''
                right_table_edge_rule_junction = ''

            if max_column_width:
                column_list = [c[:max_column_width] for c in column_list]
                trunc_rows = []
                for row in rows:
                    new_row = {}
                    for k in row.keys():
                        new_row[k[:max_column_width]] = str(row[k])[:max_column_width]
                    trunc_rows.append(new_row)
                rows = trunc_rows

            for col in column_list:
                rls = [len(str(row[col])) for row in rows]
                lengths[col] = max(rls+[len(col)])
                rules[col] = horizontal_rule*lengths[col]

            template_elements = ["%%(%s)-%ss" % (col, lengths[col]) for col in column_list]
            row_template = vertical_rule.join(template_elements)
            border_template = rule_junction.join(template_elements)
            full_line = left_table_edge_rule_junction + (border_template % rules) + right_table_edge_rule_junction
            display = []
            if border_style > 0:
                display.append(full_line)
            display.append(left_table_edge_rule + (row_template % dict(zip(column_list, column_list))) + right_table_edge_rule)
            if border_style > 0:
                display.append(full_line)
            for row in rows:
                display.append(left_table_edge_rule + (row_template % row) + right_table_edge_rule)
            if border_style > 0:
                display.append(full_line)
            return "\n".join(display)
        else:
            return ''
    else:
        return ''

class SyrupyRecord(object):

    class SyrupyRecordParseError(ValueError):
        def __init__(self, msg):
            msg += "syrupy-peak: log entry parse failure: %s" % msg
            ValueError.__init__(self, msg)

    class SyrupyRecordInsufficientFieldsError(SyrupyRecordParseError):
        def __init__(self, entry):
            msg = "insufficient number of fields in entry: '%s'" % entry
            SyrupyRecord.SyrupyRecordParseError.__init__(self, msg)

    class SyrupyRecordValueError(SyrupyRecordParseError):
        def __init__(self, entry):
            msg = "bad value type: '%s'" % entry
            SyrupyRecord.SyrupyRecordParseError.__init__(self, msg)

    def __init__(self, text=None, filename=None):
        self.filename = filename
        self.pid = None
        self.date_text = None
        self.time_text = None
        self.datetime = None
        self.elapsed_text = None
        self.elapsed_time = None
        self.cpu = None
        self.mem = None
        self.rss = None
        self.vsize = None
        if text is not None:
            self.parse(text)

    def parse(self, text):
        parts = text.split()
        if len(parts) < 8:
            raise SyrupyRecord.SyrupyRecordInsufficientFieldsError(text)
        self.pid = int(parts[0])
        self.date_text = parts[1]
        self.time_text = parts[2]
        self.elapsed_text = parts[3]
        self.cpu = float(parts[4])
        self.mem = float(parts[5])
        self.rss = int(parts[6])
        self.vsize = int(parts[7])

class SyrupyPeaks(object):

    def __init__(self, logf_path=None):
        self.logf_path = logf_path
        self.peak_mem = None
        self.peak_rss = None
        self.peak_vsize = None

    def update(self, syrec):
        self._check_and_update(syrec, 'peak_mem', 'mem')
        self._check_and_update(syrec, 'peak_rss', 'rss')
        self._check_and_update(syrec, 'peak_vsize', 'vsize')

    def _check_and_update(self, candidate, current_record_name, attr_name):
        if (getattr(self, current_record_name) is None) \
                or getattr(candidate, attr_name) > getattr(getattr(self, current_record_name), attr_name):
            if not hasattr(candidate, 'ties'):
                candidate.ties = {}
            candidate.ties[attr_name] = []
            setattr(self, current_record_name, candidate)
        elif getattr(candidate, attr_name) == getattr(getattr(self, current_record_name), attr_name):
            getattr(getattr(self, current_record_name), 'ties')[attr_name] = candidate


def main():
    parser = OptionParser(usage=_program_usage,
            add_help_option=True,
            version=_program_version,
            description=_program_description)

    parser.add_option('-i', '--ignore-errors',
            action='store_true',
            dest='ignore_all_errors',
            default=False,
            help="ignore all errors (equivalent to '--ignore-missing-errors' and '--ignore-parse-errors'")

    parser.add_option('--ignore-missing-errors',
            action='store_true',
            dest='ignore_missing_errors',
            default=False,
            help='ignore missing or non-existing log files')

    parser.add_option('--ignore-parse-errors',
            action='store_true',
            dest='ignore_parse_errors',
            default=False,
            help='ignore errors while parsing log files')

    parser.add_option('-q', '--quiet',
            action='store_true',
            dest='quiet',
            default=False,
            help='suppress progress messages')

    opts, args = parser.parse_args()

    if len(args) == 0:
        sys.exit("Path to Syrupy log files to be analyzed needs to be specifed.")

    if opts.ignore_all_errors:
        opts.ignore_parse_errors = True
        opts.ignore_missing_errors = True

    logf_paths = [ os.path.expanduser(os.path.expandvars(a)) for a in args ]
    overall_sp = SyrupyPeaks()
    log_sp = []
    num_processed = 0
    for file_idx, logf_path in enumerate(logf_paths):
        if not os.path.exists(logf_path):
            if opts.ignore_missing_errors:
                sys.stderr.write("Skipping missing log file %d of %d: '%s'\n"
                            % (file_idx+1, len(logf_paths), logf_path))
                continue
            else:
                sys.exit("Log file %d of %d not found: '%s'"
                            % (file_idx+1, len(logf_paths), logf_path))
        if not opts.quiet:
            sys.stderr.write("Processing log file %d of %d: '%s'\n"
                            % (file_idx+1, len(logf_paths), logf_path))
        logf = open(logf_path, 'rU')
        sp = SyrupyPeaks(logf_path)
        log_sp.append(sp)
        logf.readline()
        for entry_idx, entry in enumerate(logf):
            try:
                sr = SyrupyRecord(text=entry.replace('\n', ''), filename=logf_path)
            except SyrupyRecord.SyrupyRecordInsufficientFieldsError:
                if opts.ignore_parse_errors:
                    sys.stderr.write("Ignoring error parsing entry %d in log file %d of %d ('%s')\n"
                            % (entry_idx+1, file_idx+1, len(logf_paths), logf_path))
                else:
                    raise
            sp.update(sr)
            overall_sp.update(sr)
            ++num_processed

    cols = ["Log", "Mem (%)", "RSS (GB)", "VM (GB)"]
    records = []
    for sp in log_sp:
        d = {
            "Log" : sp.logf_path,
            "Mem (%)" : sp.peak_mem.mem,
            "RSS (GB)": "%0.4f" % (float(sp.peak_rss.rss) / (1024 * 1024)),
            "VM (GB)" : "%0.4f" % (float(sp.peak_vsize.vsize) / (1024 * 1024))
        }
        records.append(d)
    sys.stdout.write(format_dict_table(rows=records, column_names=cols))
    sys.stdout.write('\n')

if __name__ == '__main__':
    main()

