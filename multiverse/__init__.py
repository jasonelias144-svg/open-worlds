"""The multiverse: many worlds, one protocol, and individuals who move
between them.

Built from the founder's sketch with DeepSeek (docs/MULTIVERSE.md), one
step at a time (docs/COURSE.md). Step 1 is the sketch's core, working;
step 2 makes each individual a key that signs what it sends:

  identity.py         who an individual is: a key (components 1 and 13)
  ed25519.py          the signatures, from RFC 8032
  passport.py         where it has been (component 2)
  protocol.py         WCP/0.2, what every entity speaks (component 3)
  conformance.py      the test anyone can run against an entity
  entity.py           entering, leaving and the log, shared by all
  poetry_world.py     poets taking turns under a law (component 4)
  chemistry_world.py  reactions that must balance (component 5)
  registry.py         a registry of worlds, itself an entity (component 6)
  apprentice.py       rule-based apprentice poets (poetry engine)
  collaboration.py    all of it together (component 7)

Depends on the `cryptography` package for signatures (requirements.txt).
"""
