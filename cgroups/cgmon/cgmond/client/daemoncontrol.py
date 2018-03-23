import os
import signal
from lockfile import pidlockfile

# TODO maybe also provide a list of logfiles to support displaying last lines
#      of logfiles in an error event.
#
# [logfile1]
#
# line - (n-k)
# line - (n-k+1)
# ...
# line - (n-2)
# line - (n-1)
# line - n

# [logfile2]

# line - (n-k)
# line - (n-k+1)
# ...
# line - (n-2)
# line - (n-1)
# line - n

class DaemonControlException(Exception):
    def __init__(self, msg):
        super(DaemonControlException, self).__init__(msg)


class DaemonControl(object):
    pidfile_path = None
    start_fn = None
    stop_fn = None
    check_running_fn = None

    def __init__(self, pidfile_path=None, start_fn=None, stop_fn=None,
                 check_running_fn=None):
        self.pidfile_path = pidfile_path
        self.start_fn = start_fn
        self.stop_fn = stop_fn
        self.check_running_fn = check_running_fn


    def get_pidfile_path(self):
        return self.pidfile_path


    def get_running_pid(self):
        pidfile = pidlockfile.PIDLockFile(self.get_pidfile_path())
        if not pidfile.is_locked():
            return None

        pid = pidfile.read_pid()
        # read_pid returns None on IOError or on ValueError
        if pid is None:
            raise DaemonControlException("Could not read pidfile %s" \
                                         % self.get_pidfile_path())

        return pid


    def daemon_running(self):
        pid = self.get_running_pid()
        if pid is None:
            return False

        # if pid is not running:
        #     return False

        # if self.check_running_fn:
        #     return self.check_running_fn()

        return True


    def _stop(self):
        pid = self.get_running_pid()
        os.kill(pid, signal.SIGTERM)
        # maybe wait for it to terminate
        return True


    def start(self, *args, **kwargs):
        if self.daemon_running():
            raise DaemonControlException("Daemon is already running")

        return self.start_fn(*args, **kwargs)


    def stop(self, *args, **kwargs):
        if not self.daemon_running():
            raise DaemonControlException("Daemon is not running")

        if self.stop_fn is not None:
            return self.stop_fn(*args, **kwargs)
        else:
            return self._stop()


    def status(self):
        return self.daemon_running()


    def restart(self):
        if not self.stop():
            return False

        return self.start()
