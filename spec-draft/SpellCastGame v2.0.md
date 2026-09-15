# Game Design Document: Spell Caster Quest

**Version:** 2.0 (supersedes v1.3)

> **How to read this version.** v2.0 is a full rewrite of v1.3 after a design/balance review and two simulations (binding-puzzle solvability and combat pacing, see §10 and `spec-draft/simulation/`). Every decision that changes v1.3 gameplay is listed in §0 with its reasoning, so each one can be accepted or reverted independently. Everything not listed there is either unchanged or a clarification.

---

## 0. Decision Log: What Changed Since v1.3

| # | Change | Why |
|---|--------|-----|
| D1 | **A spell is at least 3 fragments** (Command + ≥1 Aspect + Entity). v1.3 was contradictory (syntax said 1..N Aspects; binding rules allowed Command + Entity). | The binding word is as long as the fragment count. Simulation: 2-letter words are solvable only ~94% of the time with a sane 2-letter list and usually have 1–2 solutions, so a 2-fragment spell is a coin-flip, not a "safe cantrip". 3-letter words are solvable ~100% with ~10+ solutions: a reliable floor for onboarding. |
| D2 | **Maximum spell size is a progression lever**: 3 fragments in Chapter 1, 4 in Chapter 2, 5 in Chapter 3 (6 only via an Oath). | Word length is the primary difficulty dial (3: trivial, 4: easy, 5: medium, 6: hard). Gating it per chapter gives a clean difficulty curve without XP or levels. It also prevents multiplier blow-ups from 6+ Aspect spells. |
| D3 | **Backfire ends the player's turn** (v1.3: the turn continued and the pool was replenished). | v1.3 created an "HP-for-reroll" loop: give up a spell to refresh the pool, and letters of Shrouded fragments could be "bought" by giving up. Ending the turn removes both exploits, makes the timer meaningful and keeps one mental model: *one turn = one spell attempt*. Backfire damage was lowered to compensate (D4). |
| D4 | **Backfire = 3% of Max HP × fragments** (min 1), was 5%. | With the turn-ending rule (D3) a failure already costs tempo. Simulation: at 5%/fragment big spells are never worth it for average players; at 3% they pay off for average and expert players in Chapter 2 while remaining a real risk in Chapter 3. |
| D5 | **Skip Turn removed.** | With a 3-fragment spell always available and ~100% solvable, skipping is strictly dominated (casting anything cycles the pool; skipping does not). Fewer controls in the battle UI. Kept in roadmap as a possible "Rest" action. |
| D6 | **Fizzle rule + pool solvability guarantee.** If a bound spell has no valid word at all, it *fizzles* (no Backfire, fragments discarded, same turn continues). The pool generator additionally rerolls fragments so that every buildable spell has ≥1 solution. | Unsolvable combinations exist (≈2% at 5 fragments, ≈8% at 6 with a permissive dictionary). Punishing the player for them would be unfair and unreadable. |
| D7 | **Energy math is order-independent**: sum all additive Aspects, then multiply by all multipliers. | The "apply in scroll order" rule created a trap (×2 then +1 is worse than +1 then ×2) with no upside; the new rule always equals the best ordering and is easier to preview in the UI. |
| D8 | **Buff cap: one active buff per family; picking a higher level replaces the lower.** Oathbound buffs: at most 2 held. | v1.3 allowed unbounded stacking through infinite replays, which makes balance impossible and the buff rail unreadable. With a cap, maximum player power is known (§10), the rail stays short, and replaying is still meaningful (hunt the family/level you want). |
| D9 | **Binding timer scales with word length**: 30 s for 3–4 fragments, +10 s per fragment above 4. | 5–6 letter words with ~1–3 common solutions need scanning time; a flat 30 s made 5-fragment spells expert-only in simulation. |
| D10 | **Block is defined precisely**: absorbs damage from the *next enemy action only*, unused Block expires. Block conversion is 1:1 like Attack/Heal. | v1.3 never defined Block duration. Telegraphed intents make Block a deliberate counter to big hits. |
| D11 | **Debuffs expanded to puzzle-themed ones** (Haste: shorter timer; Hex: banned letter; Fog: shroud pool fragments) in addition to Bleed and Frailty. | The puzzle is the game; enemies that attack the puzzle are more interesting than pure stat debuffs and give each chapter a new twist. |
| D12 | **Player always starts a battle at full HP.** No HP carry-over between battles. | Not specified in v1.3. Matches "cozy" tone and infinite-replay structure. |
| D13 | Numbers everywhere (fragment stats, enemy stats, buff levels) are now concrete MVP defaults, derived from simulation, not placeholders. | So that content authoring and the data schema can start immediately. All are still tuning knobs. |

---

## 1. Executive Summary

**Spell Caster Quest** is a turn-based 1v1 word-puzzle RPG. The player casts spells by **building a sentence** out of word fragments (a verb, adjectives, a noun) and then **binding** it: picking **one letter from each fragment**, in order, to form a valid English word under a timer.

**Core hook:** *Write your magic. Bind it with words. Risk HP for power.*

**Pillars**

- **Tactical drafting.** Choose which fragments to commit to based on the enemy's telegraphed intent and on which letters you think you can bind.
- **Readable math.** The spell's outcome is previewed live on the Spell Desk before you bind. No hidden rolls in the player's own actions.
- **Risk you choose.** Longer spells are stronger and their binding words are harder. Failing to bind in time causes **Backfire** and ends the turn. The "safe" 3-fragment spell is always available.
- **Lighthearted tone.** Whimsical, cozy fantasy with chunky UI and punchy feedback. Losing is cheap: no run resets, no lost progress.

**One-sentence loop:** *Look at the enemy's intent → draft a spell from your pool → bind it with a word before the timer runs out → the spell resolves → the enemy acts → repeat until one side falls → pick one buff from three → next encounter.*

---

## 2. Terminology

- **Actor:** Any character in battle (Player or Enemy).
- **Fragment:** A playable word chip (e.g., **CONJURE**, **MIGHTY**, **FIREBALL**). Fragments are consumed when cast.
- **Command:** Verb fragment. Sets a spell's base **Energy**.
- **Aspect:** Adjective fragment. Modifies Energy and/or adds a secondary effect.
- **Entity:** Noun fragment. Determines the spell's primary effect type (Attack / Block / Heal).
- **Energy (⚡):** The spell's power number before it is converted into an effect by the Entity.
- **Spell Desk:** The drafting area: sentence slots + fragment pool + controls.
- **Pool:** The fragments currently available to draft (default 8).
- **Binding Mode:** The puzzle phase where the chosen fragments become rows of letter buttons.
- **Binding Word:** The candidate word assembled in Binding Mode: exactly one letter per fragment, in sentence order.
- **Segment:** One position in the Binding Word, tied to one fragment.
- **Shrouded fragment:** A fragment whose letters are mostly hidden while drafting (e.g., **S_V_G_**). Stronger stats, unknown letters.
- **Backfire:** Damage taken when binding fails (timer expires or the player gives up). Ends the turn.
- **Fizzle:** A bound spell that has no valid word at all dissolves harmlessly (rare safety net).
- **Buff:** A permanent passive effect gained as loot. Has a **family** and a **level** (I–V).
- **Temporary buff:** A battle-only buff granted by a "?" Aspect.
- **Oathbound buff (Oath):** A strong buff that always comes with a restriction.
- **Debuff:** A negative, turn-limited effect applied by enemies.
- **Intent:** The enemy's next action, shown before the player drafts.

---

## 3. Screens and Flow

Main Menu → Chapter Screen → Battle Screen → (Loot Screen on victory) → Chapter Screen.

### 3.1 Main Menu (not finalized)

- Logo, game name, **Continue** (if a save exists) and **New Game**.
- One local profile in the MVP. Cloud saves and multiple profiles are out of scope.
- Prototype name and logo: **"Grimbeak"**, a minimalistic crow icon with a sparkle.

### 3.2 Chapter Screen (encounter list)

**Purpose:** Choose battles, review chapter progress.

- Chapter title (a location name) and introductory plot text (truncated with ellipsis, expandable). The same text is shown once as a modal on first entry to the chapter.
- A **list** of encounters with **free selection**. Each row shows enemy portrait, name, a one-line flavor text, and a **Beaten** marker (won at least once).
- **Boss row:** visually distinct (crown icon, larger portrait, bold text). Always visible.
- All encounters, including bosses, are **infinitely replayable**.
- Bottom: **"Proceed to the next chapter"**, enabled after the boss is beaten once. Previous chapters remain accessible (a chapter selector or back button).
- The player's current buffs are visible here too (same buff rail as in battle), so the player can plan what to farm.

### 3.3 Encounter Start panel

Omitted in the MVP to streamline the flow. Can be added later (enemy title, flavor line, notable debuffs, "Start Battle").

### 3.4 Battle Screen

**Purpose:** The core gameplay.

**Layout (prototype target)**

- **Top-right: Enemy bar.** Portrait, name, HP bar with numbers, **Intent** chip (e.g., "⚔️ 7", "🩸 Bleed", "💥 14 (winding up)").
- **Lower-left: Player bar.** Portrait, HP bar with numbers, current **Block** (🛡 n) if any.
- **Buff rail.** Horizontally scrollable chips above the player bar: permanent buffs, temporary buffs (marked with a small hourglass), debuffs (red, with remaining turns). Tap/hover for details.
- **Center: Dynamic Panel.** One focus area whose content depends on battle state:
  - Enemy remark / narration (greeting, victory, defeat lines)
  - **Spell Desk** (drafting)
  - **Binding puzzle** (segments + letter rows + timer)
  - **Resolution** (spell card + effect animation)

**Spell Desk (drafting state)**

- **Sentence slots:** `Command` → `Aspect` (1..max) → `Entity`. Slots for Aspects appear one at a time as they are filled, up to the chapter's maximum. Tapping a placed fragment returns it to the pool.
- **Live preview:** as soon as an Entity is placed, the desk shows the computed outcome, e.g. **"→ 9 ⚔️ + 3 🛡"**, and the binding word length ("4-letter word, 30 s").
- **Fragment pool:** clickable chips below the slots. Each chip shows the word and its stat badges. Shrouded chips show a masked word (e.g., **S_V_G_**) but full stats.
- **Controls:** **Bind** (enabled once an Entity is placed). There is no Skip Turn (see D5).

**Binding Mode** replaces the desk: Binding Word segments on top, one row of letter buttons per fragment below, the timer, and a **Give Up** button.

**Win / defeat resolution**

- **Victory:** enemy defeat line → Loot Screen.
- **Defeat:** enemy victory line → back to Chapter Screen. No penalties (permanent buffs stay). Penalties are a future consideration, not MVP.

### 3.5 Loot Screen

- **Pick 1 of 3** buff cards drawn from the enemy's loot table (weighted random, filtered to options that actually improve the player, see §6.4).
- Each card shows family icon, name with level, one-line effect, and, if the player already has a lower level, "upgrades Power II → III".
- Oath cards show the restriction prominently. If the player already holds 2 Oaths, choosing a third asks which one to replace.
- **Continue** → Chapter Screen.

---

## 4. Core Battle Loop

Battles are 1v1 and turn-based. The player always acts first. The player starts every battle at full HP (D12).

### 4.1 Turn Structure

1. **Start of player turn.** Debuff ticks (e.g., Bleed damage). Pool refills. Enemy **Intent** for this round is shown.
2. **Player turn.** Draft a spell → **Bind** → the spell resolves (success) or **Backfire** (failure). Either way the turn ends. Exception: **Fizzle** (§4.4.7) returns to drafting.
3. **Enemy turn.** The enemy performs its telegraphed intent. Block absorbs damage, then expires.
4. Repeat until an actor reaches 0 HP.

### 4.2 Spell Construction (Sentence System)

Strict syntax: **Command** → **Aspect × (1..maxAspects)** → **Entity**. Minimum 3 fragments (D1). Maximum by chapter (D2): 3 / 4 / 5.

Example: **CAST** → **HEAVY** → **FIREBALL**

#### 4.2.1 Command (verb)

- Sets base Energy **E**. Badge: ⚡ + number.
- MVP range: 3–6. Examples: **CAST (3⚡)**, **CONJURE (4⚡)**, **INVOKE (5⚡)**, **UNLEASH (6⚡)**.

#### 4.2.2 Aspect (adjective)

An Aspect does one or more of:

1. **Modify Energy:** `+N` (additive) or `×M` (multiplicative).
2. **Add a secondary effect:** `+N ⚔️`, `+N 🛡` or `+N ❤️`, applied in addition to the Entity's primary effect. This is how hybrid spells (Attack + Block, Attack + Heal) happen.
3. **Carry a mystery marker `?`:** on a successful cast, grants one random temporary buff (§6.6).

No special "trait" Aspects (e.g., Vampiric) in the MVP.

Examples: **QUICK (+1)**, **LARGE (+2)**, **MIGHTY (×1.5)**, **WARDING (+3🛡)**, **SHARPENED (+1)(+2⚔️)**, **MYSTERIOUS (+1)(?)**.

#### 4.2.3 Entity (noun)

Converts final Energy into the primary effect, 1:1:

- ⚔️ **Attack:** damage to the enemy.
- 🛡 **Block:** absorbs damage from the enemy's next action; unused Block expires at the start of the player's next turn (D10).
- ❤️ **Heal:** restores HP, capped at Max HP.

Examples: **FIREBALL (⚔️)**, **BARRIER (🛡)**, **POTION (❤️)**. An Entity may carry a small flat bonus, shown as a badge (e.g., **STORM (⚔️ +1)**); rare, keep readable.

#### 4.2.4 Math Rules (D7)

```
E      = (Command.base + Σ Aspect.add) × Π Aspect.multiply
E      = round(E × (1 + Σ Power bonuses))        // Power buffs, Rage, Momentum, etc. (§6.5)
E      = max(E, 1)
primary   = E                (converted by the Entity to ⚔️ / 🛡 / ❤️, plus Entity flat bonus)
secondary = Σ Aspect secondary effects, flat, not scaled by Power
```

Rounding is half-up. The Spell Desk always shows the final numbers, so the player never computes this.

**Examples**

| Spell | Math | Result |
|-------|------|--------|
| CAST (3) + MIGHTY (×1.5) + FIREBALL | 3 × 1.5 = 4.5 → 5 | 5 ⚔️ |
| CONJURE (4) + QUICK (+1) + POTION | 4 + 1 | 5 ❤️ |
| INVOKE (5) + WARDING (+3🛡) + BOLT | 5 | 5 ⚔️ + 3 🛡 |
| UNLEASH (6) + LARGE (+2) + MIGHTY (×1.5) + FIREBALL | (6 + 2) × 1.5 = 12 | 12 ⚔️ |
| INVOKE (5) + HEAVY (+3) + SHARPENED (+1, +2⚔️) + SAVAGE (×2) + DAGGER, with Power II (+20%) | (5+3+1) × 2 = 18; × 1.2 = 21.6 → 22 | 22 ⚔️ + 2 ⚔️ = 24 ⚔️ |

#### 4.2.5 Slot-gating (onboarding)

- No Command placed → only Command chips are active.
- Command placed → Aspect chips become active; Entity chips stay inactive until at least one Aspect is placed.
- Entity placed → **Bind** is enabled. Further Aspects can still be added (Entity stays in the last slot) until the chapter maximum.
- Hover/tap hints on empty slots: "Aspect needed", "Entity needed", "Bind to cast".

### 4.3 Enemy Intent

- At the start of each player turn the enemy's next move is shown as an **Intent** chip on the enemy bar: attack with exact damage (**⚔️ 7**), a debuff with its icon and name, or a **wind-up** big attack (**💥 14**).
- Intent is fully reliable: the enemy will do exactly that. Intent is what makes Block and Heal decisions tactical.
- Move selection: weighted random from the enemy's move list, with optional constraints (e.g., bosses cannot wind up twice in a row). See §8.

### 4.4 Binding (the puzzle)

#### 4.4.1 Entering Binding Mode

When the player presses **Bind**:

- The chosen fragments **lock**. The rest of the pool is hidden.
- Shrouded fragments **reveal all their letters**.
- Each fragment becomes a **row of letter buttons** (one button per letter, duplicates included, in word order).
- A **Binding Word** display with one **segment per fragment** appears above the rows (like a segmented code input).
- The **timer** starts: `30 s + 10 s × max(0, fragments − 4)` (D9), modified by buffs/debuffs (Focus, Haste, Oath of Pressure), minimum 10 s.

#### 4.4.2 Building the Binding Word

- Tapping a letter in row *i* fills segment *i*. Tapping another letter in the same row replaces it. Tapping the pressed letter clears the segment.
- Order is fixed: segment 1 comes from the Command, the last segment from the Entity.
- No keyboard typing into the Binding Word (mobile-first, and keeps the "letters come from fragments" fiction). A physical keyboard *may* be used as an accelerator later: typing a letter selects it in the first row that contains it and has no selection.

#### 4.4.3 Validation

- When all segments are filled, the Binding Word is checked against the dictionary **automatically** (no submit button).
- **Valid word:** success animation → spell card → effects apply → turn ends.
- **Invalid word:** the word shakes, segments stay filled, the timer keeps running, the player keeps editing. Invalid attempts are free and unlimited.
- Words must be 3+ letters, lowercase dictionary entries only (no proper nouns, no abbreviations). Words containing a **banned letter** (Hex debuff, Oath of Flame) are rejected with a distinct animation and a reason line.

#### 4.4.4 Shrouded fragments

- While drafting, a Shrouded fragment shows only 20–40% of its letters (e.g., **S_V_G_**), so the word is not obvious. Its stats are shown in full.
- Shrouded fragments have stats one tier above the equivalent normal fragment (e.g., ×2 instead of ×1.5, +3 instead of +2, 6⚡ instead of 5⚡). They are separate content entries with their own mask.
- Risk: the player commits to unknown letters. Because Backfire ends the turn (D3), letters cannot be "bought" by giving up and retrying.
- They appear from Chapter 2 (a per-chapter share of pool draws, §7.1).

#### 4.4.5 Timer, Give Up, Backfire

- If the timer reaches 0 before a valid word is bound, or the player presses **Give Up**:
  - **Backfire:** the player takes `ceil(MaxHP × 3% × fragments)` damage (min 1), modified by Resolve buffs / Oath of Glass. Backfire ignores Armor and Block.
  - The attempted spell and its fragments are discarded.
  - **The turn ends**; the enemy acts (D3).
- Backfire damage can kill the player.

#### 4.4.6 Pool refill after the turn

At the start of the next player turn, used or discarded fragments are replaced by new random draws (§7.1). Unused fragments stay.

#### 4.4.7 Fizzle (safety net, D6)

- When Bind is pressed, the engine checks whether *any* dictionary word can be formed. If none can, the spell **fizzles**: a short "the letters refuse to bind" animation, no damage, the fragments are discarded and immediately replaced, and the player stays in the drafting state of the same turn.
- The pool generator makes this rare (§7.2). The check is cheap (filter dictionary words of length *n* by per-position letter sets).

### 4.5 Enemy Turn

- The enemy executes its Intent:
  - **Attack:** `damage = round(power × (1 − Armor%))`; Block absorbs first; remainder hits HP.
  - **Debuff:** applies a debuff to the player (with duration in turns). If the same debuff is already active, its duration is refreshed, not stacked.
  - **Wind-up (bosses):** a bigger attack, telegraphed as such. Mechanically an attack with high damage.
- Then the next round starts.

### 4.6 Battle as a State Machine

```
ENEMY_GREETING
  → PLAYER_DRAFT   (pool refill, debuff ticks, intent shown)
  → PLAYER_BIND    (timer running)
      ├─ valid word  → RESOLVE_CAST  → ENEMY_ACT
      ├─ fizzle      → PLAYER_DRAFT (same turn)
      └─ timeout / give up → RESOLVE_BACKFIRE → ENEMY_ACT
  → ENEMY_ACT      (attack / debuff animation)
  → PLAYER_DRAFT … until HP ≤ 0
  → VICTORY (enemy defeat line → Loot) | DEFEAT (enemy victory line → Chapter)
```

All messages are shown in the center panel; no toasts.

---

## 5. Progression and Meta

### 5.1 Campaign structure

- Chapters are linear (1 → 2 → 3). Each has 4 standard encounters and 1 boss in the MVP.
- Free selection within a chapter; beat the boss once to unlock the next chapter.
- No XP, no gold, no leveling in the MVP. Progression is entirely **buffs** (§6) and **chapter rules** (§5.3).

### 5.2 Replay rules

- Everything is infinitely replayable. Encounters are marked **Beaten** after the first win.
- Replay is meaningful because loot is random, enemy loot tables differ, and buff levels cap (§6.4): players replay to complete or upgrade their build, not to grind indefinitely.

### 5.3 Difficulty curve (MVP: 3 chapters)

Chapter rules are data (see `ChapterRules` in the schema).

| Lever | Chapter 1 | Chapter 2 | Chapter 3 |
|-------|-----------|-----------|-----------|
| Max fragments per spell | 3 | 4 | 5 |
| Pool size (Commands / Aspects / Entities) | 8 (2 / 3 / 3) | 9 (2 / 4 / 3) | 9 (2 / 4 / 3) |
| Shrouded share of Aspect and Command draws | 0% | 20% | 35% |
| Enemy HP (standard / boss) | 18–28 / 40 | 32–44 / 60 | 48–62 / 90 |
| Enemy attack (standard / boss wind-up) | 4–8 / 14 | 7–12 / 18 | 9–15 / 24 |
| Debuffs introduced | Bleed | Frailty, Haste | Hex, Fog |
| Loot buff levels offered | I–II | II–III | III–V |
| Oaths | none | first Oath from the boss | Oaths in standard loot tables |
| New fragments | +1/+2, ×1.5, secondary effects | +3, `?` Aspects, Shrouded | ×2 (Shrouded only), Entity flat bonuses |

Chapter 1, encounter 1 uses a curated tutorial pool (short, vowel-rich fragments) and extra hints.

### 5.4 Loot

After every **victory**: pick 1 of 3 (§3.5, §6.4). After **defeat**: no loot, no penalty.

---

## 6. Buffs and Debuffs

Buffs are the progression layer. Requirements: clear, capped, stackable across families, easy to balance.

### 6.1 Buff anatomy

Every buff has a **family**, a **level** (I–V, not every family has 5), a display name ("Power III"), a one-line effect, and an icon. A family defines *what* the buff does; the level defines *how much*.

### 6.2 Families (MVP set)

| Family | Type | Levels | Effect per level (I / II / III / IV / V) | Notes |
|--------|------|--------|-------------------------------------------|-------|
| **Power** | stat | 5 | +10 / 20 / 30 / 40 / 50% Energy | Core damage/heal/block scaling |
| **Vitality** | stat | 5 | +10 / 20 / 30 / 40 / 50 Max HP | Also reduces Backfire relative to HP |
| **Armor** | stat | 5 | −10 / 15 / 20 / 25 / 30% damage taken from enemy attacks | Not Backfire, not Bleed |
| **Lifesteal** | stat | 3 | heal 10 / 20 / 30% of Attack damage dealt | Rounded down, min 0 |
| **Resolve** | stat | 3 | −25 / 50 / 75% Backfire damage | Comfort pick for weaker word-players |
| **Focus** | stat | 3 | +5 / 10 / 15 s binding time | |
| **Rage** | conditional | 3 | +15 / 25 / 35% Energy while HP ≤ 50% | |
| **Shell** | conditional | 3 | gain 3 / 5 / 8 Block at the end of your turn while HP ≤ 50% | Stacks with Block spells |
| **Payback** | conditional | 3 | +10 / 20 / 30% Energy on a turn after taking damage (attack, Bleed or Backfire) | |
| **Momentum** | conditional | 3 | +5 / 8 / 10% Energy per consecutive successful cast, max 5 stacks; Backfire resets | Shown as a counter on the chip |
| **Confidence** | conditional | 3 | +8 / 12 / 16% Energy per fragment beyond 3 in the current spell | Rewards long spells |

11 families is the full list; the MVP may ship the first 8. Chapter-appropriate levels are controlled by loot tables (§5.3).

### 6.3 Oathbound buffs

Not a rarity tier: a **category**. Strong, build-defining, always with a restriction. Some bosses guarantee one. At most **2 Oaths** held at once (D8).

| Oath | Gift | Price |
|------|------|-------|
| **Oath of Flame** | +50% Energy | Binding words cannot contain the letter **L** |
| **Oath of Glass** | Lifesteal 30% | Backfire damage ×2 |
| **Oath of Pressure** | +50% Energy | Binding time −10 s |
| **Oath of Depth** | Spells may use **one extra Aspect** (max fragments +1) | Backfire damage ×1.5 |
| **Oath of Silence** | Aspect secondary effects ×2 | All Commands −1 Energy |

Banned letters should be consonants of medium frequency (L, R, S, T, N). Simulation: banning a vowel drops 5-letter solvability from ~98% to ~86%, banning a consonant costs far less.

### 6.4 Ownership, caps and loot filtering (D8)

- The player holds **at most one buff per family**. Taking a higher level **replaces** the lower one. Levels are never lost on defeat.
- The Loot Screen offers only options that improve the player: a family at a higher level than owned, or an Oath not yet held. Options are drawn by weight from the enemy's loot table; if fewer than 3 valid options exist, the global fallback table fills in; if none exist, the reward step is skipped with a line of flavor text ("Nothing more to learn here").
- Maximum permanent power is therefore bounded and known: e.g. Power V + Confidence III on a 5-fragment spell = +50% + 32% = ×1.82. See §10 for the resulting curve.

### 6.5 Stacking and resolution order

- All **Energy percentage bonuses** (Power, Rage, Payback, Momentum, Confidence, temporary Power, Oaths) **sum** into one multiplier: `E × (1 + Σ%)`. No multiplicative chains.
- **Flat** bonuses (Block from Shell, Max HP) add.
- **Damage taken** uses one summed reduction: `× (1 − Σ Armor%)`, capped at 75%.
- Resolution order on a cast: 1) compute Energy with all bonuses; 2) apply primary + secondary effects; 3) "after damage" triggers (Lifesteal); 4) mystery buffs from `?` Aspects.
- Resolution order on an enemy attack: 1) Armor; 2) Block; 3) HP; 4) "after hit" triggers (Payback arms for next turn).

### 6.6 Temporary buffs from `?` Aspects

On a successful cast containing *k* `?` markers, grant *k* random temporary buffs from the chapter's temp-buff pool. They last until the end of the battle, stack additively with permanent buffs, and show an hourglass on the rail. Duplicates upgrade (Power +20% twice = +40%).

MVP pool: **Surge** (+20% Energy), **Ward** (−20% damage taken), **Thirst** (Lifesteal 20%), **Vigor** (+15 Max HP and heal 15), **Clarity** (+10 s binding time).

### 6.7 Debuffs (enemy-applied)

All debuffs are battle-only and turn-limited; re-applying refreshes the duration.

| Debuff | Effect | Duration | First seen |
|--------|--------|----------|------------|
| **Bleed** | lose 3 HP at the start of your turn | 3 turns | Ch 1 |
| **Frailty** | Block halved (rounded down) | 3 turns | Ch 2 |
| **Haste** | binding time −10 s | 2 turns | Ch 2 |
| **Hex** | one random consonant is banned in binding words (shown on the chip) | 2 turns | Ch 3 |
| **Fog** | 2 random non-Shrouded pool fragments become Shrouded until used | 1 application | Ch 3 |

### 6.8 Visual representation

- Chips in the buff rail: icon + short modifier (`+20%`, `−15%`, `🩸 2`). Level shown as roman numeral on hover/tap; full text in a tooltip/modal.
- Temporary buffs get an hourglass, debuffs are red with a turn counter, Oaths have a distinct frame.

---

## 7. Fragment Pool and Drafting

### 7.1 Pool behavior

- The pool has a fixed capacity per chapter (§5.3), split by category. Unused fragments persist across turns; used or discarded ones are replaced at the start of the next player turn.
- Draws are weighted random from a **fragment table**: the chapter's table if defined, otherwise the global table. Encounters can override the table (tutorial fights, themed fights).
- A pool never contains two copies of the same fragment code.
- **Shrouded draws:** with probability `shroudedShare` (per chapter) a Command or Aspect draw is taken from the table's Shrouded entries instead.
- Refill guarantees: at least 1 Command, 1 Aspect, 1 Entity (structurally always true because capacity is per category).

### 7.2 Solvability guarantee (D6)

After a refill, the generator enumerates every spell that can be built from the pool within the chapter's fragment limit (with 2 Commands, 4 Aspects and 3 Entities that is ≤ 2 × (4 + 12 + 24) × 3 = 240 combinations) and checks each has at least one dictionary word. Failing fragments are rerolled (up to a fixed number of attempts). Fizzle (§4.4.7) covers anything that slips through.

Simulated baseline without the guarantee (permissive dictionary): 3 fragments 100% solvable, 4: 99.9%, 5: 97.7%, 6: 92.5%.

### 7.3 Fragment attributes

Each fragment defines: category, word, optional shroud mask, stats (base Energy / Energy modifiers + secondary effect + `?` marker / effect type + flat bonus), rarity weight, chapter availability and tags. Full MVP list in Appendix A.

### 7.4 Word choice guidelines for content

- Words are 4–9 letters, common English, in the fantasy register, and must not themselves be offensive or ambiguous.
- Each fragment should contain **at least 2 distinct vowels** (Commands and Entities especially, since they fix the first and last letter). This is what keeps 3–4 letter words nearly always solvable.
- Avoid too many fragments starting with the same letter in one category.

---

## 8. Enemies

### 8.1 Definition

Each enemy has: name, type (standard / boss), portrait (emoji placeholder), Max HP, a **move list** (weighted), **dialogue** (greeting, defeat line, victory line, optional per-move quip), a **loot table** (buff family+level options with weights, optional guaranteed Oath for bosses).

### 8.2 Move types (MVP)

- **Attack:** fixed damage value (the Intent shows the exact number). Variance comes from having several attack moves with different weights, not from random rolls.
- **Debuff:** applies one debuff.
- **Wind-up:** an attack flagged `heavy`, for bosses. Selection rule: never twice in a row.

Intent labels are short flavor strings ("sharpens its quill", "gathers fog").

### 8.3 MVP roster

| Ch | Enemy | HP | Moves (weight) | Loot focus |
|----|-------|----|----------------|------------|
| 1 | Cellar Rat | 18 | Bite 4 (2), Scratch 6 (1) | Power I, Vitality I |
| 1 | Bog Slime | 22 | Splash 4 (2), Engulf 7 (1) | Vitality I–II, Armor I |
| 1 | Ink Imp | 25 | Poke 5 (2), Jab 8 (1), Bleed (1) | Power I–II, Lifesteal I |
| 1 | Goblin Scribe | 28 | Slash 6 (2), Stab 8 (1), Bleed (1) | Armor I–II, Resolve I |
| 1 | **Toad King** (boss) | 40 | Lick 6 (2), Slam 9 (2), Bleed (1), **Belch 14** (wind-up, 1) | Power II, Vitality II, Focus I |
| 2 | Moor Wolf | 32 | Bite 7 (2), Lunge 10 (1) | Power II, Momentum I |
| 2 | Word Bandit | 36 | Cut 8 (2), Ambush 11 (1), Frailty (1) | Armor II, Payback I |
| 2 | Marsh Wisp | 40 | Flicker 8 (2), Flare 11 (1), Haste (1) | Focus II, Rage I |
| 2 | Clay Golem | 44 | Punch 9 (2), Smash 12 (1) | Vitality III, Shell I |
| 2 | **Hedge Witch** (boss) | 60 | Curse 8 (2), Bolt 12 (2), Hex (1), **Cauldron 18** (wind-up, 1) | guaranteed Oath choice + Power III |
| 3 | Rusted Knight | 48 | Strike 9 (2), Cleave 13 (1) | Power III–IV, Confidence I |
| 3 | Wyvern | 54 | Claw 10 (2), Dive 14 (1), Bleed (1) | Lifesteal II, Rage II |
| 3 | Lich Librarian | 58 | Drain 10 (2), Curse 14 (1), Hex (1), Fog (1) | Focus III, Resolve II, Oaths |
| 3 | Bridge Troll | 62 | Club 11 (2), Crush 15 (1), Frailty (1) | Vitality IV, Shell II, Armor III |
| 3 | **Elder Wyrm** (boss) | 90 | Bite 10 (2), Flame 14 (2), Fog (1), **Inferno 24** (wind-up, 1) | Power V, Oaths |

Numbers were tuned with the combat simulation (§10) and are the MVP defaults.

---

## 9. Visual and UX Direction

### 9.1 Aesthetic, setting, tone

- Whimsical, cozy fantasy. Chunky chips, satisfying press/shake/success feedback, light humor in enemy lines.
- Temporary setting: the journey of **Grimbeak**, a crow mage apprentice who decided to become a mighty warlock. Chapters are locations on the way (e.g., *The Cellar*, *The Moor*, *The Library of Ash*). Lore is post-MVP.
- Placeholder art: emojis for portraits and icons, to be replaced with SVG.

### 9.2 Tutorial sequence (Chapter 1, encounter 1)

Curated pool: **CONJURE**, **CAST**, **LARGE**, **QUICK**, **GENTLE**, **FIREBALL**, **STONE**, **POTION**.

1. Enemy greeting: "A rat! It squeaks something rude."
2. Only Commands are active. Hint: "Pick a Command to start your spell." Player taps **CONJURE** → it moves to the first slot.
3. Aspects become active. Hint: "Add an Aspect." Player taps **LARGE**.
4. Entities become active. Hint: "Finish with an Entity." Player taps **FIREBALL**. Preview shows **→ 6 ⚔️**, "3-letter word · 30 s".
5. Hint: "Bind your spell: pick one letter from each fragment to spell a word." Player presses **Bind**.
6. Binding Mode: three rows (C O N J U R E / L A R G E / F I R E B A L L), three segments, timer. First-time hint: "Try C · A · R".
7. Player taps letters; **CAR** validates → success animation → spell card **CONJURE LARGE FIREBALL → 6 ⚔️** → rat HP 18 → 12.
8. Enemy acts (Bite 4) → player HP 100 → 96. Intent for the next round appears with a hint: "The rat shows what it will do next. Plan around it."
9. Loop continues; on victory the Loot Screen explains buffs in one line.

Later first-time hints (shown once each): first Shrouded fragment, first `?` Aspect, first wind-up intent, first debuff, first Oath offer.

### 9.3 UX rules

- Binding Mode visually focuses attention: dimmed background, large segments, big letter buttons (thumb-friendly, min 44 px).
- Timer: a ring or bar, turns red under 5 s, subtle tick sound.
- Validation feedback: green pulse on success, horizontal shake on an invalid word, a different "blocked" shake plus reason line for banned letters.
- No toasts; all narration lives in the center panel.
- Accessibility (post-MVP): "relaxed" mode with a longer timer; colorblind-safe effect icons (already emoji-distinct).

---

## 10. Balance Model and Simulation Results

Two Python simulations live in `spec-draft/simulation/` and can be re-run when numbers change.

### 10.1 Binding solvability (`bind_sim.py`)

Random spells from a 25/40/30 fragment vocabulary, one letter per fragment in order, checked against two dictionaries.

| Fragments | Solvable (permissive dict, 172k) | Solvable (common ∩ permissive, ~20k) | Median common solutions |
|-----------|-----------------------------------|--------------------------------------|-------------------------|
| 2 | 94% (curated 2-letter list) | 94% | 2 |
| 3 | 100% | 99.6% | 10 |
| 4 | 99.9% | 97% | 7 |
| 5 | 97.7% | 84% | 3 |
| 6 | 92.5% | 61% | 1 |

Reading: 3 fragments is a safe floor; 4 is easy; 5 is a real puzzle; 6 is expert territory. This motivated D1, D2, D6 and D9.

**Dictionary recommendation:** validate against a **permissive** list (ENABLE-class, ~170k words, no proper nouns) so that any real word the player knows counts; the felt difficulty is set by the common-word solution counts above, not by the validation list.

### 10.2 Combat pacing (`combat_sim.py`)

Model: pool of 8–9 fragments with the Appendix A stats, greedy drafting (heal below 45% HP, else attack), Bind success = solvability × player skill, Backfire ends the turn, enemy Intent weighted random, expected buffs per chapter (after Ch 1: Power II, Vitality I, Armor I; after Ch 2: Power III, Vitality III, Armor II, Lifesteal I).

Player skill = probability to find a word in time, given one exists: novice 0.95 / 0.80 / 0.55 / 0.30, average 0.99 / 0.92 / 0.75 / 0.50, expert 1.0 / 0.98 / 0.92 / 0.80 for 3 / 4 / 5 / 6 letters.

Win rates with Backfire at 3%/fragment, "adaptive" policy (max-size spells while HP > 50%, 3-fragment spells otherwise):

| Fight | Novice | Average | Expert |
|-------|--------|---------|--------|
| Ch 1 standard | 100% | 100% | 100% |
| Ch 1 boss | 93% | 99% | 100% |
| Ch 2 standard | 97% | 100% | 100% |
| Ch 2 boss | 60% | 89% | 96% |
| Ch 3 standard | 72% (98% with 3-fragment spells) | 93% (100%) | 99% |
| Ch 3 boss | 10% (31%) | 40% (48%) | 77% |

Typical fight length: 4–7 turns for standard enemies, 9–12 for bosses.

Conclusions baked into the design:

- Chapter 1 is an onboarding chapter: nobody should lose to standard enemies; the boss teaches wind-ups and Block.
- In Chapter 2 long spells pay off for average and expert players (D4). Novices are better off with 3-fragment spells and Resolve/Focus buffs, which exist for exactly that reason.
- In Chapter 3, 4-fragment spells are the workhorse; 5-fragment spells are swing plays that reward strong word-players. The final boss is meant to require a completed build and a few attempts.
- Backfire above 3%/fragment makes long spells a losing bet for everyone but experts; below 2% the risk stops mattering. 3% is the default.

### 10.3 Known tuning risks

- The simulation does not model the timer explicitly; D9's longer timers for 5+ letters should make 5-fragment spells slightly better than simulated.
- Heal spells scale with Power, so late-game Heal + Lifesteal may be too safe; watch for stalling and consider a Heal conversion of 0.8 if fights exceed 15 turns.
- Oath of Depth (6-fragment spells) + Confidence III + Power V is the highest-variance build; it is intended to feel like that but should be checked on real dictionaries.

---

## 11. Technical Specification (summary, non-schema)

- **Platform:** Web, mobile responsive. Later: PWA and/or Electron/Capacitor wrapper (out of MVP).
- **Stack (MVP target):** React + Vite + TypeScript + Tailwind, in a pnpm monorepo. The `fullstack-template-selfhost` template (React/Vite/Tailwind frontend on Cloudflare Pages; Fastify + Postgres backend on a VPS) is the intended starting point. The MVP needs only the frontend package: game logic runs client-side, content is static JSON, saves are in Local Storage. The backend is reserved for later cloud saves/profiles.
- **Architecture:**
  - `packages/shared`: content and save-state TypeScript types (the data schema document), pure game-logic functions (energy math, buff resolution, binding validation, pool generation) with unit tests, no React.
  - `apps/web`: React UI, TanStack Query for content/state access, a small set of async **services** (`ContentService`, `PlayerStateService`, `DictionaryService`, `BattleService`) with Local Storage / static JSON implementations that can later be swapped for API implementations without touching UI code.
- **Content:** JSON files validated at build time against the schema (zod or JSON Schema) with a content linter: dangling codes, pool solvability, vowel rule (§7.4), loot-table sanity.
- **Dictionary:** a permissive English word list (§10.1) shipped as a compressed text asset (~600 KB gzipped), loaded once into a `Set` plus a per-length index for the solvability check.
- **Determinism:** all randomness goes through a seeded RNG stored in the battle state, so battles can be replayed and tested.

---

## 12. MVP Scope

**In MVP**

- All core systems in §3–§8: drafting, binding, Backfire, Fizzle, intents, buffs with families/levels/caps, Oaths (2–3 of them), debuffs (all 5), Shrouded and `?` fragments, chapter rules.
- 3 chapters × (4 encounters + boss) with the roster in §8.3.
- ~60 fragments (Appendix A), ~30 buff entries (families × levels), 5 temporary buffs, 5 debuffs.
- Chapter 1 onboarding with first-time hints.
- Placeholder art, emoji icons, Local Storage save.
- Content linter and unit tests for game math and binding validation.

**Out of MVP**

- Final art, sound design, lore and narrative.
- More chapters, enemy move types beyond attack/debuff/wind-up, scripted boss patterns.
- Defeat penalties, roguelike resets, profiles, cloud saves, backend.
- Fine balance tuning (the simulation gives defaults; real data will follow).

---

## 13. Roadmap / Future Ideas

- **Rest action:** skip the turn to heal a small amount; a deliberate "bad pool" escape valve if playtests show stale pools.
- **Pool discard:** discard one fragment per turn for free.
- **Gold** as a meta currency (shops, rerolls, buff respec).
- **Leveling / Mana fragments:** binding manipulations (reveal a letter, swap two segments, wildcard letter, extend the timer once).
- **Synergy buffs:** buffs that reference each other (e.g., Lifesteal + HP-for-power) with explicit caps.
- **Enemy move types:** steal a fragment, shroud the whole pool, ban a category, alter syntax.
- **Scripted boss patterns** and multi-phase bosses.
- **Aether / Flow** fragments: tempo/utility effects (draw, next-turn bonuses).
- **Daily puzzle mode:** fixed seed, leaderboard by turns and HP left.
- **Difficulty hint** (★) on encounter rows; **relaxed mode** with no timer.

---

## Appendix A: MVP Content Tables

All numbers are defaults and tuning knobs. `Ch` = first chapter where the fragment enters the global table. `W` = draw weight.

### A.1 Commands

| Word | ⚡ | Ch | W | Shrouded variant |
|------|----|----|---|------------------|
| CAST | 3 | 1 | 4 | |
| BREW | 3 | 1 | 3 | |
| CHANT | 3 | 1 | 3 | |
| CONJURE | 4 | 1 | 3 | |
| SUMMON | 4 | 1 | 3 | |
| EVOKE | 4 | 2 | 2 | ⟦E_O_E⟧ 5⚡ |
| INVOKE | 5 | 1 | 2 | ⟦I__O_E⟧ 6⚡ |
| WEAVE | 5 | 2 | 2 | ⟦W_A__⟧ 6⚡ |
| KINDLE | 5 | 2 | 2 | ⟦K___L_⟧ 6⚡ |
| UNLEASH | 6 | 2 | 1 | ⟦U__E__H⟧ 7⚡ |
| CHANNEL | 6 | 3 | 1 | ⟦C_A___L⟧ 7⚡ |

### A.2 Aspects

| Word | Energy | Secondary | `?` | Ch | W | Shrouded variant |
|------|--------|-----------|-----|----|---|------------------|
| QUICK | +1 | | | 1 | 4 | |
| LARGE | +2 | | | 1 | 3 | |
| BRIGHT | +2 | | | 1 | 3 | |
| HEAVY | +3 | | | 2 | 2 | ⟦H_A__⟧ +4 |
| MIGHTY | ×1.5 | | | 1 | 3 | ⟦M__H__⟧ ×2 |
| ANCIENT | ×1.5 | | | 2 | 2 | ⟦A__I___⟧ ×2 |
| SAVAGE | ×2 | | | 3 | 1 | Shrouded only: ⟦S_V___⟧ ×2 |
| WARDING | | +3 🛡 | | 1 | 2 | |
| STOUT | +1 | +2 🛡 | | 1 | 2 | |
| GENTLE | | +3 ❤️ | | 1 | 2 | |
| SOOTHING | +1 | +2 ❤️ | | 2 | 2 | |
| SHARPENED | +1 | +2 ⚔️ | | 1 | 2 | ⟦S_A_P___D⟧ +2, +3 ⚔️ |
| THORNY | | +3 ⚔️ | | 2 | 2 | |
| MYSTERIOUS | +1 | | ? | 2 | 2 | |
| LUCKY | +2 | | ? | 2 | 1 | |
| ARCANE | ×1.5 | | ? | 3 | 1 | Shrouded only: ⟦A__A_E⟧ |
| GILDED | +2 | +2 🛡 | | 3 | 1 | ⟦G_L___⟧ +3, +3 🛡 |

### A.3 Entities

| Word | Effect | Flat | Ch | W |
|------|--------|------|----|---|
| FIREBALL | ⚔️ | | 1 | 4 |
| STONE | ⚔️ | | 1 | 3 |
| BOLT | ⚔️ | | 1 | 3 |
| DAGGER | ⚔️ | | 2 | 2 |
| STORM | ⚔️ | +1 | 3 | 2 |
| BARRIER | 🛡 | | 1 | 3 |
| SHIELD | 🛡 | | 2 | 2 |
| AEGIS | 🛡 | +1 | 3 | 1 |
| POTION | ❤️ | | 1 | 3 |
| TONIC | ❤️ | | 2 | 2 |
| ELIXIR | ❤️ | +1 | 3 | 1 |

### A.4 Buffs

See §6.2 (families and levels), §6.3 (Oaths), §6.6 (temporary), §6.7 (debuffs). Each family/level pair is one content entry, e.g. `power_3`.

### A.5 Player

Starting Max HP **100**. Backfire 3% × fragments. Base binding time 30 s (+10 s per fragment above 4).

---

## Appendix B: Open Questions for Playtesting

1. Does the turn-ending Backfire (D3) feel fair on a 30 s timer, or should the first failure per battle be forgiven?
2. Is a 9-fragment pool too much to scan on a phone? (Alternative: 7 with a larger Shrouded share.)
3. Do players understand that Block expires? (Consider a "🛡 expires" animation at turn start.)
4. Is Hex (banned letter) fun or merely annoying? If annoying, replace with a Fog variant.
5. Should Oaths be removable (at a cost) once the player regrets one?
