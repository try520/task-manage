# task-manage
一个轻量级的定时任务执行系统，支持python，nodejs,以及一切命令行任务

## 安装
```python
pip install task-manage
```

##使用方法

### 服务启动
```python
tm runserver
```

### 服务停止
```python
tm stopserver
```

### 查看任务列表
```python
tm ls
```

### 添加任务 具体参数查看 tm add --help
```python
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
```python
tm add -n test -c "0/5 * * * * * *" -p /opt/app/src/test.py
```
或者

```python
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

```python
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

```python
tm edit -n test -c "0/10 * * * * * *"
```

### 停止任务
```bash
tm stop -n test
```