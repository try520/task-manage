#!/usr/bin/python3

import os
import json
import sys
import platform
import configparser
import signal

here = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.join(here,'../')) 
from server.bottle import request, route, run, template
from server.task import Task

task = Task()
task.load()
conf = configparser.ConfigParser()
if platform.system() =="Windows":
    conf.read(os.path.join(here,'../config','config.win.cfg'))
else:
    conf.read(os.path.join(here,'../config','config.cfg'))

taskRootDir=os.path.join(here,"../task")

webPort =conf.get('web','port')

@route('/server/stop', method='GET')
def stopServer():
    try:
        ret = task.killAllTask()
        if ret=="":
            
            return json.dumps({"result": 1})
        else:
            return json.dumps({"result": 0,"msg":ret})
    except Exception as err:
        return json.dumps({"result": 0,"msg":err})

@route('/task/getItems', method='GET')
def getTaskItems():
    try:
        taskItems = task.getItems()
        return json.dumps({"result": 1, "data": taskItems})
    except Exception as err:
        return json.dumps({"result": 0, "msg": "Error:{0}".format(err)})


@route('/task/getItem/<name>', method='GET')
def getTaskItem(name):
    try:
        item = task.getItem(name)
        return json.dumps({"result": 1, "data": item})
    except Exception as err:
        return json.dumps({"result": 0, "msg": "Error:{0}".format(err)})


@route('/task/add', method='POST')
def add():
    try:
        name = request.forms.get('name')
        cron = request.forms.get('cron')
        path = request.forms.get('path')
        cmd = request.forms.get('cmd')
        args = request.forms.get('args')
        logPath=request.forms.get('logPath')
        info =request.forms.info
        ret = task.add(name, cron, path, cmd, args,info,logPath)
        return json.dumps(ret)
    except Exception as err:
        return json.dumps({"result": 0, "msg": "Error:{0}".format(err)})


@route('/task/edit', method='POST')
def edit():
    try:
        name = request.forms.get('name')
        cron = request.forms.get('cron')
        path = request.forms.get('path')
        cmd = request.forms.get('cmd')
        args = request.forms.get('args')
        info =request.forms.get('info')
        logPath = request.forms.get('logPath')
        ret = task.edit(name, cron, path, cmd, args,info,logPath)
        return json.dumps(ret)
    except Exception as err:
        return json.dumps({"result": 0, "msg": "Error:{0}".format(err)})


@route('/task/delete', method='POST')
def delete():
    try:
        name = request.forms.get('name')
        if name is None:
            return json.dumps({"result": 0, "msg": '参数丢失'})
        else:
            ret = task.delete(name)
            if ret:
                return json.dumps({"result": 1})
            else:
                 return json.dumps({"result": 0,'msg':'任务不存在'})
    except Exception as err:
        return json.dumps({"result": 0, "msg": "Error:{0}".format(err)})


@route('/task/stop', method='POST')
def stop():
    try:
        name = request.forms.get('name')
        if name == None:
            return json.dumps({"result": 0, "msg": '参数丢失'})
        else:
            task.stop(name)
            return json.dumps({"result": 1})
    except Exception as err:
        return json.dumps({"result": 0, "msg": "Error:{0}".format(err)})


@route('/task/start', method='POST')
def start():
    try:
        name = request.forms.get('name')
        if name == None:
            return json.dumps({"result": 0, "msg": '参数丢失'})
        else:
            task.start(name)
            return json.dumps({"result": 1})
    except Exception as err:
        return json.dumps({"result": 0, "msg": "Error:{0}".format(err)})

@route('/task/run', method='POST')
def runTask():
    try:
        name = request.forms.get('name')
        if name == None:
            return json.dumps({"result": 0, "msg": '参数丢失'})
        else:
            task.run(name)
            return json.dumps({"result": 1})
    except Exception as err:
        return json.dumps({"result": 0, "msg": "Error:{0}".format(err)})

@route('/task/paused', method='POST')
def paused():
    try:
        name = request.forms.get('name')
        if name == None:
            return json.dumps({"result": 0, "msg": '参数丢失'})
        else:
            task.paused(name)
            return json.dumps({"result": 1})
    except Exception as err:
        return json.dumps({"result": 0, "msg": "Error:{0}".format(err)})


@route('/task/resume', method='POST')
def resume():
    try:
        name = request.forms.get('name')
        if name is None:
            return json.dumps({"result": 0, "msg": '参数丢失'})
        else:
            task.resume(name)
            return json.dumps({"result": 1})
    except Exception as err:
        return json.dumps({"result": 0, "msg": "Error:{0}".format(err)})


pidFilePath =os.path.join(taskRootDir,'pid')
with open(pidFilePath, 'w', encoding='utf-8') as f:
    f.write(str(os.getpid()))
run(host='0.0.0.0', port=int(webPort), debug=False, reloader=False)



