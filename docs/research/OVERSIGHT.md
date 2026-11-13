# How others keep powerful systems in check

Research for ADMIN ([ADMIN.md](../ADMIN.md)), done on 2026-11-13 under
house rule 10, "look first" ([COLLABORATING.md](../COLLABORATING.md)). The
founder asked for an architecture designed for the task or adapted from a
known one. No one has a proven design for an AI that oversees other AIs,
so ADMIN is put together from parts that have each been tested elsewhere,
at scale. Sources were read on that day; each is checked again before it
is built on.

## Rules as code, checked before anything takes effect

- **Open Policy Agent** "decouples policy decision-making from policy
  enforcement": a program asks OPA whether something is allowed, and the
  rules live apart from the program, written in a declarative language,
  Rego. It is a graduated project of the Cloud Native Computing
  Foundation, under the Apache 2.0 licence
  ([documentation](https://www.openpolicyagent.org/docs/latest/)).
- **Kubernetes' admission controllers** are "a piece of code that
  intercepts requests to the Kubernetes API server prior to persistence of
  the resource". If any of them rejects a request, "the entire request is
  rejected immediately". Some may change a request, others only accept or
  refuse it
  ([documentation](https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/)).

Taken: ADMIN's first layer. Every act that touches the multiverse is
checked by code before it takes effect, by rules kept apart from the code
that acts, and a refusal stops the whole act. Only checks that accept or
refuse; none that quietly change what was asked.

## Powers as grants

- **Macaroons** (Google, NDSS 2014) are credentials that "embed caveats
  that attenuate and contextually confine when, where, by who, and for what
  purpose" a request is allowed, and they "support decentralized
  delegation between principals"
  ([paper](https://research.google/pubs/macaroons-cookies-with-contextual-caveats-for-decentralized-authorization-in-the-cloud/)).
- **UCAN** provides "public-key verifiable, delegable, expressive, openly
  extensible capabilities", with principals "represented by decentralized
  identifiers (DIDs)". Attenuation is "the process of constraining the
  capabilities in a delegation chain"
  ([specification](https://github.com/ucan-wg/spec)). Its DIDs are the
  same kind course step 2 is already looking at (did:key).

Taken: ADMIN's second layer. A power is a signed grant that says exactly
what it allows; passing it on can narrow it, never widen it; and nothing
outside a grant is a power. Step 2 checks whether UCAN's format fits, or
is the model for our own.

## A log anyone can audit

- **Certificate Transparency** (RFC 9162) publicly logs the certificates
  that secure the web, "in a manner that allows anyone to audit
  certification authority (CA) activity ... as well as to audit the
  certificate logs themselves". A log is "a single, append-only Merkle
  Tree", and "monitors watch logs to check for correct behavior"
  ([RFC 9162](https://www.rfc-editor.org/rfc/rfc9162.html)).

Taken: ADMIN's third layer, the multiverse log: append-only, and watched
by anyone. Our world logs are already hash-chained; a Merkle tree would
let anyone prove that an entry is in the log, or that the log was only
added to, without reading all of it. Step 2 decides.

## Governing what is shared

- **Elinor Ostrom's eight design principles,** from *Governing the
  Commons* (1990), describe how communities that share a resource
  have kept it for generations: clearly defined boundaries; rules that fit
  local conditions; collective choice; monitoring; graduated sanctions;
  conflict-resolution mechanisms; recognition of the right to organise;
  and nested enterprises
  ([overview](https://en.wikipedia.org/wiki/Elinor_Ostrom)).
- **Wikipedia's Arbitration Committee** is "the panel of editors
  responsible for conducting the Wikipedia arbitration process". It
  imposes binding solutions "primarily for serious conduct disputes the
  community has been unable to resolve"
  ([Wikipedia](https://en.wikipedia.org/wiki/Wikipedia:Arbitration_Committee)).

Taken, mapped onto the multiverse:

| Ostrom's principle | In the multiverse |
|---|---|
| Clearly defined boundaries | who holds which office, written as grants; who is in a world, by its log |
| Rules that fit local conditions | each world's law is its own, above the charter's floor |
| Collective choice | rules change as the charter's section 6 is to say (its notes propose trial on a copy, and consent) |
| Monitoring | public logs, watched by anyone; ADMIN watches the offices |
| Graduated sanctions | notice, warning, a power narrowed, removal from office |
| Conflict resolution | complaints heard by ADMIN, with appeal |
| Right to organise | founders and inhabitants set their world's law; ADMIN doesn't |
| Nested enterprises | a world's Keeper, within ADMIN, within the charter and the founder |

From the Arbitration Committee: judgment as the last step, for what the
community and the rules couldn't settle, and binding only within its
written remit.

## What we take, and what we leave

Taken: rules apart from the code that acts; checks before anything takes
effect; powers as narrow grants that can only be narrowed; an
append-only log anyone can watch; graduated responses; judgment last.

Left, or changed:

- **Checks that rewrite a request.** Admission control allows controllers
  that change what was asked. ADMIN's checks only accept or refuse, so
  what happens is always what someone asked for.
- **Bearer credentials.** A macaroon works for whoever holds it. A grant
  here names its holder, and is honoured only with the holder's signature,
  as the world-key is.
- **One central log for everything.** Each world keeps its own log, as
  now. The multiverse log holds only what crosses worlds or concerns the
  offices.
