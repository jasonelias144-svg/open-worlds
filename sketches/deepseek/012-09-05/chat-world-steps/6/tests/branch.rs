use chat_world::error::Result;
use chat_world::hash::body_for_signing;
use chat_world::record::*;
use chat_world::verify::{verify_branch, verify_log};
use chat_world::{Keypair, Proof, ProofOrArray, Room, RoomLog, RoomTemplate};

// ---- helpers (copied, as the spec asks) ----

fn make_room(template: RoomTemplate) -> Room {
    let alice = Keypair::generate();
    let room_kp = Keypair::generate();
    Room::create(template, room_kp, &alice).unwrap()
}

fn make_head_mode_room(interval: u64) -> Room {
    let mut template = RoomTemplate::chat("t", "test");
    template.head_interval = interval;
    make_room(template)
}

fn roundtrip(log: &RoomLog) -> RoomLog {
    let text = serde_json::to_string(log).expect("serialize RoomLog to JSON");
    serde_json::from_str(&text).expect("deserialize RoomLog from JSON")
}

fn sign_single(rec: &Record, signer: &Keypair) -> ProofOrArray {
    let body = body_for_signing(rec).unwrap();
    let sig = signer.sign(&body);
    ProofOrArray::Single(Proof::create(signer, &sig))
}

fn sign_dual(rec: &Record, subj: &Keypair, room_kp: &Keypair) -> ProofOrArray {
    let body = body_for_signing(rec).unwrap();
    let s1 = subj.sign(&body);
    let s2 = room_kp.sign(&body);
    ProofOrArray::array(vec![
        Proof::create(subj, &s1),
        Proof::create(room_kp, &s2),
    ])
}

// ---- 1. a branch of an honest room, roundtripped, verifies ----

#[test]
fn honest_branch_roundtrips_and_verifies() -> Result<()> {
    let mut parent = make_room(RoomTemplate::chat("t", "parent"));
    let bob = Keypair::generate();
    parent.join(&bob, "communicate", false)?;
    parent.post(&bob, "hello from bob", "normal")?;
    let parent_log = roundtrip(&parent.log());

    let branch_kp = Keypair::generate();
    let branch = parent.branch_at(
        parent.records().len() as u64 - 1,
        RoomTemplate::chat("t", "branch"),
        branch_kp,
        &bob,
    )?;
    let branch_log = roundtrip(&branch.log());

    verify_log(&parent_log)?;
    verify_log(&branch_log)?;
    verify_branch(&parent_log, &branch_log)?;
    Ok(())
}

// ---- 2. the branch's law differs; it enforces its own ----

#[test]
fn branch_law_differs_from_parent() -> Result<()> {
    let mut parent_template = RoomTemplate::chat("t", "parent");
    parent_template.rate_limit_count = 10;
    parent_template.rate_limit_window = 20;
    let mut parent = make_room(parent_template);
    let bob = Keypair::generate();
    parent.join(&bob, "communicate", false)?;
    parent.post(&bob, "one", "normal")?;

    // Branch with a stricter rate limit
    let mut branch_template = RoomTemplate::chat("t", "branch");
    branch_template.rate_limit_count = 1;
    branch_template.rate_limit_window = 5;
    let branch_kp = Keypair::generate();
    let mut branch = parent.branch_at(
        parent.records().len() as u64 - 1,
        branch_template,
        branch_kp,
        &bob,
    )?;

    // The branch has no members yet (aside from the maker).
    // A member of the parent must join the branch to participate.
    // bob is the maker, so he's already in. He can post once.
    branch.post(&bob, "one", "normal")?;
    let refused = branch.post(&bob, "two", "normal")?;
    match refused {
        Record::Refusal(r) => assert_eq!(r.reason, "rate_limit"),
        _ => panic!("expected rate_limit refusal on branch"),
    }

    // The parent's log still verifies; the parent's rate limit is
    // unchanged.
    verify_log(&parent.log())?;
    verify_log(&branch.log())?;
    verify_branch(&parent.log(), &branch.log())?;
    Ok(())
}

// ---- 3. no one is carried over: a parent member must join ----

#[test]
fn parent_member_not_carried_over() -> Result<()> {
    let mut parent = make_room(RoomTemplate::chat("t", "parent"));
    let bob = Keypair::generate();
    let carol = Keypair::generate();
    parent.join(&bob, "communicate", false)?;
    parent.join(&carol, "communicate", false)?;

    let branch_kp = Keypair::generate();
    let mut branch = parent.branch_at(
        parent.records().len() as u64 - 1,
        RoomTemplate::chat("t", "branch"),
        branch_kp,
        &bob,
    )?;

    // Carol was a member of the parent. She is not a member of the
    // branch. Her post is refused.
    let refused = branch.post(&carol, "hello", "normal")?;
    match refused {
        Record::Refusal(r) => assert_eq!(r.reason, "not_a_member"),
        _ => panic!("expected not_a_member"),
    }

    // After joining, she can post.
    branch.join(&carol, "communicate", false)?;
    branch.post(&carol, "hello", "normal")?;

    verify_log(&branch.log())?;
    verify_branch(&parent.log(), &branch.log())?;
    Ok(())
}

// ---- 4. a branch of a branch ----

#[test]
fn branch_of_branch_verifies() -> Result<()> {
    let mut parent = make_room(RoomTemplate::chat("t", "parent"));
    let bob = Keypair::generate();
    parent.join(&bob, "communicate", false)?;
    parent.post(&bob, "one", "normal")?;

    let branch1_kp = Keypair::generate();
    let mut branch1 = parent.branch_at(
        parent.records().len() as u64 - 1,
        RoomTemplate::chat("t", "branch1"),
        branch1_kp,
        &bob,
    )?;
    branch1.post(&bob, "hi from branch1", "normal")?;

    let branch2_kp = Keypair::generate();
    let branch2 = branch1.branch_at(
        branch1.records().len() as u64 - 1,
        RoomTemplate::chat("t", "branch2"),
        branch2_kp,
        &bob,
    )?;

    verify_branch(&parent.log(), &branch1.log())?;
    verify_branch(&branch1.log(), &branch2.log())?;
    Ok(())
}

// ---- 5. forged: checkpoint hash the parent does not hold ----

#[test]
fn forged_checkpoint_hash_refused() -> Result<()> {
    let mut parent = make_room(RoomTemplate::chat("t", "parent"));
    let bob = Keypair::generate();
    parent.join(&bob, "communicate", false)?;
    parent.post(&bob, "hello", "normal")?;
    let parent_log = parent.log();

    let branch_kp = Keypair::generate();
    let branch = parent.branch_at(
        parent.records().len() as u64 - 1,
        RoomTemplate::chat("t", "branch"),
        branch_kp,
        &bob,
    )?;

    // Tamper the branch's forked_from to name a hash the parent
    // does not hold.
    let mut branch_log = branch.log();
    if let Some(Record::RoomCreated(rc)) = branch_log.records.first_mut() {
        if let Some(ff) = &mut rc.forked_from {
            ff.checkpoint_hash = "00".repeat(32);
        }
    }

    assert!(verify_branch(&parent_log, &branch_log).is_err());
    Ok(())
}

// ---- 6. forged: checkpoint seq past the end ----

#[test]
fn forged_checkpoint_seq_past_end_refused() -> Result<()> {
    let mut parent = make_room(RoomTemplate::chat("t", "parent"));
    let bob = Keypair::generate();
    parent.join(&bob, "communicate", false)?;
    let parent_log = parent.log();

    let branch_kp = Keypair::generate();
    let branch = parent.branch_at(
        parent.records().len() as u64 - 1,
        RoomTemplate::chat("t", "branch"),
        branch_kp,
        &bob,
    )?;

    let mut branch_log = branch.log();
    if let Some(Record::RoomCreated(rc)) = branch_log.records.first_mut() {
        if let Some(ff) = &mut rc.forked_from {
            ff.checkpoint_seq = 999;
        }
    }

    assert!(verify_branch(&parent_log, &branch_log).is_err());
    Ok(())
}

// ---- 7. forged: branch names another room as parent ----

#[test]
fn forged_parent_id_refused() -> Result<()> {
    let mut parent = make_room(RoomTemplate::chat("t", "parent"));
    let bob = Keypair::generate();
    parent.join(&bob, "communicate", false)?;

    let other_kp = Keypair::generate();
    let other_template = RoomTemplate::chat("t", "other");
    let other = Room::create(other_template, other_kp, &bob)?;
    let parent_log = parent.log();
    let other_log = other.log();

    let branch_kp = Keypair::generate();
    let branch = parent.branch_at(
        parent.records().len() as u64 - 1,
        RoomTemplate::chat("t", "branch"),
        branch_kp,
        &bob,
    )?;
    let branch_log = branch.log();

    // The branch is legitimately a branch of `parent`. Verified
    // against `other`, it must fail (parent_id mismatch).
    assert!(verify_branch(&parent_log, &branch_log).is_ok());
    assert!(verify_branch(&other_log, &branch_log).is_err());
    Ok(())
}

// ---- 8. forged: branch made by a key not a member at checkpoint ----

#[test]
fn forged_creator_not_member_refused() -> Result<()> {
    let mut parent = make_room(RoomTemplate::chat("t", "parent"));
    let bob = Keypair::generate();
    parent.join(&bob, "communicate", false)?;
    parent.post(&bob, "hello", "normal")?;
    let parent_log = parent.log();

    // A non-member forges a branch. We can't use branch_at (it
    // doesn't check membership — that's verify_branch's job).
    // Forge a branch whose creator was never in the parent.
    let outsider = Keypair::generate();
    let branch_kp = Keypair::generate();
    let branch_world_id = branch_kp.did();
    let forked = ForkedFrom {
        parent_id: parent_log.world_id.clone(),
        checkpoint_seq: parent.records().len() as u64 - 1,
        checkpoint_hash: parent.records().last().unwrap().hash()?,
    };
    let mut rec = RoomCreated::branch(
        branch_world_id.clone(),
        RoomTemplate::chat("t", "forged-branch"),
        outsider.did(),
        forked,
    );
    let wrapped = Record::RoomCreated(rec.clone());
    let body = body_for_signing(&wrapped)?;
    let creator_sig = outsider.sign(&body);
    let room_sig = branch_kp.sign(&body);
    rec.proof = ProofOrArray::array(vec![
        Proof::create(&outsider, &creator_sig),
        Proof::create(&branch_kp, &room_sig),
    ]);
    let branch_log = RoomLog {
        world_id: branch_world_id,
        template: rec.template.clone(),
        records: vec![Record::RoomCreated(rec)],
        heads: vec![],
    };

    assert!(verify_branch(&parent_log, &branch_log).is_err());
    Ok(())
}

// ---- 9. verify_branch refuses a room that names no parent ----

#[test]
fn no_parent_refused() -> Result<()> {
    let mut parent = make_room(RoomTemplate::chat("t", "parent"));
    let bob = Keypair::generate();
    parent.join(&bob, "communicate", false)?;

    // A plain room has no forked_from; verify_branch must refuse
    // it.
    let plain = make_room(RoomTemplate::chat("t", "plain"));
    assert!(verify_branch(&parent.log(), &plain.log()).is_err());
    Ok(())
}

// ---- 10. a branch of a head-mode room, at a covered checkpoint ----

#[test]
fn branch_of_head_mode_room_at_covered_checkpoint() -> Result<()> {
    let mut parent = make_head_mode_room(2);
    let bob = Keypair::generate();
    parent.join(&bob, "communicate", false)?;
    parent.post(&bob, "one", "normal")?;
    parent.post(&bob, "two", "normal")?;
    // appends = 3, head at length 3 (after appends=2) and at
    // length 4 (after appends=3? no — 3/2 = 1 head, then 3 is
    // not a multiple of 2). Let me count: join=1 append,
    // post1=2, post2=3. Multiples of 2 in appends: 2. So one
    // head, at length 3. Let's check.
    assert_eq!(parent.heads().len(), 1);
    assert_eq!(parent.heads()[0].length, 3);
    // Records: 0 (created), 1 (join), 2 (post1), 3 (post2).
    // head covers length 3, i.e., records[0..3]. checkpoint_seq
    // must be < 3, so 2 is OK and 3 is not.
    let covered_seq = 2u64;
    let branch_kp = Keypair::generate();
    let branch = parent.branch_at(
        covered_seq,
        RoomTemplate::chat("t", "branch"),
        branch_kp,
        &bob,
    )?;

    // But we need to publish the parent's log (which adds a
    // closing head covering all of it). After that, the last
    // head covers everything, so the checkpoint at 2 (and at 3)
    // is allowed by the head-mode check. But `branch_at` was
    // called above on the *original* parent, where the last
    // head covered 0..3. seq=2 is fine.
    let parent_log = parent.log();
    let branch_log = branch.log();
    verify_branch(&parent_log, &branch_log)?;
    Ok(())
}

#[test]
fn branch_at_uncovered_tail_in_head_mode_refused() -> Result<()> {
    let mut parent = make_head_mode_room(2);
    let bob = Keypair::generate();
    parent.join(&bob, "communicate", false)?;
    parent.post(&bob, "one", "normal")?;
    parent.post(&bob, "two", "normal")?;
    // As above: heads has one entry at length 3; records has len 4.
    // Checkpoint at seq 3 (records[3], the last post) is past the
    // last head's coverage. branch_at must refuse.
    let branch_kp = Keypair::generate();
    let r = parent.branch_at(
        3,
        RoomTemplate::chat("t", "branch"),
        branch_kp,
        &bob,
    );
    assert!(r.is_err());
    Ok(())
}
