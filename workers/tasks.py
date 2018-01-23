# Create your tasks here
from __future__ import absolute_import, unicode_literals

from django.conf import settings  # noqa
from celery import Celery
app = Celery('mendelmd')

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

from tasks.models import Task
from workers.models import Worker
from django.db.models import Q
# from scripts.worker import IWorker

from subprocess import run, check_output

@app.task(queue="master")
def check_queue():
    #check tasks and launch workers if necessary
    print('Check Queue')
    max_workers = 55
    tasks = Task.objects.filter(status='new')
    workers = Worker.objects.filter(~Q(status='terminated'))
    n_tasks = len(tasks)
    n_workers = len(workers)
    print(n_tasks, n_workers)
    #if more tasks than workers, launch more workers
    if n_tasks > n_workers and n_workers < max_workers:
        n_workers_to_launch = min(n_tasks, max_workers - n_workers)
        print('Launch Workers', n_workers_to_launch)
        for i in range(0,n_workers_to_launch):
            launch_worker.delay()
    #if more workers than tasks, terminate workers
    if n_tasks < n_workers:
        print('Terminate Workers')
        terminate_workers()

@app.task(queue="master")
def launch_worker():
    #create workers
    worker = Worker()
    worker.name = 'New Worker'
    worker.status = 'new'
    worker.save()

    worker_result = IWorker().launch()
    worker.ip = worker_result['ip']
    worker.worker_id = worker_result['id']
    worker.save()
    install_worker.delay(worker.id)


@app.task(queue="master")
def launch_workers(n_workers, type):
    #create workers
    workers = []
    for i in range(0, int(n_workers)):
        worker = Worker()
        worker.name = 'New Worker'
        worker.type = type
        worker.status = 'new'
        worker.save()
        workers.append(worker)

    for i, worker in enumerate(workers):
        print('Launch ', i)
        # launch new worker
        worker_result = IWorker().launch(type)
        worker.ip = worker_result['ip']
        worker.worker_id = worker_result['id']
        worker.save()
        install_worker.delay(worker.id)

@app.task(queue="master")
def terminate_workers():
    idle_workers = Worker.objects.filter(status='idle')
    for worker in idle_workers:
        print('Terminate Worker')
        # command = '' % (worker.worker_id)
        run(command, shell=True)
        print('Terminate Worker', worker.id)
        worker.status = 'terminated'
        worker.save()

@app.task(queue="master")
def terminate_worker(worker_id):
    worker = Worker.objects.get(id=worker_id)
    # command = '' % (worker.worker_id)
    run(command, shell=True)
    print('Terminate Worker', worker.id)
    worker.status = 'terminated'
    worker.save()

@app.task(queue="master")
def install_worker(worker_id):
    worker = Worker.objects.get(id=worker_id)
    
    print('Install Worker', worker.id)

    # if worker.type =='qc':    
    command = "scp %s scripts/install_worker_ubuntu.sh ubuntu@%s:~/" % (worker.ip)
    run(command, shell=True)

    command = "scp %s scripts/qc_wrapper.sh ubuntu@%s:~/" % (worker.ip)
    run(command, shell=True)

    command = """bash qc_wrapper.sh 2>&1 & sleep 2"""
    command = """ssh %s -t ubuntu@%s '%s'""" % (
        params, worker.ip, command)
    
    print(command)

    run(command, shell=True)

@app.task(queue="master")
def update_workers():

    workers = Worker.objects.all()
    for worker in workers:

        ip = worker.ip
        # print(worker.status)
        # command = """top -b -n 10 -d.2 | grep 'Cpu' |  awk 'NR==3{ print($2)}'"""
        # command = 'top -b -n 1 | head -n 10'
        command = 'top -bcn1 -w512 | head -n 10'
        
        command = """ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null ubuntu@%s %s""" % (ip,command)
        output = check_output(command, shell=True)
        # print(output.decode('utf-8'))
        text = output.decode('utf-8').splitlines()

        process_list_started = False
        for line in text:
            # print(line)
            if line.startswith('%Cpu(s)'):
                cpu_usage = line.split()[0]

            if process_list_started:
                process = line
                break

            if line.startswith('  PID USER'):
                process_list_started = True
            
        # print(process.split())
        rows = process.split()
        current_process = ' '.join(rows[10:])
        output = '{} {}'.format(cpu_usage, current_process)
        # print(output)
        worker.current_status = output
        worker.save()