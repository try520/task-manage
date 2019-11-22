# task-manage
一个轻量级的定时任务执行系统，支持python，nodejs,以及一切命令行任务

## 安装
```
pip install task-manage
```

##使用方法

### 服务启动
```
tm runserver
```

### 服务停止
```
tm stopserver
```

### 查看任务列表
```
tm ls
```

### 添加任务 具体参数查看 tm add --help
```
tm add
```
Options:
  -l, --log PATH        日志文件目录路径
  -p, --path PATH       执行的文件路径
  -i, --info TEXT       任务描述信息
  -a, --args TEXT       执行命令时携带的参数 需打双引号
  -cmd, --command TEXT  cmd命令,需打双引号
  -c, --cron TEXT       cron表达式,需打双引号
  -n, --name TEXT       任务名称
  -f, --file PATH       json配置文件
  --help                Show this message and exit.

每5秒执行一次 /opt/app/src/test.py
```
tm add -n test -c "0/5 * * * * * *" -p /opt/app/src/test.py
```
或者

```
tm add -n test -c "0/5 * * * * * *" -cmd "python3 /opt/app/src/test.py"
```

通过配置文件执行
如 tm.json
```json
[
    {
        name:'test',
        cron:"0/5 * * * * * *",
        path:"/opt/app/src/test.py",
        cmd:"",
        args:"",
        logpath:"/opt/app/logs",
        info:"this is a demo"
    }
]
```

```
tm add -f tm.json
```

### 编辑任务 具体参数查看 tm edit --help
Options:
  -l, --log PATH        日志文件目录路径
  -a, --args TEXT       执行命令时携带的参数 需打双引号
  -cmd, --command TEXT  cmd命令,需打双引号
  -p, --path PATH       执行的文件路径
  -i, --info TEXT       任务描述信息
  -c, --cron TEXT       cron表达式
  -n, --name TEXT       任务名称  [required]
  --help                Show this message and exit.

```
tm edit -n test -c "0/10 * * * * * *"
```

### 停止任务
```
tm stop -n test
```

### 开始任务
```
tm start -n test
```

### 暂停任务
```
tm paused -n test
```

### 恢复暂停中的任务
```
tm resume -n test
```

### 立即执行任务
```
tm run -n test
```

### 删除任务
```
tm delete -n test
```

### 查看任务日志
```
tm log -n test
```

