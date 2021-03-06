# encoding: utf-8
"""sys.excepthook for IPython itself, leaves a detailed report on disk.

Authors:

* Fernando Perez
* Brian E. Granger
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2001-2007 Fernando Perez. <fperez@colorado.edu>
#  Copyright (C) 2008-2010  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import os
import sys
from pprint import pformat

from IPython.core import ultratb
from IPython.utils.sysinfo import sys_info

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------

# Template for the user message.
_default_message_template = """\
Oops, {app_name} crashed. We do our best to make it stable, but...

A crash report was automatically generated with the following information:
  - A verbatim copy of the crash traceback.
  - A copy of your input history during this session.
  - Data on your current {app_name} configuration.

It was left in the file named:
\t'{crash_report_fname}'
If you can email this file to the developers, the information in it will help
them in understanding and correcting the problem.

You can mail it to: {contact_name} at {contact_email}
with the subject '{app_name} Crash Report'.

If you want to do it now, the following command will work (under Unix):
mail -s '{app_name} Crash Report' {contact_email} < {crash_report_fname}

To ensure accurate tracking of this issue, please file a report about it at:
{bug_tracker}
"""


class CrashHandler(object):
    """Customizable crash handlers for IPython applications.

    Instances of this class provide a :meth:`__call__` method which can be
    used as a ``sys.excepthook``.  The :meth:`__call__` signature is::

        def __call__(self, etype, evalue, etb)
    """

    message_template = _default_message_template
    section_sep = '\n\n'+'*'*75+'\n\n'

    def __init__(self, app, contact_name=None, contact_email=None, 
                 bug_tracker=None, show_crash_traceback=True, call_pdb=False):
        """Create a new crash handler

        Parameters
        ----------
        app :  Application
            A running :class:`Application` instance, which will be queried at 
            crash time for internal information.

        contact_name : str
            A string with the name of the person to contact.

        contact_email : str
            A string with the email address of the contact.

        bug_tracker : str
            A string with the URL for your project's bug tracker.

        show_crash_traceback : bool
            If false, don't print the crash traceback on stderr, only generate
            the on-disk report

        Non-argument instance attributes:

        These instances contain some non-argument attributes which allow for
        further customization of the crash handler's behavior. Please see the
        source for further details.
        """
        self.crash_report_fname = "Crash_report_%s.txt" % app.name
        self.app = app
        self.call_pdb = call_pdb
        #self.call_pdb = True # dbg
        self.show_crash_traceback = show_crash_traceback
        self.info = dict(app_name = app.name,
                    contact_name = contact_name,
                    contact_email = contact_email,
                    bug_tracker = bug_tracker,
                    crash_report_fname = self.crash_report_fname)
        

    def __call__(self, etype, evalue, etb):
        """Handle an exception, call for compatible with sys.excepthook"""

        # Report tracebacks shouldn't use color in general (safer for users)
        color_scheme = 'NoColor'

        # Use this ONLY for developer debugging (keep commented out for release)
        #color_scheme = 'Linux'   # dbg
        try:
            rptdir = self.app.ipython_dir
        except:
            rptdir = os.getcwdu()
        if rptdir is None or not os.path.isdir(rptdir):
            rptdir = os.getcwdu()
        report_name = os.path.join(rptdir,self.crash_report_fname)
        # write the report filename into the instance dict so it can get
        # properly expanded out in the user message template
        self.crash_report_fname = report_name
        self.info['crash_report_fname'] = report_name
        TBhandler = ultratb.VerboseTB(
            color_scheme=color_scheme,
            long_header=1,
            call_pdb=self.call_pdb,
        )
        if self.call_pdb:
            TBhandler(etype,evalue,etb)
            return
        else:
            traceback = TBhandler.text(etype,evalue,etb,context=31)

        # print traceback to screen
        if self.show_crash_traceback:
            print >> sys.stderr, traceback

        # and generate a complete report on disk
        try:
            report = open(report_name,'w')
        except:
            print >> sys.stderr, 'Could not create crash report on disk.'
            return

        # Inform user on stderr of what happened
        print >> sys.stderr, '\n'+'*'*70+'\n'
        print >> sys.stderr, self.message_template.format(**self.info)

        # Construct report on disk
        report.write(self.make_report(traceback))
        report.close()
        raw_input("Hit <Enter> to quit this message (your terminal may close):")

    def make_report(self,traceback):
        """Return a string containing a crash report."""
        
        sec_sep = self.section_sep
        
        report = ['*'*75+'\n\n'+'IPython post-mortem report\n\n']
        rpt_add = report.append
        rpt_add(sys_info())
        
        try:
            config = pformat(self.app.config)
            rpt_add(sec_sep)
            rpt_add('Application name: %s\n\n' % self.app_name)
            rpt_add('Current user configuration structure:\n\n')
            rpt_add(config)
        except:
            pass
        rpt_add(sec_sep+'Crash traceback:\n\n' + traceback)

        return ''.join(report)

