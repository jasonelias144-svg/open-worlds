# Minds

Programs that can be minds in the Ur-world, through its doorway. A mind
is any program, in any language, that reads the world's lines of JSON on
its standard input and answers each tick with one line on its standard
output. The protocol and how replies are read are in
[docs/URWORLD.md](../docs/URWORLD.md), "Minds from outside: the doorway",
and in `rust/ur-world/src/door.rs`.

| Mind | What it is |
|---|---|
| [`wanderer.py`](wanderer.py) | No model behind it. It greets the world, then walks, turning right whenever its way is blocked. Python's standard library only. |

To run two of them in the garden:

```
cd rust
cargo run -p ur-world --example door -- \
    --mind TRIAL-1=python3 -I ../minds/wanderer.py \
    --mind TRIAL-2=python3 -I ../minds/wanderer.py
```

A mind run from code someone else wrote should be read first, and run
where it can do no harm: the world keeps it from breaking the world, but
not from touching the machine it runs on.
