//! Shared Library: works, fixed editions, byte-checked representations,
//! curated shelves, edition-bound annotations, and read-private lookup.

use crate::did::{DidKey, Keypair};
use crate::error::{Error, Result};
use crate::hash::{body_for_signing, hash_of, sha256_hex};
use crate::proof::{Proof, ProofOrArray};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

fn looks_like_hash(s: &str) -> bool {
    s.len() == 64 && s.chars().all(|c| c.is_ascii_hexdigit())
}

/// Specific, inspectable checks rather than a single undifferentiated "verified" badge.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum VettingLabel {
    AuthorDesignatedEdition,
    FileIdentityChecked,
    FormatRecognized,
    MetadataReviewed,
    PlaintextInspected,
    EditorialReviewAvailable,
    EncryptedClientSideCheckOnly,
}

/// Separates discoverability from file access.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "mode", rename_all = "snake_case")]
pub enum AccessPolicy {
    Public,
    PublicCardRestrictedFile { allowed_readers: Vec<DidKey> },
    PrivatePersonal { owner: DidKey },
    SharedPrivate { allowed_readers: Vec<DidKey> },
}

impl AccessPolicy {
    pub fn is_discoverable_publicly(&self) -> bool {
        matches!(
            self,
            AccessPolicy::Public | AccessPolicy::PublicCardRestrictedFile { .. }
        )
    }

    pub fn is_downloadable_publicly(&self) -> bool {
        matches!(self, AccessPolicy::Public)
    }

    pub fn can_read_file(&self, author: &DidKey, requester: Option<&DidKey>) -> bool {
        match self {
            AccessPolicy::Public => true,
            AccessPolicy::PublicCardRestrictedFile { allowed_readers } => requester
                .map(|r| r == author || allowed_readers.contains(r))
                .unwrap_or(false),
            AccessPolicy::PrivatePersonal { owner } => {
                requester.map(|r| r == owner).unwrap_or(false)
            }
            AccessPolicy::SharedPrivate { allowed_readers } => requester
                .map(|r| r == author || allowed_readers.contains(r))
                .unwrap_or(false),
        }
    }

    pub fn can_discover(&self, author: &DidKey, requester: Option<&DidKey>) -> bool {
        self.is_discoverable_publicly() || self.can_read_file(author, requester)
    }
}

/// Metadata for one concrete downloadable byte representation of an edition.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct FileRepresentation {
    pub format: String,
    pub filename: String,
    pub byte_len: u64,
    pub sha256: String,
    pub is_primary_source: bool,
    pub derived_from_sha256: Option<String>,
    pub encrypted: bool,
}

impl FileRepresentation {
    pub fn verify(&self) -> Result<()> {
        if self.format.trim().is_empty() || self.filename.trim().is_empty() {
            return Err(Error::Verification(
                "file representation: format and filename must be non-empty".into(),
            ));
        }
        if !looks_like_hash(&self.sha256) {
            return Err(Error::Verification(
                "file representation: sha256 must be 64 hex chars".into(),
            ));
        }
        if !self.is_primary_source {
            match &self.derived_from_sha256 {
                Some(parent) if looks_like_hash(parent) => {}
                _ => {
                    return Err(Error::Policy(
                        "derived file representation must cite a 64-hex derived_from_sha256"
                            .into(),
                    ));
                }
            }
        }
        Ok(())
    }
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct EditionDraft {
    pub work_id: String,
    pub title: String,
    pub attribution: String,
    pub description: String,
    pub edition_label: String,
    pub version: u64,
    pub derived_from: Option<String>,
    pub contents_outline: Vec<String>,
    pub sharing_terms: String,
    pub discussion_room: Option<DidKey>,
    pub representations: Vec<FileRepresentation>,
    pub vetting_labels: Vec<VettingLabel>,
    pub access: AccessPolicy,
    pub addresses_annotations: Vec<String>,
    pub published_at: u64,
}

/// Immutable, signed release of one edition of a work.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Edition {
    pub work_id: String,
    pub title: String,
    pub attribution: String,
    pub description: String,
    pub edition_label: String,
    pub version: u64,
    pub derived_from: Option<String>,
    pub contents_outline: Vec<String>,
    pub sharing_terms: String,
    pub discussion_room: Option<DidKey>,
    pub representations: Vec<FileRepresentation>,
    pub vetting_labels: Vec<VettingLabel>,
    pub access: AccessPolicy,
    pub addresses_annotations: Vec<String>,
    pub author: DidKey,
    pub published_at: u64,
    pub proof: ProofOrArray,
}

impl Edition {
    pub fn sign(draft: EditionDraft, author_kp: &Keypair) -> Result<Self> {
        let mut ed = Edition {
            work_id: draft.work_id,
            title: draft.title,
            attribution: draft.attribution,
            description: draft.description,
            edition_label: draft.edition_label,
            version: draft.version,
            derived_from: draft.derived_from,
            contents_outline: draft.contents_outline,
            sharing_terms: draft.sharing_terms,
            discussion_room: draft.discussion_room,
            representations: draft.representations,
            vetting_labels: draft.vetting_labels,
            access: draft.access,
            addresses_annotations: draft.addresses_annotations,
            author: author_kp.did(),
            published_at: draft.published_at,
            proof: ProofOrArray::placeholder(),
        };
        ed.validate_fields()?;
        let body = body_for_signing(&ed)?;
        let sig = author_kp.sign(&body);
        ed.proof = ProofOrArray::single(Proof::create(author_kp, &sig));
        Ok(ed)
    }

    fn validate_fields(&self) -> Result<()> {
        if self.work_id.trim().is_empty() || self.title.trim().is_empty() {
            return Err(Error::Policy(
                "edition: work_id and title must be non-empty".into(),
            ));
        }
        if self.version == 0 {
            return Err(Error::Policy("edition: version must be >= 1".into()));
        }
        if self.version == 1 && self.derived_from.is_some() {
            return Err(Error::Policy(
                "edition: version 1 cannot declare derived_from".into(),
            ));
        }
        if let Some(parent) = &self.derived_from {
            if !looks_like_hash(parent) {
                return Err(Error::Policy(
                    "edition: derived_from must be a 64-hex edition hash".into(),
                ));
            }
        }
        if self.representations.is_empty() {
            return Err(Error::Policy(
                "edition: must include at least one file representation".into(),
            ));
        }
        let mut has_encrypted = false;
        for rep in &self.representations {
            rep.verify()?;
            if rep.encrypted {
                has_encrypted = true;
            }
        }
        if has_encrypted && self.vetting_labels.contains(&VettingLabel::PlaintextInspected) {
            return Err(Error::Policy(
                "edition: cannot claim PlaintextInspected on an encrypted representation".into(),
            ));
        }
        if let AccessPolicy::PrivatePersonal { ref owner } = self.access {
            if owner != &self.author {
                return Err(Error::Policy(
                    "edition: PrivatePersonal owner must match edition author".into(),
                ));
            }
        }
        Ok(())
    }

    pub fn hash(&self) -> Result<String> {
        hash_of(self)
    }

    pub fn verify(&self) -> Result<()> {
        self.validate_fields()?;
        let body = body_for_signing(self)?;
        let proof = self
            .proof
            .find_by_method(&self.author)
            .ok_or_else(|| Error::Verification("edition: missing author proof".into()))?;
        proof.verify(&body)
    }
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "shelf_kind", rename_all = "snake_case")]
pub enum ShelfKind {
    AuthorShelf,
    PersonalShelf,
    RoomShelf { room_id: DidKey },
    QuestionShelf { question: String },
    ReadingPath,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ShelfEntry {
    pub edition_hash: String,
    pub curator_note: String,
    pub guiding_question: Option<String>,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ShelfDraft {
    pub shelf_id: String,
    pub title: String,
    pub kind: ShelfKind,
    pub public: bool,
    pub entries: Vec<ShelfEntry>,
    pub created_at: u64,
}

/// Curated collection of edition references, signed by its curator.
/// Curator notes remain attributable to `curator`, never the work's author.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Shelf {
    pub shelf_id: String,
    pub title: String,
    pub kind: ShelfKind,
    pub public: bool,
    pub entries: Vec<ShelfEntry>,
    pub curator: DidKey,
    pub created_at: u64,
    pub proof: ProofOrArray,
}

impl Shelf {
    pub fn sign(draft: ShelfDraft, curator_kp: &Keypair) -> Result<Self> {
        if draft.shelf_id.trim().is_empty() || draft.title.trim().is_empty() {
            return Err(Error::Policy(
                "shelf: shelf_id and title must be non-empty".into(),
            ));
        }
        for entry in &draft.entries {
            if !looks_like_hash(&entry.edition_hash) {
                return Err(Error::Policy(
                    "shelf entry: edition_hash must be 64 hex chars".into(),
                ));
            }
        }
        let mut shelf = Shelf {
            shelf_id: draft.shelf_id,
            title: draft.title,
            kind: draft.kind,
            public: draft.public,
            entries: draft.entries,
            curator: curator_kp.did(),
            created_at: draft.created_at,
            proof: ProofOrArray::placeholder(),
        };
        let body = body_for_signing(&shelf)?;
        let sig = curator_kp.sign(&body);
        shelf.proof = ProofOrArray::single(Proof::create(curator_kp, &sig));
        Ok(shelf)
    }

    pub fn hash(&self) -> Result<String> {
        hash_of(self)
    }

    pub fn verify(&self) -> Result<()> {
        if self.shelf_id.trim().is_empty() || self.title.trim().is_empty() {
            return Err(Error::Verification(
                "shelf: empty shelf_id or title".into(),
            ));
        }
        for entry in &self.entries {
            if !looks_like_hash(&entry.edition_hash) {
                return Err(Error::Verification(
                    "shelf entry: invalid edition_hash".into(),
                ));
            }
        }
        let body = body_for_signing(self)?;
        let proof = self
            .proof
            .find_by_method(&self.curator)
            .ok_or_else(|| Error::Verification("shelf: missing curator proof".into()))?;
        proof.verify(&body)
    }
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "locator", rename_all = "snake_case")]
pub enum PassageLocator {
    WholeEdition,
    ChapterSection {
        chapter: u64,
        section: Option<String>,
    },
    PageRef {
        page: u64,
    },
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "annotation_kind", rename_all = "snake_case")]
pub enum AnnotationKind {
    Question,
    Commentary,
    ErrataProposal,
    AuthorResponse { in_reply_to: String },
    ComparativeNote { other_edition_hash: String },
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct AnnotationDraft {
    pub edition_hash: String,
    pub locator: PassageLocator,
    pub kind: AnnotationKind,
    pub body: String,
    pub public: bool,
    pub created_at: u64,
}

/// Separate attributable note anchored strictly to one immutable `edition_hash`.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Annotation {
    pub edition_hash: String,
    pub locator: PassageLocator,
    pub kind: AnnotationKind,
    pub body: String,
    pub public: bool,
    pub author: DidKey,
    pub created_at: u64,
    pub proof: ProofOrArray,
}

impl Annotation {
    pub fn sign(draft: AnnotationDraft, author_kp: &Keypair) -> Result<Self> {
        if !looks_like_hash(&draft.edition_hash) {
            return Err(Error::Policy(
                "annotation: edition_hash must be 64 hex chars".into(),
            ));
        }
        if draft.body.trim().is_empty() {
            return Err(Error::Policy("annotation: body cannot be empty".into()));
        }
        let mut ann = Annotation {
            edition_hash: draft.edition_hash,
            locator: draft.locator,
            kind: draft.kind,
            body: draft.body,
            public: draft.public,
            author: author_kp.did(),
            created_at: draft.created_at,
            proof: ProofOrArray::placeholder(),
        };
        let body = body_for_signing(&ann)?;
        let sig = author_kp.sign(&body);
        ann.proof = ProofOrArray::single(Proof::create(author_kp, &sig));
        Ok(ann)
    }

    pub fn hash(&self) -> Result<String> {
        hash_of(self)
    }

    pub fn verify(&self) -> Result<()> {
        if !looks_like_hash(&self.edition_hash) {
            return Err(Error::Verification(
                "annotation: invalid edition_hash".into(),
            ));
        }
        if self.body.trim().is_empty() {
            return Err(Error::Verification("annotation: empty body".into()));
        }
        let body = body_for_signing(self)?;
        let proof = self
            .proof
            .find_by_method(&self.author)
            .ok_or_else(|| Error::Verification("annotation: missing author proof".into()))?;
        proof.verify(&body)
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum SearchScope {
    MetadataOnly,
    MetadataAndOutline,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct SearchHit {
    pub edition_hash: String,
    pub work_id: String,
    pub title: String,
    pub edition_label: String,
    pub version: u64,
    pub scope: SearchScope,
    pub matched_fields: Vec<String>,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CatalogueCard {
    pub edition_hash: String,
    pub work_id: String,
    pub title: String,
    pub attribution: String,
    pub description: String,
    pub edition_label: String,
    pub version: u64,
    pub is_preferred_edition: bool,
    pub downloadable_by_public: bool,
    pub sharing_terms: String,
    pub discussion_room: Option<DidKey>,
    pub representations: Vec<FileRepresentation>,
    pub vetting_labels: Vec<VettingLabel>,
    pub public_shelf_count: usize,
    pub public_annotation_count: usize,
}

/// Shared Library holding immutable editions, byte blobs, shelves, and
/// annotations. All lookup, search, and download methods take `&self` so
/// reading leaves zero persistent history.
#[derive(Default)]
pub struct SharedLibrary {
    editions: HashMap<String, Edition>,
    preferred_edition: HashMap<String, String>,
    work_author: HashMap<String, DidKey>,
    blobs: HashMap<String, Vec<u8>>,
    shelves: HashMap<String, Shelf>,
    annotations: HashMap<String, Annotation>,
}

impl SharedLibrary {
    pub fn new() -> Self {
        Self::default()
    }

    /// Publish a verified edition alongside all of its declared file blobs.
    pub fn publish_edition(
        &mut self,
        edition: Edition,
        files: Vec<(String, Vec<u8>)>,
    ) -> Result<String> {
        edition.verify()?;

        if let Some(parent_hash) = &edition.derived_from {
            let parent = self.editions.get(parent_hash).ok_or_else(|| {
                Error::Policy("derived_from references unknown parent edition".into())
            })?;
            if parent.work_id != edition.work_id {
                return Err(Error::Policy(
                    "derived edition must preserve parent work_id".into(),
                ));
            }
            if edition.version <= parent.version {
                return Err(Error::Policy(
                    "derived edition version must exceed parent version".into(),
                ));
            }
        }

        if let Some(existing_author) = self.work_author.get(&edition.work_id) {
            if edition
                .vetting_labels
                .contains(&VettingLabel::AuthorDesignatedEdition)
                && existing_author != &edition.author
            {
                return Err(Error::Policy(
                    "only the original work author may publish an AuthorDesignatedEdition".into(),
                ));
            }
        }

        for ann_hash in &edition.addresses_annotations {
            if !self.annotations.contains_key(ann_hash) {
                return Err(Error::Policy(
                    "addresses_annotations references unknown annotation".into(),
                ));
            }
        }

        let mut supplied: HashMap<String, Vec<u8>> = HashMap::new();
        for (claimed_sha, bytes) in files {
            let actual_sha = sha256_hex(&bytes);
            if actual_sha != claimed_sha {
                return Err(Error::Verification(
                    "supplied file bytes do not match claimed sha256".into(),
                ));
            }
            supplied.insert(claimed_sha, bytes);
        }

        for rep in &edition.representations {
            let bytes = supplied
                .get(&rep.sha256)
                .or_else(|| self.blobs.get(&rep.sha256))
                .ok_or_else(|| {
                    Error::Policy(format!(
                        "missing file bytes for representation {}",
                        rep.filename
                    ))
                })?;
            if bytes.len() as u64 != rep.byte_len {
                return Err(Error::Verification(format!(
                    "byte_len mismatch for {}: declared {}, actual {}",
                    rep.filename,
                    rep.byte_len,
                    bytes.len()
                )));
            }
        }

        let ed_hash = edition.hash()?;
        let is_designated = edition
            .vetting_labels
            .contains(&VettingLabel::AuthorDesignatedEdition);
        let work_id = edition.work_id.clone();
        let author = edition.author.clone();

        for (sha, bytes) in supplied {
            self.blobs.entry(sha).or_insert(bytes);
        }
        self.editions.insert(ed_hash.clone(), edition);
        self.work_author.entry(work_id.clone()).or_insert(author);
        if is_designated || !self.preferred_edition.contains_key(&work_id) {
            self.preferred_edition.insert(work_id, ed_hash.clone());
        }

        Ok(ed_hash)
    }

    pub fn publish_shelf(&mut self, shelf: Shelf) -> Result<String> {
        shelf.verify()?;
        for entry in &shelf.entries {
            let ed = self.editions.get(&entry.edition_hash).ok_or_else(|| {
                Error::Policy("shelf references unknown edition_hash".into())
            })?;
            if shelf.public && !ed.access.is_discoverable_publicly() {
                return Err(Error::Policy(
                    "public shelf cannot reference a hidden private edition".into(),
                ));
            }
            if !shelf.public && !ed.access.can_discover(&ed.author, Some(&shelf.curator)) {
                return Err(Error::Policy(
                    "curator does not have access to reference this private edition".into(),
                ));
            }
        }
        let h = shelf.hash()?;
        self.shelves.insert(h.clone(), shelf);
        Ok(h)
    }

    pub fn publish_annotation(&mut self, ann: Annotation) -> Result<String> {
        ann.verify()?;
        let ed = self.editions.get(&ann.edition_hash).ok_or_else(|| {
            Error::Policy("annotation references unknown edition_hash".into())
        })?;
        if ann.public && !ed.access.is_discoverable_publicly() {
            return Err(Error::Policy(
                "public annotation cannot attach to a hidden private edition".into(),
            ));
        }
        if !ann.public && !ed.access.can_discover(&ed.author, Some(&ann.author)) {
            return Err(Error::Policy(
                "annotator does not have access to this private edition".into(),
            ));
        }

        match &ann.kind {
            AnnotationKind::AuthorResponse { in_reply_to } => {
                if ann.author != ed.author {
                    return Err(Error::Policy(
                        "only the edition's author may publish an AuthorResponse".into(),
                    ));
                }
                let parent = self.annotations.get(in_reply_to).ok_or_else(|| {
                    Error::Policy("AuthorResponse references unknown annotation".into())
                })?;
                if parent.edition_hash != ann.edition_hash {
                    return Err(Error::Policy(
                        "AuthorResponse must target an annotation on the same edition".into(),
                    ));
                }
            }
            AnnotationKind::ComparativeNote { other_edition_hash } => {
                let other = self.editions.get(other_edition_hash).ok_or_else(|| {
                    Error::Policy(
                        "ComparativeNote references unknown other_edition_hash".into(),
                    )
                })?;
                if ann.public && !other.access.is_discoverable_publicly() {
                    return Err(Error::Policy(
                        "public ComparativeNote cannot reference a hidden private edition".into(),
                    ));
                }
            }
            _ => {}
        }

        let h = ann.hash()?;
        self.annotations.insert(h.clone(), ann);
        Ok(h)
    }

    // ---- Read-only, zero-history query interface (`&self` only) ----

    pub fn preferred_edition(&self, work_id: &str) -> Option<(&str, &Edition)> {
        let h = self.preferred_edition.get(work_id)?;
        let ed = self.editions.get(h)?;
        Some((h.as_str(), ed))
    }

    pub fn catalogue_card(
        &self,
        edition_hash: &str,
        requester: Option<&DidKey>,
    ) -> Result<CatalogueCard> {
        let ed = self
            .editions
            .get(edition_hash)
            .ok_or_else(|| Error::Policy("edition not found".into()))?;
        if !ed.access.can_discover(&ed.author, requester) {
            return Err(Error::Policy("edition is private".into()));
        }
        let is_preferred = self
            .preferred_edition
            .get(&ed.work_id)
            .map(|h| h == edition_hash)
            .unwrap_or(false);
        let public_shelf_count = self
            .shelves
            .values()
            .filter(|s| s.public && s.entries.iter().any(|e| e.edition_hash == edition_hash))
            .count();
        let public_annotation_count = self
            .annotations
            .values()
            .filter(|a| a.public && a.edition_hash == edition_hash)
            .count();

        Ok(CatalogueCard {
            edition_hash: edition_hash.to_string(),
            work_id: ed.work_id.clone(),
            title: ed.title.clone(),
            attribution: ed.attribution.clone(),
            description: ed.description.clone(),
            edition_label: ed.edition_label.clone(),
            version: ed.version,
            is_preferred_edition: is_preferred,
            downloadable_by_public: ed.access.is_downloadable_publicly(),
            sharing_terms: ed.sharing_terms.clone(),
            discussion_room: ed.discussion_room.clone(),
            representations: ed.representations.clone(),
            vetting_labels: ed.vetting_labels.clone(),
            public_shelf_count,
            public_annotation_count,
        })
    }

    /// Download exact verified bytes for a declared representation.
    /// Takes `&self`: leaves no record of who downloaded what.
    pub fn download_bytes(
        &self,
        edition_hash: &str,
        sha256: &str,
        requester: Option<&DidKey>,
    ) -> Result<&[u8]> {
        let ed = self
            .editions
            .get(edition_hash)
            .ok_or_else(|| Error::Policy("edition not found".into()))?;
        if !ed.access.can_read_file(&ed.author, requester) {
            return Err(Error::Policy("download refused: requester not authorized".into()));
        }
        let rep = ed
            .representations
            .iter()
            .find(|r| r.sha256 == sha256)
            .ok_or_else(|| {
                Error::Policy("requested sha256 does not belong to this edition".into())
            })?;
        let bytes = self
            .blobs
            .get(&rep.sha256)
            .ok_or_else(|| Error::Verification("blob missing from storage".into()))?;
        if sha256_hex(bytes) != rep.sha256 {
            return Err(Error::Verification("stored blob failed digest check".into()));
        }
        Ok(bytes.as_slice())
    }

    /// Plain word search over publicly discoverable editions only.
    /// Private drafts never appear in public search results.
    pub fn search_public(&self, query: &str, scope: SearchScope) -> Vec<SearchHit> {
        let terms: Vec<String> = query
            .split_whitespace()
            .map(|w| w.to_lowercase())
            .filter(|w| !w.is_empty())
            .collect();
        if terms.is_empty() {
            return Vec::new();
        }

        let mut hits = Vec::new();
        for (ed_hash, ed) in &self.editions {
            if !ed.access.is_discoverable_publicly() {
                continue;
            }
            let title_lc = ed.title.to_lowercase();
            let desc_lc = ed.description.to_lowercase();
            let attr_lc = ed.attribution.to_lowercase();
            let outline_lc = ed.contents_outline.join(" ").to_lowercase();

            let mut all_matched = true;
            let mut matched_fields = Vec::new();
            for term in &terms {
                let in_title = title_lc.contains(term);
                let in_desc = desc_lc.contains(term);
                let in_attr = attr_lc.contains(term);
                let in_outline =
                    scope == SearchScope::MetadataAndOutline && outline_lc.contains(term);
                if !(in_title || in_desc || in_attr || in_outline) {
                    all_matched = false;
                    break;
                }
                if in_title && !matched_fields.contains(&"title".to_string()) {
                    matched_fields.push("title".to_string());
                }
                if in_desc && !matched_fields.contains(&"description".to_string()) {
                    matched_fields.push("description".to_string());
                }
                if in_attr && !matched_fields.contains(&"attribution".to_string()) {
                    matched_fields.push("attribution".to_string());
                }
                if in_outline && !matched_fields.contains(&"contents_outline".to_string()) {
                    matched_fields.push("contents_outline".to_string());
                }
            }
            if all_matched {
                hits.push(SearchHit {
                    edition_hash: ed_hash.clone(),
                    work_id: ed.work_id.clone(),
                    title: ed.title.clone(),
                    edition_label: ed.edition_label.clone(),
                    version: ed.version,
                    scope,
                    matched_fields,
                });
            }
        }

        hits.sort_by(|a, b| {
            a.work_id
                .cmp(&b.work_id)
                .then_with(|| b.version.cmp(&a.version))
                .then_with(|| a.edition_hash.cmp(&b.edition_hash))
        });
        hits
    }

    pub fn shelves_for_edition(
        &self,
        edition_hash: &str,
        requester: Option<&DidKey>,
    ) -> Vec<&Shelf> {
        let mut out: Vec<&Shelf> = self
            .shelves
            .values()
            .filter(|s| {
                (s.public || requester.map(|r| r == &s.curator).unwrap_or(false))
                    && s.entries.iter().any(|e| e.edition_hash == edition_hash)
            })
            .collect();
        out.sort_by(|a, b| a.shelf_id.cmp(&b.shelf_id));
        out
    }

    /// Returns annotations anchored strictly to `edition_hash` (never redirected
    /// from or to another edition of the same work).
    pub fn annotations_for_edition(
        &self,
        edition_hash: &str,
        requester: Option<&DidKey>,
    ) -> Vec<&Annotation> {
        let mut out: Vec<&Annotation> = self
            .annotations
            .values()
            .filter(|a| {
                a.edition_hash == edition_hash
                    && (a.public || requester.map(|r| r == &a.author).unwrap_or(false))
            })
            .collect();
        out.sort_by(|a, b| a.created_at.cmp(&b.created_at).then_with(|| a.body.cmp(&b.body)));
        out
    }
}
