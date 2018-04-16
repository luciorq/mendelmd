from django.db import models
from individuals.models import Individual

class Variant(models.Model):

    individual = models.ForeignKey(Individual, on_delete=models.CASCADE)

    index = models.TextField(db_index=True)#ex. 1-2387623-G-T
    pos_index = models.TextField(db_index=True)#ex. 1-326754756

    #First save all 9 VCF columns
    chr = models.TextField(verbose_name="Chr", db_index=True)
    pos = models.IntegerField(db_index=True)
    variant_id = models.TextField(verbose_name="ID", db_index=True)
    ref = models.TextField(null=True, blank=True, db_index=True)
    alt = models.TextField(null=True, blank=True)
    qual = models.FloatField(db_index=True)
    filter = models.TextField(db_index=True)
    # info = models.TextField(null=True, blank=True)
    format = models.TextField(null=True, blank=True, db_index=True)
    genotype_col = models.TextField(null=True, blank=True, db_index=True)
    genotype = models.TextField(db_index=True)

    #metrics from genotype_info DP field
    read_depth = models.IntegerField()

    gene = models.TextField(null=True, blank=True, db_index=True)
    mutation_type = models.TextField(null=True, db_index=True)
    # vartype = models.TextField(null=True, db_index=True)

    #Annotation From 1000genomes
    genomes1k_maf = models.FloatField(null=True, blank=True, verbose_name="1000 Genomes Frequency", db_index=True)
    gnomead_exome_maf = models.FloatField(null=True, blank=True, verbose_name="GnomeAD Exome Frequency", db_index=True)
    gnomead_genome_maf = models.FloatField(null=True, blank=True, verbose_name="GnomeAD Genome Frequency", db_index=True)
    
    #dbsnp
    # dbsnp_pm = models.TextField(null=True, blank=True)
    # dbsnp_clnsig = models.TextField(null=True, blank=True)
    dbsnp_build = models.IntegerField(null=True, db_index=True)

    #VEP
    sift = models.FloatField(null=True, blank=True, db_index=True)
    sift_pred = models.TextField(null=True, blank=True, db_index=True)

    polyphen2 = models.FloatField(null=True, blank=True, db_index=True)
    polyphen2_pred = models.TextField(null=True, blank=True, db_index=True)

    cadd = models.FloatField(null=True, blank=True, db_index=True)

    # #hi_index
    # hi_index_str = models.TextField(null=True, blank=True, db_index=True)
    # hi_index = models.FloatField(null=True, blank=True, db_index=True)
    # hi_index_perc = models.FloatField(null=True, blank=True, db_index=True)

    #OMIM
    is_at_omim = models.BooleanField(default=False, db_index=True)

    #HGMD
    is_at_hgmd = models.BooleanField(default=False, db_index=True)
    hgmd_class = models.TextField(null=True, blank=True, db_index=True)
    hgmd_phen = models.TextField(null=True, blank=True, db_index=True)

    #snpeff annotation
    snpeff_effect = models.TextField(null=True, blank=True, db_index=True)
    snpeff_impact = models.TextField(null=True, blank=True, db_index=True)
    snpeff_func_class = models.TextField(null=True, blank=True, db_index=True)
    snpeff_codon_change = models.TextField(null=True, blank=True, db_index=True)
    snpeff_aa_change = models.TextField(null=True, blank=True, db_index=True)
    # snpeff_aa_len = models.TextField(null=True, blank=True)
    # snpeff_gene_name = models.TextField(null=True, blank=True, db_index=True)
    # snpeff_biotype = models.TextField(null=True, blank=True, db_index=True)
    # snpeff_gene_coding = models.TextField(null=True, blank=True, db_index=True)
    # snpeff_transcript_id = models.TextField(null=True, blank=True, db_index=True)
    # snpeff_exon_rank = models.TextField(null=True, blank=True, db_index=True)
    # snpeff_genotype_number = models.TextField(null=True, blank=True)

    #vep annotation
    # vep_allele = models.TextField(null=True, blank=True, db_index=True)
    # vep_gene = models.TextField(null=True, blank=True, db_index=True)
    # vep_feature = models.TextField(null=True, blank=True, db_index=True)
    # vep_feature_type = models.TextField(null=True, blank=True, db_index=True)
    # vep_consequence = models.TextField(null=True, blank=True, db_index=True)
    # vep_cdna_position = models.TextField(null=True, blank=True, db_index=True)
    # vep_cds_position = models.TextField(null=True, blank=True, db_index=True)
    # vep_protein_position = models.TextField(null=True, blank=True, db_index=True)
    # vep_amino_acids = models.TextField(null=True, blank=True, db_index=True)
    # vep_codons = models.TextField(null=True, blank=True, db_index=True)
    # vep_existing_variation = models.TextField(null=True, blank=True, db_index=True)
    # vep_distance = models.TextField(null=True, blank=True, db_index=True)
    # vep_strand = models.TextField(null=True, blank=True, db_index=True)
    # vep_symbol = models.TextField(null=True, blank=True, db_index=True)
    # vep_symbol_source = models.TextField(null=True, blank=True, db_index=True)
    # vep_sift = models.TextField(null=True, blank=True, db_index=True)
    # vep_polyphen = models.TextField(null=True, blank=True, db_index=True)
    # vep_condel = models.TextField(null=True, blank=True, db_index=True)

    #new annotations
    # ensembl_clin_HGMD = models.BooleanField(default=False, db_index=True)
    # ensembl_clin_HGMD = models.BooleanField(default=False, db_index=True)
    # clinvar_CLNSRC = models.TextField(null=True, blank=True, db_index=True)
    # ensembl_phen.CLIN_pathogenic
    #ensembl_phen.CLIN_likely_pathogenic
    # ensembl_clin.CLIN_pathogenic

    #DBNFSP
    SIFT_score = models.TextField(null=True, blank=True, db_index=True)
    SIFT_converted_rankscore = models.TextField(null=True, blank=True, db_index=True)

    CADD_raw = models.TextField(null=True, blank=True, db_index=True)
    CADD_raw_rankscore = models.TextField(null=True, blank=True, db_index=True)
    CADD_phred = models.TextField(null=True, blank=True, db_index=True)

    mcap_score = models.FloatField(null=True, blank=True, db_index=True)
    mcap_rankscore = models.FloatField(null=True, blank=True, db_index=True)
    mcap_pred = models.TextField(null=True, blank=True, db_index=True)

    clinvar_rs = models.TextField(null=True, blank=True, db_index=True)
    clinvar_clnsig = models.TextField(null=True, blank=True, db_index=True)
    clinvar_trait = models.TextField(null=True, blank=True, db_index=True)
    clinvar_golden_stars = models.TextField(null=True, blank=True, db_index=True)


    def get_fields(self):
    	return [(field.name, field.verbose_name.title().replace('_', ' ')) for field in Variant._meta.fields]

