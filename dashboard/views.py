from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect


import os
# Create your views here.
from individuals.models import Individual
from django.contrib import messages
from django.conf import settings
from django.utils.text import slugify
from individuals.tasks import *

from tasks.models import Task
from tasks.tasks import annotate_vcf

def index(request):
    if request.user.is_staff:
        individuals = Individual.objects.all().order_by('-id')
    elif request.user.is_authenticated:
        individuals = Individual.objects.filter(user=request.user).order_by('-id')
    else:
        individuals = Individual.objects.filter(user=None).order_by('-id')

    return render(request, 'dashboard/dashboard.html', {'individuals':individuals})

@login_required
def bulk_action(request):
    if request.method == 'POST':
        individuals = request.POST.getlist('individuals')
        print(individuals)
        individuals = list(reversed([int(x) for x in individuals]))
        print(individuals)

        if request.POST['selectionField'] == "Show":
            for individual_id in individuals:
                individual = get_object_or_404(Individual, pk=individual_id)
                individual.featured = True
                individual.save()
        if request.POST['selectionField'] == "Hide":
            for individual_id in individuals:
                individual = get_object_or_404(Individual, pk=individual_id)
                individual.featured = False
                individual.save()
        if request.POST['selectionField'] == "Delete":
            for individual_id in individuals:
                individual = get_object_or_404(Individual, pk=individual_id)

                individual_id = individual.id
                if individual.user:
                    username = individual.user.username
                else:
                    username = 'public'
                #delete files
                if individual.vcf_file:
                    individual.vcf_file.delete()
                # if individual.strs_file:
                #     individual.strs_file.delete()
                # if individual.cnvs_file:
                #     individual.cnvs_file.delete()
                os.system('rm -rf %s/genomes/%s/%s' % (settings.BASE_DIR, slugify(username), individual_id))

                individual.delete()
            messages.add_message(request, messages.INFO, "Individuals deleted with success!")
            #os.system('rm -rf mendelmd14/site_media/media/genomes/%s/%s' % (username, individual_id))
        if request.POST['selectionField'] == "Populate":
            for individual_id in individuals:
                individual = get_object_or_404(Individual, pk=individual_id)
                PopulateVariants.delay(individual.id)

        if request.POST['selectionField'] == "Annotate":
            for individual_id in individuals:
                individual = get_object_or_404(Individual, pk=individual_id)
                individual.status = 'new'
                individual.n_lines = 0
                individual.save()
                task = Task(user=request.user)
                task.name = 'Annotate Individual %s' % (individual.name)
                task.status= 'new'
                task.type = 'annotation'
                task.save()
                task.individuals.add(individual)
                annotate_vcf.delay(task.id)
                # AnnotateVariants.delay(individual.id)
        if request.POST['selectionField'] == "Find_Medical_Conditions_and_Medicines":
            for individual_id in individuals:
                individual = get_object_or_404(Individual, pk=individual_id)
                Find_Medical_Conditions_and_Medicines.delay(individual.id)

    return redirect('dashboard')
