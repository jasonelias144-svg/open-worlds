//! Start a GardenServer, drive a resident over HTTP.

use std::sync::{Arc, Mutex};

use ur_world::garden::{Garden, PlantKind};
use ur_world::garden_client::GardenClient;
use ur_world::garden_server::GardenServer;
use ur_world::garden::rnn::{
    SamplingMode, TinyRnn, Weights,
};
use ur_world::garden::rnn_mind::TinyRnnMind;
use ur_world::world::{Cell, Mind, World};
use formats::proof::SigningKey;

fn main() {
    // Build the garden
    let curator_key = SigningKey::generate();
    let keeper_did = curator_key.did();
    let world = World::new("garden:demo".to_string(), 0);
    let mut g = Garden::new(
        world, "demo garden".to_string(), curator_key,
        9, 8, 1,
    );
    g.add_plant("fern".into(), PlantKind::Fern,
        Cell { x: 2, y: 2, z: 0 }, 0xAAAA).unwrap();
    g.add_plant("vine".into(), PlantKind::Vine,
        Cell { x: 4, y: 6, z: 0 }, 0xBBBB).unwrap();
    let g = Arc::new(Mutex::new(g));

    // Start server
    let server = GardenServer::new(
        g.clone(),
        keeper_did.clone(),
        "http://127.0.0.1:8765".to_string(),
        "Demo Garden".to_string(),
        "a two-plant garden".to_string(),
    );
    let server_handle = std::thread::spawn(move || {
        server.run("127.0.0.1:8765").expect("server run");
    });
    std::thread::sleep(std::time::Duration::from_millis(200));

    // Agent over HTTP
    let agent_key = SigningKey::generate();
    let mut client = GardenClient::new(
        "http://127.0.0.1:8765".to_string(),
        agent_key,
    );
    client.connect().expect("connect");
    client.petition("ALICE").expect("petition");
    client.enter(Cell { x: 0, y: 4, z: 0 }).expect("enter");

    // Mind
    let weights = Weights {
        w_in: vec![vec![0.1; 7]; 4],
        w_h: vec![vec![0.05; 4]; 4],
        w_out: vec![vec![0.1; 4]; 3],
        b_out: vec![0.0; 3],
        h_prev: vec![0.0; 4],
        baseline: 0.0,
    };
    let mut mind = TinyRnnMind::new(
        TinyRnn::from_weights(weights),
        42, SamplingMode::Softmax,
    );

    for _ in 0..10 {
        let obs = client.observe().expect("observe");
        let action = mind.observe(obs);
        let _ = client.act(action);
        mind.receive(ur_world::garden::rnn_mind::Outcome {
            accepted: true, reward_micros: 50_000,
        });
    }

    // Keeper advances the cycle via signed request
    // (simplified — a full demo would sign the request body)
    {
        let mut gg = g.lock().unwrap();
        gg.advance_cycle(1).expect("advance");
    }

    // Verify locally
    {
        let gg = g.lock().unwrap();
        gg.verify_log().expect("log");
        gg.verify_cross_references().expect("xref");
        println!("final log length: {}", gg.log.len());
    }

    // Drop by terminating; the server thread will exit.
    std::process::exit(0);
}
