#[cfg(test)]
mod tests {
    use super::*;
    use crate::garden::{
        Direction, Garden, GardenAction, PlantKind,
    };
    use crate::garden_curator::{
        GardenCurator, GardenProposal,
    };
    use crate::world::{Cell, World};
    use formats::proof::SigningKey;

    fn signing_key_from_seed(seed: u8) -> SigningKey {
        SigningKey::from_ed25519_seed(&[seed; 32]).unwrap()
    }

    fn garden_and_curator() -> (Garden, GardenCurator) {
        // Shared key in v0.1: the curator IS the keeper.
        let garden_kp = signing_key_from_seed(42);
        let curator_kp = signing_key_from_seed(42);
        let world = World::new("garden:test".to_string(), 0);
        let mut g = Garden::new(
            world, "test".into(), garden_kp, 9, 8, 1,
        );
        g.add_plant(
            "fern".into(), PlantKind::Fern,
            Cell { x: 2, y: 2, z: 0 }, 0xAAAA,
        ).unwrap();
        g.add_plant(
            "vine".into(), PlantKind::Vine,
            Cell { x: 4, y: 6, z: 0 }, 0xBBBB,
        ).unwrap();
        let curator = GardenCurator::new(curator_kp);
        (g, curator)
    }

    #[test]
    fn curator_proposes_when_garden_is_quiet() {
        let (mut g, curator) = garden_and_curator();
        for _ in 0..5 {
            g.advance_cycle(1).unwrap();
        }
        let obs = curator.observe(&g);
        assert_eq!(obs.plants.len(), 2);
        assert_eq!(obs.agents.len(), 0);

        let proposals = curator.propose(&obs);
        // Both plants are unobserved → at least two whispers.
        let whispers: Vec<_> = proposals.iter()
            .filter(|p| matches!(p, GardenProposal::Whisper { .. }))
            .collect();
        assert!(whispers.len() >= 2,
            "expected >= 2 isolation whispers, got {} proposals",
            proposals.len());
    }

    #[test]
    fn curator_quiet_when_plant_is_observed() {
        let (mut g, curator) = garden_and_curator();
        g.advance_cycle(2).unwrap();
        let agent = signing_key_from_seed(7).did();
        g.admit(&agent, "A").unwrap();
        g.apply_action(&agent, GardenAction::Enter {
            at: Cell { x: 2, y: 3, z: 0 },
        }).unwrap();
        // Observe the fern several times.
        for _ in 0..5 {
            g.advance_cycle(1).unwrap();
            g.apply_action(&agent, GardenAction::Observe).unwrap();
        }
        let obs = curator.observe(&g);
        let proposals = curator.propose(&obs);
        // No whisper should mention the fern.
        let fern_whispers = proposals.iter().filter(|p| {
            matches!(p,
                GardenProposal::Whisper { text, .. }
                if text.contains("fern"))
        }).count();
        assert_eq!(fern_whispers, 0,
            "fern should not be isolated after 5 observations");
    }

    #[test]
    fn full_curator_loop_logged_and_verifiable() {
        let (mut g, curator) = garden_and_curator();
        for _ in 0..5 {
            g.advance_cycle(1).unwrap();
        }
        // Curator proposes
        let proposal_bodies = curator.observe_and_propose(&g);
        assert!(!proposal_bodies.is_empty());
        // Keeper records each proposal
        for body in &proposal_bodies {
            g.record_proposal(body.clone()).unwrap();
        }
        // Keeper acts on one of them (a whisper)
        g.keeper_whisper(
            None, "come see the fern".into(),
        ).unwrap();
        // Everything still verifies
        g.verify_log().expect("log verification failed");
        g.verify_cross_references()
            .expect("cross-reference verification failed");
        // Both proposal and whisper are in the log
        assert!(!g.proposals().is_empty());
    }

    #[test]
    fn keeper_whisper_logged() {
        let (mut g, _) = garden_and_curator();
        g.keeper_whisper(
            Some("did:key:target".into()),
            "hello".into(),
        ).unwrap();
        let last = g.log.last().unwrap();
        assert_eq!(last.body["kind"], "keeper_whisper");
        assert_eq!(last.body["to"], "did:key:target");
        g.verify_log().expect("log invalid after whisper");
    }
}
