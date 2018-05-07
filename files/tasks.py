# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from celery import shared_task


from files.models import File
from tasks.models import Task

from django.conf import settings  # noqa

from settings.models import S3Credential
import boto3

from subprocess import run
import os

def import_files():
    credentials = S3Credential.objects.all()
    for credential in credentials:
        print(credential)

@shared_task()
def download_file(task_id):

    task = Task.objects.get(id=task_id)

    task_location = '{}/run_tasks/tasks/{}/'.format(settings.BASE_DIR, task.id)
    command = 'mkdir -p %s' % (task_location)
    run(command, shell=True)

    os.chdir(task_location)

    file = File.objects.get(pk=task.manifest['file'])

    if file.location.startswith('ftp://'):

        basename = os.path.basename(file.location)
        if not os.path.exists('input/{}'.format(basename)):
            command = 'wget -P input/ {}'.format(file.location)
            run(command, shell=True)

            command = 'md5sum input/{}'.format(basename)
            output = check_output(command, shell=True).decode('utf-8').split()[0]

            file.md5 = output
            
            file.url = file.location
            file.status = 'downloaded'
            file.save()
