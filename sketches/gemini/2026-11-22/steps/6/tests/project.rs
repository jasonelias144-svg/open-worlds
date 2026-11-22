use chat_world::error::Result;
use chat_world::hash::sha256_hex;
use chat_world::project::{
    AcceptanceDecision, AcceptanceDraft, ArtifactRevision, CaptureProvenance, ConversationTurn,
    EditProposal, GapMarker, HandoffPackage, ParticipantRole, ProjectPermission, ProjectSnapshot,
    ProjectWorkspace, ProposalDraft, ReviewCoverage, ReviewDraft, ReviewRecord, ReviewVerdict,
    RevisionDraft, TaskAssignment, TaskDraft, TurnDraft, TurnRole,
};
use chat_world::Keypair;

#[test]
fn full_collaboration_cycle_capture_import_independent_drafts_synthesis_and_recovery() -> Result<()>
{
    let founder = Keypair::generate();
    let collab_a = Keypair::generate();
    let collab_b = Keypair::generate();

    // 1. Create project around a short demonstration document and seed Revision 1.
    let mut project = ProjectWorkspace::create(
        "proj/amto-intro",
        "Refine the introduction while preserving formal definitions.",
        "revision-pass",
        founder.did(),
        "founder",
        100,
    )?;
    project.set_terminology("carrier", "declared set of admitted cases");
    project.add_open_question("Should Section 1.2 keep the dipole example inline?");

    project.add_participant(
        &founder.did(),
        ParticipantRole {
            participant_id: collab_a.did(),
            label: "collaborator-a".into(),
            permissions: vec![
                ProjectPermission::Read,
                ProjectPermission::CommentOrReview,
                ProjectPermission::ProposeChanges,
            ],
        },
    )?;
    project.add_participant(
        &founder.did(),
        ParticipantRole {
            participant_id: collab_b.did(),
            label: "collaborator-b".into(),
            permissions: vec![
                ProjectPermission::Read,
                ProjectPermission::CommentOrReview,
                ProjectPermission::ProposeChanges,
            ],
        },
    )?;

    let rev1 = ArtifactRevision::sign(
        RevisionDraft {
            project_id: "proj/amto-intro".into(),
            artifact_id: "doc/intro.md".into(),
            revision_num: 1,
            parent_revision_hash: None,
            content: "Introduction v1: Opposites require an explicit carrier.".into(),
            derived_from_proposals: vec![],
            summary: "Initial baseline".into(),
            created_at: 101,
        },
        &founder,
    )?;
    let rev1_hash = project.seed_artifact(rev1)?;

    // 2. Capture a native prompt and response.
    let t0 = ConversationTurn::sign(
        TurnDraft {
            project_id: "proj/amto-intro".into(),
            thread_id: "main".into(),
            turn_index: 0,
            role: TurnRole::Prompt,
            text: "Let's produce two independent intro revisions.".into(),
            attachments: vec![],
            gaps: vec![],
            provenance: CaptureProvenance::NativeSigned,
            ts: 110,
        },
        &founder,
    )?;
    let t1 = ConversationTurn::sign(
        TurnDraft {
            project_id: "proj/amto-intro".into(),
            thread_id: "main".into(),
            turn_index: 1,
            role: TurnRole::Response,
            text: "Understood; keeping carrier terminology exact.".into(),
            attachments: vec![],
            gaps: vec![],
            provenance: CaptureProvenance::NativeSigned,
            ts: 111,
        },
        &collab_a,
    )?;
    project.record_turn(t0)?;
    project.record_turn(t1)?;

    // 3. Import a conversation record from an external app with a detectable gap.
    let raw_export = b"--- exported snippet (missing earlier prompt) ---";
    let imported = ConversationTurn::sign(
        TurnDraft {
            project_id: "proj/amto-intro".into(),
            thread_id: "external-notes".into(),
            turn_index: 0,
            role: TurnRole::Response,
            text: "Suggested tightening the opening paragraph.".into(),
            attachments: vec!["notes.txt".into()],
            gaps: vec![GapMarker::MissingPrompt],
            provenance: CaptureProvenance::Imported {
                submitted_by: founder.did(),
                claimed_speaker: "external-assistant".into(),
                source_format: "markdown-export/v1".into(),
                raw_source_sha256: sha256_hex(raw_export),
            },
            ts: 115,
        },
        &founder,
    )?;
    project.record_turn(imported)?;
    assert_eq!(project.turns_count(), 3);

    // 4. Assign two independent edit tasks against rev1.
    let task_a = TaskAssignment::sign(
        TaskDraft {
            task_id: "task/draft-a".into(),
            project_id: "proj/amto-intro".into(),
            assignee: collab_a.did(),
            artifact_id: "doc/intro.md".into(),
            base_revision_hash: rev1_hash.clone(),
            objective: "Tighten opening prose without altering carrier definition.".into(),
            constraints: vec!["preserve carrier terminology".into()],
            stop_condition: "submit one proposal".into(),
            independent_of_other_drafts: true,
            assigned_at: 120,
        },
        &founder,
    )?;
    let task_b = TaskAssignment::sign(
        TaskDraft {
            task_id: "task/draft-b".into(),
            project_id: "proj/amto-intro".into(),
            assignee: collab_b.did(),
            artifact_id: "doc/intro.md".into(),
            base_revision_hash: rev1_hash.clone(),
            objective: "Improve readability independently of collaborator A.".into(),
            constraints: vec!["preserve carrier terminology".into()],
            stop_condition: "submit one proposal".into(),
            independent_of_other_drafts: true,
            assigned_at: 120,
        },
        &founder,
    )?;
    project.assign_task(task_a)?;
    project.assign_task(task_b)?;

    // Collaborator A submits Draft A first.
    let prop_a = EditProposal::sign(
        ProposalDraft {
            proposal_id: "prop/a".into(),
            project_id: "proj/amto-intro".into(),
            task_id: Some("task/draft-a".into()),
            artifact_id: "doc/intro.md".into(),
            base_revision_hash: rev1_hash.clone(),
            proposed_content: "Introduction A: Every opposition specifies its carrier.".into(),
            rationale: "Direct opening sentence.".into(),
            preserved_invariants: vec!["carrier definition intact".into()],
            synthesizes_proposals: vec![],
            created_at: 130,
        },
        &collab_a,
    )?;
    let prop_a_hash = project.submit_proposal(prop_a)?;

    // 5. Generate handoff for Collaborator B: because task/draft-b is independent,
    //    Draft A MUST NOT appear in B's visible_proposals!
    let handoff_b = project.generate_handoff(&collab_b.did(), Some("task/draft-b"))?;
    assert!(handoff_b.visible_proposals.is_empty());
    assert_eq!(
        handoff_b.current_approved_revisions.get("doc/intro.md"),
        Some(&rev1_hash)
    );
    assert!(handoff_b
        .coverage_limits
        .iter()
        .any(|c| c.contains("recorded gap")));

    // Collaborator B submits Draft B independently.
    let prop_b = EditProposal::sign(
        ProposalDraft {
            proposal_id: "prop/b".into(),
            project_id: "proj/amto-intro".into(),
            task_id: Some("task/draft-b".into()),
            artifact_id: "doc/intro.md".into(),
            base_revision_hash: rev1_hash.clone(),
            proposed_content: "Introduction B: To call things opposites is to state their carrier and respect.".into(),
            rationale: "Names both carrier and respect up front.".into(),
            preserved_invariants: vec!["carrier definition intact".into()],
            synthesizes_proposals: vec![],
            created_at: 135,
        },
        &collab_b,
    )?;
    let prop_b_hash = project.submit_proposal(prop_b)?;

    // 6. Propose synthesis combining Draft A and Draft B, and attach a partial review.
    let synth = EditProposal::sign(
        ProposalDraft {
            proposal_id: "prop/synthesis".into(),
            project_id: "proj/amto-intro".into(),
            task_id: None,
            artifact_id: "doc/intro.md".into(),
            base_revision_hash: rev1_hash.clone(),
            proposed_content: "Introduction v2: Every opposition specifies its carrier and respect.".into(),
            rationale: "Combines A's brevity with B's respect clause.".into(),
            preserved_invariants: vec!["carrier definition intact".into()],
            synthesizes_proposals: vec![prop_a_hash.clone(), prop_b_hash],
            created_at: 140,
        },
        &collab_a,
    )?;
    let synth_hash = project.submit_proposal(synth.clone())?;

    let review = ReviewRecord::sign(
        ReviewDraft {
            project_id: "proj/amto-intro".into(),
            target_hash: synth_hash.clone(),
            base_revision_hash: rev1_hash.clone(),
            verdict: ReviewVerdict::ApproveWithNotes,
            coverage: ReviewCoverage {
                sections_supplied: vec!["sec-1.1".into(), "sec-1.2".into()],
                sections_examined: vec!["sec-1.1".into()],
                checks_performed: vec!["terminology check".into()],
                missing_or_unexamined: vec!["sec-1.2 not yet checked".into()],
            },
            findings: vec!["Opening matches glossary.".into()],
            unresolved_questions: vec!["Confirm sec-1.2 transition.".into()],
            reviewed_at: 145,
        },
        &collab_b,
    )?;
    project.submit_review(review)?;

    // 7. Founder accepts synthesis -> advances doc/intro.md to Revision 2.
    let rev2 = ArtifactRevision::sign(
        RevisionDraft {
            project_id: "proj/amto-intro".into(),
            artifact_id: "doc/intro.md".into(),
            revision_num: 2,
            parent_revision_hash: Some(rev1_hash.clone()),
            content: synth.proposed_content.clone(),
            derived_from_proposals: vec![synth_hash.clone()],
            summary: "Adopted synthesized introduction".into(),
            created_at: 150,
        },
        &founder,
    )?;
    let rev2_hash = rev2.hash()?;
    let decision = AcceptanceDecision::sign(
        AcceptanceDraft {
            project_id: "proj/amto-intro".into(),
            artifact_id: "doc/intro.md".into(),
            expected_current_revision_hash: rev1_hash.clone(),
            accepted_proposal_hashes: vec![synth_hash],
            resulting_revision_hash: rev2_hash.clone(),
            rationale: "Accepted synthesis after terminology review".into(),
            decided_at: 150,
        },
        &founder,
    )?;

    project.accept_revision(decision.clone(), rev2.clone())?;
    // Duplicate delivery of the exact same decision is idempotent.
    project.accept_revision(decision, rev2)?;
    assert_eq!(project.decisions_count(), 1);
    assert_eq!(
        project.current_revision_hash("doc/intro.md"),
        Some(rev2_hash.as_str())
    );

    // 8. Stale proposal based on rev1 cannot silently overwrite rev2!
    let stale_rev3 = ArtifactRevision::sign(
        RevisionDraft {
            project_id: "proj/amto-intro".into(),
            artifact_id: "doc/intro.md".into(),
            revision_num: 3,
            parent_revision_hash: Some(rev2_hash.clone()),
            content: "Introduction A: Every opposition specifies its carrier.".into(),
            derived_from_proposals: vec![prop_a_hash.clone()],
            summary: "Attempted un-reconciled accept of stale prop_a".into(),
            created_at: 160,
        },
        &founder,
    )?;
    let stale_dec = AcceptanceDecision::sign(
        AcceptanceDraft {
            project_id: "proj/amto-intro".into(),
            artifact_id: "doc/intro.md".into(),
            expected_current_revision_hash: rev2_hash.clone(),
            accepted_proposal_hashes: vec![prop_a_hash],
            resulting_revision_hash: stale_rev3.hash()?,
            rationale: "Should fail because prop_a targeted rev1".into(),
            decided_at: 160,
        },
        &founder,
    )?;
    assert!(project.accept_revision(stale_dec, stale_rev3).is_err());

    // 9. Export portable snapshot to JSON, restore in a fresh session, and verify handoff.
    let snap_json = serde_json::to_string(&project.export_snapshot()).unwrap();
    let parsed: ProjectSnapshot = serde_json::from_str(&snap_json).unwrap();
    let restored = ProjectWorkspace::restore(parsed)?;

    let next_handoff = restored.generate_handoff(&collab_a.did(), None)?;
    assert_eq!(
        next_handoff.current_approved_revisions.get("doc/intro.md"),
        Some(&rev2_hash)
    );
    assert_eq!(
        next_handoff
            .current_document_contents
            .get("doc/intro.md")
            .map(|s| s.as_str()),
        Some("Introduction v2: Every opposition specifies its carrier and respect.")
    );
    assert!(next_handoff
        .coverage_limits
        .iter()
        .any(|c| c.contains("sec-1.2 not yet checked")));
    assert_eq!(next_handoff.open_questions.len(), 1);

    Ok(())
}

#[test]
fn authority_boundaries_provenance_checks_and_json_strictness_are_enforced() -> Result<()> {
    let founder = Keypair::generate();
    let reviewer_only = Keypair::generate();
    let outsider = Keypair::generate();

    let mut project = ProjectWorkspace::create(
        "proj/strict",
        "Verify authority and provenance.",
        "alpha",
        founder.did(),
        "founder",
        10,
    )?;
    project.add_participant(
        &founder.did(),
        ParticipantRole {
            participant_id: reviewer_only.did(),
            label: "reviewer".into(),
            permissions: vec![ProjectPermission::Read, ProjectPermission::CommentOrReview],
        },
    )?;

    let rev1 = ArtifactRevision::sign(
        RevisionDraft {
            project_id: "proj/strict".into(),
            artifact_id: "doc/spec.md".into(),
            revision_num: 1,
            parent_revision_hash: None,
            content: "Spec v1".into(),
            derived_from_proposals: vec![],
            summary: "Seed".into(),
            created_at: 11,
        },
        &founder,
    )?;
    let rev1_hash = project.seed_artifact(rev1)?;

    // Reviewer without ProposeChanges cannot submit a proposal.
    let unauth_prop = EditProposal::sign(
        ProposalDraft {
            proposal_id: "prop/unauth".into(),
            project_id: "proj/strict".into(),
            task_id: None,
            artifact_id: "doc/spec.md".into(),
            base_revision_hash: rev1_hash.clone(),
            proposed_content: "Unauthorized edit".into(),
            rationale: "Attempt".into(),
            preserved_invariants: vec![],
            synthesizes_proposals: vec![],
            created_at: 12,
        },
        &reviewer_only,
    )?;
    assert!(project.submit_proposal(unauth_prop).is_err());

    // Outsider cannot generate a handoff package.
    assert!(project.generate_handoff(&outsider.did(), None).is_err());

    // Imported turn where signer != provenance.submitted_by is refused at signing time.
    let bad_import = ConversationTurn::sign(
        TurnDraft {
            project_id: "proj/strict".into(),
            thread_id: "t".into(),
            turn_index: 0,
            role: TurnRole::Response,
            text: "Forged attribution".into(),
            attachments: vec![],
            gaps: vec![],
            provenance: CaptureProvenance::Imported {
                submitted_by: founder.did(),
                claimed_speaker: "other".into(),
                source_format: "txt".into(),
                raw_source_sha256: sha256_hex(b"raw"),
            },
            ts: 15,
        },
        &reviewer_only,
    );
    assert!(bad_import.is_err());

    // Tampered revision content fails verification even before acceptance.
    let mut tampered = ArtifactRevision::sign(
        RevisionDraft {
            project_id: "proj/strict".into(),
            artifact_id: "doc/spec.md".into(),
            revision_num: 2,
            parent_revision_hash: Some(rev1_hash),
            content: "Spec v2".into(),
            derived_from_proposals: vec![],
            summary: "v2".into(),
            created_at: 20,
        },
        &founder,
    )?;
    tampered.content = "Spec v2 tampered".into();
    assert!(tampered.verify().is_err());

    // HandoffPackage JSON refuses unknown injected fields.
    let honest_handoff = project.generate_handoff(&reviewer_only.did(), None)?;
    let mut val = serde_json::to_value(&honest_handoff).unwrap();
    val["hidden_private_notes"] = serde_json::json!("leaked");
    assert!(serde_json::from_value::<HandoffPackage>(val).is_err());

    Ok(())
}
