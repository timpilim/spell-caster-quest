# Data Schema — Spell Caster Quest

> **Status:** Draft v2.0, aligned with `SpellCastGame v2.0.md`. Section references (§) point to that document.
>
> **Scope:** content/config entities, save state, and the battle runtime state the engine needs. **Out of scope:** UI component props, animation data, internal React state.
>
> **Form:** TypeScript-first. These types are meant to live verbatim in `packages/shared` (see GDD §11) and to be enforced on JSON content with zod (or JSON Schema generated from them). A relational mapping for a future backend is sketched in §14.

## 1) Overview

The game is **data-driven**: chapters, encounters, enemies, fragments, statuses (buffs/debuffs/Oaths) and rules are JSON, loaded through async services (static files + Local Storage in the MVP; swappable later).

Suggested content layout (`apps/web/public/content/` or a `content/` package):

| File | Contains | Schema |
|------|----------|--------|
| `game-config.json` | global knobs | `GameConfig` |
| `chapters.json` | chapters with rules and encounter order | `ChapterDefinition[]` |
| `encounters.json` | one battle each | `EncounterDefinition[]` |
| `enemies.json` | enemy actors: stats, moves, dialogue, loot | `EnemyDefinition[]` |
| `fragments.json` | all fragments incl. Shrouded variants | `FragmentDefinition[]` |
| `fragment-tables.json` | draw tables: global + chapter/encounter overrides | `FragmentTable[]` |
| `statuses.json` | buffs (family × level), Oaths, temporary buffs, debuffs | `StatusDefinition[]` |
| `loot-tables.json` | loot tables referenced by enemies + global fallback | `LootTable[]` |
| `hints.json` | first-time hint texts | `HintDefinition[]` |
| `dictionary.txt.gz` | validation word list | see §10 |

Cross-references are always by **code** (string). A content linter (§13) verifies every reference resolves.

## 2) Conventions

- `code`: stable, lowercase, snake_case, unique **within its entity type** (`fireball`, `power_3`, `oath_flame`, `ch1_toad_king`).
- Percentages are **fractions** (`0.2` = 20%). Multipliers are decimals (`1.5` = ×1.5). HP, Energy, seconds, turns are integers.
- Text shown to the player lives in `label`/`description`/dialogue fields (English only in the MVP; a string-table indirection can be added later).
- Every numeric value is a **tuning knob**; nothing here is a hard promise.
- Optional fields are omitted, never `null`.

## 3) Primitives

```ts
/** Stable identifier used to reference content across files. */
export type Code = string;

/** 0..1 fraction (0.15 = 15%). May exceed 1 where documented (e.g. summed Power bonuses). */
export type Fraction = number;

/** Multiplier such as 1.5 (×1.5). */
export type Multiplier = number;

/** Whole number (HP, Energy, turns, seconds). */
export type Int = number;

/** Milliseconds since epoch. */
export type UnixMs = number;

/** Single uppercase letter A–Z. */
export type Letter = string;

/** Weighted reference; omitted weight means 1. */
export interface Weighted<T extends Code = Code> {
  code: T;
  weight?: number;
}

/** Primary effect types produced by spells (GDD §4.2.3). */
export type EffectType = "attack" | "block" | "heal";
```

## 4) Global configuration

```ts
/**
 * Global rules that are not per-chapter. Keep small: chapter-level knobs live in ChapterRules.
 * Defaults in comments are the GDD v2.0 values.
 */
export interface GameConfig {
  /** Player starting Max HP. Default 100. */
  playerMaxHp: Int;

  /** Backfire rule (GDD §4.4.5, D4). */
  backfire: {
    /** Fraction of Max HP per fragment in the failed spell. Default 0.03. */
    maxHpFractionPerFragment: Fraction;
    /** Floor for Backfire damage. Default 1. */
    minDamage: Int;
  };

  /** Binding timer rule (GDD §4.4.1, D9). */
  bindingTimer: {
    /** Base seconds for spells up to `baseCoversFragments`. Default 30. */
    baseSec: Int;
    /** Fragment count covered by baseSec. Default 4. */
    baseCoversFragments: Int;
    /** Extra seconds per fragment above baseCoversFragments. Default 10. */
    extraSecPerFragment: Int;
    /** Hard floor after debuffs/Oaths. Default 10. */
    minSec: Int;
  };

  /** Minimum fragments in any spell (Command + 1 Aspect + Entity). Default 3. */
  minFragmentsPerSpell: Int;

  /** Maximum Oathbound statuses the player may hold. Default 2. */
  maxOaths: Int;

  /** Loot screen option count. Default 3. */
  lootOptions: Int;

  /** Summed Armor reduction cap (GDD §6.5). Default 0.75. */
  maxDamageReduction: Fraction;

  /** Global fallback loot table used when an enemy table has too few valid options (GDD §6.4). */
  fallbackLootTableCode: Code;

  /** Word list to validate binding words against (§10). */
  dictionaryCode: Code;

  /** Max reroll attempts when enforcing pool solvability (GDD §7.2). Default 20. */
  poolSolvabilityAttempts: Int;
}
```

## 5) Chapters and encounters

```ts
/**
 * Per-chapter difficulty levers (GDD §5.3). Encounters may override individual fields.
 */
export interface ChapterRules {
  /** Max fragments per spell: 3 / 4 / 5 in the MVP chapters. */
  maxFragmentsPerSpell: Int;

  /** Pool capacity per category (GDD §7.1). */
  poolSize: { commands: Int; aspects: Int; entities: Int };

  /** Probability that a Command or Aspect draw is taken from Shrouded entries. 0 / 0.2 / 0.35. */
  shroudedShare: Fraction;

  /** Fragment table used for draws unless the encounter overrides it. */
  fragmentTableCode: Code;

  /** Temporary buffs a `?` Aspect can grant in this chapter (GDD §6.6). */
  tempBuffPool: Weighted[];
}

/**
 * A chapter: the player-facing encounter list plus its rules.
 */
export interface ChapterDefinition {
  code: Code;
  /** Location name shown as the chapter title. */
  title: string;
  /** Intro plot text (shown once as a modal, then truncated at the top of the list). */
  intro: string;
  /** Chapter unlocked after this one's boss is beaten; omitted for the last chapter. */
  nextChapterCode?: Code;
  rules: ChapterRules;
  /** Ordered encounter codes as shown in the list; the boss is `bossEncounterCode` and is rendered separately. */
  encounterCodes: Code[];
  bossEncounterCode: Code;
}

/**
 * One selectable battle. MVP: exactly one enemy.
 */
export interface EncounterDefinition {
  code: Code;
  enemyCode: Code;
  /** One-line flavor text on the encounter row. */
  flavor?: string;
  /** Overrides of the chapter rules for this fight (tutorial pools, themed fights). */
  rulesOverride?: Partial<ChapterRules>;
  /** Hints to show the first time this encounter is played (tutorial). */
  hintCodes?: Code[];
}
```

## 6) Fragments and fragment tables

```ts
export type FragmentCategory = "command" | "aspect" | "entity";

/**
 * Fields shared by all fragment categories.
 */
export interface FragmentBase {
  code: Code;
  category: FragmentCategory;
  /** The full word, uppercase A–Z only, 4–9 letters. */
  word: string;
  /**
   * Shroud mask for Shrouded fragments (GDD §4.4.4). Same length as `word`;
   * `_` = hidden, `.` = visible (e.g. "S_V___"). Omitted for normal fragments.
   * Shrouded variants are separate entries with their own code and stats.
   */
  shroudMask?: string;
  /** Free-form tags for tooling (e.g. "tutorial", "fire"). */
  tags?: string[];
}

/** Command (verb): sets base Energy (GDD §4.2.1). */
export interface CommandFragment extends FragmentBase {
  category: "command";
  baseEnergy: Int;
}

/** A flat secondary effect carried by an Aspect (GDD §4.2.2). Not scaled by Power. */
export interface SecondaryEffect {
  type: EffectType;
  value: Int;
}

/** Aspect (adjective): modifies Energy, may add a secondary effect and/or a `?` marker. */
export interface AspectFragment extends FragmentBase {
  category: "aspect";
  /** Additive Energy change (+1, +2, +3). */
  energyAdd?: Int;
  /** Multiplicative Energy change (1.5, 2). */
  energyMultiply?: Multiplier;
  secondary?: SecondaryEffect;
  /** Number of `?` markers (temporary buffs granted on cast). Usually 1. */
  mysteryMarkers?: Int;
}

/** Entity (noun): converts Energy into the primary effect 1:1 (GDD §4.2.3). */
export interface EntityFragment extends FragmentBase {
  category: "entity";
  effectType: EffectType;
  /** Rare flat bonus added to the primary effect (e.g. STORM +1). */
  flatBonus?: Int;
}

export type FragmentDefinition = CommandFragment | AspectFragment | EntityFragment;

/**
 * A draw table for pool refills (GDD §7.1). The chapter names its table; encounters may override.
 * Shrouded entries are listed separately so `ChapterRules.shroudedShare` can select between the two lists.
 */
export interface FragmentTable {
  code: Code;
  label?: string;
  /** Normal fragments, all categories, with draw weights. */
  entries: Weighted[];
  /** Shrouded fragments (must have `shroudMask`). May be empty in early chapters. */
  shroudedEntries: Weighted[];
}
```

## 7) Statuses: buffs, Oaths, temporary buffs, debuffs

One definition type covers every passive effect on the player. The `kind` decides ownership rules (GDD §6):

- `buff`: permanent loot; one per `family`, higher `level` replaces lower.
- `oath`: permanent loot; at most `GameConfig.maxOaths`; always has at least one negative effect.
- `temp_buff`: battle-only, granted by `?` Aspects; duplicates stack.
- `debuff`: battle-only, applied by enemies, turn-limited; re-application refreshes duration.

### 7.1 Effects

Effects are a closed union rather than a generic "target/operator" pair, so the engine, the linter and the UI tooltip generator all know exactly what can exist. Add a member when a new mechanic is designed.

```ts
/** Gate for conditional effects (GDD §6.2). */
export type StatusCondition =
  /** Rage, Shell: HP ≤ fraction of Max HP. */
  | { type: "hp_at_most"; fraction: Fraction }
  /** Payback: the player took damage (attack, Bleed or Backfire) during the previous round. */
  | { type: "damaged_last_round" };

/** Multiplies the effect value by a runtime counter (GDD §6.2). */
export type StatusScaling =
  /** Momentum: consecutive successful casts, reset by Backfire. */
  | { by: "consecutive_casts"; maxStacks: Int }
  /** Confidence: fragments in the current spell beyond `beyond`. */
  | { by: "fragments_beyond"; beyond: Int };

export type StatusEffect =
  /** Summed into the Energy multiplier: E × (1 + Σ). Power, Rage, Payback, Momentum, Confidence, Surge, Oaths. */
  | { type: "energy_pct"; value: Fraction; condition?: StatusCondition; scaling?: StatusScaling }
  /** Vitality, Vigor. Applied at battle start (and heals the same amount when gained mid-battle). */
  | { type: "max_hp_add"; value: Int }
  /** Armor, Ward. Summed, capped by GameConfig.maxDamageReduction. Enemy attacks only. */
  | { type: "damage_taken_reduction"; value: Fraction }
  /** Lifesteal, Thirst, Oath of Glass: heal fraction of Attack damage dealt (floor). Summed. */
  | { type: "lifesteal"; value: Fraction }
  /** Resolve (0.75, 0.5, 0.25), Oath of Glass (2), Oath of Depth (1.5). Multiplied together. */
  | { type: "backfire_multiplier"; value: Multiplier }
  /** Focus, Clarity (+), Haste, Oath of Pressure (−). Summed, then floored at GameConfig.bindingTimer.minSec. */
  | { type: "binding_time_add_sec"; value: Int }
  /** Oath of Depth: +1 to the chapter's maxFragmentsPerSpell. */
  | { type: "max_fragments_add"; value: Int }
  /** Oath of Flame (fixed letter) and Hex (random consonant chosen when applied, stored on the instance). */
  | { type: "banned_letter"; letter: Letter | "random_consonant" }
  /** Shell: gain Block at the end of the player's turn. */
  | { type: "block_at_turn_end"; value: Int; condition?: StatusCondition }
  /** Bleed: HP change at the start of the player's turn (negative = damage; ignores Armor and Block). */
  | { type: "hp_at_turn_start"; value: Int }
  /** Frailty: multiply Block gained (0.5). */
  | { type: "block_multiplier"; value: Multiplier }
  /** Oath of Silence: multiply Aspect secondary effects. */
  | { type: "secondary_multiplier"; value: Multiplier }
  /** Oath of Silence: add to every Command's base Energy (negative allowed). */
  | { type: "command_energy_add"; value: Int }
  /** Fog: when applied, shroud N random normal pool fragments until they are used. */
  | { type: "shroud_pool_fragments"; count: Int };
```

### 7.2 Definitions

```ts
export type StatusKind = "buff" | "oath" | "temp_buff" | "debuff";

/** Buff families (GDD §6.2). Also used for icons and loot filtering. */
export type BuffFamily =
  | "power" | "vitality" | "armor" | "lifesteal" | "resolve" | "focus"
  | "rage" | "shell" | "payback" | "momentum" | "confidence";

/**
 * A buff, Oath, temporary buff or debuff.
 */
export interface StatusDefinition {
  code: Code;
  kind: StatusKind;
  /** Display name, e.g. "Power III", "Oath of Flame", "Bleed". */
  label: string;
  /** One-line effect text for chips and loot cards, e.g. "+30% Energy". */
  summary: string;
  /** Longer tooltip text. Optional; can be generated from effects. */
  description?: string;
  /** Emoji placeholder now, icon code later. */
  icon: string;

  /** Required for kind = "buff": family + level drive the one-per-family cap (GDD §6.4). */
  family?: BuffFamily;
  /** 1..5. Required for kind = "buff". */
  level?: Int;

  /** Required for kind = "debuff": turns it stays active (GDD §6.7). Omitted = until battle end. */
  durationTurns?: Int;

  effects: StatusEffect[];
}
```

### 7.3 Examples

```jsonc
// statuses.json (excerpt)
[
  { "code": "power_3", "kind": "buff", "family": "power", "level": 3,
    "label": "Power III", "summary": "+30% Energy", "icon": "🔥",
    "effects": [{ "type": "energy_pct", "value": 0.3 }] },

  { "code": "rage_2", "kind": "buff", "family": "rage", "level": 2,
    "label": "Rage II", "summary": "+25% Energy while HP ≤ 50%", "icon": "😤",
    "effects": [{ "type": "energy_pct", "value": 0.25, "condition": { "type": "hp_at_most", "fraction": 0.5 } }] },

  { "code": "momentum_1", "kind": "buff", "family": "momentum", "level": 1,
    "label": "Momentum I", "summary": "+5% Energy per consecutive cast (max 5)", "icon": "🌀",
    "effects": [{ "type": "energy_pct", "value": 0.05, "scaling": { "by": "consecutive_casts", "maxStacks": 5 } }] },

  { "code": "oath_flame", "kind": "oath", "label": "Oath of Flame",
    "summary": "+50% Energy · no letter L in binding words", "icon": "🕯️",
    "effects": [{ "type": "energy_pct", "value": 0.5 }, { "type": "banned_letter", "letter": "L" }] },

  { "code": "tmp_surge", "kind": "temp_buff", "label": "Surge", "summary": "+20% Energy this battle", "icon": "⚡",
    "effects": [{ "type": "energy_pct", "value": 0.2 }] },

  { "code": "bleed", "kind": "debuff", "durationTurns": 3, "label": "Bleed", "summary": "−3 HP at turn start", "icon": "🩸",
    "effects": [{ "type": "hp_at_turn_start", "value": -3 }] },

  { "code": "hex", "kind": "debuff", "durationTurns": 2, "label": "Hex", "summary": "one letter is banned", "icon": "🔮",
    "effects": [{ "type": "banned_letter", "letter": "random_consonant" }] }
]
```

## 8) Enemies, moves, dialogue, loot

```ts
export type EnemyMoveType = "attack" | "debuff";

/**
 * One enemy action. Intent shows exactly this (GDD §4.3): attacks show `damage`, debuffs show the status icon.
 */
export interface EnemyMove {
  code: Code;
  type: EnemyMoveType;
  /** Short intent line, e.g. "sharpens its quill". */
  intentLabel: string;
  /** Attack damage before player Armor/Block. Required for type = "attack". */
  damage?: Int;
  /** Bosses: telegraphed big hit (💥). Never selected twice in a row. */
  heavy?: boolean;
  /** Debuff applied to the player. Required for type = "debuff". */
  statusCode?: Code;
  /** Draw weight (default 1). */
  weight?: number;
  /** Optional flavor line shown when the move resolves. */
  quip?: string;
}

export interface EnemyDialogue {
  /** Shown before the first player turn. */
  greeting: string[];
  /** Enemy loses (player victory). */
  onDefeat: string[];
  /** Enemy wins (player defeat). */
  onVictory: string[];
}

export type EnemyType = "standard" | "boss";

/**
 * Enemy actor (GDD §8). The player actor is not content; it comes from GameConfig + save state.
 */
export interface EnemyDefinition {
  code: Code;
  name: string;
  type: EnemyType;
  /** Emoji placeholder now, asset code later. */
  portrait: string;
  maxHp: Int;
  moves: EnemyMove[];
  dialogue: EnemyDialogue;
  /** Loot table offered after victory (GDD §5.4). */
  lootTableCode: Code;
}

/**
 * Loot table: weighted status codes (buffs and Oaths). The Loot Screen filters to options that improve
 * the player (GDD §6.4), draws `GameConfig.lootOptions`, and tops up from the fallback table.
 */
export interface LootTable {
  code: Code;
  entries: Weighted[];
  /** Bosses: an Oath choice is always among the options on the first victory. */
  guaranteedOathOnFirstWin?: boolean;
}
```

## 9) Hints

```ts
/**
 * First-time hints (GDD §9.2). Shown once per save; `trigger` names an engine event.
 */
export interface HintDefinition {
  code: Code;
  trigger:
    | "draft_command" | "draft_aspect" | "draft_entity" | "press_bind" | "binding_started"
    | "first_intent" | "first_shrouded" | "first_mystery" | "first_heavy_intent" | "first_debuff"
    | "first_oath_offer" | "first_loot";
  text: string;
}
```

## 10) Dictionary

```ts
/**
 * Word list for binding validation (GDD §10.1). Ships as gzipped plain text, one lowercase word per line.
 * Loaded once into a Set plus a per-length index (words grouped by length) for the solvability check.
 */
export interface DictionaryConfig {
  code: Code;
  label?: string;
  /** Asset path or URL. */
  resource: string;
  /** Words shorter than this are ignored even if present. Default 3. */
  minWordLength: Int;
}
```

Validation rule: `isValidBindingWord(word) = word.length ≥ minWordLength && dictionary.has(word.toLowerCase()) && !bannedLetters.some(l => word.includes(l))`.

Solvability check for a spell with letter sets `S₁..Sₙ` (one per fragment): any word `w` of length `n` in the per-length index with `w[i] ∈ Sᵢ` for all `i`, ignoring banned letters.

## 11) Save state

```ts
/**
 * Persistent player progress (Local Storage in the MVP). No battle state, no HP.
 */
export interface PlayerSave {
  /** Schema version for migrations, e.g. "2.0". */
  version: string;
  createdAt: UnixMs;
  updatedAt: UnixMs;

  /** Chapters the player may open. */
  unlockedChapterCodes: Code[];
  /** Last opened chapter, for "Continue". */
  currentChapterCode: Code;

  /** Encounters beaten at least once (Beaten marker, boss gate). */
  beatenEncounterCodes: Code[];
  /** Encounters played at least once (for tutorial hints and first-win Oath guarantees). */
  playedEncounterCodes: Code[];

  /**
   * Held permanent statuses (kind "buff" or "oath"), at most one per family and at most
   * GameConfig.maxOaths Oaths. Levels are never lost (GDD §6.4).
   */
  heldStatusCodes: Code[];

  /** Hint codes already shown. */
  shownHintCodes: Code[];

  /** Lightweight stats for the future (not shown in MVP). */
  stats?: {
    battlesWon: Int;
    battlesLost: Int;
    spellsCast: Int;
    backfires: Int;
    longestBindingWord?: string;
  };
}
```

## 12) Battle runtime state

Engine-facing shapes. Serializable, so a battle can be resumed after a reload and replayed in tests. All randomness comes from `rngState`.

```ts
export type BattlePhase =
  | "enemy_greeting"
  | "player_draft"
  | "player_bind"
  | "resolve_cast"
  | "resolve_backfire"
  | "resolve_fizzle"
  | "enemy_act"
  | "victory"
  | "defeat";

/**
 * A status applied in this battle (permanent ones are copied in at battle start).
 */
export interface StatusInstance {
  /** Unique within the battle; lets the same temp buff stack twice. */
  instanceId: string;
  statusCode: Code;
  source: "permanent" | "mystery" | "enemy";
  /** Turns left for debuffs; omitted = until battle end. */
  remainingTurns?: Int;
  /** Resolved at application time for `banned_letter: "random_consonant"`. */
  bannedLetter?: Letter;
}

/**
 * A fragment sitting in the pool. Instance-level because Fog can shroud a normal fragment at runtime.
 */
export interface PoolFragment {
  instanceId: string;
  fragmentCode: Code;
  /** True if the chip currently shows a mask (Shrouded definition, or Fogged). */
  shrouded: boolean;
  /** Mask in effect when shrouded (definition mask, or a generated one for Fog). */
  shroudMask?: string;
}

/** The spell on the desk, in sentence order: [command, ...aspects, entity]. */
export interface SpellDraft {
  fragmentInstanceIds: string[];
}

/**
 * Binding Mode state (GDD §4.4). One segment per fragment.
 */
export interface BindingState {
  /** Frozen at Bind time. */
  spell: SpellDraft;
  /** Selected letter index into fragment.word per segment; -1 = empty. */
  selectedLetterIndex: Int[];
  /** Wall-clock deadline; remaining time is derived, so pausing/resuming is a UI concern. */
  deadlineAt: UnixMs;
  /** Total seconds granted (for the timer ring). */
  totalSec: Int;
  /** Letters rejected by Hex/Oath, for the "blocked" feedback. */
  bannedLetters: Letter[];
  /** Number of invalid words tried (analytics, hints). */
  invalidAttempts: Int;
}

/**
 * Computed outcome of a cast, shown on the spell card and applied in resolve_cast.
 */
export interface CastResult {
  fragmentCodes: Code[];
  bindingWord: string;
  energy: Int;
  primary: { type: EffectType; value: Int };
  secondary: SecondaryEffect[];
  /** Temp buffs granted by `?` markers. */
  grantedStatusCodes: Code[];
  /** HP healed by Lifesteal. */
  lifestealHeal: Int;
}

export interface PlayerBattleState {
  hp: Int;
  maxHp: Int;
  /** Block active until the start of the next player turn. */
  block: Int;
  statuses: StatusInstance[];
  /** Momentum counter; reset by Backfire. */
  consecutiveCasts: Int;
  /** Payback flag: damage taken during the previous round. */
  damagedLastRound: boolean;
}

export interface EnemyBattleState {
  enemyCode: Code;
  hp: Int;
  /** Move the enemy will perform this round (Intent). */
  intentMoveCode: Code;
  /** For the "no heavy twice in a row" rule. */
  lastMoveCode?: Code;
}

/**
 * Full battle snapshot.
 */
export interface BattleState {
  battleId: string;
  encounterCode: Code;
  /** Effective rules = chapter rules + encounter override + Oath of Depth. */
  rules: ChapterRules;
  /** Serializable PRNG state (e.g. xorshift seed) for deterministic replays. */
  rngState: string;
  /** 1-based round counter. */
  round: Int;
  phase: BattlePhase;
  player: PlayerBattleState;
  enemy: EnemyBattleState;
  pool: PoolFragment[];
  draft: SpellDraft;
  /** Present only in phase player_bind. */
  binding?: BindingState;
  /** Present in resolve_cast / resolve_backfire. */
  lastCast?: CastResult;
  lastBackfireDamage?: Int;
  /** Center-panel narration line for the current phase. */
  narration?: string;
}
```

## 13) Content validation (linter rules)

Run at build time and in unit tests:

1. Every `Code` reference resolves (`enemyCode`, `statusCode`, `lootTableCode`, `fragmentTableCode`, table entries, `tempBuffPool`, `nextChapterCode`, `bossEncounterCode` ∈ chapter encounters or listed separately).
2. Fragments: `word` matches `^[A-Z]{4,9}$`; Commands and Entities contain ≥ 2 distinct vowels (GDD §7.4); `shroudMask` has the word's length, uses only `_`/`.`, and hides 60–80% of letters; Shrouded entries appear only in `shroudedEntries`.
3. Fragment tables referenced by a chapter contain at least `poolSize.x + 1` distinct fragments per category so refills never stall.
4. Pool solvability sanity: for each chapter table, sample 1,000 random pools and report the share needing rerolls (target < 5%).
5. Statuses: `kind = buff` has `family` and `level`; levels within a family are contiguous from 1 and effect values are monotonic; `kind = oath` has at least one negative effect; `kind = debuff` has `durationTurns` (or is Fog); `banned_letter` letters are consonants.
6. Enemies: attack moves have `damage`, debuff moves have a `statusCode` of kind `debuff`, at most one `heavy` move per enemy, weights > 0.
7. Loot tables reference only `buff`/`oath` statuses; boss tables contain at least one Oath when `guaranteedOathOnFirstWin`.
8. `hints.json` covers every trigger used by chapter 1 encounters.

## 14) Future backend mapping (not MVP)

When cloud saves arrive on the Fastify + Postgres backend from the template:

- Content stays as versioned JSON assets (or a `content_bundle(version, json)` table); it is not normalized into tables.
- `PlayerSave` maps to `player_save(user_id PK, version, json JSONB, updated_at)`. One row per user is enough; conflict resolution by `updatedAt`.
- Optional analytics: `battle_result(user_id, encounter_code, won, rounds, backfires, longest_word, played_at)`.

## Appendix: changes from the previous draft

- `GameConfig`: removed `fragmentPoolSize` (now per chapter), added Backfire/timer rules per GDD v2.0, Oath cap, loot options, fallback table.
- `Chapter` → `ChapterDefinition` with explicit `ChapterRules` (max fragments, pool sizes, Shrouded share, temp-buff pool).
- `Actor` → `EnemyDefinition`; moves show exact damage (no ranges), added `heavy`, dialogue keys renamed (`onDefeat`/`onVictory`).
- `FragmentPool` → `FragmentTable` with separate `shroudedEntries`; Shrouded variants are separate fragments.
- `AspectFragment.tempBuffOnCast` → `mysteryMarkers` count; the temp-buff pool moved to `ChapterRules`.
- `GameBuff` + generic `Modifier` → `StatusDefinition` with a closed `StatusEffect` union, `kind`, `family`, `level`; debuffs and temp buffs share it.
- Save state tracks `heldStatusCodes` (one per family), `playedEncounterCodes`, `shownHintCodes`.
- Battle state: instance ids for pool fragments and statuses, deadline-based timer, `CastResult`, PRNG state, `resolve_fizzle` phase; removed `revealedHiddenIndices` (all letters reveal at Bind).
