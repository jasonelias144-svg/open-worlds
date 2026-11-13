# What games and simulated worlds have learned

Research for the Ur-world and its individuals, done on 2026-11-13 at the
founder's request: "Let's look to role-playing games seriously as an
example for ideas ... Don't limit to my short list of ideas, let's also
look at other simulation worlds. How do they do it?" And later: "The more
we can follow industry standards and take advantage of the lessons
already learned over decades, instead of learning them again
unnecessarily."

The sources are web pages, read on that day. Many are design analyses,
reviews or community wikis rather than primary sources; where a claim
rests on weaker sources, it says so. The design pages that draw on this
are [MINDS.md](../MINDS.md) and [WORLD-KEY.md](../WORLD-KEY.md).

## How characters grow

- **From levels to skills that grow with use.** Classic role-playing games
  had experience points, levels and a class. Many now let a skill improve
  by being used, and some let any character learn anything ("classless")
  ([Game Developer](https://gamedeveloper.com/design/skill-progression-in-rpgs-based-on-play-style),
  [design overview](https://multigamedev.blogspot.com/2025/08/rpg-character-progression-leveling-systems.html)).
  A common criticism of skill trees is that the choices converge on the
  same few "necessary" skills
  ([analysis](https://www.wayline.io/blog/rpg-class-homogenization)).
- **Practice, rust and titles.** In *Dwarf Fortress*, each job done adds
  experience to that skill; a skill left unused for long is marked
  "rusty"; and each level earns a title. Personality limits what can be
  learned: an honest dwarf never gains the Liar skill
  ([wiki](https://dwarffortresswiki.org/index.php/DF2014:Experience)).
- **Knowledge as the only progression.** *Outer Wilds* gives no new powers
  or items. "Knowledge becomes your upgrades": what the player has
  learned is what opens the world. Its ship log keeps a map of what is
  known, marking entries that still have more to find
  ([Game Developer](https://gamedeveloper.com/design/outer-wilds-critical-analysis),
  [learning-design analysis](https://rigdern.github.io/a/learning-about-learning/learning-design-insights-from-outer-wilds/)).
- **The inner life as part of the game.** In *Disco Elysium*, an
  idea met in the world can be "internalised" into one of a few slots of a
  "thought cabinet", which shapes the character; changing what is held
  has a cost ([analysis](https://awkwardmixture.blogspot.com/2020/03/disco-elysium-skill-checks.html)).
- **Characters who outlive their story.** *Wildermyth* carries heroes into
  later campaigns with their items, transformations, history and
  abilities; years pass between chapters, and heroes age, marry, have
  children and retire ([wiki](https://wildermyth.com/wiki/Legacy)).

## How a character is put together

- **Mind, body and what lasts are kept apart.** Unreal Engine splits a
  player into a controller (what decides), a pawn (the body in the
  current level, which is thrown away on death or a change of level), a
  player state (what others can see, like name and score), and saved
  data. The lesson its users repeat: never keep what must last on the body
  ([Unreal forums](https://forums.unrealengine.com/t/playercontroller-on-possess/423098/3),
  [Epic's documentation](https://dev.epicgames.com/documentation/unreal-engine/gameplay-framework-in-unreal-engine)).
- **Built from parts, not from a type.** In the entity-component pattern, a
  character is an identity with components attached; it is defined by
  what it has, not what it is, and new kinds of part can be added without
  redesign. Bevy, the Rust engine, works this way
  ([overview](https://en.wikipedia.com/wiki/Entity_component_system),
  [Hytale's explainer](https://hytale.com/news/2024/6/summer-2024-technical-explainer-hytale-s-entity-component-system-oPwpCAMdI)).
- **Change only through named effects.** Unreal's ability system gives a
  character abilities, numeric attributes and hierarchical tags (such as
  "in water"), which allow or block actions. State changes only through
  named effects, which grant or remove abilities and tags
  ([Epic](https://dev.epicgames.com/documentation/unreal-engine/gameplay-attributes-and-attribute-sets-for-the-gameplay-ability-system-in-unreal-engine?lang=en-US),
  [community documentation](https://github.com/phalasz/gasdocumentation)).
- **How one acts, apart from what one believes.** *Dwarf Fortress* rates
  each character on about 50 facets (how they act) and about 30 values
  (what they believe). Needs come from these; relationships form where
  values agree or clash; memories, each an event with an emotion, can
  slowly change personality
  ([facets](https://dwarffortresswiki.org/index.php/DF2014:Personality_facet),
  [needs](https://dwarffortresswiki.org/index.php/DF2014:Need),
  [memories](https://gamedeveloper.com/game-platforms/-i-dwarf-fortress-i-is-giving-its-dwarves-the-ability-to-form-and-dwell-on-memories),
  [Tarn Adams' paper](https://wileywiggins.com//documents/dorf/Adams%20-%20Characterization%20and%20Emergent%20Narrative%20in%20Dwarf%20F.pdf)).

## How worlds teach

- **The manual is in the world.** *Tunic*'s instruction manual is found
  page by page while exploring, partly written in a script the player
  learns to read; gathering it is what opens the true ending
  ([GameSpot](https://Www.Gamespot.com/articles/tunics-in-game-manual-gives-mechanical-importance-to-collectibles/1100-6509945/)).
- **A language with no words.** *The Witness* teaches a puzzle grammar
  through sequences of panels, each group opening with a few that teach a
  rule ([overview](https://gamingbolt.com/wordless-games-communicating-gameplay-without-words)).
- **A language learned word by word.** In *No Man's Sky*, alien languages
  are learned one word at a time, from stones, ruins and conversations
  ([guide](https://gamerguides.com/no-mans-sky/guide/walkthrough/tips-and-tricks/how-to-learn-languages)).
- **A tree of advancements.** Minecraft guides players through an ordered
  tree of challenges in several categories; some community versions lock
  abilities behind advancements
  ([wiki](https://minecraft.fandom.com/wiki/Advancement)).

## How simulated worlds run

- **A storyteller paces events.** *RimWorld*'s storyteller follows a rising
  and falling curve of tension, and comes in different temperaments
  ([wiki](https://rimworldwiki.com/wiki/AI_Storytellers)).
- **A game master turns actions into outcomes.** DeepMind's Concordia runs
  worlds for language-model agents with a "game master", borrowed from
  tabletop role-playing; in Concordia it is usually a model
  ([repository](https://WWW.GITHUB.COM/google-deepmind/concordia)).
- **A world remembers its history.** *Dwarf Fortress*'s Legends mode shows
  the history of every civilisation and figure who lived in a world
  ([wiki](https://dwarffortresswiki.org/Dwarf_Fortress)).

## Worlds built for AI agents

- **A skill library and a curriculum.** Voyager, a language-model agent in
  Minecraft, stores each skill it masters as a routine it can reuse,
  built from simpler ones, and gets its next task from a curriculum that
  fits its progress and surroundings. It was not trained; it learned by
  keeping routines ([paper](https://arxiv.org/pdf/2305.16291v2.pdf)).
- **Memory, reflection and plans.** Generative Agents ("Smallville") kept
  each agent's experiences as a stream of memories, recalled by recency,
  importance and relevance, with reflections and plans built on them. A
  known failure: reflections can invent relationships that never happened
  ([overview](https://www.emergentmind.com/topics/generative-agents-smallville)).
- **A civilisation of agents.** Project Sid ran up to about a thousand
  agents in Minecraft; they took jobs, used a currency, voted on taxes and
  spread a religion. These are early results, mostly from press reports
  ([paper](https://arxiv.org/abs/2411.00114?context=cs),
  [MIT Technology Review](https://technologyreview.com/2024/11/27/1107377/a-minecraft-town-of-ai-characters-made-friends-invented-jobs-and-spread-religion)).
- **Memory can hurt.** A 2026 benchmark found that agents with add-on
  memory or skill libraries sometimes did worse than agents without
  ([PATH-Bench](https://www.alphaxiv.org/abs/2608.01149)).

## Open source to learn from

The founder: "We should definitely take advantage of how others have
solved the problems we are considering." So each course step begins by
looking at how open-source projects already solved it, and what was
looked at is written down here.

**How we may use others' work.** This project is given to the public
domain (CC0), so:

- learning patterns from any code, with credit, is always fine;
- depending on a library under a permissive licence (MIT, Apache, BSD) is
  fine, and the library keeps its own licence;
- code is copied only from permissive licences, with its notice kept beside
  it, and the copy says so. Code under the GPL is read for ideas, never
  copied, since copying it would bind the whole project to its terms.

The licences below are as reported by the sources found on 2026-11-13;
each is confirmed from the project's own licence file before use.

| Project | What it offers us | For | Licence |
|---|---|---|---|
| TextWorld (Microsoft) | an engine that generates text games with quests, from settings such as map size, quest length and complexity, and runs them for agents ([Microsoft Research](https://www.microsoft.com/en-us/research/project/textworld/), [listing](https://awesome.ecosyste.ms/projects/github.com%2FMicrosoft%2FTextWorld)) | the Keeper's paths; the hunt | MIT (one listing says "other") |
| pyBKT | Bayesian knowledge tracing: estimating what a learner knows from what they do ([paper](https://arxiv.org/abs/2105.00385v2)) | the Keeper's learner model | MIT |
| Concordia (DeepMind) | a game master for worlds of language-model agents ([repository](https://WWW.GITHUB.COM/google-deepmind/concordia)) | the Keeper | Apache 2.0 |
| Evennia | a framework for persistent text worlds, with a ladder of powers: players, helpers, builders, admins, developers ([licensing](https://www.evennia.com/docs/0.x/Licensing.html), [permissions](https://www.evennia.com/docs/0.x/Building-Permissions.html)) | what the Keeper and operators may do | BSD 3-clause |
| Letta (formerly MemGPT) | persistent memory blocks that agents edit themselves ([overview](https://www.developersdigest.tech/agent-memory/letta)) | held thoughts; memory | Apache 2.0 |
| AI Town | an open re-implementation of the Smallville simulation ([repository](https://github.com/a16z-infra/ai-town/)) | memory; a town of agents | MIT |
| Voyager | a skill library of routines, and a curriculum ([paper](https://arxiv.org/pdf/2305.16291v2.pdf)) | routines; the Keeper's next challenge | MIT, to confirm |
| Bevy | the entity-component system | the kernel (course step 4) | MIT or Apache 2.0, to confirm |
| WaveFunctionCollapse | generating land that fits its neighbours, piece by piece ([mirror](https://sourceforge.net/projects/wavefunctioncollapse.mirror/), [history](https://records.sigmm.org/?p=12589)) | generator 2, land decided when first seen | code MIT; its sample images are not, to confirm |

## What we take, and what we leave

Taken, and where it goes:

- knowledge as a kind of growth, beside skills and things (the sheet's
  knowledge log, [MINDS.md](../MINDS.md));
- the orientation found in pieces, partly in symbols, rather than told
  all at once ([WORLD-KEY.md](../WORLD-KEY.md));
- skills that grow with practice and rust, with titles;
- two kinds of skill: abilities a world grants, and routines an
  individual writes and keeps;
- a few slots of held thoughts, chosen by the individual;
- memories tied to the record, so an invented one shows;
- mind, body and what lasts kept apart; parts, not types; change only
  through logged effects;
- how one acts kept apart from what one believes, with the first measured
  and the second stated;
- a storyteller as part of a world's law;
- legends pages, written from the logs.

Left, or changed:

- **Assigned personality.** ALICE's and BOB's characters come from their
  minds. Traits are observed and recorded, never handed out.
- **Removing others.** No mechanic lets anyone remove anyone else; leaving
  is only the leaver's choice.
- **A model as judge.** In the Ur-world the kernel decides what happens,
  in code that anyone can check. Each world's Keeper, an AI, designs
  challenges and paces events, but the kernel checks and places what it
  designs, and the law stays above both ([WORLD-KEY.md](../WORLD-KEY.md),
  "The Keeper").
- **Copying content.** We borrow ideas and mechanics, not any game's
  content.
- **Memory taken on trust.** Because memory can hurt, it is measured
  (experiment 002), not assumed.
