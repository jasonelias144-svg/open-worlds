use chat_world::error::Result;
use chat_world::patterns::{
    check_composition, ApplicationDraft, ApplicationEvidence, EvidenceDraft, EvidenceVerdict,
    PatternApplication, PatternCard, PatternContext, PatternDraft, PatternLedger,
    PatternTransformation, SourceVisibility,
};
use chat_world::Keypair;
use std::collections::{BTreeMap, BTreeSet};

fn make_probe_pattern(author: &Keypair) -> Result<PatternCard> {
    PatternCard::sign(
        PatternDraft {
            pattern_id: "pat/bounded-reversible-probe".into(),
            version: 1,
            derived_from: None,
            title: "Bounded Reversible Probe".into(),
            problem: "A consequential choice depends on uncertainty that a smaller action could reduce.".into(),
            goal: "Reduce decision uncertainty before committing full resources.".into(),
            context: PatternContext {
                roles: vec!["prober".into(), "subject".into()],
                constraints: vec!["material effects must stay within reversible bounds".into()],
                assumptions: vec!["small-scale response is informative about target decision".into()],
            },
            requires: vec![
                "identified_uncertainty".into(),
                "reversible_trial_scope".into(),
            ],
            provides: vec!["reduced_uncertainty".into()],
            destroys: vec!["untested_assumption".into()],
            exclusions: vec!["irreversible_disclosure_required".into()],
            transformation: PatternTransformation {
                actions: vec![
                    "define informative bounded trial".into(),
                    "run trial on disposable copy or limited audience".into(),
                ],
                observations: vec!["compare observed effect against prediction".into()],
                stop_conditions: vec!["uncertainty resolved or trial budget exhausted".into()],
            },
            mechanism: "A smaller commitment reveals failure modes at lower cost than full execution.".into(),
            costs: vec!["trial_time".into()],
            known_failures: vec!["trial is unrepresentative of full scale".into()],
            sharing_terms: "CC0-1.0".into(),
            created_at: 100,
        },
        author,
    )
}

fn make_separate_states_pattern(author: &Keypair) -> Result<PatternCard> {
    PatternCard::sign(
        PatternDraft {
            pattern_id: "pat/separate-independent-states".into(),
            version: 1,
            derived_from: None,
            title: "Separate Independent States".into(),
            problem: "Two coupled lifecycles prevent changing one without disrupting the other.".into(),
            goal: "Allow independent transitions while declaring explicit dependencies.".into(),
            context: PatternContext {
                roles: vec!["designer".into()],
                constraints: vec!["dependencies between lifecycles remain auditable".into()],
                assumptions: vec!["the two concerns can validly vary independently".into()],
            },
            requires: vec!["reduced_uncertainty".into()],
            provides: vec!["decoupled_lifecycles".into()],
            destroys: vec![],
            exclusions: vec!["strictly_atomic_invariants_only".into()],
            transformation: PatternTransformation {
                actions: vec![
                    "split state container into separate records".into(),
                    "declare explicit cross-lifecycle guards".into(),
                ],
                observations: vec!["verify independent transitions leave sibling state intact".into()],
                stop_conditions: vec!["all target transitions verified independently".into()],
            },
            mechanism: "Explicit state boundaries eliminate accidental coupling during change.".into(),
            costs: vec!["extra_boundary_checks".into()],
            known_failures: vec!["stale permissions if genuine coupling is omitted".into()],
            sharing_terms: "CC0-1.0".into(),
            created_at: 105,
        },
        author,
    )
}

fn make_divide_reconcile_pattern(author: &Keypair) -> Result<PatternCard> {
    PatternCard::sign(
        PatternDraft {
            pattern_id: "pat/divide-then-reconcile".into(),
            version: 1,
            derived_from: None,
            title: "Divide Work, Then Reconcile".into(),
            problem: "Independent subquestions are unnecessarily serialized.".into(),
            goal: "Explore separable branches in parallel and synthesize without erasing dissent.".into(),
            context: PatternContext {
                roles: vec!["coordinator".into(), "branch_contributors".into()],
                constraints: vec!["shared baseline frozen before branching".into()],
                assumptions: vec!["subquestions are separable over the branch interval".into()],
            },
            requires: vec!["shared_baseline".into()],
            provides: vec![
                "identified_uncertainty".into(),
                "reversible_trial_scope".into(),
            ],
            destroys: vec![],
            exclusions: vec!["tightly_coupled_live_state".into()],
            transformation: PatternTransformation {
                actions: vec![
                    "freeze baseline and assign separable branches".into(),
                    "compare results and publish attributable synthesis".into(),
                ],
                observations: vec!["record agreements, conflicts, and open remainders".into()],
                stop_conditions: vec!["synthesis reviewed or branches closed".into()],
            },
            mechanism: "Parallel independent work preserves diverse formulations before convergence.".into(),
            costs: vec!["reconciliation_effort".into()],
            known_failures: vec!["drifting assumptions across long branches".into()],
            sharing_terms: "CC0-1.0".into(),
            created_at: 90,
        },
        author,
    )
}

#[test]
fn pattern_transfers_across_domains_and_accumulates_auditable_evidence() -> Result<()> {
    let alice = Keypair::generate();
    let bob = Keypair::generate();
    let carol = Keypair::generate();
    let mut ledger = PatternLedger::new();

    let probe = make_probe_pattern(&alice)?;
    let probe_hash = ledger.register_card(probe.clone())?;

    // Application 1: Writing domain (Bob)
    let mut write_roles = BTreeMap::new();
    write_roles.insert("prober".into(), "author".into());
    write_roles.insert("subject".into(), "first_reader".into());
    let app_writing = PatternApplication::sign(
        ApplicationDraft {
            pattern_id: probe.pattern_id.clone(),
            pattern_version: probe.version,
            pattern_hash: probe_hash.clone(),
            domain: "writing".into(),
            setting_summary: "Test revised introduction on one reader before full rewrite.".into(),
            role_mapping: write_roles,
            present_conditions: BTreeSet::from([
                "identified_uncertainty".into(),
                "reversible_trial_scope".into(),
            ]),
            applied_at: 200,
        },
        &bob,
    )?;
    let app_writing_hash = ledger.register_application(app_writing)?;

    // Application 2: Software domain (Carol)
    let mut sw_roles = BTreeMap::new();
    sw_roles.insert("prober".into(), "maintainer".into());
    sw_roles.insert("subject".into(), "throwaway_branch".into());
    let app_sw = PatternApplication::sign(
        ApplicationDraft {
            pattern_id: probe.pattern_id.clone(),
            pattern_version: probe.version,
            pattern_hash: probe_hash.clone(),
            domain: "software".into(),
            setting_summary: "Run schema migration on disposable copy with sample corpus.".into(),
            role_mapping: sw_roles,
            present_conditions: BTreeSet::from([
                "identified_uncertainty".into(),
                "reversible_trial_scope".into(),
            ]),
            applied_at: 210,
        },
        &carol,
    )?;
    let app_sw_hash = ledger.register_application(app_sw)?;

    // Evidence 1: Writing trial succeeded partially
    let ev1 = ApplicationEvidence::sign(
        EvidenceDraft {
            application_hash: app_writing_hash,
            verdict: EvidenceVerdict::Partial,
            observed_effects: vec!["reader caught ambiguous term before full rewrite".into()],
            failure_or_limit_note: Some("single reader did not test expert audience".into()),
            source_visibility: SourceVisibility::Public {
                source_ref: "commons/room-editorial/seq-42".into(),
            },
            reported_at: 220,
        },
        &bob,
    )?;
    ledger.register_evidence(ev1)?;

    // Evidence 2: Software trial supported, from a confidential uninspectable source
    let ev2 = ApplicationEvidence::sign(
        EvidenceDraft {
            application_hash: app_sw_hash,
            verdict: EvidenceVerdict::Supported,
            observed_effects: vec!["disposable migration caught duplicate key edge case".into()],
            failure_or_limit_note: None,
            source_visibility: SourceVisibility::ConfidentialUninspectable,
            reported_at: 230,
        },
        &carol,
    )?;
    ledger.register_evidence(ev2)?;

    let summary = ledger.evidence_summary(&probe_hash)?;
    assert_eq!(summary.applications, 2);
    assert_eq!(
        summary.distinct_domains,
        BTreeSet::from(["software".to_string(), "writing".to_string()])
    );
    assert_eq!(summary.supported, 1);
    assert_eq!(summary.partial, 1);
    assert_eq!(summary.failed, 0);
    assert_eq!(summary.public_reports, 1);
    assert_eq!(summary.confidential_reports, 1);
    assert_eq!(ledger.find_providing("reduced_uncertainty").len(), 1);

    Ok(())
}

#[test]
fn failed_application_leads_to_narrowed_revision_without_migrating_old_evidence() -> Result<()> {
    let alice = Keypair::generate();
    let bob = Keypair::generate();
    let mut ledger = PatternLedger::new();

    let v1 = make_probe_pattern(&alice)?;
    let v1_hash = ledger.register_card(v1.clone())?;

    // Exclusion check: trying to apply v1 where irreversible disclosure is required -> refused.
    let mut bad_roles = BTreeMap::new();
    bad_roles.insert("prober".into(), "alice".into());
    bad_roles.insert("subject".into(), "public_board".into());
    let excluded_app = PatternApplication::sign(
        ApplicationDraft {
            pattern_id: v1.pattern_id.clone(),
            pattern_version: 1,
            pattern_hash: v1_hash.clone(),
            domain: "governance".into(),
            setting_summary: "Publish private draft publicly as a test.".into(),
            role_mapping: bad_roles.clone(),
            present_conditions: BTreeSet::from([
                "identified_uncertainty".into(),
                "reversible_trial_scope".into(),
                "irreversible_disclosure_required".into(),
            ]),
            applied_at: 300,
        },
        &bob,
    )?;
    assert!(ledger.register_application(excluded_app).is_err());

    // Valid application that fails empirically because trial scale was unrepresentative.
    let app = PatternApplication::sign(
        ApplicationDraft {
            pattern_id: v1.pattern_id.clone(),
            pattern_version: 1,
            pattern_hash: v1_hash.clone(),
            domain: "networking".into(),
            setting_summary: "Test gossip sync on 2 local nodes.".into(),
            role_mapping: bad_roles,
            present_conditions: BTreeSet::from([
                "identified_uncertainty".into(),
                "reversible_trial_scope".into(),
            ]),
            applied_at: 310,
        },
        &bob,
    )?;
    let app_hash = ledger.register_application(app)?;

    let fail_ev = ApplicationEvidence::sign(
        EvidenceDraft {
            application_hash: app_hash,
            verdict: EvidenceVerdict::Failed,
            observed_effects: vec!["2-node test passed but 50-node mesh saturated".into()],
            failure_or_limit_note: Some("scale-dependent bottleneck invisible in tiny trial".into()),
            source_visibility: SourceVisibility::Public {
                source_ref: "commons/room-net/seq-18".into(),
            },
            reported_at: 320,
        },
        &bob,
    )?;
    ledger.register_evidence(fail_ev)?;

    // Publish narrowed version 2 derived from v1 requiring representative scale.
    let v2 = PatternCard::sign(
        PatternDraft {
            pattern_id: v1.pattern_id.clone(),
            version: 2,
            derived_from: Some(v1_hash.clone()),
            title: "Bounded Reversible Probe (Scale-Checked)".into(),
            problem: v1.problem.clone(),
            goal: v1.goal.clone(),
            context: v1.context.clone(),
            requires: vec![
                "identified_uncertainty".into(),
                "reversible_trial_scope".into(),
                "representative_failure_mode".into(),
            ],
            provides: v1.provides.clone(),
            destroys: v1.destroys.clone(),
            exclusions: v1.exclusions.clone(),
            transformation: v1.transformation.clone(),
            mechanism: v1.mechanism.clone(),
            costs: v1.costs.clone(),
            known_failures: vec![
                "trial is unrepresentative of full scale".into(),
                "scale-dependent bottlenecks may not trigger below threshold".into(),
            ],
            sharing_terms: "CC0-1.0".into(),
            created_at: 350,
        },
        &alice,
    )?;
    let v2_hash = ledger.register_card(v2)?;

    // v1 keeps its failure evidence; v2 starts fresh with 0 applications.
    let s1 = ledger.evidence_summary(&v1_hash)?;
    let s2 = ledger.evidence_summary(&v2_hash)?;
    assert_eq!(s1.failed, 1);
    assert_eq!(s1.recorded_limits.len(), 1);
    assert_eq!(s2.applications, 0);
    assert_eq!(s2.failed, 0);

    Ok(())
}

#[test]
fn strategy_composition_validates_prerequisites_destroyed_conditions_and_exclusions() -> Result<()> {
    let alice = Keypair::generate();
    let divide = make_divide_reconcile_pattern(&alice)?;
    let probe = make_probe_pattern(&alice)?;
    let separate = make_separate_states_pattern(&alice)?;

    // 1. Valid 3-step strategy: divide -> probe -> separate
    let initial = BTreeSet::from(["shared_baseline".to_string(), "untested_assumption".to_string()]);
    let trace = check_composition(&initial, &[&divide, &probe, &separate])?;
    assert_eq!(trace.steps.len(), 3);
    assert!(trace.final_conditions.contains("decoupled_lifecycles"));
    assert!(!trace.final_conditions.contains("untested_assumption"));
    assert_eq!(trace.cumulative_costs.len(), 3);

    // 2. Missing prerequisite: starting at `separate` without `reduced_uncertainty` -> refused.
    assert!(check_composition(&initial, &[&separate]).is_err());

    // 3. Destroyed prerequisite: a step that depends on `untested_assumption` after `probe`
    // destroyed it -> refused with explicit error.
    let needs_untested = PatternCard::sign(
        PatternDraft {
            pattern_id: "pat/needs-untested".into(),
            version: 1,
            derived_from: None,
            title: "Needs Untested Assumption".into(),
            problem: "Test step".into(),
            goal: "Verify destroyed-condition check".into(),
            context: PatternContext {
                roles: vec!["actor".into()],
                constraints: vec![],
                assumptions: vec![],
            },
            requires: vec!["untested_assumption".into()],
            provides: vec!["done".into()],
            destroys: vec![],
            exclusions: vec![],
            transformation: PatternTransformation {
                actions: vec!["act".into()],
                observations: vec![],
                stop_conditions: vec![],
            },
            mechanism: "test".into(),
            costs: vec![],
            known_failures: vec![],
            sharing_terms: "CC0-1.0".into(),
            created_at: 110,
        },
        &alice,
    )?;
    let err = check_composition(&initial, &[&divide, &probe, &needs_untested]).unwrap_err();
    assert!(err.to_string().contains("destroyed"));

    // 4. Triggered exclusion: initial condition contains `tightly_coupled_live_state` -> refused.
    let coupled_start = BTreeSet::from([
        "shared_baseline".to_string(),
        "tightly_coupled_live_state".to_string(),
    ]);
    assert!(check_composition(&coupled_start, &[&divide]).is_err());

    Ok(())
}

#[test]
fn tampered_pattern_and_unknown_json_fields_are_refused() -> Result<()> {
    let alice = Keypair::generate();
    let mut card = make_probe_pattern(&alice)?;
    card.verify()?;

    // Mutating mechanism after signing invalidates the proof.
    card.mechanism = "altered mechanism".into();
    assert!(card.verify().is_err());

    // Injecting an unknown JSON field into PatternCard is refused by deny_unknown_fields.
    let honest = make_probe_pattern(&alice)?;
    let mut val = serde_json::to_value(&honest).unwrap();
    val["endorsement_score"] = serde_json::json!(999);
    assert!(serde_json::from_value::<PatternCard>(val).is_err());

    Ok(())
}
