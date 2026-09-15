# Game Design Document: Spell Caster Quest

**Version:** 1.3

## 1. Executive Summary

**Spell Caster Quest** is a turn-based, 1v1 word‑puzzle RPG where players cast spells by **building a sentence** out of word fragments and then **binding** it by **selecting letters from those fragments** to form a valid English word.

**Core hook:** *Write your magic. Bind it with words. Risk HP for power.*

**Pillars**

- **Tactical drafting:** Choose which fragments to commit to a spell based on the enemy’s telegraphed intent.
- **Readable math:** Outcomes are easy to predict (base energy + clear modifiers).
- **Risk management:** You can keep attempting to **bind** a spell, but **running out of time** (or giving up) causes **Backfire** damage.
- **Lighthearted tone:** Whimsical, cozy fantasy with punchy UI feedback.

## 2. Terminology

- **Actor:** Any character in battle (Player or Enemy).
- **Fragment:** A playable word chip (e.g., **CONJURE**, **MIGHTY**, **FIREBALL**).
- **Command:** Verb fragment. Sets a spell’s base energy.
- **Aspect:** Adjective fragment. Modifies energy and/or adds secondary effects.
- **Entity:** Noun fragment. Determines the spell’s primary effect type.
- **Spell desk:** The active construction area where the player builds the sentence.
- **Binding Mode:** The puzzle phase where chosen fragments transform into letter-buttons.
- **Binding Word:** The candidate word assembled during Binding Mode. It has **one letter segment per chosen fragment**.
- **Segment:** One position in the Binding Word, tied to a specific fragment.
- **Shrouded (Mystery) Fragment:** A fragment displayed with many hidden letters (e.g., **F___B__L**). Shrouded fragments have higher stats but add risk.
- **Backfire:** Damage taken when the player **fails to bind in time** (timer expires) or explicitly gives up.
- **Buff:** A mostly-permanent passive effect gained as loot.
- **Debuff:** A negative effect applied by enemies.

## 3. Game Flow Overview (Screens)

This section defines the concrete screen flow for the prototype.

### 3.1 Main Menu (Not Finalized)

**Purpose:** Entry point.

- For now: just a logo, game name and “Continue” (if applicable) and “New Game” buttons.
- Single local profile in the MVP scope. Cloud saves / multiple profiles are out of scope.
- Temporary/prototype name and logo: "Grimbeak", minimalistic crow icon with a sparkle.

### 3.2 Chapter Screen (Map / Encounter List)

**Purpose:** Choose battles, review chapter progress.

- **Presentation:** A **list** of encounters with **free selection**.
- At the top: chapter title (presumably, a location name) and introductory plot text (truncated with ellipsis, can be expanded on click).
- Introductory plot text also appears on first entry to the chapter as a modal.
- Each encounter row shows:
  - Enemy name + small portrait
  - **Beaten marker** (won at least once)
- **Boss row:** Always visible with a clear **Boss indicator**. Details to be discussed, but likely a crown icon, larger portrait, bold text.
- Encounters (including bosses) are **infinitely replayable**.
- At the bottom - "Proceed to the next chapter" button. Enabled only after the boss is defeated.

### 3.3 Encounter Start (Optional Panel / Modal)

**NOTE**: It was decided to omit this in the MVP to streamline the flow. Can be added later.

**Purpose:** Show quick preview before entering battle.

- Enemy title, short flavor line, notable debuff(s) (if any).
- “Start Battle” button.

### 3.4 Battle Screen

**Purpose:** The core gameplay.

**Layout (prototype target)**

- **Top-right:** Enemy bar: sprite/portrait, HP bar, and **next intent**.
- **Lower-left:** Player bar: sprite/portrait and HP bar.
- **Buff rail:** Active buffs/debuffs shown as a **horizontally scrollable** list within or directly above the player bar. Displayed as mini-chips (icon, modifier), more details on click/hover.
- **Center (Dynamic Panel):** One main focus area that swaps its content by battle state. Content can be either of:
  - Enemy remark / narration (greeting, win, defeat lines)
  - Spell construction (“Spell Desk”): drafting area + fragment pool + controls
  - Binding puzzle (segments + letter-buttons + timer)
  - Resolution (spell card + animations)

**Spell Desk (when in drafting state)**

- **Build area:** Sentence slots: Command → Aspect(s) → Entity.
- **Fragment pool:** Clickable chips below the Build Area.
- **Controls:** **Bind** (enabled once an Entity is selected) and **Skip Turn**.
  - In Binding Mode, the controls are replaced by the binding UI (segments + letter-buttons), a **timer**, and an optional **Give Up** button.

**Win/defeat resolution**

- **On victory:** show win line from the enemy's dialogue, then transition to Loot Screen.
- **On defeat:** show defeat line from the enemy's dialogue, then exit to Chapter Screen.
  - Penalties (e.g., losing buffs, run reset) are **future considerations**, not MVP.

### 3.5 Loot Screen

**Purpose:** Resolve battle and award loot.

- Loot choice: **Pick 1 of 3** buffs from enemy’s loot table (weighted random). Number of options can be tuned.
- Return to Chapter Screen.

## 4. Core Gameplay Loop (Battle)

Battles are 1v1 turn-based encounters.

### 4.1 Turn Structure

- **Player Turn:** Build a spell → enter binding mode → either succeed (cast) or fail (Backfire mechanic).
- **Enemy Turn:** Enemy performs one move (e.g.: Attack, cast Debuff).

### 4.2 Spell Construction (Sentence System)

Player builds a spell by selecting fragments from the pool, they are then placed into the Build Area in the corresponding order. Spells follow a strict syntax:

**Command (mandatory)** → **Aspect(s) (1..N)** → **Entity (mandatory)**

E.g., **CAST** → **HEAVY** → **FIREBALL**

Syntax can be expanded in future with additional fragment types, that's out of MVP scope.

#### 4.2.1 Command (Verb)

- **Role:** Sets base spell energy **E**.
- **UI:** Verb + badge with ⚡️ and number.
- Examples: **CAST (3 ⚡️)**, **CONJURE (4 ⚡️)**, **UNLEASH (6 ⚡️)**.

#### 4.2.2 Aspect (Adjective)

- **Role (MVP):** An Aspect can do **one** of the following, or a **combination**:

  1. **Modify energy**: `×N` or `+N`
  2. Add a **secondary numeric effect**: `+N ⚔️` or `+N 🛡` or `+N ❤️`
  3. Add a mystery buff (**?**), see below.

- **No special trait Aspects** in MVP (e.g., no Vampiric/Lifesteal-as-a-trait fragments).

- **Mystery buff marker (“?”):** Some Aspects may include a **?** badge. On a successful cast, this grants a **random temporary buff** to the player (not the spell) for this battle only (details in 4.2.5).

- **UI:** Adjective + one or more badges with operator and number(s).

**Examples**

- **MIGHTY (×2)**
- **QUICK (+1)**
- **WARDING (+2 🛡)**
- **SHARPENED (×1.5) (+1 ⚔)**
- **MYSTERIOUS (+2) (?)**

**Hybrid spell note:** Because Aspects can add secondary numeric outputs, a single cast can produce hybrids like **Attack + Block** or **Attack + Heal**.

#### 4.2.3 Entity (Noun)

- **Role:** Converts final energy into the **primary effect type**.
- **Effect types (MVP):**
  - ⚔️ **Attack**
  - 🛡 **Block**
  - ❤️ **Heal**
- **UI:** Noun + badge with effect icon.
- Examples: **FIREBALL (⚔️)**, **BARRIER (🛡)**, **POTION (❤️)**.

#### 4.2.4 Math Rules

- Start with base energy **E** from Command.
- Apply Aspects in the order they appear on the Build Area:
  - **Additive** aspects: `E = E + k`
  - **Multiplicative** aspects: `E = E × m`
- Entity converts final **E** into the primary effect amount.
- Any Aspect secondary outputs are applied **in addition** to the primary effect.

**Examples**

1. **UNLEASH (5 ⚡️) + MIGHTY (×2) + FIREBALL (⚔️)** → **10 damage**

2. **CAST (3 ⚡️) + WARDING (+2🛡️) + FIREBALL (⚔️)** → **3 damage + 2 block**

3. **CONJURE (4 ⚡️) + QUICK (+1) + POTION (❤️)** → **5 heal**

#### 4.2.5 Mystery Temporary Buffs (Battle-Only)

Some Aspects include a **?** badge. This represents a **temporary buff reward** tied to the cast.

**Rule (MVP):**

- When a spell that includes one or more **?** fragments is successfully **bound and cast**, grant **one random temporary buff per “?”**.
- Temporary buffs last **until the end of the battle**.
- Temporary buffs behave exactly like normal buffs (Section 6) while active; the only difference is they do not persist after the battle.

**Temporary buff pool (example):**

- **Power** (e.g., +20% power)
- **Armor** (e.g., -20% damage taken)
- **Vitality** (e.g., +10% max HP for the battle)
- **Momentum / Scale** variants that are clearly counted and readable (more on them below in the Buff section).

(Exact numbers and pool composition are tuning knobs.)

### 4.3 Slot-Gating (Onboarding Rules)

To teach the syntax, the UI actively gates invalid choices.

- If no Command selected: only Command fragments are active.
- After selecting a Command: Entities/Aspects become active.
- Spell cannot be bound until an Entity is selected.

### 4.4 Binding Mechanics (The Puzzle)

Binding validates the spell and is the primary word puzzle.

#### 4.4.1 Entering Binding Mode
- The player can enter Binding Mode once the Build Area contains at least a **Command** and an **Entity**.
- On entering Binding Mode:
  - The selected fragments **lock** (you cannot unselect them). The remaining pool gets hidden from the UI.
  - Any hidden letters in Shrouded fragments become uncovered ("?" replaced by the actual letter in Binding Mode).
  - Each chosen fragment transforms into a row of **letter buttons**.
  - A **Binding Word** display appears above, split into **segments** (one per fragment, in Build Area order). E.g.  `_ _ _ _` for 4 fragments.
    - It can look similar to those segmented "enter code from email" inputs.
  - The **Binding timer** countdown starts (visible on the UI).

#### 4.4.2 Building the Binding Word
- Each fragment corresponds to exactly **one segment** in the Binding Word.
- Clicking a letter button in fragment **i** fills segment **i**.
- Only one letter may be selected per fragment:
  - The selected letter remains visually “pressed”.
  - Choosing another letter in the same fragment un-presses the previous one and replaces the segment.
- The player cannot type into the Binding Word with the keyboard.

#### 4.4.3 Validation, Success, and Failure Feedback
- When all segments are filled, the game concatenates the segments to form the candidate Binding Word.
- If the Binding Word exists in the game dictionary:
  - A success animation plays.
  - Binding completes automatically and the spell is cast.
- If the Binding Word is not in the dictionary:
  - A failure animation plays (e.g., the Binding Word “shakes”).
  - The player stays in Binding Mode and can keep trying by changing letters.
  - The timer continues counting down.

#### 4.4.4 Shrouded (Mystery) Fragments
Shrouded fragments add risk/reward.
- In drafting mode, a Shrouded fragment displays many letters as hidden (typically **60–80%** hidden), so the word is not easily recognizable.
- In Binding Mode, all letters are immediately uncovered.
- Shrouded fragments have **higher stats** than comparable normal fragments (more energy, stronger multipliers, or larger secondary effects).

#### 4.4.5 Timer, Give Up, and Backfire
- Binding Mode has a **time limit** (default **30 seconds**).
- If the timer reaches 0 before a valid Binding Word is formed:
  - **Backfire triggers** (player takes Backfire damage).
  - The attempted spell is discarded.
  - Used fragments are discarded and the fragment pool replenishes.
  - The player returns to the drafting state (same turn continues).
- The player may click **Give Up** to trigger Backfire immediately.

**Backfire damage (tunable rule):**
- Default: `BackfireDamage = 5% of Max HP × (# fragments on Scroll)` (minimum 1).

#### 4.4.6 Skip Turn
- **Skip Turn** ends the player’s turn without casting. Available only in the drafting state (not in Binding Mode).
- Skip Turn does **not** trigger Backfire.

### 4.5 Enemy Turn & Intent

- At the start of the player’s turn, the enemy’s **next intent** is shown.
- Enemy actions (MVP) are simple and telegraphed. Can be either of:
  - **Attack:** deal damage (varying power)
  - **Debuff:** apply a negative status to the player
- Move selection: **randomly chosen** from the enemy’s moveset.

### 4.6 Battle Feedback as a State Machine

The battle experience is presented as explicit states, shown in the center “battle state panel”.

**State sequence (typical):**

1. Enemy greeting message
2. Player drafts **Command**
3. Player drafts **Aspect(s)** and **Entity** (until Entity chosen)
4. Enter **Binding Mode** (segments + letter-buttons + timer shown)
5. Player selects letters to fill all segments
   - **Success:** valid dictionary word → spell card appears → effects apply
   - **Invalid word:** binding word shakes → player keeps trying (timer continues)
   - **Timer expires / Give Up:** Backfire damage animation → return to drafting (same turn continues)
6. Enemy turn resolves (attack/debuff)
7. Repeat until Win/Lose
8. Win screen / Lose screen with enemy commentary

## 5. Progression & Meta Systems

### 5.1 Campaign Structure

- Chapters progress linearly (Chapter 1 → Chapter 2 → Chapter 3 …).
- Each chapter has multiple standard encounters and one boss.
- Free selection of encounters within a chapter.
- **Advancement gate:** Defeat the **boss once** to unlock the next chapter.
- **No XP system** in the MVP.

### 5.2 Encounter Replay Rules

- All encounters, including bosses, are **infinitely replayable**.
- An encounter is marked **Beaten** once the player has won it at least once.
- Replay is meaningful because loot is randomized and enemy loot pools differ.

### 5.3 Loot: Buff Rewards

After every **victory**:

- Present **3** buff options (selected from enemy's loot table by weighted random).
- Player selects **1**.
- Buffs are added permanently to the player.

After **defeat**:

- **No loot**.
- Return to chapter.
- Existing buffs remain (see below).

### 5.4 Buff Persistence

- **Permanent buffs persist** across battles and **persist through defeat**.
- Temporary buffs (from **?** fragments) and debuffs expire as defined.

## 6. Buff & Debuff System

The buff system is the primary progression layer and must be clear, stackable, and easy to balance.

### 6.1 Buff Types

1. **Stat buffs** (always-on)

- Examples: `+10% Power`, `+10% Max HP`, `-10% Backfire`.

2. **Conditional buffs** (triggered by current or historical game state)

- Example: **Rage**: gain +20% Power when below 50% HP
- Example: **Payback:** gain power/block when took damage in prev turn (including Backfire)
- Example: **Momentum:** gain bonus after consecutive successful damages to enemy in prev turns

### 6.2 Intended Buff Families (MVP)

These families guide content creation and balance.

- **Power:** +N% spell power
- **Armor:** adds Block: reduces damage taken (-N%)
- **Vitality:** increases max HP
- **Lifesteal:** heal N HP based on damage dealt
- **Payback:** “when hit” responses (+N% power per each damage taken in the prev turn - including Backfire)
- **Rage:** +N% spell power if you lost half your HP
- **Shell:** adds Block if you lost half your HP
- **Momentum:** scale power during battle: +N% power per damage dealt to enemy in prev turn
- **Confidence:** incentives complex spells, +N% spell power per fragment used in current spell
- **Oathbound (see below):** powerful buffs with restrictions

### 6.3 Intended Buff levels (MVP)

For each buff family, we'll have a series of differently powered versions. E.g. Power I: +10% power, Power II: +20% etc. Let's say, 5 levels each. More powerful ones will be more concentrated toward the mid and end game.

### 6.4 Stacking Rules (MVP-Friendly)

- Flat bonuses stack additively.
- Percent bonuses stack additively within the same stat (avoid multiplicative blowups in MVP).
- If multiple buffs trigger on the same event, resolve in a consistent order:
  1. “Before damage” modifiers
  2. Damage/heal application
  3. “After damage” triggers

### 6.5 Oathbound Buffs

Instead of a rarity system, the game features a special category of high-impact buffs:

**Oathbound Buffs**

- Strong, build-defining.
- Always include a restriction, cost, or rule twist.
- Can be guaranteed rewards from certain bosses.

**Examples (illustrative):**

- *Oath of Flame:* `+50% Power`, but you cannot bind with words including letter L.
- *Oath of Glass:* `+40% Lifesteal` , but Backfire damage is doubled.
- *Oath of Pressure:* `+50% Power`, but binding time limit is reduced (e.g., 30s → 20s).

*(Exact numbers and restrictions are balance knobs.)*

### 6.6 Debuffs (Enemy-applied)

MVP debuffs should be simple and visible.

- **Frailty:** block effectiveness reduced.
- **Bleed:** lose HP at the start of your turn.

### 6.7 Visual Representation

- Buffs and debuffs are shown as small chips/icons in a horizontally scrollable rail above the player HP bar.
- Each buff shows:
  - Icon
  - Short modifier (e.g., `+10%`, `-20%`)
- Level indicator (e.g., I, II, III) is hidden for simplicity, but cna be shown on hover
- On hover/click, show full buff details in a tooltip/modal.

## 7. Fragment Pool & Drafting

### 7.1 Pool Behavior

- Replenishing - each player turn the fragment pool refills to its normal capacity by adding random fragments in place of the used ones. Important: that also happens after **Backfire** (timer expiry / Give Up) — the fragments in the discarded spell are removed and the pool replenishes.
- How fragment pool is filled and replenished: we have a global set of possible fragments, from which they are picked randomly. An encounter or chapter can optionally have their own fragment pool, then it is used instead of the global one - useful for early-game/tutorial encounters.
- Pool refill must always guarantee at least:
  - **1 Command**
  - **1 Aspect**
  - **1 Entity**
- Each chapter has a pool configuration: how many fragments of each type (Command / Aspect / Entity), and how many total fragments. This allows to limit the pool size (especially aspects) in early chapters for onboarding.

### 7.2 Fragment Attributes (Design Level)

Each fragment defines:

- Category (Command / Aspect / Entity)
- Visible word text
- **Shrouded settings** (if Shrouded: hidden-letter mask; hidden letters become visible in Binding Mode)
- Core effect stats. Depending on category: base energy, primary and secondary modifier, entity effect type.
- Optional temporary buff property

More details on fragment - see in "Spell Construction" section above.

## 8. Enemies (MVP)

Each enemy defines:

- Name
- Type (for MVP: standard / boss)
- Portrait / sprite (emoji placeholder for MVP, later to be replaced with SVG icon)
- HP
- A moveset of only (for now):
  - Attacks (varying damage)
  - Debuffs (simple status effects, active only during this battle) 
- Dialogue lines:
  - Greeting
  - Player victory line (enemy loses)
  - Enemy victory line (player loses)
- Loot pool (buff options)

## 9. Visual & UX Direction

### 9.1 Aesthetic, setting, and tone

- Whimsical, cozy fantasy.
- Readable UI with chunky chips and satisfying feedback.
- Light humor in enemy lines.

- Setting and lore: to be developed after MVP. For now, temporary setting is:
 - A journey of a crow mage apprentice who decided to become a mighty warlock. Code name "Grimbeak".

### 9.2 Early-Game Battle Example (Tutorial Sequence)

Example early pool: **CONJURE**, **LARGE**, **CURSE**, **FIREBALL**, **STRIKE**.

1. At battle start, only **Commands** are active; Entities/Aspects are greyed out.
2. Player clicks **CONJURE** → it moves to the Scroll, locks in place.
3. Hover hint on the Scroll shows: “**Aspect needed**”.
4. Now, Aspects become active; player clicks **LARGE** → it moves to the Scroll.
5. Entities become selectable. Player clicks **FIREBALL** → it moves to the Scroll.
6. Hover hint shows: “**Bind required**”. The **Bind** button becomes active.
7. Player clicks **Bind** → Binding Mode opens with 3 segments (one per fragment), letter-buttons, and a **30s** timer.
8. A hint appears: “**Build a valid 3-letter binding word using letters from each fragment**”.
8. Player taps one letter from **CONJURE**, one letter from **LARGE**, and one letter from **FIREBALL**. When all segments are filled, the game checks the dictionary.
   - If the word is invalid: it shakes, and the player keeps trying.
   - If the word is valid (e.g., **CAR**, **JAR**, **EAR**, etc.): success triggers automatically, success animation plays.
9. Spell card animates in: **CONJURE LARGE FIREBALL** with computed outcome.
10. Effects apply → enemy HP decreases.
11. Enemy intent resolves next turn.

### 9.3 UX Features

- Binding mode that visually focuses attention:
  - binding word **segments**
  - letter-button rows
  - timer + clear validation feedback (success vs shake)
- No toast notifications; messages appear in the central battle panel.

### 9.4 UI decisions

- Initially, use emojis for player/enemy sprites, buff icons etc. Will be replaced with SVG icons at a later stage of the MVP.

## 10. Technical Specifications (Summary, Non-Schema)

- Platform: Web (mobile responsive). Potential desktop and mobile (e.g. Electron) wrapper or PWA later (out of MVP).
- Tech stack (MVP target): React + Vite + Tailwind.
  - Data fetching / server-state: **TanStack Query**.
  - A small set of async **services** provides all game content + state access (e.g., `ContentService`, `EncounterService`, `PlayerStateService`, `DictionaryService`).
    - In the MVP these are “short-wired” to Local Storage (for state) and local or remote JSON files (for content).
    - The service interfaces are designed so implementations can later be swapped (e.g., backend) without changing UI code.
- Persistence for player state: Local storage for MVP.
- Data-driven content: chapters, enemies, fragments, buffs loaded from config files (JSON or CSV).
- Dictionary: compressed word list shipped with the game; the **binding word** must be in dictionary.

## 11. MVP Scope

**In MVP**

- All the above core systems fully implemented.
- Basic onboarding (chapter 1) to teach core mechanics.
- A small set of chapters (e.g., 3) with multiple encounters and bosses. No perfect balance tuning needed.
- Basic fragment pool with a limited number of fragments.
- Basic enemy set with simple movesets.
- Basic buff set with a limited number of buffs.
- Simple, clear UI with placeholder art (emojis, basic icons).
- Local storage persistence for player state.

**Out of MVP (explicitly excluded for now)**

- Full art assets (character sprites, environment, UI polish)
- Finished lore, worldbuilding, and narrative
- Full set of chapters and enemies
- Balance tuning
- Additional enemy move types (disrupt, steal fragments, etc.)
- Punitive roguelike resets
- Save slot complexity
- Player profiles
- Cloud persistence

## 12. Roadmap / Future Ideas

- **Gold** as a meta-currency (shops, rerolls, unlocks).
- **Leveling** that unlocks extra binding manipulations (e.g., reveal extra hidden letters, swap two segments, or re-roll one segment’s selection) enabling deeper spellcraft.
- **Mana fragments** that temporarily grant binding manipulations within a battle (e.g., reveal a “?” without selecting it, or extend the binding timer once).
- **Synergic** buffs system: adjust buffs such so that they can match into powerful "combos": e.g. one adds HP per damage dealt, other drains HP for extra power. Take care to avoid spiraling out of control (too OP combinations).
- **Expanded enemy move types** (disrupt, steal, alter rules) once the MVP is stable.
- **Difficulty hint** (optional, e.g., ★) against certain encounters in the chapter screen.
- **Aether / Flow** fragments: tempo/utility effects (draw, next-turn bonuses, etc.).