# Data Schema Draft — Spell Caster Quest

> **Status:** Draft / proposal (not final).
>
> This document proposes a **lean, data-driven schema** for Spell Caster Quest.
> It is meant to serve as a shared “backbone” for development and content authoring.
> Field names and shapes may change during implementation.
>
> **Scope:** content/config entities + minimal runtime/save state entities.
> **Out of scope:** UI component props, rendering/animation details, internal engine data structures.

## 1) High-level data model
The game is intended to be **configured via JSON** and loaded through async “services” (LocalStorage + local files in MVP; swappable later).

Suggested content files (not mandatory):
- `content/chapters.json` — chapters + encounter ordering
- `content/encounters.json` — encounter definitions (single-enemy in MVP)
- `content/actors.json` — enemy actors + dialogue + movesets
- `content/fragments.json` — all fragments (Command / Aspect / Entity)
- `content/fragment-pools.json` — global pool + optional overrides for chapters/encounters
- `content/buffs.json` — buffs and debuffs (same schema)
- `content/dictionary.json` (or `dictionary.txt`) — valid English words for binding validation
- `content/game-config.json` — small global knobs (timer, backfire defaults, etc.)

## 2) Naming and conventions
- `code` fields are stable string identifiers used for referencing, e.g. `"fireball"` or `"goblin_warrior"`.
- All numeric tuning values are **design knobs**, not hard guarantees.
- Percentages are represented as decimals (e.g., `0.1` for 10%).
- Multipliers are represented as decimals (e.g., `1.2` for ×1.2).

---

## 3) Shared primitive types

```ts
/** Stable code used to reference content across JSON files. */
export type Code = string;

/** 0..1 fraction. Example: 0.15 == 15%. */
export type Fraction = number;

/** Multipliers like 1.1 (x1.1). */
export type Multiplier = number;

/** Whole-number counters (HP, turns, etc.). */
export type Int = number;

/** Milliseconds since epoch (for saves). */
export type UnixMs = number;

/**
 * Weighted choice helper.
 * If weight is omitted, treat as weight=1.
 */
export interface WeightedRef<T> {
  code: T;
  weight?: number;
}
```

---

## 4) Global configuration

```ts
/**
 * Global tuning knobs.
 * Keep this small; most balancing should live in content (fragments/buffs/actors).
 */
export interface GameConfig {
  /** Default binding timer in seconds (MVP: 30). */
  bindingTimeLimitSec: Int;

  /**
   * Backfire base damage formula (tunable).
   * Engine may interpret this as: backfire = maxHp * basePerFragment * fragmentsUsed,
   * then apply modifiers from buffs.
   */
  backfire: {
    /** e.g. 0.05 means 5% of Max HP per fragment used. */
    baseMaxHpFractionPerFragment: Fraction;
    /** Minimum damage so Backfire always matters. */
    minDamage: Int;
  };

  /** Default fragment pool size at the start of a player turn (e.g., 7–10). */
  fragmentPoolSize: Int;

  /** Player starting stats. */
  player: {
    /** Starting max HP for the player (e.g., 100). */
    startingMaxHp: Int;
  };
}
```

---

## 5) Campaign structure: chapters and encounters

```ts
/**
 * A chapter is the player-facing “map” list.
 * Encounters are infinitely replayable; “beaten” is tracked in save state.
 */
export interface Chapter {
  code: Code;
  name: string;

  /** Ordered list shown on the Chapter screen. */
  encounterCodes: Code[];

  /** Encounter that gates progression (must be beaten once to unlock next chapter). */
  bossEncounterCode: Code;

  /** Optional fragment pool override for the chapter (useful for tutorials). */
  fragmentPoolCode?: Code;

  /** Optional flavor text. */
  description?: string;
}

/**
 * One selectable battle on the chapter list.
 * MVP assumption: exactly one hostile actor.
 */
export interface Encounter {
  code: Code;
  name: string;

  /** Enemy actor encountered. */
  actorCode: Code;

  /** Optional pool override for this encounter (tutorial fight, theme fights). */
  fragmentPoolCode?: Code;

  /** Optional difficulty hint shown in the UI (★, numeric, or text). */
  difficultyHint?: string;
}
```

---

## 6) Actors and moves

```ts
/**
 * Dialogue lines used by UI at battle lifecycle moments.
 * Arrays enable simple random selection.
 */
export interface ActorDialogue {
  greeting?: string[];
  onLose?: string[]; // enemy wins, player loses
  onWin?: string[];  // player wins, enemy loses
}

/** MVP move types: enemies can attack or apply a debuff to the player. */
export type MoveType = "attack" | "debuff_player";

/**
 * Enemy move.
 * Enemy intent is derived from this (intentLabel + numbers/effects).
 */
export interface ActorMove {
  code: Code;
  type: MoveType;

  /** Short line shown as “intent” (e.g., "raises a dagger"). */
  intentLabel: string;

  /** For attacks: base damage. */
  value?: Int;

  /** For debuffs: buff/debuff code applied to the player. */
  appliesBuffCode?: Code;

  /** Optional weight for random choice within the moveset. */
  weight?: number;
}

/**
 * An actor is any combatant.
 * In MVP, only hostile actors are configured here (enemies).
 */
export interface Actor {
  code: Code;
  hostile: boolean; // MVP: true

  name: string;
  maxHp: Int;

  /** Optional, can start as emoji then later become asset codes/URLs. */
  avatar?: string;

  /** Randomly choose a move from this list each enemy turn (weighted). */
  moveList: ActorMove[];

  /**
   * Loot pool: buff codes that this actor can offer after defeat.
   * On victory, the game picks N options (e.g., 3) and the player chooses 1.
   */
  buffPool: WeightedRef<Code>[];

  dialogue?: ActorDialogue;
}
```

---

## 7) Fragments and fragment pools
Fragments are the “chips” used to build spells.

**Key design points implemented in schema:**
- **No runes.** Binding is built by selecting **one letter per fragment**.
- **Shrouded fragments** hide many letters in drafting mode and reveal on selection in binding mode.
- Aspects can carry a `?` marker that grants temporary buffs on cast.

```ts
/** Fragment categories used by the sentence syntax. */
export type FragmentCategory = "command" | "aspect" | "entity";

/** Primary effect types for Entities. */
export type EntityEffectType = "attack" | "block" | "heal";

/**
 * A single fragment.
 * The engine can treat fragments as immutable templates.
 */
export interface FragmentBase {
  code: Code;

  /** The underlying English word (always stored fully). */
  word: string;

  /** Mask string for shrouded fragments. '?' indicates hidden letters, '.' indicates visible letters (e.g., "??..?.?"). */
  shroudMask: string;

  category: FragmentCategory;

  /** Optional tags for content tooling and balance queries. */
  tags?: string[];
}

/**
 * Command (Verb): defines the spell’s base energy E.
 */
export interface CommandFragment extends FragmentBase {
  category: "command";

  /** Base energy generated by the command. */
  baseEnergy: Int;
}

/**
 * Aspect (Adjective): modifies energy and/or adds secondary numeric effects.
 *
 * MVP rules:
 * - Can apply an additive (+k) and/or multiplicative (×m) modifier to energy.
 * - Can also add one secondary numeric effect (attack/block/heal).
 * - Can optionally grant mystery temporary buffs via `tempBuffOnCast`.
 */
export interface AspectFragment extends FragmentBase {
  category: "aspect";

  energyMod?: {
    /** Additive change to energy (e.g., +1). */
    add?: Int;
    /** Multiplicative change to energy (e.g., ×1.5). */
    multiply?: Multiplier;
  };

  /** Optional secondary effect that applies in addition to the Entity primary effect. */
  secondaryEffect?: {
    type: EntityEffectType;
    value: Int;
  };

  /**
   * If set, this Aspect carries the “?” marker and grants temporary buffs when the spell is cast.
   * One random buff is granted per marker.
   */
  tempBuffOnCast?: {
    /** Number of random temporary buffs granted when included in a successfully cast spell. */
    count: Int;

    /** Pool to draw temporary buffs from. Uses buff codes (defined in buffs.json). */
    pool: WeightedRef<Code>[];
  };
}

/**
 * Entity (Noun): converts the final energy into the primary effect type.
 */
export interface EntityFragment extends FragmentBase {
  category: "entity";

  effectType: EntityEffectType;

  /** Optional flat bonus to the converted effect (rare; keep readable). */
  flatBonus?: Int;
}

export type Fragment = CommandFragment | AspectFragment | EntityFragment;

/**
 * Fragment pool definition.
 * A pool can be global or scoped to a chapter/encounter.
 */
export interface FragmentPool {
  code: Code;
  label?: string;

  /**
   * The set of fragments available to be rolled into the player pool.
   * Use weights to influence frequency.
   */
  fragments: WeightedRef<Code>[];

  /** Optional pool size override (otherwise use GameConfig.fragmentPoolSize). */
  poolSizeOverride?: Int;
}
```

---

## 8) Buffs and debuffs (Modifier pattern)
Buffs and debuffs share the same definition. A debuff is simply a `GameBuff` with `isDebuff: true`.

This section is based on the earlier “modifier pattern” draft in the chat PDF, updated for the newer binding mechanics (no runes; binding timer; shrouded behavior).

```ts
/**
 * Stats/rules the engine can modify.
 * Keep this list minimal and expand only when needed.
 */
export type TargetStat =
  // Combat
  | "damage_outgoing"          // multiplier or additive bonus
  | "damage_incoming"          // multiplier (damage reduction)
  | "max_hp"                   // add or multiply max HP
  | "lifesteal"                // additive fraction of damage healed
  | "backfire_damage_multiplier" // multiply computed backfire damage

  // Drafting / binding rules
  | "binding_time_limit_sec"   // override or add seconds
  | "max_fragments_per_spell"  // cap spell size (early progression lever)
  | "binding_banned_char"      // restriction: binding word cannot contain this letter

  // Enemy flow (future-facing but already discussed)
  | "enemy_skip_turn_chance"   // additive probability
  | "chips_per_turn";          // pool size modifier

/**
 * Optional scaling sources used for reactive/conditional buffs.
 */
export type ScalingSource =
  | "constant"
  | "hp_lost_percent"
  | "dmg_taken_prev"
  | "dmg_dealt_prev"
  | "fragments_in_spell";

/**
 * A simple condition gate for a modifier.
 * Extend as needed.
 */
export type BuffCondition =
  | { type: "hp_below_percent"; value: Fraction }
  | { type: "turn_count_gte"; value: Int };

/**
 * A modifier describes one atomic rule change.
 */
export interface Modifier {
  target: TargetStat;

  /** How to apply the value to the target. */
  operator: "add" | "multiply" | "append" | "override";

  /**
   * Base value for the operation.
   * - numbers for most stats
   * - strings for list-like restrictions (e.g., banned char)
   */
  baseValue: number | string;

  /** Optional scaling, enabling Payback/Momentum/Scale families. */
  scaling?: {
    source: ScalingSource;
    factor: number;
  };

  /** Optional condition gate. */
  condition?: BuffCondition;
}

/**
 * Buff definition (also used for debuffs).
 * Buffs are mostly permanent when earned as loot; debuffs are typically temporary.
 */
export interface GameBuff {
  code: Code;

  /** Display label for UI pills and reward choices. */
  label: string;

  /** If true, this is displayed as a debuff (red) and is expected to be temporary. */
  isDebuff?: boolean;

  /**
   * Tier clarifies “build-defining with restriction” vs normal.
   * This replaces a rarity ladder in MVP.
   */
  tier?: "standard" | "oathbound";

  /** Optional quick family tag for tooling/balance. */
  family?:
    | "power"
    | "armor"
    | "vitality"
    | "lifesteal"
    | "payback"
    | "rage"
    | "momentum"
    | "power_scale"
    | "oathbound";

  /**
   * Default duration hint.
   * - Loot buffs: usually permanent (omit)
   * - Debuffs: typically battle or N turns
   */
  defaultDuration?:
    | { kind: "battle" }
    | { kind: "turns"; turns: Int };

  /** The actual logic of the buff. */
  modifiers: Modifier[];
}
```

### Example: Oathbound restriction and timer reduction
```ts
// Example content entry (buffs.json)
const oathOfPressure: GameBuff = {
  code: "oath_pressure",
  label: "Oath of Pressure",
  tier: "oathbound",
  family: "oathbound",
  modifiers: [
    { target: "damage_outgoing", operator: "multiply", baseValue: 1.5 },
    { target: "binding_time_limit_sec", operator: "override", baseValue: 20 }
  ]
};
```

---

## 9) Dictionary configuration
The binding word must be validated against a dictionary.

```ts
/**
 * Dictionary config describes where/how to load word validation data.
 * The actual word list may be stored as a text file for size/perf.
 */
export interface DictionaryConfig {
  code: Code;

  /** A human label (“common-20k”, “full-english”, etc.). */
  label?: string;

  /**
   * Resource path or key for loading.
   * In MVP this can be a local file path.
   */
  resource: string;

  /** Optional: normalize to lowercase during validation. */
  caseInsensitive?: boolean;
}
```

---

## 10) Save state (persistent player progress)
This schema is intentionally small. It stores **progress and permanent buffs**, not battle state.

```ts
/**
 * Persistent player profile (LocalStorage for MVP).
 */
export interface PlayerSave {
  version: string;
  updatedAt: UnixMs;

  /** Chapters unlocked/available to select. */
  unlockedChapterCodes: Code[];

  /** Encounters beaten at least once (used for “Beaten” markers). */
  beatenEncounterCodes: Code[];

  /** Permanent buffs earned from victory rewards. */
  permanentBuffCodes: Code[];

  /** Optional: which chapter the user last viewed/played. */
  lastChapterCode?: Code;
}
```

---

## 11) Battle runtime state (minimal engine-facing shapes)
These types represent the **runtime** objects used during a battle.
They are not necessarily stored as JSON content files.

```ts
/**
 * An instance of an actor in battle.
 * Keeps current HP and currently applied statuses.
 */
export interface BattleActorState {
  actorCode: Code;
  currentHp: Int;

  /** Active buffs/debuffs for this battle instance. */
  activeBuffs: ActiveBuffInstance[];

  /** Cached intent for UI (computed each enemy turn). */
  nextIntent?: ActorMove;
}

/**
 * A buff instance applied in battle.
 * Permanent buffs still appear here for battle calculations, but are sourced from save state.
 */
export interface ActiveBuffInstance {
  buffCode: Code;

  /** Remaining turns if this is a temporary effect. */
  remainingTurns?: Int;

  /** Where it came from (useful for debugging). */
  source?: "permanent" | "enemy_move" | "aspect_question_mark";
}

/**
 * The player’s drafting pool for the current turn.
 */
export interface DraftPoolState {
  /** Fragment codes currently available to pick. */
  fragmentCodes: Code[];
}

/**
 * A spell being built on the Scroll.
 * Ordering matters for both energy math and binding segments.
 */
export interface SpellDraft {
  /** Fragment codes in scroll order. */
  fragmentCodes: Code[];
}

/**
 * Binding mode state: one segment per fragment.
 * Each segment stores the selected letter index for that fragment.
 */
export interface BindingModeState {
  /** Spell being bound (frozen at binding mode entry). */
  spell: SpellDraft;

  /** Timer remaining (seconds). */
  timeRemainingSec: Int;

  /**
   * Per-fragment selection.
   * selectedIndex is an index into the fragment.word.
   */
  selections: Array<{
    fragmentCode: Code;

    /** Selected character index for this fragment, or undefined if not chosen yet. */
    selectedIndex?: Int;

    /** Which hidden indices have been revealed (for shrouded fragments). */
    revealedHiddenIndices?: Int[];
  }>;
}

/**
 * Full battle state snapshot.
 */
export interface BattleState {
  battleCode: Code;

  encounterCode: Code;

  /** Player and enemy states. */
  player: BattleActorState;
  enemy: BattleActorState;

  /** Current draft pool and scroll. */
  pool: DraftPoolState;
  scroll: SpellDraft;

  /** Present only while binding. */
  binding?: BindingModeState;

  /** Turn counter, starting at 1. */
  turn: Int;

  /** Who acts next. */
  phase: "player_draft" | "player_binding" | "enemy" | "resolved";
}
```

---

## 12) Notes for implementers
- **Fragment masks are deterministic** using `ShroudSpec.hiddenIndices`. This keeps puzzles consistent and testable.
- **Invalid binding words do not cause Backfire.** Only timer expiry or Give Up triggers Backfire.
- Consider implementing content validation tooling early:
  - detect missing codes
  - ensure fragment pools can satisfy `draftingGuarantees`
  - ensure buffs referenced by actors and aspects exist

---

## Appendix: quick mapping from older schema to updated mechanics
- “Rune”/`runeIndex` → **removed** (binding is letter-selection by segment).
- `seal_banned_char` → `binding_banned_char`.
- “Mystery fragments” → `shroud` + “?” buttons reveal letters in Binding Mode.
- Typed sealing input → removed; dictionary validation happens after all segments are filled.
