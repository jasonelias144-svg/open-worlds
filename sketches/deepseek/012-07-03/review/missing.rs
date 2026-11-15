// Ours, not DeepSeek's (see ../README.md). The two functions world.rs
// imports from rule.rs, which rule.rs never defines, written from the
// record's own words ("Dieback", record line 322, and "Growth priority",
// line 333): growth picks the tip with the most light, then the
// shallowest, then the lowest (x, y, direction); dieback picks the tip
// with the least light, then the deepest, then the lowest
// (x, y, direction). "Lowest" is our reading: the record doesn't say.
// review/run.sh appends this file to a scratch copy's rule.rs, so the
// sketch can be built and its behaviour checked.

pub fn growth_priority(
    t: &Template,
    map: &HashMap<i32, Vec<i32>>,
    tip: &Tip,
) -> (u32, std::cmp::Reverse<u32>, std::cmp::Reverse<(i32, i32, u8)>) {
    (
        gathered_at(t, map, tip),
        std::cmp::Reverse(tip.depth),
        std::cmp::Reverse((tip.x, tip.y, tip.direction)),
    )
}

pub fn dieback_priority(
    t: &Template,
    map: &HashMap<i32, Vec<i32>>,
    tip: &Tip,
) -> (std::cmp::Reverse<u32>, u32, std::cmp::Reverse<(i32, i32, u8)>) {
    (
        std::cmp::Reverse(gathered_at(t, map, tip)),
        tip.depth,
        std::cmp::Reverse((tip.x, tip.y, tip.direction)),
    )
}
