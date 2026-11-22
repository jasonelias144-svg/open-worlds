use chat_world::contact::{
    AttentionFocus, ClientSnapshot, ContactMode, DeliveredItem, HandoffAttestation,
    InvitationState, ParticipantClient, SessionStatus, TemporaryHandoff,
};
use chat_world::error::Result;
use chat_world::Keypair;

#[test]
fn outing_split_defer_accept_private_call_and_restart() -> Result<()> {
    let alice_kp = Keypair::generate();
    let bob_kp = Keypair::generate();
    let music_room = Keypair::generate().did();
    let story_room = Keypair::generate().did();

    let mut alice = ParticipantClient::new(alice_kp.clone());
    let mut bob = ParticipantClient::new(bob_kp.clone());

    // 1. Both start together in Music room and exchange contact permissions.
    alice.enter_public_room(music_room.clone());
    bob.enter_public_room(music_room.clone());

    let perm_from_bob = bob.grant_contact(
        alice.did(),
        "endpoint://bob-contact-01".into(),
        vec![ContactMode::LiveCall],
        1000,
    )?;
    alice.receive_permission(perm_from_bob.clone())?;

    // 2. They separate into different rooms.
    bob.enter_public_room(story_room.clone());
    assert!(alice.public_rooms().contains(&music_room));
    assert!(bob.public_rooms().contains(&story_room));

    // 3. Alice sends a bounded invitation with a clear purpose.
    let inv = alice.send_invitation(
        &perm_from_bob.permission_id,
        ContactMode::LiveCall,
        "Found a pattern question—want to compare notes?".into(),
        100,
        200,
    )?;
    bob.receive_invitation(inv.clone(), 105)?;
    // Duplicate retry delivery does not create a second inbox item or error.
    bob.receive_invitation(inv.clone(), 106)?;

    // 4. Bob defers to finish his current story exchange.
    bob.defer_invitation(
        &inv.invitation_id,
        Some("Finishing one turn in the story room first.".into()),
        110,
    )?;
    assert!(matches!(
        bob.inbox_state(&inv.invitation_id),
        Some(InvitationState::Deferred { .. })
    ));

    // 5. Bob accepts while still valid; public-room memberships do not change.
    let session = bob.accept_invitation(&inv.invitation_id, 150)?;
    alice.sync_accepted_session(session.clone())?;
    assert!(bob.public_rooms().contains(&story_room));
    assert!(alice.public_rooms().contains(&music_room));

    // 6. Focus safety: Alice is still focused on the public music room,
    // so attempting to post privately with stale focus is refused.
    let stale_focus = AttentionFocus::PublicRoom(music_room.clone());
    assert!(alice
        .post_private(&session.session_id, &stale_focus, "should not leak", 155)
        .is_err());

    // 7. Alice switches focus explicitly to the private session and sends a message.
    let priv_focus = AttentionFocus::PrivateSession(session.session_id.clone());
    alice.set_focus(priv_focus.clone());
    let msg = alice.post_private(&session.session_id, &priv_focus, "Look at A B A C A.", 160)?;
    bob.receive_private(msg)?;
    bob.keep_in_conversation(&session.conversation_id, "Question: What can change?".into())?;

    // 8. Bob ends the call unilaterally without requiring Alice's cooperation.
    bob.end_session(&session.session_id, 200)?;
    assert!(matches!(
        bob.session(&session.session_id).unwrap().status,
        SessionStatus::Ended { .. }
    ));

    // 9. Restart recovery: snapshot to JSON, drop client, and restore.
    let snap_json = serde_json::to_string(&bob.snapshot()).unwrap();
    let parsed_snap: ClientSnapshot = serde_json::from_str(&snap_json).unwrap();
    let mut bob_restarted = ParticipantClient::restore(parsed_snap, bob_kp)?;

    assert!(matches!(
        bob_restarted.session(&session.session_id).unwrap().status,
        SessionStatus::Ended { .. }
    ));
    assert_eq!(
        bob_restarted
            .conversation(&session.conversation_id)
            .unwrap()
            .kept_items,
        vec!["Question: What can change?".to_string()]
    );

    // Messages sent to an ended session are refused after restart.
    let late_msg = alice.post_private(&session.session_id, &priv_focus, "still there?", 210)?;
    assert!(bob_restarted.receive_private(late_msg).is_err());

    Ok(())
}

#[test]
fn revocation_blocks_pending_and_new_calls_while_disconnect_also_ends_active() -> Result<()> {
    let alice_kp = Keypair::generate();
    let bob_kp = Keypair::generate();
    let mut alice = ParticipantClient::new(alice_kp);
    let mut bob = ParticipantClient::new(bob_kp.clone());

    let perm = bob.grant_contact(
        alice.did(),
        "endpoint://bob-02".into(),
        vec![ContactMode::LiveCall],
        500,
    )?;
    alice.receive_permission(perm.clone())?;

    // Accept one live session first.
    let inv1 = alice.send_invitation(&perm.permission_id, ContactMode::LiveCall, "call 1".into(), 10, 100)?;
    bob.receive_invitation(inv1.clone(), 11)?;
    let sess1 = bob.accept_invitation(&inv1.invitation_id, 12)?;
    alice.sync_accepted_session(sess1.clone())?;

    // Send a second pending invitation.
    let inv2 = alice.send_invitation(&perm.permission_id, ContactMode::LiveCall, "call 2".into(), 20, 100)?;
    bob.receive_invitation(inv2.clone(), 21)?;

    // Revoking permission cancels pending inv2 and blocks acceptance,
    // but leaves already-accepted sess1 alive under its own session authorization.
    let revoked_perm = bob.revoke_permission(&perm.permission_id)?;
    assert_eq!(bob.inbox_state(&inv2.invitation_id), Some(&InvitationState::Revoked));
    assert!(bob.accept_invitation(&inv2.invitation_id, 25).is_err());
    assert_eq!(bob.session(&sess1.session_id).unwrap().status, SessionStatus::Active);

    // Anti-rollback: Alice receives the revocation, then tries to replay the older permission.
    alice.receive_permission(revoked_perm)?;
    assert!(alice.receive_permission(perm.clone()).is_err());
    assert!(alice
        .send_invitation(&perm.permission_id, ContactMode::LiveCall, "call 3".into(), 30, 100)
        .is_err());

    // Revocation survives client restart.
    let snap = bob.snapshot();
    let mut bob_restored = ParticipantClient::restore(snap, bob_kp)?;
    assert!(bob_restored.accept_invitation(&inv2.invitation_id, 35).is_err());

    // Explicit disconnect revokes and ends the active session too.
    bob_restored.disconnect(&perm.permission_id, 40)?;
    assert!(matches!(
        bob_restored.session(&sess1.session_id).unwrap().status,
        SessionStatus::Ended { .. }
    ));

    Ok(())
}

#[test]
fn ignore_leaves_no_acceptance_and_mode_limits_are_enforced() -> Result<()> {
    let alice_kp = Keypair::generate();
    let bob_kp = Keypair::generate();
    let mut alice = ParticipantClient::new(alice_kp);
    let mut bob = ParticipantClient::new(bob_kp);

    let perm = bob.grant_contact(
        alice.did(),
        "endpoint://bob-03".into(),
        vec![ContactMode::LiveCall],
        500,
    )?;
    alice.receive_permission(perm.clone())?;

    // AsyncMessage is not in allowed_modes -> refused.
    assert!(alice
        .send_invitation(
            &perm.permission_id,
            ContactMode::AsyncMessage,
            "unsolicited async note".into(),
            10,
            100,
        )
        .is_err());

    // Ignoring keeps invitation pending until it expires; silence never accepts.
    let inv = alice.send_invitation(
        &perm.permission_id,
        ContactMode::LiveCall,
        "quick hello".into(),
        10,
        50,
    )?;
    bob.receive_invitation(inv.clone(), 12)?;
    bob.ignore_invitation(&inv.invitation_id)?;
    assert_eq!(bob.inbox_state(&inv.invitation_id), Some(&InvitationState::Pending));

    // Past expiry (10 + 50 = 60), acceptance fails and marks Expired.
    assert!(bob.accept_invitation(&inv.invitation_id, 61).is_err());
    assert_eq!(bob.inbox_state(&inv.invitation_id), Some(&InvitationState::Expired));

    Ok(())
}

#[test]
fn temporary_handoff_leaves_only_lifecycle_attestation_and_clean_item() -> Result<()> {
    let alice = Keypair::generate().did();
    let bob = Keypair::generate().did();
    let secret_payload = b"confidential draft constraint".to_vec();

    let mut handoff = TemporaryHandoff::open("commons/dock-04", 1000, 60)?;
    handoff.admit(alice.clone(), 1001)?;
    handoff.admit(bob.clone(), 1002)?;

    // Third participant is refused.
    let carol = Keypair::generate().did();
    assert!(handoff.admit(carol, 1003).is_err());

    handoff.offer_item(
        &alice,
        DeliveredItem {
            title: "Constraint Note".into(),
            media_type: "text/plain".into(),
            bytes: secret_payload.clone(),
        },
        1010,
    )?;

    // Sender cannot accept their own item; recipient takes it cleanly.
    assert!(handoff.accept_item(&alice, 1011).is_err());
    let received = handoff.accept_item(&bob, 1012)?;
    assert_eq!(received.bytes, secret_payload);

    // Close consumes the room and returns ONLY the signed lifecycle attestation.
    let attestation = handoff.close(1020)?;
    attestation.verify()?;

    // Verify zero participant or content leakage in the attestation JSON.
    let att_json = serde_json::to_string(&attestation).unwrap();
    assert!(!att_json.contains(alice.as_str()));
    assert!(!att_json.contains(bob.as_str()));
    assert!(!att_json.contains("Constraint Note"));
    assert!(!att_json.contains("confidential"));

    // Verify zero exchange provenance leakage in the retained item JSON.
    let item_json = serde_json::to_string(&received).unwrap();
    assert!(!item_json.contains(alice.as_str()));
    assert!(!item_json.contains(bob.as_str()));
    assert!(!item_json.contains(attestation.room_key.as_str()));
    assert!(!item_json.contains("commons/dock-04"));

    // Attestation rejects unknown injected fields (e.g. a leaked roster).
    let mut bad_att = serde_json::to_value(&attestation).unwrap();
    bad_att["participants"] = serde_json::json!([alice.as_str(), bob.as_str()]);
    assert!(serde_json::from_value::<HandoffAttestation>(bad_att).is_err());

    Ok(())
}
