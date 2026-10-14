"""V6 preserves the 12/24 ontology; makes evidence qualifications explicit."""
from .core.schema import KINDS,RELATIONS,ENDPOINTS,CAUSAL
VERSION='6.0'

def certainty_group(value):
    if value in {'guidance','source_recommendation'}:return 'reference_guidance'
    if value in {'reported_action','case_treatment_outcome'}:return 'reported_action'
    if value in {'case_observed','case_check','case_evidence'}:return 'source_observation'
    if value in {'case_identified','source_case_conclusion'}:return 'identified_in_source'
    if value in {'possible','probable','suspected','source_hypothesis','fault_tree_hypothesis',
                 'source_hypothesis_unmeasured','source_initial_hypothesis'}:return 'hypothesis_or_possible'
    if value=='conditional':return 'conditional_statement'
    if value in {'case_interpretation','source_interpretation','case_inferred'}:return 'source_interpretation'
    if value=='historical_case_reference':return 'referenced_case_not_current_case'
    return 'source_statement_or_index'

NODE_REQUIRED={'graph_version','schema_version','kind_zh','display_name','entity_level',
               'scope_id','knowledge_zone'}
EDGE_REQUIRED={'id','assertion_id','graph_version','schema_version','name','scope_id',
               'source_id','passage_id','quote','certainty','certainty_group',
               'expert_review','source_review_extent'}
