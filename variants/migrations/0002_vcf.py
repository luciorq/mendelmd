# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-09-30 22:14
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('individuals', '0002_individual_location'),
        ('variants', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='VCF',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('index', models.TextField(db_index=True)),
                ('pos_index', models.TextField(db_index=True)),
                ('chr', models.TextField(db_index=True, verbose_name='Chr')),
                ('pos', models.IntegerField(db_index=True)),
                ('variant_id', models.TextField(db_index=True, verbose_name='ID')),
                ('ref', models.TextField(blank=True, db_index=True, null=True)),
                ('alt', models.TextField(blank=True, db_index=True, null=True)),
                ('qual', models.FloatField(db_index=True)),
                ('filter', models.TextField(db_index=True)),
                ('info', models.TextField(blank=True, null=True)),
                ('format', models.TextField(blank=True, db_index=True, null=True)),
                ('genotype_col', models.TextField(blank=True, db_index=True, null=True)),
                ('genotype', models.TextField(db_index=True)),
                ('individual', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='individuals.Individual')),
            ],
        ),
    ]
