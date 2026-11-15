#[cfg(test)]
mod tests {
    use super::*;
    use crate::garden::{Direction, Garden, GardenAction, PlantKind};
    use crate::world::{Cell, World};
    use formats::proof::SigningKey;

    fn garden_with_plants() -> Garden {
        let world = World::new("garden:test".to_string(), 0);
        let curator = SigningKey::generate();
        let mut g = Garden::new(world, "test garden".to_string(), curator, 9, 8, 1);
        g.add_plant("fern".into(), PlantKind::Fern, Cell { x: 2, y: 2, z: 0 }, 0xAAAA).unwrap();
        g.add_plant("vine".into(), PlantKind::Vine, Cell { x: 4, y: 6, z: 0 }, 0xBBBB).unwrap();
        g
    }

    #[test]
    fn add_plant_logs_entry() {
        let g = garden_with_plants();
        assert_eq!(g.log.len(), 2);
        assert_eq!(g.log[0].body["kind"], "plant_added");
        assert!(g.verify_log().is_ok());
    }

    #[test]
    fn out_of_bounds_refused() {
        let mut g = garden_with_plants();
        let agent = SigningKey::generate().did();
        g.admit(&agent, "A").unwrap();
        let result = g.apply_action(&agent, GardenAction::Enter {
            at: Cell { x: 100, y: 100, z: 0 },
        });
        assert!(result.is_err());
    }

    #[test]
    fn walk_into_plant_refused() {
        let mut g = garden_with_plants();
        let agent = SigningKey::generate().did();
        g.admit(&agent, "A").unwrap();
        g.apply_action(&agent, GardenAction::Enter {
            at: Cell { x: 2, y: 3, z: 0 },
        }).unwrap();
        let result = g.apply_action(&agent, GardenAction::Walk {
            direction: Direction::North,
        });
        assert!(result.is_err());
    }

    #[test]
    fn observe_adjacent_plant() {
        let mut g = garden_with_plants();
        g.advance_cycle(3).unwrap();
        let agent = SigningKey::generate().did();
        g.admit(&agent, "A").unwrap();
        g.apply_action(&agent, GardenAction::Enter {
            at: Cell { x: 2, y: 3, z: 0 },
        }).unwrap();
        g.apply_action(&agent, GardenAction::Observe).unwrap();
        let last = g.log.last().unwrap();
        assert_eq!(last.body["result"], "observed_plant");
        assert!(g.verify_cross_references().is_ok());
    }

    #[test]
    fn tampered_cross_reference_fails() {
        let mut g = garden_with_plants();
        g.advance_cycle(2).unwrap();
        let agent = SigningKey::generate().did();
        g.admit(&agent, "A").unwrap();
        g.apply_action(&agent, GardenAction::Enter {
            at: Cell { x: 2, y: 3, z: 0 },
        }).unwrap();
        g.apply_action(&agent, GardenAction::Observe).unwrap();
        // Tamper the reference
        let idx = g.log.len() - 1;
        g.log[idx].body["plant_event_hash"] = serde_json::json!("00".repeat(32));
        // The chain is now broken (hash won't match JCS body)
        assert!(g.verify_log().is_err());
    }

    #[test]
    fn full_verify_on_clean_log() {
        let mut g = garden_with_plants();
        for _ in 0..5 {
            g.advance_cycle(1).unwrap();
        }
        let agent = SigningKey::generate().did();
        g.admit(&agent, "A").unwrap();
        g.apply_action(&agent, GardenAction::Enter {
            at: Cell { x: 0, y: 0, z: 0 },
        }).unwrap();
        g.apply_action(&agent, GardenAction::Walk {
            direction: Direction::East,
        }).unwrap();
        g.apply_action(&agent, GardenAction::Speak {
            text: "hello".into(),
        }).unwrap();
        assert!(g.verify_log().is_ok());
        assert!(g.verify_cross_references().is_ok());
    }
}
