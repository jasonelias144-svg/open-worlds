// rust/formats/src/records/mod.rs

pub mod garden_curator_proposal;
pub use garden_curator_proposal::{
    GardenCuratorProposalPayload, GardenProposal,
    GardenProposalKindTag, SignedGardenCuratorProposal,
};
