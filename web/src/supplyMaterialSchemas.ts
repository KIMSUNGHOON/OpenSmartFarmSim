import {closed,need} from './storedLeafReplayIO';
import {type WireDocument} from './supplyMorphologyGraphValues';
// Field inventories from the accepted own-public archive; values are validated separately.
const SHAPES:Readonly<Record<string,readonly (readonly string[])[]>>={
 "supply-forcing-definition-v1":[["G0_G4","R2","code_sha256","kernel_code_sha256","partition","rights","schema_version","scope","source","spans","stop_at"]],
 "supply-forcing-history-page-v1":[["after_current_sha256","before_current_sha256","evidence","kind","previous_cursor_sha256","schema_version"]],
 "supply-forcing-interval-candidate-v1":[["G0_G4","R2","arithmetic_code_sha256","checkpoint_issued","code_sha256","component_code_sha256","current","forcing_transition","history_committed","input_sha256","interval","material_consumed","model_version","pending","progress","schema_version","scope","span_sha256","status"]],
 "supply-forcing-interval-state-v1":[["G0_G4","R2","active_input_sha256","at","branch_integrated_transfers","branch_ledgers","branch_steps","code_sha256","event_sequence","geometry_diagnostics","global_ledgers","grid_index","grid_remainder_exact","last_confirmed","lifetime_transfers_exact","model_version","next_grid_endpoint_exact","phase","point_totals_exact","schedule","schema_version","scope","transfer_origins"]],
 "supply-forcing-owner-basis-v1":[["arithmetic_basis","schema_version","source","source_arithmetic_code_sha256","source_current_sha256","source_rights"]],
 "supply-forcing-owner-current-v1":[["G0_G4","R2","at","code_sha256","definition_sha256","effective_rights","integration_count","numeric","output_cursor","output_prefix_sha256","phase","schema_version","scope","span_index"]],
 "supply-forcing-owner-cursor-v1":[["G0_G4","R2","basis_sha256","code_sha256","current_sha256","definition_sha256","history_page_sha256","previous_cursor_sha256","schema_version","scope"]],
 "supply-forcing-pending-page-v1":[["definition_sha256","previous_cursor_sha256","reason","result","schema_version"]],
 "supply-material-current-v1":[["G0_G4","R2","at","code_sha256","definition_sha256","effective_rights","integration_count","numeric","output_cursor","output_prefix_sha256","phase","schema_version","scope","span_index"]],
 "supply-material-cursor-v1":[["G0_G4","R2","basis_sha256","code_sha256","current_sha256","definition_sha256","history_page_sha256","previous_cursor_sha256","schema_version","scope"]],
 "supply-material-definition-v1":[["G0_G4","R2","code_sha256","expected_point_sha256","inputs","pending_page_sha256","point_sha256","proof_code_sha256","schema_version","scope","source","time_tolerance_seconds_exact"]],
 "supply-material-geometry-origins-v1":[["baselines","point_sha256","previous_origin_sha256","schema_version"]],
 "supply-material-history-page-v1":[["after_current_sha256","before_current_sha256","evidence","kind","previous_cursor_sha256","schema_version"],["after_current_sha256","kind","point_sha256","schema_version","source","source_current_sha256"]],
 "supply-material-numeric-v1":[["G0_G4","R2","active_input_sha256","at","branch_integrated_transfers","branch_ledgers","branch_steps","code_sha256","event_sequence","geometry_diagnostics","global_ledgers","grid_index","grid_remainder_exact","last_confirmed","lifetime_transfers_exact","next_grid_endpoint_exact","phase","point_totals_exact","schedule","schema_version","scope","transfer_origins"]],
 "supply-material-owner-basis-v1":[["numeric_basis","origin_records","point_sha256","schema_version","source","source_current_sha256"]],
 "supply-material-physical-origins-v1":[["baselines","point_sha256","previous_origin_sha256","schema_version"]],
 "supply-season-basis-v1":[["profile_sha256","root_program","root_seed","schema_version","seed","shoot_base_temperature","source","source_checkpoint_sha256"]],
 "supply-season-current-v1":[["G0_G4","R2","at","branch_integrated_transfers","branch_ledgers","branch_steps","event_sequence","geometry_diagnostics","global_ledgers","grid_index","last_confirmed","lifetime_transfers_exact","output_cursor","output_prefix_sha256","phase","point_totals_exact","schedule","schema_version","scope","transfer_origins"]],
 "supply-season-cursor-v1":[["G0_G4","R2","basis_sha256","code_sha256","current_sha256","definition_sha256","history_page_sha256","previous_cursor_sha256","schema_version","scope"]],
 "supply-season-definition-v1":[["G0_G4","R2","code_sha256","forcing_span","method","rights","schema_version","scope","source","stop_at"]],
 "supply-season-history-page-v1":[["after_current_sha256","before_current_sha256","interval","kind","previous_cursor_sha256","schema_version"]],
 "supply-season-material-point-result-v1":[["G0_G4","R2","after_birth_baselines","after_costs","after_derived","after_geometry_baselines","after_organs","after_program","after_rates","after_stage","after_state","after_state_layout","at","before_dense","calculation_sha256","candidate_RHS_evaluations","candidate_sha256","checkpoint_issued","code_sha256","cursor_sha256","definition_sha256","effective_rights","elapsed_seconds_advanced","flow_components","growth_costs","history_committed","hold","initial_binding_sha256","input_sha256","inputs","leaf_receipts","material_consumed","model_version","new_birth_baselines","pending_page_sha256","point_balances","point_flows_exact","point_order","point_stage_RHS_evaluations","policy","post_point_global_ledgers_preview","post_point_lifetime_transfers_exact_preview","post_point_point_totals_exact_preview","preview_scope","progress","root_certificate","schedule_adoption","schema_version","scope","seed_compatibility","source_current_sha256","source_event","source_schedule","source_transfer_origins","status"]],
};
export function materialStoredSchema(doc:WireDocument){
 const schema=doc.value.schema_version;need(typeof schema==='string'&&Object.hasOwn(SHAPES,schema));
 const keys=Object.keys(doc.value),shape=SHAPES[schema]!.find(s=>s.length===keys.length&&s.every(k=>Object.hasOwn(doc.value,k)));need(shape);closed(doc.value,[...shape]);
}
