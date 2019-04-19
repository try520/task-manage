#!/usr/bin/python3
import click
import os
import sys
import json
import requests
import socket
import time
import signal
import platform
import shutil
import configparser  
from prettytable import PrettyTable
from time import sleep

here = os.path.abspath(os.path.dirname(__file__))#获取项目根目录
conf = configparser.ConfigParser()

sysstr = platform.system()
if sysstr =="Windows":
    conf.read(os.path.join(here,'../config','config.win.cfg'))
else:
	conf.read(os.path.join(here,'../config','config.cfg'))
apiUrl='http://127.0.0.1:19090'
taskDataPath=conf.get('base','taskdir')




@click.group()
def tm():
    pass

@click.command()
def startup():
    if sysstr =="Linux":
        sourceFile = os.path.join(here,  "../config/task-manage-svr.sh") 
        targetFile ="/etc/init.d/task-manage-svr.sh"
        shutil.copyfile(sourceFile,targetFile)
        if os.path.exists(targetFile):
            os.system("sudo chmod +x /etc/init.d/task-manage-svr.sh")
            os.system("sudo update-rc.d task-manage-svr.sh defaults 90")
            click.echo('设置开机启动成功')
        else:
            click.echo('服务创建失败')
    else:
        click.echo('不支持此系统')

@click.command()
def startdown():
    os.system("sudo update-rc.d -f task-manage-svr.sh remove")
    click.echo('服务移除成功')

@click.command()
def runserver():
    
    if sysstr =="Linux":
        os.system("nohup runtaskmanageserver &")
    else:
        os.system("runtaskmanageserver")
    click.echo('服务启动')

@click.command()
def stopserver():
    pidFilePath =os.path.join(taskDataPath,'pid')
    with open(pidFilePath, 'r', encoding='utf-8') as f:
	    pid=f.read()
    os.kill(int(pid),signal.SIGTERM)
    click.echo('服务终止')



@click.command()
def ls():
    ret = requests.get(url=apiUrl+'/task/getItems')
    data = ret.json()
    if data['result']==1:
        # click.echo(data['data'])
        tb = PrettyTable()
        tb.field_names = ["PID","名称", "计划周期", "状态", "下次运行时间","运行命令","路径","携带参数"]
        for item in data['data']:
            tb.add_row([item['pid'],item['name'],item['cron'], item['state'], item['nextRunTime'],item['cmd'],item['path'],item['args']])
        print(tb)
    else:
        click.echo(data['msg'])
    



@click.option('--file',  '-f', help='json配置文件',required=False)
@click.option('--name', '-n', help='任务名称',required=False)
@click.option('--cron',  '-c',  help='cron表达式,需打双引号', required=False)
@click.option('--command',  '-cmd',  help='cmd命令,需打双引号',required=False)
@click.option('--args',  '-a',  help='执行命令时携带的参数 需打双引号 ',required=False)
@click.option('--path','-p',type=click.Path(exists=True,resolve_path=True), help='执行的文件路径',required=False)
@click.command()
def add(name,cron,path,file,command,args):

    if file:
        pass
    else:
        pass
        if name == None or cron==None:
            click.echo('参数丢失 [-n] [-c]  或者 [--name] [--cron]')
        elif path==None and command==None:
            click.echo('参数丢失 [-p] [-cmd]  或者 [--path] [--command]')
        else:
           

            if path==None:
                path=""
            if args==None:
                args=""
            task={'name':name,'cron':cron,'path':path,'cmd':command,'args':args}
            ret = requests.post(url=apiUrl+'/task/add',data=task)
            retData=ret.json()

            if retData['result']==1:
                click.echo('添加成功')
            else:
                click.echo('添加失败:'+retData['msg'])

@click.option('--name', '-n', help='任务名称',required=True)
@click.option('--cron',  '-c', help='cron表达式',required=False)
@click.option('--path','-p',type=click.Path(exists=True,resolve_path=True), help='执行的文件路径',required=False)
@click.option('--command',  '-cmd',  help='cmd命令,需打双引号',required=False)
@click.option('--args',  '-a',  help='执行命令时携带的参数 需打双引号 ',required=False)
@click.command()
def edit(name,cron,path,command,args):
    if name==None :
        click.echo('参数丢失 [-n] [-c]  或者 [--name] [--cron]')
    else:
        task={'name':name,'cron':cron,'path':path,'cmd':command,'args':args}
        ret = requests.post(url=apiUrl+'/task/edit',data=task)
        retData=ret.json()
        if retData['result']==1:
            click.echo('修改成功')
        else:
            click.echo('修改失败:'+retData['msg'])
        


@click.option('--name', '-n', help='任务名称',required=True)
@click.command()
def stop(name):
    ret = requests.post(url=apiUrl+'/task/stop',data={"name":name})
    retData=ret.json()
    if retData['result']==1:
        click.echo('停止成功')
    else:
        click.echo('停止失败:'+retData['msg'])

@click.option('--name', '-n', help='任务名称',required=True)
@click.command()
def start(name):
    ret = requests.post(url=apiUrl+'/task/start',data={"name":name})
    retData=ret.json()
    if retData['result']==1:
        click.echo('开始成功')
    else:
        click.echo('开始失败:'+retData['msg'])

@click.option('--name', '-n', help='任务名称',required=True)
@click.command()
def paused(name):
    ret = requests.post(url=apiUrl+'/task/paused',data={"name":name})
    retData=ret.json()
    if retData['result']==1:
        click.echo('暂停成功')
    else:
        click.echo('暂停失败:'+retData['msg'])

@click.option('--name', '-n', help='任务名称',required=True)
@click.command()
def resume(name):
    ret = requests.post(url=apiUrl+'/task/resume',data={"name":name})
    retData=ret.json()
    if retData['result']==1:
        click.echo('恢复成功')
    else:
        click.echo('恢复失败:'+retData['msg'])

@click.option('--name', '-n', help='任务名称',required=True)
@click.command()
def run(name):
    ret = requests.post(url=apiUrl+'/task/run',data={"name":name})
    retData=ret.json()
    if retData['result']==1:
        click.echo('开始运行,正在获取运行日志')
    
    else:
        click.echo('运行失败:'+retData['msg'])

@click.option('--name', '-n', help='任务名称',required=True)
@click.command()
def delete(name):
    click.echo('正在停止任务...请稍等')
    ret = requests.post(url=apiUrl+'/task/delete',data={"name":name})
    retData=ret.json()
    if retData['result']==1:
        click.echo('删除成功')
    else:
        click.echo('删除失败:'+retData['msg'])

@click.option('--name', '-n', help='任务名称',required=True)
@click.command()
def log(name):
    logFileName = time.strftime('%Y-%m-%d', time.localtime(time.time()))+'.log'
    logFilePath = os.path.join(taskDataPath, name, 'log', logFileName)
    if os.path.exists(logFilePath):
        with open(logFilePath,'r') as f:
            lines =  f.readlines()
        if len(lines)<20:
            for line in lines:
                click.echo(line.strip('\n'))
        else:
            _lines=[]
        for i in range(len(lines)-1,len(lines)-20,-1):
            _lines.insert(0,lines[i])
        for line in _lines:
            click.echo(line.strip('\n'))

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sk:
        sk.connect(('127.0.0.1',19091))
        sk.send(json.dumps({"cmd": "subscriber", "tag": name}).encode())
        while True:
            data = sk.recv(1024)
            msg = data.decode()
            click.echo(msg)


tm.add_command(ls)
tm.add_command(start)
tm.add_command(stop)
tm.add_command(add)
tm.add_command(edit)
tm.add_command(delete)
tm.add_command(paused)
tm.add_command(resume)
tm.add_command(run)
tm.add_command(log)
tm.add_command(runserver)
tm.add_command(stopserver)
tm.add_command(startup)
tm.add_command(startdown)


if __name__ == '__main__':
    tm()
    
