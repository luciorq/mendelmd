from django.core.management.base import BaseCommand, CommandError
from individuals.models import Individual
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import gzip
import os

class Command(BaseCommand):
    help = 'Closes the specified poll for voting'

    def add_arguments(self, parser):
        parser.add_argument('individual_id', nargs='+', type=int)

    def handle(self, *args, **options):
        for individual_id in options['individual_id']:
            try:
                individual = Individual.objects.get(pk=individual_id)
            except Individual.DoesNotExist:
                raise CommandError('Individual "%s" does not exist' % individual_id)

            vcf = individual.vcf_file
            filename = str(vcf)
            dir = os.path.dirname(filename)
            # create directory if it does not exist
            if not os.path.exists(dir):
                os.makedirs(dir)
            #print(individual.vcf_file)
            #print(dir(individual.vcf_file))
            #print(individual.vcf_file)
            #if str(individual.vcf_file).endswith('.gz'):
            #    print('gz file!')
                #file = open('test.vcf.gz')
                #file.write(vcf)
            with open(filename, 'wb') as f:
                f.write(vcf.read())

            #individual.vcf_file.save('sample.vcf.gz', ContentFile('content'))
            #poll.opened = False
            #poll.save()

            self.stdout.write(self.style.SUCCESS('Successfully closed poll "%s"' % individual_id))
