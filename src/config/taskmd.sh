#! /bin/sh
### BEGIN INIT INFO
# Provides:          testd
# Required-Start:    $remote_fs
# Required-Stop:     
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Start task manage server
### END INIT INFO

set -e
export PATH="${PATH:+$PATH:}/usr/sbin:/sbin"
do_start(){
    # /usr/bin/python3 /usr/local/lib/python3.5/dist-packages/task_manage-1.0-py3.5.egg/server/main.py &
    start-stop-daemon   --start  --name taskmd --background --exec /usr/bin/python3 /usr/local/lib/python3.5/dist-packages/task_manage-1.0-py3.5.egg/server/main.py 
    
}

do_stop(){
    start-stop-daemon  --stop --name taskmd --retry
}

case "$1" in
  start)
   do_start
    ;;
  stop)
    do_stop
    ;;
  
  restart|force-reload)
    $0 stop
    $0 start
    ;;
  *)
    echo "Usage: sudo service taskmd {start|stop|restart}" >&2
    exit 1
    ;;
esac

exit 0
