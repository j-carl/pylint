# Copyright (c) 2002-2004 LOGILAB S.A. (Paris, FRANCE).
# http://www.logilab.fr/ -- mailto:contact@logilab.fr
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
"""
generic classes/functions for pyreverse core/extensions
"""

__revision__ = "$Id: utils.py,v 1.12 2006-03-14 09:56:06 syt Exp $"

import sys
import re

from logilab.astng import ASTNGManager, IgnoreChild, Project
from logilab.astng.utils import is_interface, is_exception, \
     get_raises, get_returns
from logilab.astng.manager import astng_wrapper

from logilab.common.configuration import ConfigurationMixIn

from pyreverse.__pkginfo__ import version
from pyreverse import config

def time_tag():
    """
    return a timestamp as string
    """
    from time import time, localtime, strftime
    return strftime('%b %d at %T', localtime(time()))

def LOG(msg):
    """LOG doesn't do anything by default"""
    pass

def info(msg):
    """print an informal message on stdout"""
    LOG(msg)
            

# astng utilities #############################################################

PROTECTED = re.compile('^_[A-Za-z]+(_*[A-Za-z]+)*_?$')
PRIVATE = re.compile('^__[A-Za-z]+(_*[A-Za-z]+)*_?$')
SPECIAL = re.compile('^__[A-Za-z]+__$')

def get_visibility(name):
    """return the visibility from a name: public, protected, private or special
    """
    if SPECIAL.match(name):
        visibility = 'special'
    elif PROTECTED.match(name):
        visibility = 'protected'
    elif PRIVATE.match(name):
        visibility = 'private'
    else:
        visibility = 'public'
    return visibility

ABSTRACT = re.compile('^.*Abstract.*')
FINAL = re.compile('^[A-Z_]*$')

def is_abstract(node):
    """return true if the given class node correspond to an abstract class
    definition
    """
    return ABSTRACT.match(node.name)

def is_final(node):
    """return true if the given class/function node correspond to final
    definition
    """
    return FINAL.match(node.name)



# Helpers #####################################################################

_CONSTRUCTOR = 1
_SPECIAL = 2
_PROTECTED = 4
_PRIVATE = 8
MODES = {
    'ALL'       : 0,
    'PUB_ONLY'  : _SPECIAL + _PROTECTED + _PRIVATE,
    'SPECIAL'   : _SPECIAL,
    'OTHER'     : _PROTECTED + _PRIVATE,
}

class FilterMixIn:
    """filter nodes according to a mode and nodes'visibility
    """


    options = (
        ("filter-mode",
         {'default': 'PUB_ONLY', 'dest' : 'mode',
          'type' : 'string', 'action' : 'store', 'metavar' : '<mode>',
          'help' : """filter attributes and functions according to
          <mode>. Correct modes are :
                                    'PUB_ONLY' filter all non public attributes
                                      [DEFAULT], equivalent to PRIVATE+SPECIAL_A
                                    'ALL' no filter 
                                    'SPECIAL' filter Python special functions
                                      except constructor
                                    'OTHER' filter protected and private
                                      attributes"""}),
        )
    
    def __init__(self):
        pass

    def get_mode(self):
        """return the integer value of a mode string
        """
        try:
            return self.__mode
        except AttributeError:
            mode = 0
            for nummod in self.config.mode.split('+'):
                try:
                    mode += MODES[nummod]
                except KeyError, ex:
                    print >> sys.stderr, 'Unknown filter mode %s' % ex
            self.__mode = mode
            return mode
        
    def filter(self, node):
        """return true if the node should be treaten
        """
        mode = self.get_mode()
        visibility = get_visibility(getattr(node, 'name', node))
        if mode & _SPECIAL and visibility == 'special':
            return 0
        if mode & _PROTECTED and visibility == 'protected':
            return 0
        if mode & _PRIVATE and visibility == 'private':
            return 0
        return 1


class RunHelper(ConfigurationMixIn):
    """command line helper
    """
    name = 'main'
    options = (('quiet', {'help' : 'run quietly', 'action' : 'store_true',
                          'short': 'q'}),
               )
    
    def __init__(self, usage, options_providers):
        ConfigurationMixIn.__init__(self, """\
USAGE: %%prog [options] <file or module>...
%s""" % usage, version="%%prog %s" % version)
        config.insert_default_options()
        manager = ASTNGManager()
        # FIXME: use an infinite cache
        manager._cache = {}
        # add options
        self.register_options_provider(manager)
        for provider in options_providers:
            self.register_options_provider(provider)
        #self.load_file_configuration()
        args = self.load_command_line_configuration()
        if not args:
            self.help()
        else:
            global LOG
            LOG = self.log
            # extract project representation
            project = manager.project_from_files(args, astng_wrapper)
            self.do_run(project)

    def do_run(self, project):
        """method to override in concrete classes"""
        raise NotImplementedError()

    def log(self, msg):
        """print an informal message on stdout"""
        if not self.config.quiet:
            print '-'*80
            print msg
            
