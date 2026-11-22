//! Continuing participant client, consent-first private contact protocol,
//! and zero-trail temporary handoff rooms.
//!
//! All timestamps are externally supplied (`u64` ticks or epoch seconds)
//! so expiry, deferral, and restart behavior are deterministic and auditable.

use crate::did::{DidKey, Keypair};
use crate::error::{Error, Result};
use crate::hash::{body_for_signing, sha256_hex};
use crate::proof::{Proof, ProofOrArray};
use serde::{Deserialize, Serialize};
use std::collections::{HashMap, HashSet};

/// Communication modes must be enabled explicitly; permission to request a
/// live call does not grant permission to deposit asynchronous messages.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ContactMode {
    LiveCall,
    AsyncMessage,
}

/// Signed permission authorizing one specific peer to request contact via
/// an authenticated endpoint, with explicit modes, expiry, and revision.
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ContactPermission {
    pub permission_id: String,
    pub grantor: DidKey,
    pub grantee: DidKey,
    pub endpoint: String,
    pub allowed_modes: Vec<ContactMode>,
    pub revision: u64,
    pub expires_at: u64,
    pub revoked: bool,
    pub proof: ProofOrArray,
}

impl ContactPermission {
    pub fn issue(
        grantor_kp: &Keypair,
        grantee: DidKey,
        endpoint: String,
        allowed_modes: Vec<ContactMode>,
        expires_at: u64,
    ) -> Result<Self> {
        let grantor = grantor_kp.did();
        if grantor == grantee {
            return Err(Error::Policy("cannot grant contact permission to self".into()));
        }
        if endpoint.trim().is_empty() {
            return Err(Error::Policy("contact endpoint cannot be empty".into()));
        }
        if allowed_modes.is_empty() {
            return Err(Error::Policy("allowed_modes cannot be empty".into()));
        }
        let id_seed = format!("perm|{}|{}|{}", grantor.as_str(), grantee.as_str(), endpoint);
        let permission_id = format!("perm:{}", &sha256_hex(id_seed.as_bytes())[..16]);

        let mut perm = ContactPermission {
            permission_id,
            grantor,
            grantee,
            endpoint,
            allowed_modes,
            revision: 1,
            expires_at,
            revoked: false,
            proof: ProofOrArray::placeholder(),
        };
        let body = body_for_signing(&perm)?;
        let sig = grantor_kp.sign(&body);
        perm.proof = ProofOrArray::single(Proof::create(grantor_kp, &sig));
        Ok(perm)
    }

    /// Produce a signed revocation at `revision + 1`.
    pub fn revoke(&self, grantor_kp: &Keypair) -> Result<Self> {
        if grantor_kp.did() != self.grantor {
            return Err(Error::Policy("only the grantor can revoke a permission".into()));
        }
        let mut next = self.clone();
        next.revision = self.revision + 1;
        next.revoked = true;
        next.proof = ProofOrArray::placeholder();
        let body = body_for_signing(&next)?;
        let sig = grantor_kp.sign(&body);
        next.proof = ProofOrArray::single(Proof::create(grantor_kp, &sig));
        Ok(next)
    }

    pub fn verify(&self) -> Result<()> {
        if self.grantor == self.grantee {
            return Err(Error::Policy("contact permission: grantor == grantee".into()));
        }
        if self.revision == 0 {
            return Err(Error::Verification("contact permission: revision must be >= 1".into()));
        }
        let body = body_for_signing(self)?;
        let proof = self
            .proof
            .find_by_method(&self.grantor)
            .ok_or_else(|| Error::Verification("contact permission: missing grantor proof".into()))?;
        proof.verify(&body)
    }
}

/// One bounded proposal to open a private session under a granted permission.
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ContactInvitation {
    pub invitation_id: String,
    pub caller: DidKey,
    pub recipient: DidKey,
    pub permission_id: String,
    pub permission_revision: u64,
    pub mode: ContactMode,
    pub purpose: String,
    pub created_at: u64,
    pub expires_at: u64,
    pub proof: ProofOrArray,
}

impl ContactInvitation {
    pub fn create(
        caller_kp: &Keypair,
        perm: &ContactPermission,
        mode: ContactMode,
        purpose: String,
        now: u64,
        ttl: u64,
    ) -> Result<Self> {
        perm.verify()?;
        if caller_kp.did() != perm.grantee {
            return Err(Error::Policy("caller is not the permission grantee".into()));
        }
        if perm.revoked {
            return Err(Error::Policy("cannot invite using a revoked permission".into()));
        }
        if now > perm.expires_at {
            return Err(Error::Policy("cannot invite using an expired permission".into()));
        }
        if !perm.allowed_modes.contains(&mode) {
            return Err(Error::Policy("requested contact mode not permitted".into()));
        }
        if ttl == 0 {
            return Err(Error::Policy("invitation ttl must be positive".into()));
        }
        let expires_at = now.saturating_add(ttl).min(perm.expires_at);
        let id_seed = format!(
            "inv|{}|{}|{}|{}|{}",
            caller_kp.did().as_str(),
            perm.grantor.as_str(),
            perm.permission_id,
            now,
            purpose
        );
        let invitation_id = format!("inv:{}", &sha256_hex(id_seed.as_bytes())[..16]);

        let mut inv = ContactInvitation {
            invitation_id,
            caller: caller_kp.did(),
            recipient: perm.grantor.clone(),
            permission_id: perm.permission_id.clone(),
            permission_revision: perm.revision,
            mode,
            purpose,
            created_at: now,
            expires_at,
            proof: ProofOrArray::placeholder(),
        };
        let body = body_for_signing(&inv)?;
        let sig = caller_kp.sign(&body);
        inv.proof = ProofOrArray::single(Proof::create(caller_kp, &sig));
        Ok(inv)
    }

    pub fn verify(&self) -> Result<()> {
        if self.caller == self.recipient {
            return Err(Error::Policy("contact invitation: caller == recipient".into()));
        }
        if self.expires_at < self.created_at {
            return Err(Error::Verification("contact invitation: expires_at < created_at".into()));
        }
        let body = body_for_signing(self)?;
        let proof = self
            .proof
            .find_by_method(&self.caller)
            .ok_or_else(|| Error::Verification("contact invitation: missing caller proof".into()))?;
        proof.verify(&body)
    }
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum InvitationState {
    Pending,
    Deferred { note: Option<String> },
    Accepted { session_id: String },
    Declined,
    Cancelled,
    Expired,
    Revoked,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum SessionStatus {
    Active,
    OnHold,
    Ended { ended_by: DidKey, at: u64 },
}

/// An accepted period of live exchange. Its lifecycle is separate from the
/// persistent `ConversationSpace` and from future contact permissions.
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CallSession {
    pub session_id: String,
    pub conversation_id: String,
    pub invitation_id: String,
    pub participants: [DidKey; 2],
    pub status: SessionStatus,
    pub started_at: u64,
    pub expires_at: Option<u64>,
}

/// A signed private message bound explicitly to one conversation and session,
/// preventing stale or misrouted replies from reaching the wrong audience.
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct PrivateMessage {
    pub conversation_id: String,
    pub session_id: String,
    pub seq: u64,
    pub sender: DidKey,
    pub recipient: DidKey,
    pub text: String,
    pub ts: u64,
    pub proof: ProofOrArray,
}

impl PrivateMessage {
    pub fn verify(&self) -> Result<()> {
        if self.sender == self.recipient {
            return Err(Error::Policy("private message: sender == recipient".into()));
        }
        let body = body_for_signing(self)?;
        let proof = self
            .proof
            .find_by_method(&self.sender)
            .ok_or_else(|| Error::Verification("private message: missing sender proof".into()))?;
        proof.verify(&body)
    }
}

/// A continuing private thread between a fixed pair of participants.
/// Outlives individual live sessions and holds items both chose to keep.
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ConversationSpace {
    pub conversation_id: String,
    pub participants: [DidKey; 2],
    pub messages: Vec<PrivateMessage>,
    pub kept_items: Vec<String>,
}

/// Where the participant's active attention is currently directed.
/// Changing focus never alters public-room membership or private sessions.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum AttentionFocus {
    Lobby,
    PublicRoom(DidKey),
    PrivateSession(String),
    Conversation(String),
}

/// Durable serialized state of a continuing participant client.
/// Never contains the participant's private `Keypair`.
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ClientSnapshot {
    pub participant_id: DidKey,
    pub focus: AttentionFocus,
    pub public_rooms: HashSet<DidKey>,
    pub granted_permissions: HashMap<String, ContactPermission>,
    pub received_permissions: HashMap<String, ContactPermission>,
    pub inbox: HashMap<String, (ContactInvitation, InvitationState)>,
    pub outbox: HashMap<String, (ContactInvitation, InvitationState)>,
    pub sessions: HashMap<String, CallSession>,
    pub conversations: HashMap<String, ConversationSpace>,
}

pub fn pair_conversation_id(a: &DidKey, b: &DidKey) -> String {
    let (first, second) = if a.as_str() <= b.as_str() {
        (a.as_str(), b.as_str())
    } else {
        (b.as_str(), a.as_str())
    };
    let seed = format!("conv|{first}|{second}");
    format!("conv:{}", &sha256_hex(seed.as_bytes())[..16])
}

/// Continuing private client whose lifetime is independent of any room.
pub struct ParticipantClient {
    keypair: Keypair,
    focus: AttentionFocus,
    public_rooms: HashSet<DidKey>,
    granted_permissions: HashMap<String, ContactPermission>,
    received_permissions: HashMap<String, ContactPermission>,
    inbox: HashMap<String, (ContactInvitation, InvitationState)>,
    outbox: HashMap<String, (ContactInvitation, InvitationState)>,
    sessions: HashMap<String, CallSession>,
    conversations: HashMap<String, ConversationSpace>,
}

impl ParticipantClient {
    pub fn new(keypair: Keypair) -> Self {
        ParticipantClient {
            keypair,
            focus: AttentionFocus::Lobby,
            public_rooms: HashSet::new(),
            granted_permissions: HashMap::new(),
            received_permissions: HashMap::new(),
            inbox: HashMap::new(),
            outbox: HashMap::new(),
            sessions: HashMap::new(),
            conversations: HashMap::new(),
        }
    }

    pub fn did(&self) -> DidKey {
        self.keypair.did()
    }

    pub fn focus(&self) -> &AttentionFocus {
        &self.focus
    }

    pub fn set_focus(&mut self, focus: AttentionFocus) {
        self.focus = focus;
    }

    pub fn enter_public_room(&mut self, room_id: DidKey) {
        self.public_rooms.insert(room_id.clone());
        self.focus = AttentionFocus::PublicRoom(room_id);
    }

    pub fn leave_public_room(&mut self, room_id: &DidKey) {
        self.public_rooms.remove(room_id);
        if self.focus == AttentionFocus::PublicRoom(room_id.clone()) {
            self.focus = AttentionFocus::Lobby;
        }
    }

    pub fn public_rooms(&self) -> &HashSet<DidKey> {
        &self.public_rooms
    }

    pub fn inbox_state(&self, invitation_id: &str) -> Option<&InvitationState> {
        self.inbox.get(invitation_id).map(|(_, st)| st)
    }

    pub fn session(&self, session_id: &str) -> Option<&CallSession> {
        self.sessions.get(session_id)
    }

    pub fn conversation(&self, conversation_id: &str) -> Option<&ConversationSpace> {
        self.conversations.get(conversation_id)
    }

    pub fn snapshot(&self) -> ClientSnapshot {
        ClientSnapshot {
            participant_id: self.did(),
            focus: self.focus.clone(),
            public_rooms: self.public_rooms.clone(),
            granted_permissions: self.granted_permissions.clone(),
            received_permissions: self.received_permissions.clone(),
            inbox: self.inbox.clone(),
            outbox: self.outbox.clone(),
            sessions: self.sessions.clone(),
            conversations: self.conversations.clone(),
        }
    }

    pub fn restore(snapshot: ClientSnapshot, keypair: Keypair) -> Result<Self> {
        if keypair.did() != snapshot.participant_id {
            return Err(Error::Verification(
                "client restore: keypair does not match snapshot participant_id".into(),
            ));
        }
        for perm in snapshot.granted_permissions.values() {
            perm.verify()?;
        }
        for perm in snapshot.received_permissions.values() {
            perm.verify()?;
        }
        for (inv, _) in snapshot.inbox.values() {
            inv.verify()?;
        }
        for (inv, _) in snapshot.outbox.values() {
            inv.verify()?;
        }
        for conv in snapshot.conversations.values() {
            for msg in &conv.messages {
                msg.verify()?;
            }
        }
        Ok(ParticipantClient {
            keypair,
            focus: snapshot.focus,
            public_rooms: snapshot.public_rooms,
            granted_permissions: snapshot.granted_permissions,
            received_permissions: snapshot.received_permissions,
            inbox: snapshot.inbox,
            outbox: snapshot.outbox,
            sessions: snapshot.sessions,
            conversations: snapshot.conversations,
        })
    }

    /// Deliberately grant one peer a scoped contact permission.
    pub fn grant_contact(
        &mut self,
        grantee: DidKey,
        endpoint: String,
        allowed_modes: Vec<ContactMode>,
        expires_at: u64,
    ) -> Result<ContactPermission> {
        let perm = ContactPermission::issue(
            &self.keypair,
            grantee,
            endpoint,
            allowed_modes,
            expires_at,
        )?;
        self.granted_permissions
            .insert(perm.permission_id.clone(), perm.clone());
        Ok(perm)
    }

    /// Record a permission received from a peer, enforcing monotonic revisions
    /// so an older unrevoked copy cannot roll back a newer revocation.
    pub fn receive_permission(&mut self, perm: ContactPermission) -> Result<()> {
        perm.verify()?;
        if perm.grantee != self.did() {
            return Err(Error::Policy("permission is not addressed to this client".into()));
        }
        if let Some(existing) = self.received_permissions.get(&perm.permission_id) {
            if perm.grantor != existing.grantor {
                return Err(Error::Verification("permission grantor mismatch".into()));
            }
            if perm.revision < existing.revision {
                return Err(Error::Policy(
                    "permission rollback refused: older revision than stored".into(),
                ));
            }
        }
        self.received_permissions
            .insert(perm.permission_id.clone(), perm);
        Ok(())
    }

    /// Revoke future and pending uses of a permission. Already-accepted
    /// sessions keep their own separate lifecycle until ended or disconnected.
    pub fn revoke_permission(&mut self, permission_id: &str) -> Result<ContactPermission> {
        let current = self
            .granted_permissions
            .get(permission_id)
            .ok_or_else(|| Error::Policy("permission not found".into()))?
            .clone();
        let revoked = current.revoke(&self.keypair)?;
        self.granted_permissions
            .insert(permission_id.to_string(), revoked.clone());

        for (inv, st) in self.inbox.values_mut() {
            if inv.permission_id == permission_id
                && matches!(st, InvitationState::Pending | InvitationState::Deferred { .. })
            {
                *st = InvitationState::Revoked;
            }
        }
        Ok(revoked)
    }

    /// Revoke future contact AND unilaterally end all active/held sessions with that peer.
    pub fn disconnect(&mut self, permission_id: &str, now: u64) -> Result<ContactPermission> {
        let revoked = self.revoke_permission(permission_id)?;
        let peer = revoked.grantee.clone();
        let me = self.did();
        let mut ended_ids = Vec::new();
        for (sid, sess) in self.sessions.iter_mut() {
            let involves_peer = sess.participants.iter().any(|p| p == &peer);
            if involves_peer && !matches!(sess.status, SessionStatus::Ended { .. }) {
                sess.status = SessionStatus::Ended {
                    ended_by: me.clone(),
                    at: now,
                };
                ended_ids.push(sid.clone());
            }
        }
        if let AttentionFocus::PrivateSession(active_sid) = &self.focus {
            if ended_ids.contains(active_sid) {
                self.focus = AttentionFocus::Lobby;
            }
        }
        Ok(revoked)
    }

    /// Create and record an outgoing invitation under a received permission.
    pub fn send_invitation(
        &mut self,
        permission_id: &str,
        mode: ContactMode,
        purpose: String,
        now: u64,
        ttl: u64,
    ) -> Result<ContactInvitation> {
        let perm = self
            .received_permissions
            .get(permission_id)
            .ok_or_else(|| Error::Policy("no received permission with that id".into()))?
            .clone();
        let inv = ContactInvitation::create(&self.keypair, &perm, mode, purpose, now, ttl)?;
        self.outbox
            .insert(inv.invitation_id.clone(), (inv.clone(), InvitationState::Pending));
        Ok(inv)
    }

    /// Deliver an invitation to the recipient's durable inbox.
    /// Idempotent on duplicate delivery of the same `invitation_id`.
    pub fn receive_invitation(&mut self, inv: ContactInvitation, now: u64) -> Result<()> {
        inv.verify()?;
        if inv.recipient != self.did() {
            return Err(Error::Policy("invitation addressed to another recipient".into()));
        }
        if self.inbox.contains_key(&inv.invitation_id) {
            return Ok(());
        }
        let perm = self
            .granted_permissions
            .get(&inv.permission_id)
            .ok_or_else(|| Error::Policy("unknown contact permission".into()))?;
        if perm.revoked {
            return Err(Error::Policy("contact permission has been revoked".into()));
        }
        if inv.permission_revision != perm.revision {
            return Err(Error::Policy("invitation uses stale permission revision".into()));
        }
        if perm.grantee != inv.caller {
            return Err(Error::Policy("invitation caller does not match permission grantee".into()));
        }
        if !perm.allowed_modes.contains(&inv.mode) {
            return Err(Error::Policy("invitation mode not allowed by permission".into()));
        }
        if now > perm.expires_at || now > inv.expires_at {
            return Err(Error::Policy("invitation or permission has expired".into()));
        }
        self.inbox
            .insert(inv.invitation_id.clone(), (inv, InvitationState::Pending));
        Ok(())
    }

    /// Leave an invitation pending with an optional private deferral note.
    pub fn defer_invitation(
        &mut self,
        invitation_id: &str,
        note: Option<String>,
        now: u64,
    ) -> Result<()> {
        let (inv, st) = self
            .inbox
            .get_mut(invitation_id)
            .ok_or_else(|| Error::Policy("invitation not found in inbox".into()))?;
        if now > inv.expires_at {
            *st = InvitationState::Expired;
            return Err(Error::Policy("invitation expired".into()));
        }
        if !matches!(st, InvitationState::Pending | InvitationState::Deferred { .. }) {
            return Err(Error::Policy("invitation is no longer open".into()));
        }
        *st = InvitationState::Deferred { note };
        Ok(())
    }

    /// Explicitly decline a pending or deferred invitation.
    pub fn decline_invitation(&mut self, invitation_id: &str) -> Result<()> {
        let (_, st) = self
            .inbox
            .get_mut(invitation_id)
            .ok_or_else(|| Error::Policy("invitation not found in inbox".into()))?;
        if !matches!(st, InvitationState::Pending | InvitationState::Deferred { .. }) {
            return Err(Error::Policy("invitation is no longer open".into()));
        }
        *st = InvitationState::Declined;
        Ok(())
    }

    /// Ignore an invitation without altering state or emitting any record;
    /// silence never counts as acceptance, and expiry closes it naturally.
    pub fn ignore_invitation(&self, invitation_id: &str) -> Result<()> {
        if !self.inbox.contains_key(invitation_id) {
            return Err(Error::Policy("invitation not found in inbox".into()));
        }
        Ok(())
    }

    /// Caller cancels an unaccepted outgoing invitation.
    pub fn cancel_invitation(&mut self, invitation_id: &str) -> Result<()> {
        let (_, st) = self
            .outbox
            .get_mut(invitation_id)
            .ok_or_else(|| Error::Policy("invitation not found in outbox".into()))?;
        if !matches!(st, InvitationState::Pending | InvitationState::Deferred { .. }) {
            return Err(Error::Policy("invitation cannot be cancelled in current state".into()));
        }
        *st = InvitationState::Cancelled;
        Ok(())
    }

    /// Recipient accepts a still-valid invitation, creating a `CallSession`
    /// and ensuring the shared `ConversationSpace` exists. Public-room
    /// memberships remain completely untouched.
    pub fn accept_invitation(&mut self, invitation_id: &str, now: u64) -> Result<CallSession> {
        let (inv, is_open) = {
            let (inv, st) = self
                .inbox
                .get(invitation_id)
                .ok_or_else(|| Error::Policy("invitation not found in inbox".into()))?;
            (
                inv.clone(),
                matches!(st, InvitationState::Pending | InvitationState::Deferred { .. }),
            )
        };
        if !is_open {
            return Err(Error::Policy("invitation is no longer open".into()));
        }
        if now > inv.expires_at {
            if let Some((_, st)) = self.inbox.get_mut(invitation_id) {
                *st = InvitationState::Expired;
            }
            return Err(Error::Policy("invitation expired".into()));
        }
        let perm = self
            .granted_permissions
            .get(&inv.permission_id)
            .ok_or_else(|| Error::Policy("contact permission not found".into()))?;
        if perm.revoked || perm.revision != inv.permission_revision {
            if let Some((_, st)) = self.inbox.get_mut(invitation_id) {
                *st = InvitationState::Revoked;
            }
            return Err(Error::Policy("contact permission revoked or superseded".into()));
        }
        if now > perm.expires_at {
            return Err(Error::Policy("contact permission expired".into()));
        }

        let conversation_id = pair_conversation_id(&inv.caller, &inv.recipient);
        let session_id = format!("sess:{}", inv.invitation_id);
        let session = CallSession {
            session_id: session_id.clone(),
            conversation_id: conversation_id.clone(),
            invitation_id: inv.invitation_id.clone(),
            participants: [inv.caller.clone(), inv.recipient.clone()],
            status: SessionStatus::Active,
            started_at: now,
            expires_at: None,
        };

        self.sessions.insert(session_id.clone(), session.clone());
        self.conversations
            .entry(conversation_id.clone())
            .or_insert_with(|| ConversationSpace {
                conversation_id,
                participants: [inv.caller.clone(), inv.recipient.clone()],
                messages: Vec::new(),
                kept_items: Vec::new(),
            });
        if let Some((_, st)) = self.inbox.get_mut(invitation_id) {
            *st = InvitationState::Accepted { session_id };
        }
        Ok(session)
    }

    /// Caller records that the recipient accepted their outgoing invitation.
    pub fn sync_accepted_session(&mut self, session: CallSession) -> Result<()> {
        let (inv, st) = self
            .outbox
            .get_mut(&session.invitation_id)
            .ok_or_else(|| Error::Policy("outgoing invitation not found".into()))?;
        if !matches!(st, InvitationState::Pending | InvitationState::Deferred { .. }) {
            return Err(Error::Policy("outgoing invitation is no longer pending".into()));
        }
        if !session.participants.contains(&inv.caller)
            || !session.participants.contains(&inv.recipient)
        {
            return Err(Error::Verification("session participants do not match invitation".into()));
        }
        *st = InvitationState::Accepted {
            session_id: session.session_id.clone(),
        };
        let conv_id = session.conversation_id.clone();
        let parts = session.participants.clone();
        self.sessions.insert(session.session_id.clone(), session);
        self.conversations
            .entry(conv_id.clone())
            .or_insert_with(|| ConversationSpace {
                conversation_id: conv_id,
                participants: parts,
                messages: Vec::new(),
                kept_items: Vec::new(),
            });
        Ok(())
    }

    pub fn hold_session(&mut self, session_id: &str) -> Result<()> {
        let sess = self
            .sessions
            .get_mut(session_id)
            .ok_or_else(|| Error::Policy("session not found".into()))?;
        if sess.status != SessionStatus::Active {
            return Err(Error::Policy("only an active session can be placed on hold".into()));
        }
        sess.status = SessionStatus::OnHold;
        Ok(())
    }

    pub fn resume_session(&mut self, session_id: &str) -> Result<()> {
        let sess = self
            .sessions
            .get_mut(session_id)
            .ok_or_else(|| Error::Policy("session not found".into()))?;
        if sess.status != SessionStatus::OnHold {
            return Err(Error::Policy("only a held session can be resumed".into()));
        }
        sess.status = SessionStatus::Active;
        Ok(())
    }

    /// Unilaterally end participation in a live session without requiring peer cooperation.
    pub fn end_session(&mut self, session_id: &str, now: u64) -> Result<()> {
        let me = self.did();
        let sess = self
            .sessions
            .get_mut(session_id)
            .ok_or_else(|| Error::Policy("session not found".into()))?;
        if matches!(sess.status, SessionStatus::Ended { .. }) {
            return Ok(());
        }
        sess.status = SessionStatus::Ended {
            ended_by: me,
            at: now,
        };
        if self.focus == AttentionFocus::PrivateSession(session_id.to_string()) {
            self.focus = AttentionFocus::Lobby;
        }
        Ok(())
    }

    /// Send a private message bound to `session_id`. Requires `expected_focus`
    /// to match the client's current `AttentionFocus` so a stale reply cannot
    /// accidentally fire into a public room or a different private thread.
    pub fn post_private(
        &mut self,
        session_id: &str,
        expected_focus: &AttentionFocus,
        text: &str,
        now: u64,
    ) -> Result<PrivateMessage> {
        let required_focus = AttentionFocus::PrivateSession(session_id.to_string());
        if &self.focus != expected_focus || expected_focus != &required_focus {
            return Err(Error::Policy(
                "destination safety check failed: current focus does not match target session"
                    .into(),
            ));
        }
        let sess = self
            .sessions
            .get(session_id)
            .ok_or_else(|| Error::Policy("session not found".into()))?;
        if sess.status != SessionStatus::Active {
            return Err(Error::Policy("session is not active".into()));
        }
        if let Some(exp) = sess.expires_at {
            if now > exp {
                return Err(Error::Policy("session has expired".into()));
            }
        }
        let me = self.did();
        let peer = if sess.participants[0] == me {
            sess.participants[1].clone()
        } else if sess.participants[1] == me {
            sess.participants[0].clone()
        } else {
            return Err(Error::Policy("client is not a participant in this session".into()));
        };
        let conv_id = sess.conversation_id.clone();
        let conv = self
            .conversations
            .get_mut(&conv_id)
            .ok_or_else(|| Error::Policy("conversation space missing".into()))?;
        let seq = conv.messages.len() as u64;

        let mut msg = PrivateMessage {
            conversation_id: conv_id,
            session_id: session_id.to_string(),
            seq,
            sender: me,
            recipient: peer,
            text: text.to_string(),
            ts: now,
            proof: ProofOrArray::placeholder(),
        };
        let body = body_for_signing(&msg)?;
        let sig = self.keypair.sign(&body);
        msg.proof = ProofOrArray::single(Proof::create(&self.keypair, &sig));
        conv.messages.push(msg.clone());
        Ok(msg)
    }

    /// Receive a private message from a peer. Allowed while the session is
    /// `Active` or `OnHold`; refused once the session has `Ended`.
    pub fn receive_private(&mut self, msg: PrivateMessage) -> Result<()> {
        msg.verify()?;
        if msg.recipient != self.did() {
            return Err(Error::Policy("private message addressed to another recipient".into()));
        }
        let sess = self
            .sessions
            .get(&msg.session_id)
            .ok_or_else(|| Error::Policy("unknown session".into()))?;
        if matches!(sess.status, SessionStatus::Ended { .. }) {
            return Err(Error::Policy("session has ended".into()));
        }
        if sess.conversation_id != msg.conversation_id {
            return Err(Error::Verification("message conversation_id mismatch".into()));
        }
        if !sess.participants.contains(&msg.sender) {
            return Err(Error::Policy("sender is not a participant in this session".into()));
        }
        let conv = self
            .conversations
            .get_mut(&msg.conversation_id)
            .ok_or_else(|| Error::Policy("conversation space missing".into()))?;
        if conv
            .messages
            .iter()
            .any(|m| m.seq == msg.seq && m.sender == msg.sender)
        {
            return Ok(());
        }
        conv.messages.push(msg);
        Ok(())
    }

    /// Save a deliberate note or shared artifact reference onto the conversation table.
    pub fn keep_in_conversation(&mut self, conversation_id: &str, note: String) -> Result<()> {
        let conv = self
            .conversations
            .get_mut(conversation_id)
            .ok_or_else(|| Error::Policy("conversation space not found".into()))?;
        conv.kept_items.push(note);
        Ok(())
    }
}

// =====================================================================
// ZERO-TRAIL TEMPORARY HANDOFF ROOM
// =====================================================================

/// The only record that survives a `TemporaryHandoff`: a signed attestation
/// that a handoff space existed at `location` during `[opened_at, closed_at]`.
/// Carries zero participant IDs, zero message counts, and zero content hashes.
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct HandoffAttestation {
    pub location: String,
    pub room_key: DidKey,
    pub opened_at: u64,
    pub closed_at: u64,
    pub proof: ProofOrArray,
}

impl HandoffAttestation {
    pub fn verify(&self) -> Result<()> {
        if self.location.trim().is_empty() {
            return Err(Error::Verification("handoff attestation: empty location".into()));
        }
        if self.closed_at < self.opened_at {
            return Err(Error::Verification(
                "handoff attestation: closed_at < opened_at".into(),
            ));
        }
        let body = body_for_signing(self)?;
        let proof = self
            .proof
            .find_by_method(&self.room_key)
            .ok_or_else(|| Error::Verification("handoff attestation: missing room proof".into()))?;
        proof.verify(&body)
    }
}

/// Clean payload retained by a recipient. Intentionally carries no room ID,
/// no sender ID, and no exchange timestamp.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct DeliveredItem {
    pub title: String,
    pub media_type: String,
    pub bytes: Vec<u8>,
}

/// Transient in-memory handoff space (deliberately non-serializable).
/// Consumed on `close`, dropping all participant handles and unaccepted data.
pub struct TemporaryHandoff {
    location: String,
    room_kp: Keypair,
    opened_at: u64,
    expires_at: u64,
    participants: Vec<DidKey>,
    pending_item: Option<(DidKey, DeliveredItem)>,
}

impl TemporaryHandoff {
    pub fn open(location: &str, now: u64, ttl: u64) -> Result<Self> {
        if location.trim().is_empty() {
            return Err(Error::Policy("handoff location cannot be empty".into()));
        }
        if ttl == 0 {
            return Err(Error::Policy("handoff ttl must be positive".into()));
        }
        Ok(TemporaryHandoff {
            location: location.to_string(),
            room_kp: Keypair::generate(),
            opened_at: now,
            expires_at: now.saturating_add(ttl),
            participants: Vec::new(),
            pending_item: None,
        })
    }

    pub fn admit(&mut self, participant: DidKey, now: u64) -> Result<()> {
        if now > self.expires_at {
            return Err(Error::Policy("handoff room has expired".into()));
        }
        if self.participants.contains(&participant) {
            return Err(Error::Policy("participant already in handoff room".into()));
        }
        if self.participants.len() >= 2 {
            return Err(Error::Policy("handoff room is limited to two participants".into()));
        }
        self.participants.push(participant);
        Ok(())
    }

    pub fn offer_item(&mut self, sender: &DidKey, item: DeliveredItem, now: u64) -> Result<()> {
        if now > self.expires_at {
            return Err(Error::Policy("handoff room has expired".into()));
        }
        if !self.participants.contains(sender) {
            return Err(Error::Policy("sender is not admitted to handoff room".into()));
        }
        if self.pending_item.is_some() {
            return Err(Error::Policy("an item is already waiting in this handoff room".into()));
        }
        self.pending_item = Some((sender.clone(), item));
        Ok(())
    }

    /// Recipient deliberately takes ownership of the clean `DeliveredItem`,
    /// immediately wiping it from the transient room buffer.
    pub fn accept_item(&mut self, recipient: &DidKey, now: u64) -> Result<DeliveredItem> {
        if now > self.expires_at {
            return Err(Error::Policy("handoff room has expired".into()));
        }
        if !self.participants.contains(recipient) {
            return Err(Error::Policy("recipient is not admitted to handoff room".into()));
        }
        let Some((sender, _)) = &self.pending_item else {
            return Err(Error::Policy("no item waiting in handoff room".into()));
        };
        if sender == recipient {
            return Err(Error::Policy("sender cannot accept their own offered item".into()));
        }
        let (_, item) = self.pending_item.take().unwrap();
        Ok(item)
    }

    /// Consume the temporary room, wiping all transient state and returning
    /// only the signed lifecycle attestation.
    pub fn close(self, now: u64) -> Result<HandoffAttestation> {
        if now < self.opened_at {
            return Err(Error::Policy("close time precedes open time".into()));
        }
        let mut att = HandoffAttestation {
            location: self.location,
            room_key: self.room_kp.did(),
            opened_at: self.opened_at,
            closed_at: now,
            proof: ProofOrArray::placeholder(),
        };
        let body = body_for_signing(&att)?;
        let sig = self.room_kp.sign(&body);
        att.proof = ProofOrArray::single(Proof::create(&self.room_kp, &sig));
        Ok(att)
    }
}
