# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from celery import shared_task

from files.models import File
from .models import Task as Taskobj

import urllib.request, os

from projects.models import ProjectFile

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
from workers.tasks import launch_worker, launch_workers, terminate_workers

import os
from subprocess import run, check_output
import subprocess

from individuals.tasks import parse_vcf
from individuals.models import Individual
from variants.models import Variant

from django.core.mail import send_mail

import zipfile
import gzip
import datetime
import time
import socket
import json

from urllib.parse import urlparse

from ftplib import FTP, FTP_TLS
import ftplib

from mapps.models import App
from helpers import b2_wrapper
from helpers.aws_wrapper import AWS

b2 = b2_wrapper.B2()

import csv
from contextlib import closing
from io import StringIO
from django.db import connection

@shared_task()
def get_file(file):
    if file.location.startswith('ftp://'):

        basename = os.path.basename(file.location)
        if not os.path.exists('input/{}'.format(basename)):
            command = 'wget -P input/ {}'.format(file.location)
            run(command, shell=True)

            command = 'md5sum input/{}'.format(basename)
            output = check_output(command, shell=True).decode('utf-8').split()[0]

            file.md5 = output
            #upload to b2
            command = 'b2 upload_file mendelmd input/{} files/{}/{}'.format(basename, file.id, basename)
            output = check_output(command, shell=True)
            
            print(output.decode('utf-8'))
            
            file.params = output.decode('utf-8')
            file.url = file.location
            file.location = 'b2://mendelmd/files/{}/{}'.format(file.id, basename)
            file.save()
    elif file.location.startswith('b2://'):

        basename = os.path.basename(file.location)

        if not os.path.exists('input/{}'.format(basename)):

            b2_location = file.location.replace('b2://mendelmd/','')
            command = 'b2 download-file-by-name mendelmd {} input/{}'.format(b2_location, basename)
            output = check_output(command, shell=True)
            print(output.decode('utf-8'))


    return(file)
    # file = File.objects.get(pk=project_file_id)
    # link = file.location

def calculate_md5(path):
    md5_dict = {}
    files = os.listdir(path)
    for file in files:
        command = 'md5sum output/{}'.format(file)
        output = check_output(command, shell=True).decode('utf-8').split()[0]
        file_md5 = output
        md5_dict[file_md5] = file
    return(md5_dict)

@shared_task()
def task_run_task(task_id):
    print('RUN TASK: ', task_id)
    log_output = ''

    task = Task.objects.get(id=task_id)
    
    task.output = ''
    
    start = datetime.datetime.now()
    manifest = task.manifest
    # task.machine = socket.gethostbyname(socket.gethostname())
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    task.machine = s.getsockname()[0]
    s.close()
    task.status = 'running'
    task.started = start
    task.save()

    worker = Worker.objects.filter(ip=socket.gethostbyname(socket.gethostname())).reverse()[0]
    worker.n_tasks += 1 
    worker.status = 'running task %s' % (task.id)
    worker.started = start
    worker.save()


    task_location = '/projects/tasks/%s/' % (task.id)
    command = 'mkdir -p %s' % (task_location)
    run(command, shell=True)

    command = 'mkdir -p %s/input' % (task_location)
    run(command, shell=True)

    command = 'mkdir -p %s/output' % (task_location)
    run(command, shell=True)

    command = 'mkdir -p %s/scripts' % (task_location)
    run(command, shell=True)


    os.chdir(task_location)

    with open('manifest.json', 'w') as fp:
        json.dump(manifest, fp, sort_keys=True,indent=4)
    # file_list = []

    # for file_id in manifest['files']:        
    #     print(file_id)
    #     file = File.objects.get(pk=file_id)        
    #     file = get_file(file)
        # file_list.append(file.name)

    #start analysis
    for analysis_name in manifest['analysis_types']:
        print('analysis_name', analysis_name)
        analysis = App.objects.filter(name=analysis_name)[0]
        print(analysis)

        
        command = 'mkdir -p /projects/programs/'
        run(command, shell=True)
        os.chdir('/projects/programs/')

        basename = os.path.basename(analysis.repository)
        print('basename', basename)
        
        command = 'git clone {}'.format(analysis.source)
        run(command, shell=True)

        os.chdir(basename)

        # install
        command = 'bash scripts/install.sh'
        output = check_output(command, shell=True)

        log_output += output.decode('utf-8')
        #run
        
        os.chdir(task_location)
        command = 'python /projects/programs/{}/main.py -i {}'.format(basename, ' '.join(manifest['files']))
        print(command)
        output = run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        log_output += output.stdout.decode('utf-8')

    AWS.upload(task_location+'/output', task.id)

    #upload results to b2/s3
    # md5_dict = calculate_md5('output/')
    # for hash in md5_dict:
    #     print(hash)
    #     try:
    #         file = File.objects.get(md5=hash)
    #     except:
    #         pass
    #         file = File(user=task.user)
    #         file.md5 = hash
    #         file.name = md5_dict[hash]
    #         file.save()

    #         source = 'output/{}'.format(file.name)
    #         dest = 'files/{}/{}'.format(file.id, file.name)

    #         output = b2.upload(source, dest)
            
    #         file.params = output
    #         file.location = 'b2://mendelmd/files/{}/{}'.format(file.id, file.name)
    #         file.save()    
    #         # if task.analysis:
    #         #     task.analysis_set.all()[0].files.add(file)
    #     task.files.add(file)

    # add files if needed :)

    task.status = 'done'
    stop = datetime.datetime.now()
    task.execution_time = str(stop - start)
    task.finished = stop
    task.output = log_output
    task.save()

    worker = Worker.objects.filter(ip=socket.gethostbyname(socket.gethostname())).reverse()[0]
    worker.n_tasks -= 1
    if worker.n_tasks == 0:
        worker.status = 'idle'
    worker.finished = stop
    worker.execution_time = str(stop - start)
    worker.save()
    print('Finished Task %s' % (task.name))

@app.task(queue="qc")
def run_qc(task_id):

    print('RUN QC :D')
    print('task_id', task_id)

    task = Task.objects.get(id=task_id)
    task.status = 'will be running'
    task.save()
    start = datetime.datetime.now()

    manifest = task.manifest

    task.machine = ''
    task.status = 'running'
    task.started = start
    task.save()

    # worker = Worker.objects.filter(ip=socket.gethostbyname(socket.gethostname())).reverse()[0]
    # worker.n_tasks += 1 
    # worker.status = 'running task %s' % (task.id)
    # worker.started = start
    # worker.save()

    task_location = '/projects/tasks/%s/' % (task.id)
    command = 'mkdir -p %s' % (task_location)
    run(command, shell=True)

    os.chdir(task_location)

    with open('manifest.json', 'w') as fp:
        json.dump(manifest, fp, sort_keys=True,indent=4)
    

    task.status = 'done'
    stop = datetime.datetime.now()
    task.execution_time = str(stop - start)
    task.finished = stop
    task.save()

    # worker = Worker.objects.filter(ip=socket.gethostbyname(socket.gethostname())).reverse()[0]
    
    # worker.n_tasks -= 1

    # if worker.n_tasks == 0:
    #     worker.status = 'idle'

    # worker.finished = stop
    # worker.execution_time = str(stop - start)
    # worker.save()

    print('Finished QC %s' % (task.name))


@shared_task()
def import_project_files_task(project_id):
    print('Import Files on ', project_id)

def human_size(bytes, units=[' bytes','KB','MB','GB','TB', 'PB', 'EB']):
    """ Returns a human readable string reprentation of bytes"""
    return str(bytes) + units[0] if bytes < 1024 else human_size(bytes>>10, units[1:])

from multiprocessing import Lock
L = Lock()


@shared_task()
def check_file(task_id):
    global mutex
    task = Taskobj.objects.get(pk=task_id)

    task.status = 'started'
    task.save()

    manifest = task.manifest
    file_id = manifest['file']
    print('File ID', file_id)

    file = File.objects.get(pk=file_id)

    if file.location.startswith('ftp://'):
        print('ftp')
        print(file.location)

     
        file.name = os.path.basename(file.location)

        command = 'curl -sI {} | grep Content-Length'.format(file.location)
        output = check_output(command, shell=True)

        # print()
        size = output.split()[1]

        file.size = int(size)
        # file.human_size = human_size(file.size)



    elif file.location.startswith('http'):
        link = file.location
        print('link', link)
        print('link', link.strip())
        print('link', link.encode())

        file.name = os.path.basename(link)
        
        site = urllib.request.urlopen(link)
        file_size = site.info()['Content-Length']
        file.size = int(file_size)
        # file.human_size = human_size(int(file_size))
        
    elif file.location.startswith('/'):

        path = '/'.join(file.location.split('/')[:-1])

        command = 'ls -lah {}'.format(path)
        output = check_output(command, shell=True)
        file.last_output = output.decode('utf-8')

        filename, file_extension = os.path.splitext(file.location)

        if file_extension in ['.gz', '.zip', '.rar', 'bz2', '.7z']:
            compression = file_extension
            filename, file_extension  = os.path.splitext(filename)
            file_extension += compression

        file.extension = file_extension

        command = 'file {}'.format(file.location)
        output = check_output(command, shell=True)
        file.file_type = ' '.join(output.decode('utf-8').strip().split(' ')[1:])

        file.name = os.path.basename(file.location)
        # print(os.stat(file.location))
        # print(os.path.getsize(file.location))
        file.size = int(os.path.getsize(file.location))

    print('File Name', file.name)
    file.status = 'checked'
    file.save()

    task.status = 'done'
    task.save()


@shared_task()
def compress_file(task_id):

    task = Taskobj.objects.get(pk=task_id)

    task.status = 'started'
    task.save()

    manifest = task.manifest
    file_id = manifest['file']
    print('File ID', file_id)

    file = File.objects.get(pk=file_id)
        
    if file.location.startswith('/'):

        path = '/'.join(file.location.split('/')[:-1])

        command = 'bgzip {}'.format(file.location)

        output = check_output(command, shell=True)
        
        file.last_output = output.decode('utf-8')
        file.location += '.gz'

    file.save()

    task.status = 'done'
    task.save()

@app.task(queue="annotation")
def annotate_vcf(task_id):

    start = datetime.datetime.now()

    task = Task.objects.get(id=task_id)
    
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    task.machine = s.getsockname()[0]

    task.status = 'running'
    task.started = start
    task.save()

    print('Annotate VCF', task.id)
    individual = task.individuals.all()[0]
    print(individual.location)

    path, vcf = os.path.split(individual.location)

    task_location = '/projects/tasks/%s/' % (task.id)
    command = 'mkdir -p %s' % (task_location)
    run(command, shell=True)
    os.chdir(task_location)

    # if not os.path.exists('%s/output/gatk'):
    # os.makedirs(directory)

    #get vcf from remote location
    worker = AWS()
    worker.get(individual.location, task.id)
    #annotate it

    filename = vcf.strip()

    if filename.endswith('.vcf'):
        command = 'cp %s sample.vcf' % (filename)
        os.system(command)
    if filename.endswith('.gz'):
        command = 'gunzip -c -d %s > sample.vcf' % (filename)
        os.system(command)
    if filename.endswith('.zip'):
        command = 'unzip -p %s > sample.vcf' % (filename)
        os.system(command)
    if filename.endswith('.rar'):
        command = 'unrar e %s' % (filename)
        os.system(command)
        #now change filename to sample.vcf
        command = 'mv %s sample.vcf' % (filename.replace('.rar', ''))
        os.system(command)



    command = 'pynnotator -i sample.vcf'
    run(command, shell=True)

    final_file = 'ann_sample/annotation.final.vcf'
    if os.path.exists(final_file):

        command = 'zip annotation.final.vcf.zip ann_sample/annotation.final.vcf'
        run(command, shell=True)

        #send results to s3
        print('Send to S3')
        local = '/projects/tasks/%s/annotation.final.vcf.zip' % (task.id)
        worker.upload(local,individual.id)
        stop = datetime.datetime.now()
        elapsed = stop - start
        individual.annotation_time = elapsed
        individual.status = 'annotated'
        individual.save()
        task.status = 'annotated'
        # task.execution_time = elapsed
        task.save()

        task_location = '/projects/tasks/%s/' % (task.id)
        command = 'rm -rf %s' % (task_location)
        run(command, shell=True)
        #add insertion task
        insert_vcf.delay(task.id)
    else:
        task.status = 'failed'
        task.retry += 1
        task.save()
        annotate_vcf.delay(task.id)

@app.task(queue="insertion")
def insert_vcf(task_id):
    
    task = Task.objects.get(pk=task_id)
    individual = task.individuals.all()[0]

    vcf = '/projects/tasks/%s/annotation.final.vcf.zip' % (task.id)

    task_location = '/projects/tasks/%s/' % (task.id)
    command = 'mkdir -p %s' % (task_location)
    run(command, shell=True)
    os.chdir(task_location)

    annotation_file = '{}{}/annotation.final.vcf.zip'.format(settings.UPLOAD_FOLDER, individual.id)

    worker = AWS()

    if not os.path.isfile(vcf):
        worker.get(annotation_file, task.id)
    
    task_location = '/projects/tasks/%s/' % (task.id)
    command = 'mkdir -p %s' % (task_location)
    run(command, shell=True)
    os.chdir(task_location)

    #delete variants from individual before inserting
    Variant.objects.filter(individual=individual).delete()
    #SnpeffAnnotation.objects.filter(individual=individual).delete()
    #VEPAnnotation.objects.filter(individual=individual).delete()

    filepath = '/projects/tasks/%s' % (task.id)

    print('Populating %s' % (individual.id))

    z = zipfile.ZipFile('%s/annotation.final.vcf.zip' % (filepath), 'r')
    data = z.open('ann_sample/annotation.final.vcf', 'r')

    start = datetime.datetime.now()
    count = 0
    variants = []
    count2 = 0

    snpeff_dict = {}
    vep_dict = {}

    # with open('annotation.final.sql', 'w') as sqlfile:
        # sqlfile.writelines('COPY public.variants_variant (individual_id, index, pos_index, chr, pos, variant_id, ref, alt, qual, filter, genotype, genotype_col, format, read_depth, gene, mutation_type, genomes1k_maf, gnomead_exome_maf, gnomead_genome_maf, dbsnp_build, sift, sift_pred, polyphen2, polyphen2_pred, cadd, hgmd_class, hgmd_phen, is_at_omim, snpeff_effect, snpeff_impact, snpeff_func_class, snpeff_codon_change, snpeff_aa_change) FROM stdin;\n')
    stream = StringIO()
    # stream = open('annotation.final.csv', 'w')
    writer = csv.writer(stream, delimiter='\t')
    # writer.writerow(['individual_id', 'index', 'pos_index', 'chr', 'pos', 'variant_id', 'ref', 'alt', 'qual', 'filter', 'genotype', 'genotype_col', 'format', 'read_depth', 'gene', 'vep_cds_position', 'mutation_type', 'genomes1k_maf', 'gnomead_exome_maf', 'gnomead_genome_maf', 'dbsnp_build', 'sift', 'sift_pred', 'polyphen2', 'polyphen2_pred', 'cadd', 'hgmd_class', 'hgmd_phen', 'is_at_omim', 'is_at_hgmd', 'snpeff_effect', 'snpeff_impact', 'snpeff_func_class', 'snpeff_codon_change', 'snpeff_aa_change'])
    for line in data:
        line = line.decode("utf-8", "ignore")
        if line != '':
            if not line.startswith('#'):
                if count > 10000:
                    # print(count2)
                    count = 0
                    stream.seek(0)
                    with closing(connection.cursor()) as cursor:
                        cursor.copy_from(
                            file=stream,
                            table='variants_variant',
                            sep='\t',
                            columns=('individual_id', 'index', 'pos_index', 'chr', 'pos', 'variant_id', 'ref', 'alt', 'qual', 'filter', 'genotype', 'genotype_col', 'format', 'read_depth', 'gene', 'vep_cds_position','mutation_type', 'genomes1k_maf', 'gnomead_exome_maf', 'gnomead_genome_maf', 'dbsnp_build', 'sift', 'sift_pred', 'polyphen2', 'polyphen2_pred', 'cadd', 'hgmd_class', 'hgmd_phen', 'is_at_omim', 'is_at_hgmd', 'snpeff_effect', 'snpeff_impact', 'snpeff_func_class', 'snpeff_codon_change', 'snpeff_aa_change'),
                            null='',
                        )
                    stream = StringIO()
                    # stream = open('annotation.final.csv', 'w')
                    writer = csv.writer(stream, delimiter='\t')
                count += 1
                count2 += 1
                    
                #now parse
                variant = parse_vcf(line)
                # variant_obj = Variant(
                #     individual=individual,
                #     index=variant['index'],
                #     pos_index=variant['pos_index'],
                #     chr=variant['chr'],
                #     pos=variant['pos'],
                #     variant_id=variant['variant_id'],
                #     ref=variant['ref'],
                #     alt=variant['alt'],
                #     qual=variant['qual'],
                #     filter=variant['filter'],
                #     genotype=variant['genotype'],
                #     genotype_col=variant['genotype_col'],
                #     format=variant['format'],
                #     read_depth=variant['read_depth'],
                #     gene=variant['gene'],
                #     vep_cds_position=variant['vep_cds_position'],
                #     mutation_type=variant['mutation_type'],
                #     genomes1k_maf=variant['1000g_af'],
                #     gnomead_exome_maf=variant['gnomead_exome_af'],
                #     gnomead_genome_maf=variant['gnomead_genome_af'],
                #     dbsnp_build=variant['dbsnp_build'],
                #     sift=variant['sift'],
                #     sift_pred=variant['sift_pred'],
                #     polyphen2=variant['polyphen2'],
                #     polyphen2_pred=variant['polyphen2_pred'],
                #     cadd=variant['cadd'],
                #     hgmd_class=variant['hgmd_class'],
                #     hgmd_phen=variant['hgmd_phen'],
                #     is_at_omim=variant['is_at_omim'],
                #     snpeff_effect=variant['effect'],
                #     snpeff_impact=variant['impact'],
                #     snpeff_func_class=variant['func_class'],
                #     snpeff_codon_change=variant['codon_change'],
                #     snpeff_aa_change=variant['aa_change']
                # )
                # variants.append(variant_obj)

                # for key in variant:
                #     variant[key] = str(variant[key])
                # writer.writerow(variant)
                # break
                writer.writerow([str(individual.id), variant['index'], variant['pos_index'], variant['chr'], variant['pos'], variant['variant_id'], variant['ref'], variant['alt'], variant['qual'], variant['filter'], variant['genotype'], variant['genotype_col'], variant['format'], variant['read_depth'], variant['gene'], variant['vep_cds_position'], variant['mutation_type'], variant['1000g_af'], variant['gnomead_exome_af'], variant['gnomead_genome_af'], variant['dbsnp_build'], variant['sift'], variant['sift_pred'], variant['polyphen2'], variant['polyphen2_pred'], variant['cadd'], variant['hgmd_class'], variant['hgmd_phen'], variant['is_at_omim'], variant['is_at_hgmd'], variant['effect'], variant['impact'], variant['func_class'], variant['codon_change'], variant['aa_change']])
                # variants.append(variant_obj)
    # Variant.objects.bulk_create(variants)
        # sqlfile.writelines('\.\n')
        # print('inserting ', count, ' rows')
        # command = 'psql -f annotation.final.sql mendelmd_dev'
        # run(command, shell=True)
    # Variant.objects.from_csv('annotation.final.csv', delimiter='\t', null='NULL')
    # Variant.objects.bulk_create(variants)
    stream.seek(0)
    with closing(connection.cursor()) as cursor:
        cursor.copy_from(
            file=stream,
            table='variants_variant',
            sep='\t',
            columns=('individual_id', 'index', 'pos_index', 'chr', 'pos', 'variant_id', 'ref', 'alt', 'qual', 'filter', 'genotype', 'genotype_col', 'format', 'read_depth', 'gene', 'vep_cds_position','mutation_type', 'genomes1k_maf', 'gnomead_exome_maf', 'gnomead_genome_maf', 'dbsnp_build', 'sift', 'sift_pred', 'polyphen2', 'polyphen2_pred', 'cadd', 'hgmd_class', 'hgmd_phen', 'is_at_omim', 'is_at_hgmd', 'snpeff_effect', 'snpeff_impact', 'snpeff_func_class', 'snpeff_codon_change', 'snpeff_aa_change'),
            null='',
        )
    # query = 'COPY public.databases_genome1ksamplevariant (id, genotype_id, sample_id, variant_id) FROM \'.csv' DELIMITER ',' CSV HEADER;'
    # Variant.objects.raw(query)


    stop = datetime.datetime.now()
    elapsed = stop - start

    individual.insertion_time = elapsed


    individual.status = 'populated'
    individual.n_lines = count2
    individual.save()

    stop = datetime.datetime.now()
    task.finished = stop
    task.status = 'populated'
    task.save()

    # message = """
    #         The individual %s was inserted to the database with success!
    #         Now you can check the variants on the link: \n
    #         http://mendelmd.org/individuals/view/%s
    #             """ % (individual.name, individual.id)

    print('Individual %s Populated!' % (individual.id))

    command = 'rm -rf %s' % (task_location)
    # run(command, shell=True)

    # command = 'rm -rf %s/ann_sample' % (filepath)
    # os.system(command)
