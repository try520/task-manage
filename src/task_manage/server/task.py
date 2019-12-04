#!/usr/bin/python3
# apscheduler https://www.jianshu.com/p/4f5305e220f0
import _thread
import os
import sys
import json
import time
import shutil
import signal
import logging
import subprocess
import socket
import platform
import configparser
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from apscheduler.events import EVENT_SCHEDULER_PAUSED, EVENT_SCHEDULER_RESUMED, EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, \
    EVENT_JOB_MISSED

here = os.path.abspath(os.path.dirname(__file__))  # 获取项目根目录
sys.path.append(os.path.join(here,'../../'))
conf = configparser.ConfigParser()
taskRootDir = os.path.join(here, "../task")  # 任务目录
if platform.system() == "Windows":
    conf.read(os.path.join(here, '../config', 'config.win.cfg'))
else:
    conf.read(os.path.join(here, '../config', 'config.cfg'))

# 执行器  常用的就线程池和进程池两种
executors = {
    'default': ThreadPoolExecutor(5),
    'processpool': ProcessPoolExecutor(5)
}

# 调度器配置
job_defaults = {
    'coalesce': False,
    # 当由于某种原因导致某个job积攒了好几次没有实际运行（比如说系统挂了5分钟后恢复，有一个任务是每分钟跑一次的，按道理说这5分钟内本来是“计划”运行5次的，但实际没有执行），如果coalesce为True，下次这个job被submit给executor时，只会执行1次，也就是最后这次，如果为False，那么会执行5次
    'max_instances': 1,
    # 就是说同一个job同一时间最多有几个实例再跑，比如一个耗时10分钟的job，被指定每分钟运行1次，如果我们max_instance值为5，那么在第6~10分钟上，新的运行实例不会被执行，因为已经有5个实例在跑了
    'misfire_grace_time': 1
    # 设想和上述coalesce类似的场景，如果一个job本来14:00有一次执行，但是由于某种原因没有被调度上，现在14:01了，这个14:00的运行实例被提交时，会检查它预订运行的时间和当下时间的差值（这里是1分钟），大于我们设置的30秒限制，那么这个运行实例不会被执行。
}


class Task(object):

    def __init__(self):
        self.isStop = False
        self.taskItems = []
        self.jobs = {}
        self.socketClients = []

        self.scheduler = BackgroundScheduler(executors=executors, job_defaults=job_defaults,
                                             daemonic=True)  # 实例化定时任务调度对象(非阻塞方式)
        self.scheduler.add_listener(self.errorListener, EVENT_JOB_ERROR | EVENT_JOB_MISSED)
        self.scheduler.add_listener(self.jobExecuteListener, EVENT_JOB_EXECUTED)
        self.scheduler.add_listener(self.jobPausedListener, EVENT_SCHEDULER_PAUSED)
        self.scheduler.add_listener(self.jobResumedListener, EVENT_SCHEDULER_RESUMED)
        signal.signal(signal.SIGINT, self.sigint_handler)  # 终止进程（ctrl+c）
        # signal.signal(signal.SIGCHLD, self.sigint_handler) #子进程退出或中断
        signal.signal(signal.SIGTERM, self.sigint_handler)  # 终止信号,软件终止信号;
        # self.bindSocket()
        _thread.start_new_thread(self.bindSocket, ())

    def bindSocket(self):
        try:

            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sk:
                sk.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sk.bind(("0.0.0.0", int(conf.get('socket', 'port'))))
                sk.listen(5)
                print('socket server on port {port} ...'.format(port=19091))
                while True:
                    conn, address = sk.accept()  # 等待客户端连接
                    addr = "{0}:{1}".format(address[0], address[1])

                    self.socketClients.append({'address': addr, 'conn': conn, 'tag': ''})
                    _thread.start_new_thread(self.recv, (addr,))
        except Exception as err:
            print(err)
            pass

    def recv(self, addr):
        item = {}
        for client in self.socketClients:
            if client['address'] == addr:
                item = client
                conn = client['conn']
        if conn is not None:
            # conn.send('ok')
            while True:
                data = conn.recv(1024)
                # print(data)
                if data == b'':
                    self.closeClient(addr)
                    return
                msg = data.decode()
                # print(msg)
                msgJson = json.loads(msg)
                if msgJson['cmd'] == 'getLog':
                    pass
                elif msgJson['cmd'] == 'subscriber':
                    tags = item['tag'].split(',')
                    tags.append(msgJson['tag'])
                    item['tag'] = ','.join(tags)
                elif msgJson['cmd'] == 'close':
                    self.closeClient(addr)
                    return

    def closeClient(self, addr):
        for i in range(len(self.socketClients) - 1, -1, -1):
            if self.socketClients[i]['address'] == addr:
                self.socketClients[i]['conn'].close()
                del self.socketClients[i]

    def sendMsgToClient(self, addr, msg):
        for client in self.socketClients:
            if client['address'] == addr:
                conn = client['conn']
        if conn is not None:
            conn.send(msg)

    def errorListener(self, ev):
        name = ev.job_id
        item = self.getItem(name)
        taskDir = os.path.join(taskRootDir, name)
        if ev.exception:
            item['state'] = 'error'
            taskDir = os.path.join(taskRootDir, name)
            with open(taskDir + '/info.json', 'w', encoding='utf-8') as f:
                json.dump(item, f, indent=4)

    def jobExecuteListener(self, ev):
        name = ev.job_id
        item = self.getItem(name)
        if item['state'] != 'stop':
            item['state'] = 'await next run'
            item['nextRunTime'] = "{0}-{1}-{2} {3}:{4}:{5}".format(ev.scheduled_run_time.year,
                                                                   ev.scheduled_run_time.month,
                                                                   ev.scheduled_run_time.day,
                                                                   ev.scheduled_run_time.hour,
                                                                   ev.scheduled_run_time.minute,
                                                                   ev.scheduled_run_time.second)
            taskDir = os.path.join(taskRootDir, name)
            with open(taskDir + '/info.json', 'w', encoding='utf-8') as f:
                json.dump(item, f, indent=4)
        # print('job-execute',item)

    def jobPausedListener(self, ev):
        name = ev.job_id
        item = self.getItem(name)
        item['state'] = 'paused'
        item['nextRunTime'] = "{0}-{1}-{2} {3}:{4}:{5}".format(ev.scheduled_run_time.year, ev.scheduled_run_time.month,
                                                               ev.scheduled_run_time.day, ev.scheduled_run_time.hour,
                                                               ev.scheduled_run_time.minute,
                                                               ev.scheduled_run_time.second)
        taskDir = os.path.join(taskRootDir, name)
        with open(taskDir + '/info.json', 'w', encoding='utf-8') as f:
            json.dump(item, f, indent=4)
        # print('job-execute',item)

    def jobResumedListener(self, ev):
        name = ev.job_id
        item = self.getItem(name)
        item['state'] = 'await next run'
        item['nextRunTime'] = "{0}-{1}-{2} {3}:{4}:{5}".format(ev.scheduled_run_time.year, ev.scheduled_run_time.month,
                                                               ev.scheduled_run_time.day, ev.scheduled_run_time.hour,
                                                               ev.scheduled_run_time.minute,
                                                               ev.scheduled_run_time.second)
        taskDir = os.path.join(taskRootDir, name)
        with open(taskDir + '/info.json', 'w', encoding='utf-8') as f:
            json.dump(item, f, indent=4)
        # print('job-execute',item)

    def add(self, name, cron, path, commend, args, info, logPath,commandName,logBackupDay):
        taskDir = os.path.join(taskRootDir, name)
        if name is None or cron is None :
            return {"result": 0, "msg": "参数丢失"}
        else:
            # taskItems=task.getItems()
            for item in self.taskItems:
                if item['name'] == name:
                    return {"result": 0, "msg": "任务已经存在"}
            item = {'name': name, 'cron': cron, 'path': path, 'state': 'await run', 'nextRunTime': '', 'cmd': commend,
                    'args': args, 'info': info, 'logPath': logPath,'commandName':commandName,'logBackupDay':logBackupDay}

            self.taskItems.append(item)

            if os.path.exists(taskDir) == False:
                os.makedirs(taskDir)

            if logPath is not None and logPath!='' and  os.path.exists(logPath) == False:
                os.makedirs(logPath)

            with open(taskDir + '/info.json', 'w', encoding='utf-8') as f:
                json.dump(item, f, indent=4)
            self.addJob(item)
            return {"result": 1}

    def edit(self, name, cron, path, commend, args ,info, logPath,commandName,logBackupDay):
        taskDir = os.path.join(taskRootDir,name)
        if name is None or cron is None:
            return {"result": 0, "msg": "参数丢失"}
        else:
            item = {}
            isHas = False

            for i in range(0, len(self.taskItems)):
                if self.taskItems[i]['name'] == name:
                    if cron is not None and cron != '':
                        self.taskItems[i]['cron'] = cron
                    if path is not None and path != '':
                        self.taskItems[i]['path'] = path
                    if commend is not None and commend != '':
                        self.taskItems[i]['cmd'] = commend
                    if args is not None and args != '':
                        self.taskItems[i]['args'] = args
                    if info is not None and info != '':
                        self.taskItems[i]['info'] = info
                    if logPath is not None and logPath != '':
                        self.taskItems[i]['logPath'] = logPath
                    if commandName is not None and commandName != '':
                        self.taskItems[i]['commandName'] = commandName
                    if logBackupDay is not None and logBackupDay != '':
                        self.taskItems[i]['logBackupDay'] = logBackupDay
                    item = self.taskItems[i]
                    isHas = True

            if isHas:
                with open(taskDir + '/info.json', 'w', encoding='utf-8') as f:
                    json.dump(item, f, indent=4)

                self.scheduler.remove_job(name)
                self.addJob(item)

                return {"result": 1}
            else:
                return {"result": 0, "msg": '任务不存在'}

    def delete(self, name):
        taskDir = taskRootDir + '/' + name
        isHas = False
        for i in range(len(self.taskItems) - 1, -1, -1):
            if self.taskItems[i]['name'] == name:
                isHas = True
                if self.taskItems[i]['state'] == 'runing':
                    self.stop(name)
                del self.taskItems[i]
        if isHas:
            time.sleep(2)
            shutil.rmtree(taskDir)  # 递归删除文件夹
        else:
            return False
        return True

    def getItems(self):
        if len(self.taskItems) == 0:
            dirList = os.listdir(taskRootDir)  # 列出文件夹下所有的目录与文件
            for i in range(0, len(dirList)):
                path = os.path.join(taskRootDir, dirList[i])
                if os.path.isfile(path) == False:  # 如果是目录
                    with open(path + '/info.json', 'r') as f:
                        _taskItem = json.load(f)
                        self.taskItems.append(_taskItem)

        return self.taskItems

    def getItem(self, name):
        item = None
        for _task in self.taskItems:
            if _task['name'] == name:
                item = _task
        return item

    def load(self):
        _taskItems = self.getItems()
        for item in _taskItems:
            if item['state'] != 'stop':
                item['state'] = "await run"
                self.addJob(item)
        self.scheduler.start()
        jobs = self.scheduler.get_jobs()
        for job in jobs:
            for item in _taskItems:
                if item['name'] == job.id:
                    item['nextRunTime'] = "{0}-{1}-{2} {3}:{4}:{5}".format(job.next_run_time.year,
                                                                           job.next_run_time.month,
                                                                           job.next_run_time.day,
                                                                           job.next_run_time.hour,
                                                                           job.next_run_time.minute,
                                                                           job.next_run_time.second)
        # print(self.taskItems)

    def reload(self):
        self.scheduler.shutdown(wait=True)
        self.load()

    def addJob(self, item):
        try:
            cron = item['cron'].split(' ')
            self.scheduler.add_job(id=item['name'], func=self.runTask, trigger='cron', args=[item], year=cron[6],
                                   month=cron[4], day=cron[3], day_of_week=cron[5], hour=cron[2], minute=cron[1],
                                   second=cron[0], max_instances=1)
        except Exception as err:
            print("addJob task err:name={0},info={1}".format(item['name'], err))

    def stop(self, name):
        try:
            taskDir = os.path.join(taskRootDir, name)
            item = self.getItem(name)
            if item['state'] == 'runing':
                pid = item['pid']
                if platform.system() == "Windows":
                    os.kill(pid + 1, signal.SIGTERM)
                else:
                    os.kill(pid + 1, signal.SIGKILL)
                    # os.system("ps -ef | grep {0} | grep -v grep | awk '{print $2}' |sudo xargs kill -9".format(name))
                time.sleep(4)
                # os.kill(pid, signal.SIGTERM)
                # time.sleep(1)
            item['state'] = 'stop'
            with open(taskDir + '/info.json', 'w', encoding='utf-8') as f:
                json.dump(item, f, indent=4)
            self.scheduler.remove_job(name)
            time.sleep(1)
            return True
        except Exception as err:
            print("stop task err:name={0},info={1}".format(item['name'], err))
            return False

    def kill(self, name):
        try:
            taskDir = os.path.join(taskRootDir, name)
            item = self.getItem(name)
            if item['state'] == 'runing':
                pid = item['pid']
                if platform.system() == "Windows":
                    os.kill(pid + 1, signal.SIGTERM)
                else:
                    os.kill(pid + 1, signal.SIGKILL)
                time.sleep(4)
                # os.kill(pid, signal.SIGTERM)
                # time.sleep(1)
            item['state'] = 'await run'
            with open(taskDir + '/info.json', 'w', encoding='utf-8') as f:
                json.dump(item, f, indent=4)
            self.scheduler.remove_job(name)
            return True
        except Exception as err:
            print("kill task err:name={0},info={1}".format(item['name'], err))
            return False

    def killAllTask(self):
        try:
            _taskItems = self.getItems()
            for item in _taskItems:
                if item["state"] != "stop":
                    self.kill(item['name'])
            return ""
        except Exception as err:
            print("killAllTask err:{0}".format(err))
            return "err:{0}".format(err)

    def run(self, name):
        item = self.getItem(name)
        if item is not None:
            self.runTask(item)

    def start(self, name):
        item = self.getItem(name)
        cron = item['cron'].split(' ')
        if item['state'] == 'stop':
            item['state'] = 'await run'
            self.scheduler.add_job(id=item['name'], func=self.runTask, trigger='cron', args=[item], year=cron[6],
                                   month=cron[4], day=cron[3], day_of_week=cron[5], hour=cron[2], minute=cron[1],
                                   second=cron[0], max_instances=1)
            jobs = self.scheduler.get_jobs()
            for job in jobs:
                if item['name'] == job.id:
                    item['nextRunTime'] = "{0}-{1}-{2} {3}:{4}:{5}".format(job.next_run_time.year,
                                                                           job.next_run_time.month,
                                                                           job.next_run_time.day,
                                                                           job.next_run_time.hour,
                                                                           job.next_run_time.minute,
                                                                           job.next_run_time.second)

            taskDir = os.path.join(taskRootDir, name)
            with open(taskDir + '/info.json', 'w', encoding='utf-8') as f:
                json.dump(item, f, indent=4)
            return {"result": 1}
        else:
            return {"result": 0, "msg": '任务状态必须是stop才能再次运行'}

    def paused(self, name):
        item = self.getItem(name)
        item['state'] = 'paused'
        taskDir = os.path.join(taskRootDir, name)
        with open(taskDir + '/info.json', 'w', encoding='utf-8') as f:
            json.dump(item, f, indent=4)
        self.scheduler.pause_job(name)

    def resume(self, name):
        item = self.getItem(name)
        item['state'] = 'await run'
        taskDir = os.path.join(taskRootDir, name)
        with open(taskDir + '/info.json', 'w', encoding='utf-8') as f:
            json.dump(item, f, indent=4)
        self.scheduler.resume_job(name)

    def runTask(self, taskItem):
        if taskItem["state"] == "runing" or taskItem["state"] == "stop":
            return
        if taskItem["state"] == "error":
            self.kill(taskItem['name'])

        taskDir = os.path.join(taskRootDir, taskItem['name'])
        logDir = taskItem["logPath"]
        cmd = ""
        commandName = taskItem["commandName"]

        if taskItem['path'] is not None and taskItem['path'] != '':
            _path = taskItem['path'].split('.')
            ext = _path[len(_path) - 1]
            if commandName is None:
                if ext.lower() == 'py':
                    commandName = conf.get('base', 'pycmd')
                elif ext.lower() == 'js':
                    commandName = "node"

            cmd = '{0} {1} {2}'.format(commandName, taskItem['path'], taskItem['args'])

        if taskItem['cmd'] is not None and taskItem['cmd'] != '':
            cmd = taskItem['cmd']

        child = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)

        for i in range(0, len(self.taskItems)):
            if self.taskItems[i]['name'] == taskItem['name']:
                self.taskItems[i]['state'] = 'runing'
                self.taskItems[i]['pid'] = child.pid
                with open(taskDir + '/info.json', 'w', encoding='utf-8') as f:
                    json.dump(self.taskItems[i], f, indent=4)

        logger = logging.getLogger(taskItem['name'])

        while True:
            outbye = child.stdout.readline()
            if self.isStop:  # 监测停止信号
                print('任务关闭：' + taskItem['name'])
                # self.stop(taskItem['name'])
                child.kill()
                time.sleep(2)
                break
            elif outbye == b'':  # 内部报错退出
                if child.poll() is not None:
                    break
            else:

                # 获取运行日志
                if logDir is not None and logDir != "":
                    filename = time.strftime('%Y-%m-%d', time.localtime(time.time())) + '.log'
                    filename = os.path.join(logDir, filename)
                    handler = logging.FileHandler(filename, mode='a', encoding='utf-8')
                    logger.addHandler(handler)
                    logger.setLevel(logging.INFO)
                    try:
                        outStr = outbye.decode('utf-8')
                    except Exception as err:
                        outStr = outbye.decode('gbk')
                    # print(outStr)
                    data = outStr.replace('\r\n', '')
                    message = time.strftime(
                        '%Y-%m-%d %H:%M:%S', time.localtime(time.time())) + ":" + data
                    logger.info(message)
                    logger.removeHandler(handler)  # 在记录日志之后移除句柄

                    # print(message)
                    for client in self.socketClients:
                        if client['tag'].index(taskItem['name']):
                            conn = client['conn']
                            conn.send(message.encode())



    def removeLog(self, taskItem):
        logDir = taskItem["logPath"]
        logBackupDay = taskItem["logBackupDay"]

        if logDir is None or logDir == "":
            return
        if logBackupDay is None:
            logBackupDay = 7

        now = datetime.now()
        dirList = os.listdir(logDir)  # 列出文件夹下所有的目录与文件
        deleteFileName = []
        for n in dirList:
            timeStr = n.replace('.log', '')
            time = datetime.strptime(timeStr, "%Y-%m-%d")
            span = (now - time).days
            if span > logBackupDay:
                deleteFileName.append(n)

        for fileName in deleteFileName:
            filePath = os.path.join(logDir, fileName)
            os.remove(filePath)

    def sigint_handler(self, signum, frame):
        # print("sigint_handler",signum,frame)
        print('请稍等，正在关闭task-manage服务')
        self.isStop = True
        time.sleep(2)
        self_pid = os.getpid()
        try:
            pidFilePath = os.path.join(taskRootDir, 'pid')
            if os.path.exists(pidFilePath):
                os.remove(pidFilePath)
            if platform.system() == "Windows":
                os.kill(self_pid, signal.SIGTERM)
            else:
                os.kill(self_pid, signal.SIGKILL)
        finally:
            print('task-manage 服务关闭')
