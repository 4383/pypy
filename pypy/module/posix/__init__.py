# Package initialisation
from pypy.interpreter.mixedmodule import MixedModule

import os
exec 'import %s as posix' % os.name

class Module(MixedModule):
    """This module provides access to operating system functionality that is
standardized by the C Standard and the POSIX standard (a thinly
disguised Unix interface).  Refer to the library manual and
corresponding Unix manual entries for more information on calls."""

    applevel_name = os.name

    appleveldefs = {
    'error'      : 'app_posix.error',
    'stat_result': 'app_posix.stat_result',
    'fdopen'     : 'app_posix.fdopen',
    }
    
    interpleveldefs = {
    'open'      : 'interp_posix.open',
    'lseek'     : 'interp_posix.lseek',
    'write'     : 'interp_posix.write',
    'isatty'    : 'interp_posix.isatty',
    'read'      : 'interp_posix.read',
    'close'     : 'interp_posix.close',
    'fstat'     : 'interp_posix.fstat',
    'stat'      : 'interp_posix.stat',
    'lstat'     : 'interp_posix.lstat',
    'dup'       : 'interp_posix.dup',
    'dup2'      : 'interp_posix.dup2',
    'system'    : 'interp_posix.system',
    'unlink'    : 'interp_posix.unlink',
    'remove'    : 'interp_posix.remove',
    'getcwd'    : 'interp_posix.getcwd',
    'chdir'     : 'interp_posix.chdir',
    'mkdir'     : 'interp_posix.mkdir',
    'rmdir'     : 'interp_posix.rmdir',
    'environ'   : 'interp_posix.get(space).w_environ',
    'listdir'   : 'interp_posix.listdir',
    'strerror'  : 'interp_posix.strerror',
    'pipe'      : 'interp_posix.pipe',
    'chmod'     : 'interp_posix.chmod',
    'rename'    : 'interp_posix.rename',
    '_exit'     : 'interp_posix._exit',
    'abort'     : 'interp_posix.abort',
    'access'    : 'interp_posix.access',
    }
    if hasattr(os, 'ftruncate'):
        interpleveldefs['ftruncate'] = 'interp_posix.ftruncate'
    if hasattr(os, 'putenv'):
        interpleveldefs['putenv'] = 'interp_posix.putenv'
    if hasattr(posix, 'unsetenv'): # note: emulated in os
        interpleveldefs['unsetenv'] = 'interp_posix.unsetenv'
    if hasattr(os, 'getpid'):
        interpleveldefs['getpid'] = 'interp_posix.getpid'
    if hasattr(os, 'link'):
        interpleveldefs['link'] = 'interp_posix.link'
    if hasattr(os, 'symlink'):
        interpleveldefs['symlink'] = 'interp_posix.symlink'
    if hasattr(os, 'readlink'):
        interpleveldefs['readlink'] = 'interp_posix.readlink'
    if hasattr(os, 'fork'):
        interpleveldefs['fork'] = 'interp_posix.fork'
    if hasattr(os, 'waitpid'):
        interpleveldefs['waitpid'] = 'interp_posix.waitpid'
    if hasattr(os, 'chown'):
        interpleveldefs['chown'] = 'interp_posix.chown'
    if hasattr(os, 'chroot'):
        interpleveldefs['chroot'] = 'interp_posix.chroot'


for constant in dir(os):
    value = getattr(os, constant)
    if constant.isupper() and type(value) is int:
        Module.interpleveldefs[constant] = "space.wrap(%s)" % value
