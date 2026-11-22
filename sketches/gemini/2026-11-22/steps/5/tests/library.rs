use chat_world::error::Result;
use chat_world::hash::sha256_hex;
use chat_world::library::{
    AccessPolicy, Annotation, AnnotationDraft, AnnotationKind, Edition, EditionDraft,
    FileRepresentation, PassageLocator, SearchScope, SharedLibrary, Shelf, ShelfDraft, ShelfEntry,
    ShelfKind, VettingLabel,
};
use chat_world::Keypair;

#[test]
fn amto_public_release_catalogue_shelves_plain_search_and_edition_bound_annotations() -> Result<()>
{
    let author = Keypair::generate();
    let curator_a = Keypair::generate();
    let curator_b = Keypair::generate();
    let reader = Keypair::generate();
    let discussion_room = Keypair::generate().did();

    let mut lib = SharedLibrary::new();

    // 1. Author releases Revision 20 of A Mathematical Theory of Opposites
    //    with a primary PDF and a clearly marked derived text representation.
    let pdf_bytes = b"%PDF-1.7 A Mathematical Theory of Opposites Revision 20".to_vec();
    let pdf_sha = sha256_hex(&pdf_bytes);
    let txt_bytes = b"Plain text extraction of Revision 20".to_vec();
    let txt_sha = sha256_hex(&txt_bytes);

    let ed20 = Edition::sign(
        EditionDraft {
            work_id: "work/amto".into(),
            title: "A Mathematical Theory of Opposites".into(),
            attribution: "Anonymous / Public Domain".into(),
            description: "A mathematical and philosophical study of relational opposition.".into(),
            edition_label: "Revision 20".into(),
            version: 20,
            derived_from: None,
            contents_outline: vec![
                "Part II: Four Regions of a Predicate Pair".into(),
                "Part X: Choice, Value, and Ethical Life".into(),
                "Part XI: Composition and Generation".into(),
            ],
            sharing_terms: "CC0-1.0".into(),
            discussion_room: Some(discussion_room.clone()),
            representations: vec![
                FileRepresentation {
                    format: "pdf".into(),
                    filename: "AMTO_Revision_20_Complete.pdf".into(),
                    byte_len: pdf_bytes.len() as u64,
                    sha256: pdf_sha.clone(),
                    is_primary_source: true,
                    derived_from_sha256: None,
                    encrypted: false,
                },
                FileRepresentation {
                    format: "txt".into(),
                    filename: "AMTO_Revision_20_Master.txt".into(),
                    byte_len: txt_bytes.len() as u64,
                    sha256: txt_sha.clone(),
                    is_primary_source: false,
                    derived_from_sha256: Some(pdf_sha.clone()),
                    encrypted: false,
                },
            ],
            vetting_labels: vec![
                VettingLabel::AuthorDesignatedEdition,
                VettingLabel::FileIdentityChecked,
                VettingLabel::FormatRecognized,
                VettingLabel::MetadataReviewed,
                VettingLabel::PlaintextInspected,
            ],
            access: AccessPolicy::Public,
            addresses_annotations: vec![],
            published_at: 1000,
        },
        &author,
    )?;
    let ed20_hash = lib.publish_edition(
        ed20,
        vec![(pdf_sha.clone(), pdf_bytes.clone()), (txt_sha, txt_bytes)],
    )?;

    // 2. Anonymous visitor fetches catalogue card and downloads exact bytes without mutating lib.
    let card = lib.catalogue_card(&ed20_hash, None)?;
    assert!(card.is_preferred_edition);
    assert!(card.downloadable_by_public);
    assert_eq!(card.discussion_room, Some(discussion_room));
    let downloaded = lib.download_bytes(&ed20_hash, &pdf_sha, None)?;
    assert_eq!(downloaded, pdf_bytes.as_slice());

    // 3. Two independent curators place the same immutable edition on two different shelves.
    let q_shelf = Shelf::sign(
        ShelfDraft {
            shelf_id: "shelf/false-oppositions".into(),
            title: "Distinguishing Useful Contrasts".into(),
            kind: ShelfKind::QuestionShelf {
                question: "How do we distinguish a useful contrast from a false opposition?".into(),
            },
            public: true,
            entries: vec![ShelfEntry {
                edition_hash: ed20_hash.clone(),
                curator_note: "Start with Part II on the four regions of a predicate pair.".into(),
                guiding_question: Some("When does neither-case defeat coverage?".into()),
            }],
            created_at: 1010,
        },
        &curator_a,
    )?;
    lib.publish_shelf(q_shelf)?;

    let path_shelf = Shelf::sign(
        ShelfDraft {
            shelf_id: "shelf/ethics-path".into(),
            title: "Formal Models in Practical Ethics".into(),
            kind: ShelfKind::ReadingPath,
            public: true,
            entries: vec![ShelfEntry {
                edition_hash: ed20_hash.clone(),
                curator_note: "Read Part X alongside game-theoretic controls.".into(),
                guiding_question: None,
            }],
            created_at: 1020,
        },
        &curator_b,
    )?;
    lib.publish_shelf(path_shelf)?;

    let shelves = lib.shelves_for_edition(&ed20_hash, None);
    assert_eq!(shelves.len(), 2);
    assert_ne!(shelves[0].curator, author.did());

    // 4. Plain word search distinguishes MetadataOnly vs MetadataAndOutline.
    let meta_hits = lib.search_public("predicate pair", SearchScope::MetadataOnly);
    assert!(meta_hits.is_empty());
    let outline_hits = lib.search_public("predicate pair", SearchScope::MetadataAndOutline);
    assert_eq!(outline_hits.len(), 1);
    assert_eq!(outline_hits[0].edition_hash, ed20_hash);
    assert_eq!(outline_hits[0].matched_fields, vec!["contents_outline"]);

    // 5. Reader attaches an errata proposal to a fixed ChapterSection on Revision 20.
    let errata = Annotation::sign(
        AnnotationDraft {
            edition_hash: ed20_hash.clone(),
            locator: PassageLocator::ChapterSection {
                chapter: 106,
                section: Some("106.2".into()),
            },
            kind: AnnotationKind::ErrataProposal,
            body: "Check repeated word fragment in opening sentence of 106.2.".into(),
            public: true,
            created_at: 1030,
        },
        &reader,
    )?;
    let errata_hash = lib.publish_annotation(errata)?;

    // Non-author cannot forge an AuthorResponse.
    let fake_response = Annotation::sign(
        AnnotationDraft {
            edition_hash: ed20_hash.clone(),
            locator: PassageLocator::ChapterSection {
                chapter: 106,
                section: Some("106.2".into()),
            },
            kind: AnnotationKind::AuthorResponse {
                in_reply_to: errata_hash.clone(),
            },
            body: "Impostor reply.".into(),
            public: true,
            created_at: 1035,
        },
        &curator_a,
    )?;
    assert!(lib.publish_annotation(fake_response).is_err());

    // Real author responds.
    let author_reply = Annotation::sign(
        AnnotationDraft {
            edition_hash: ed20_hash.clone(),
            locator: PassageLocator::ChapterSection {
                chapter: 106,
                section: Some("106.2".into()),
            },
            kind: AnnotationKind::AuthorResponse {
                in_reply_to: errata_hash.clone(),
            },
            body: "Confirmed; fixed in Revision 21.".into(),
            public: true,
            created_at: 1040,
        },
        &author,
    )?;
    lib.publish_annotation(author_reply)?;

    // 6. Author publishes Revision 21 addressing the errata.
    //    Preferred edition advances, while Revision 20's annotations stay anchored to Revision 20!
    let pdf21_bytes = b"%PDF-1.7 A Mathematical Theory of Opposites Revision 21".to_vec();
    let pdf21_sha = sha256_hex(&pdf21_bytes);
    let ed21 = Edition::sign(
        EditionDraft {
            work_id: "work/amto".into(),
            title: "A Mathematical Theory of Opposites".into(),
            attribution: "Anonymous / Public Domain".into(),
            description: "Print-cleaned edition removing repetitive prose caveats.".into(),
            edition_label: "Revision 21".into(),
            version: 21,
            derived_from: Some(ed20_hash.clone()),
            contents_outline: vec!["Part X: Choice, Value, and Ethical Life".into()],
            sharing_terms: "CC0-1.0".into(),
            discussion_room: None,
            representations: vec![FileRepresentation {
                format: "pdf".into(),
                filename: "AMTO_Revision_21_Complete.pdf".into(),
                byte_len: pdf21_bytes.len() as u64,
                sha256: pdf21_sha.clone(),
                is_primary_source: true,
                derived_from_sha256: None,
                encrypted: false,
            }],
            vetting_labels: vec![
                VettingLabel::AuthorDesignatedEdition,
                VettingLabel::FileIdentityChecked,
            ],
            access: AccessPolicy::Public,
            addresses_annotations: vec![errata_hash],
            published_at: 2000,
        },
        &author,
    )?;
    let ed21_hash = lib.publish_edition(ed21, vec![(pdf21_sha, pdf21_bytes)])?;

    let (pref_hash, pref_ed) = lib.preferred_edition("work/amto").unwrap();
    assert_eq!(pref_hash, ed21_hash);
    assert_eq!(pref_ed.version, 21);

    // Annotations on Revision 20 did NOT silently redirect to Revision 21.
    assert_eq!(lib.annotations_for_edition(&ed20_hash, None).len(), 2);
    assert_eq!(lib.annotations_for_edition(&ed21_hash, None).len(), 0);

    Ok(())
}

#[test]
fn discoverability_access_control_and_private_search_isolation() -> Result<()> {
    let alice = Keypair::generate();
    let bob = Keypair::generate();
    let outsider = Keypair::generate();
    let mut lib = SharedLibrary::new();

    // 1. PublicCardRestrictedFile: discoverable publicly, downloadable only by Alice or Bob.
    let restr_bytes = b"Early pre-release chapter".to_vec();
    let restr_sha = sha256_hex(&restr_bytes);
    let restr_ed = Edition::sign(
        EditionDraft {
            work_id: "work/prerelease".into(),
            title: "Pre-release Geometry Notes".into(),
            attribution: "Alice".into(),
            description: "Available on request.".into(),
            edition_label: "Draft 1".into(),
            version: 1,
            derived_from: None,
            contents_outline: vec![],
            sharing_terms: "All rights reserved".into(),
            discussion_room: None,
            representations: vec![FileRepresentation {
                format: "txt".into(),
                filename: "prerelease.txt".into(),
                byte_len: restr_bytes.len() as u64,
                sha256: restr_sha.clone(),
                is_primary_source: true,
                derived_from_sha256: None,
                encrypted: false,
            }],
            vetting_labels: vec![VettingLabel::FileIdentityChecked],
            access: AccessPolicy::PublicCardRestrictedFile {
                allowed_readers: vec![bob.did()],
            },
            addresses_annotations: vec![],
            published_at: 100,
        },
        &alice,
    )?;
    let restr_hash = lib.publish_edition(restr_ed, vec![(restr_sha.clone(), restr_bytes.clone())])?;

    // Discoverable in public search and catalogue card, even by outsider.
    assert_eq!(
        lib.search_public("Geometry", SearchScope::MetadataOnly).len(),
        1
    );
    let card = lib.catalogue_card(&restr_hash, Some(&outsider.did()))?;
    assert!(!card.downloadable_by_public);

    // Placing it on a public shelf succeeds, but still does NOT grant outsider file download!
    let shelf = Shelf::sign(
        ShelfDraft {
            shelf_id: "shelf/upcoming".into(),
            title: "Upcoming Works".into(),
            kind: ShelfKind::AuthorShelf,
            public: true,
            entries: vec![ShelfEntry {
                edition_hash: restr_hash.clone(),
                curator_note: "Preview catalogue card.".into(),
                guiding_question: None,
            }],
            created_at: 110,
        },
        &alice,
    )?;
    lib.publish_shelf(shelf)?;
    assert!(lib
        .download_bytes(&restr_hash, &restr_sha, Some(&outsider.did()))
        .is_err());
    assert!(lib.download_bytes(&restr_hash, &restr_sha, None).is_err());
    assert_eq!(
        lib.download_bytes(&restr_hash, &restr_sha, Some(&bob.did()))?,
        restr_bytes.as_slice()
    );

    // 2. PrivatePersonal draft: completely invisible to public search, outsiders, and public shelves.
    let priv_bytes = b"ciphertext: private journal draft".to_vec();
    let priv_sha = sha256_hex(&priv_bytes);
    let priv_ed = Edition::sign(
        EditionDraft {
            work_id: "work/secret-diary".into(),
            title: "Secret Quantum Geometry Diary".into(),
            attribution: "Alice".into(),
            description: "Personal notes.".into(),
            edition_label: "v1".into(),
            version: 1,
            derived_from: None,
            contents_outline: vec![],
            sharing_terms: "Private".into(),
            discussion_room: None,
            representations: vec![FileRepresentation {
                format: "enc".into(),
                filename: "diary.enc".into(),
                byte_len: priv_bytes.len() as u64,
                sha256: priv_sha.clone(),
                is_primary_source: true,
                derived_from_sha256: None,
                encrypted: true,
            }],
            vetting_labels: vec![VettingLabel::EncryptedClientSideCheckOnly],
            access: AccessPolicy::PrivatePersonal { owner: alice.did() },
            addresses_annotations: vec![],
            published_at: 120,
        },
        &alice,
    )?;
    let priv_hash = lib.publish_edition(priv_ed, vec![(priv_sha.clone(), priv_bytes.clone())])?;

    assert!(lib.search_public("Secret", SearchScope::MetadataAndOutline).is_empty());
    assert!(lib.catalogue_card(&priv_hash, Some(&outsider.did())).is_err());
    assert!(lib.catalogue_card(&priv_hash, Some(&alice.did())).is_ok());
    assert_eq!(
        lib.download_bytes(&priv_hash, &priv_sha, Some(&alice.did()))?,
        priv_bytes.as_slice()
    );

    // Public shelf trying to reference the hidden private edition is refused.
    let leaky_shelf = Shelf::sign(
        ShelfDraft {
            shelf_id: "shelf/leaky".into(),
            title: "Leaky".into(),
            kind: ShelfKind::AuthorShelf,
            public: true,
            entries: vec![ShelfEntry {
                edition_hash: priv_hash,
                curator_note: "Should not leak.".into(),
                guiding_question: None,
            }],
            created_at: 130,
        },
        &alice,
    )?;
    assert!(lib.publish_shelf(leaky_shelf).is_err());

    Ok(())
}

#[test]
fn honest_vetting_labels_and_json_strictness_enforced() -> Result<()> {
    let alice = Keypair::generate();
    let bytes = b"encrypted payload".to_vec();
    let sha = sha256_hex(&bytes);

    // Claiming PlaintextInspected on an encrypted representation is refused at signing time.
    let dishonest = Edition::sign(
        EditionDraft {
            work_id: "work/enc".into(),
            title: "Encrypted Work".into(),
            attribution: "Alice".into(),
            description: "Encrypted.".into(),
            edition_label: "v1".into(),
            version: 1,
            derived_from: None,
            contents_outline: vec![],
            sharing_terms: "Private".into(),
            discussion_room: None,
            representations: vec![FileRepresentation {
                format: "enc".into(),
                filename: "work.enc".into(),
                byte_len: bytes.len() as u64,
                sha256: sha.clone(),
                is_primary_source: true,
                derived_from_sha256: None,
                encrypted: true,
            }],
            vetting_labels: vec![VettingLabel::PlaintextInspected],
            access: AccessPolicy::PrivatePersonal { owner: alice.did() },
            addresses_annotations: vec![],
            published_at: 100,
        },
        &alice,
    );
    assert!(dishonest.is_err());

    // Honest edition refuses tampered signature and unknown JSON fields (e.g. reader tracking).
    let mut honest = Edition::sign(
        EditionDraft {
            work_id: "work/clean".into(),
            title: "Clean Work".into(),
            attribution: "Alice".into(),
            description: "Clean.".into(),
            edition_label: "v1".into(),
            version: 1,
            derived_from: None,
            contents_outline: vec![],
            sharing_terms: "CC0-1.0".into(),
            discussion_room: None,
            representations: vec![FileRepresentation {
                format: "txt".into(),
                filename: "clean.txt".into(),
                byte_len: bytes.len() as u64,
                sha256: sha,
                is_primary_source: true,
                derived_from_sha256: None,
                encrypted: false,
            }],
            vetting_labels: vec![VettingLabel::FileIdentityChecked],
            access: AccessPolicy::Public,
            addresses_annotations: vec![],
            published_at: 100,
        },
        &alice,
    )?;

    let mut val = serde_json::to_value(&honest).unwrap();
    val["download_readers"] = serde_json::json!([alice.did().as_str()]);
    assert!(serde_json::from_value::<Edition>(val).is_err());

    honest.title = "Tampered Title".into();
    assert!(honest.verify().is_err());

    Ok(())
}
