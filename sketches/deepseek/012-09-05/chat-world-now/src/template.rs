use crate::did::DidKey;
use crate::error::Result;
use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ModeratorSpec {
    pub moderator_id: DidKey,
    pub moderator_type: String,
    pub capabilities: Vec<String>,
    pub can_be_overridden: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub knowledge_world_id: Option<DidKey>,
    #[serde(default, skip_serializing_if = "is_false")]
    pub meta_room: bool,
}

fn is_false(b: &bool) -> bool { !*b }

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct RoomTemplate {
    pub template_id: String,
    pub topic: String,
    pub max_msg_len: u64,
    pub rate_limit_count: u64,
    pub rate_limit_window: u64,
    pub join_policy: String,
    pub moderation: String,
    pub membership: String,
    pub inter_ai_pace: u64,
    pub mode: String,
    pub personal: bool,
    pub redaction_rules: Vec<String>,
    /// Signing mode. `1` (default): the room signs every record
    /// (dual-sign). `N > 1`: the room signs a head every N
    /// records appended after the seed; individual records carry
    /// only their author's proof.
    pub head_interval: u64,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub welcome: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub moderator: Option<ModeratorSpec>,
    /// How many are in the room is shown outside it, unless this
    /// is set. Left out of what is written when it is not set, so
    /// a law written before this field hashes as it did.
    #[serde(default, skip_serializing_if = "is_false")]
    pub count_hidden: bool,
}

impl RoomTemplate {
    pub fn chat(template_id: &str, topic: &str) -> Self {
        RoomTemplate {
            template_id: template_id.into(),
            topic: topic.into(),
            max_msg_len: 4000,
            rate_limit_count: 10,
            rate_limit_window: 20,
            join_policy: "open".into(),
            moderation: "moderator".into(),
            membership: "mixed".into(),
            inter_ai_pace: 0,
            mode: "async".into(),
            personal: false,
            redaction_rules: vec![
                "author_request".into(),
                "spam".into(),
                "low_effort".into(),
                "off_topic".into(),
                "harassment".into(),
                "private_info".into(),
            ],
            head_interval: 1,
            welcome: None,
            moderator: None,
            count_hidden: false,
        }
    }

    pub fn personal_home(topic: &str) -> Self {
        RoomTemplate {
            template_id: "home-v1".into(),
            topic: topic.into(),
            max_msg_len: 8000,
            rate_limit_count: 100,
            rate_limit_window: 100,
            join_policy: "invite".into(),
            moderation: "author_only".into(),
            membership: "human_only".into(),
            inter_ai_pace: 0,
            mode: "async".into(),
            personal: true,
            redaction_rules: vec![
                "author_request".into(),
                "private_info".into(),
            ],
            head_interval: 1,
            welcome: None,
            moderator: None,
            count_hidden: true,
        }
    }

    pub fn hash(&self) -> Result<String> {
        crate::hash::hash_of(self)
    }
}
