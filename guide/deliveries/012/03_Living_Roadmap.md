# Living roadmap: a working convention for the Open Worlds Guide

Prepared 21 November 2026.  
Source snapshot: `7ade210ace929b80ab82458536415ce83faab415`.  
Status: the founder's direction is received; the editorial mechanism below is a proposal for review.

## 1. The direction received

The founder has confirmed that the guide should be the main reference manual and should also fill in planned development, act as a living roadmap, and help preserve consistency. The exact message is retained in `00_Read_First.md`.

This package applies that direction to I.2. It explains an available observer's route, describes the designed Commons and Library, and identifies the gaps that keep those pieces from forming a continuous participant experience. It gives the planned parts meaningful content now.

The source revision remains explicit. Receiving the founder's direction in this conversation does not mean it has already been entered into the repository's decision record.

## 2. Add one compact note to the existing conventions

Keep the existing stable chapter and section IDs, six maturity labels, chapter Progress, and source commit. Where a subject is incomplete, add a short **Next update** note containing:

| Item | Purpose |
|---|---|
| Gap or reader question | Say what remains unestablished or what the reader still needs. |
| Dependency | Name the decision, design, course item, or implementation result that can resolve it. |
| Revisit when | Identify an observable change that should trigger rereading and updating the section. |

An Open section also names who decides, as the existing guide rules require. A note need not repeat information already stated clearly in the section.

A concrete example for the room section:

> **Next update:** describe the canonical room's actual arrival, speech, reply, and departure sequence once the room integration is reviewed. The existing foundation is step 3b's record work; canonical room integration belongs to step 3c. Revisit when the technical lead records and checks that integration. Hosting and public access have further dependencies.

This is a proposal for the guide's maintenance, not an additional development commitment. The current rules already require source-based sections and rereading when their sources change. This note makes the expected next change easier to see.

Sources: [Writing rules](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/guide/README.md#L212-L249); [Built record foundation and next room work](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/COURSE.md#L373-L460).

## 3. Fill planned sections with useful accounts

An incomplete capability can still have a substantive explanation. Give it:

- the experience or problem it is intended to address;
- the decisions already made, with their sources;
- the proposed behavior at the level those decisions support;
- its known dependencies and unresolved questions;
- the evidence that would allow a more definite account.

For example, the planned Library can already be described as a local reference copy reached by plain word search, with the copy and article identified and personal lookup history unrecorded. Its actual interface and return path to a room still need checked instructions. The current source also distinguishes the core lookup from later topic-based discovery. See [The Library](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/COMMONS.md#L570-L605) and [Core-first scope](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/COMMONS.md#L973-L987).

A blank should therefore become a bounded account of what is known and what remains to be worked out. It should not be filled with an invented button, API, decision, deadline, or deployment.

## 4. Keep writing order and development order identifiable

The guide's edition plan determines which chapters are written together. The project's course determines the current development sequence, with its recorded rechecks.

Both can change, but the guide should not silently maintain a second engineering queue. A section can explain dependencies or propose a change; an adopted change belongs in the project's normal decision and course records.

The current course expressly describes itself as a revisable plan. Its first-life summary also says that the Commons-first ordering is to be incorporated at a recheck and that a Library step is to be added. This package does not supply an invented step number or present that recheck as completed.

Sources: [Course method](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/COURSE.md#L1-L20); [Pending first-life reordering](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/COURSE.md#L361-L371); [Guide writing order](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/guide/OUTLINE.md#L309-L319).

## 5. Apply the convention to the first walk

The entries below identify dependencies and proposed evidence for updating the guide. They are not assignments or a newly approved implementation schedule.

| Part of the reader's route | Current footing | What remains to explain or connect | Evidence for the next guide update |
|---|---|---|---|
| Observe the garden and plants | Built local Map and Plant Watch over stored records. | A route from viewing to actual participation is not provided by those pages. | A reviewed participant interface with accurate arrival, available-action, and departure instructions. |
| Converse in a room | Room designs and collaborator sketches; the record foundation at 3b is built. | Canonical room integration at 3c, including speech, replies, record behavior, and departure. | Integrated behavior checked against its law and implementation, with a newcomer walkthrough. |
| Choose among hosted rooms | Commons hosting is designed at 3f, initially with trial keys and scripted guests. | Hosting, offices, and lifecycle integration; publication is a further boundary. | A demonstrated route among hosted rooms and an account of what identity and records each step uses. |
| Look something up | The local Library and plain word search are designed. | Implemented lookup, result attribution, private reading, and deliberate sharing into a conversation. | Checked lookup results and a verified account of what is and is not recorded. |
| Exchange privately | Privacy levels are decided; complete private-room facilities remain designed. | The private container and group-key behavior, with the current room-retention decisions respected. | A reviewed account of membership, key changes, retained metadata, and the limits of the privacy claim. |
| Leave a participating world | Exit is a charter commitment; local world interfaces already have their own behavior. | The actual departure path for each new participant interface, including interruption behavior. | A clear user action and a checked observable outcome; closing a view must not be silently treated as departure. |
| Reach a public integrated service | No deployed public multiverse is identified at this source snapshot. | Hosting and address decisions, the required private container, and the relevant integrations. | A recorded publication decision and verified access instructions for the actual service. |

Principal sources: [web/README.md](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/web/README.md); [Rooms, offices, lifecycle, hosting](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/COURSE.md#L432-L528); [Private container](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/COURSE.md#L587-L617); [Privacy levels and limits](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/COMMONS.md#L169-L220); [Library](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/COMMONS.md#L570-L605); [Deployment status](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/STATUS.md#L1-L13).

## 6. Use the roadmap to preserve consistency

The first walk supplies several concrete distinctions to carry through the rest of the book:

- **A view and a presence:** opening a record viewer does not by itself make the reader a participant.
- **Replay and world time:** changing the displayed tick does not change or erase a world's history.
- **Trial identities and project identities:** a checked signature under a public trial key does not establish the identity of a deployed official world.
- **A component and an experience:** built record formats or checking functions do not make the complete room or account experience built.
- **Public records and private activity:** a complete reference manual must explain what is retained and what is deliberately not recorded.
- **A decision and its enforcement:** the guide should state both the recorded commitment and its current implementation scope.
- **An intended route and a development sequence:** the reader's order of discovery need not be the engineering order.

These are reminders grounded in the reviewed sources and the existing labels, rather than a new terminology scheme. Use the project's glossary for terms such as agent, participant, person, presence, mind, and office. [Glossary](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/GLOSSARY.md)

When a source changes, check what it changes for the reader: an action, a guarantee, a record, a limit, an example, or a dependency. Update all affected sections at the same source revision where practical, and state any known discrepancy explicitly. The book's source map can make those affected sections findable.

A planned section can become more detailed without becoming Built. Promote its label only when the claim at that section's scope is supported.

## 7. Small source wording issues exposed by I.2

These are proposed follow-ups for the technical lead's review:

1. **URWORLD's viewer limit.** The sentence at line 270, “There is no viewer yet beyond the text map,” is too broad beside the built browser map and Plant Watch. A narrower statement about the remaining interactive inhabited-view work would remove the conflict. Source: [Current limits](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/URWORLD.md#L249-L270).
2. **“Live view” in the map description.** The current pages fetch stored runs and replay them. Use wording that makes this clear when describing today's behavior; retain live or ongoing behavior where the design genuinely means future work. Sources: [Fixed input paths](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/web/map/index.html#L160-L164); [Loading the selected record](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/web/plant/index.html#L470-L521); [Endless-world work remains ahead](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/FRACTALS.md#L221-L224).
3. **“Checks before showing” needs its scope.** The Map and Plant Watch do not use identical conditions for drawing. Plant Watch reports head and birth-record problems separately from its chain/growth drawing condition. Its documentation should not suggest that a visible drawing proves every verification succeeded. Source: [Rendering conditions](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/web/plant/index.html#L438-L451).
4. **The checklist count in web/README.** The Plant Watch introduction says it checks “four things,” but the current list has five items after adding reproduction by its own Rust code. Rewording this as “the following checks” would avoid another count becoming stale. Source: [Plant Watch checks](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/web/README.md#L9-L29).

These findings concern documentation wording and the scope of claims; they should be reviewed alongside the corresponding chapter statements.

## 8. Delivery numbering

The numeric prefixes in this package are for reading order on a phone. They do not replace the book's stable identifiers.

- `01_Review_and_I_1.md` retains the earlier complete review and Chapter I.1.
- `02_I_2_First_Walk.md` contains Chapter I.2.
- `03_Living_Roadmap.md` contains this proposal.
- `00_Read_First.md` explains the package and preserves the founder's new instruction.

The chapters' proposed repository homes still follow the guide's convention: `guide/I/01-what-open-worlds-is.md` and `guide/I/02-a-first-walk-through-a-multiverse.md`. The first file is an earlier combined handoff; its Chapter I.1 can be extracted when reviewed.

