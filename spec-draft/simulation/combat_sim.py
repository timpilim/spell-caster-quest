"""
Combat pacing simulation (numbers match GDD v2.0 §8.3 / Appendix A; see §10.2 for how to read the output).
Usage: python3 combat_sim.py [safe|adaptive|max]

Combat pacing simulation for Spell Caster Quest.
Models: fragment pool with real stats, greedy spell building, bind success by word length
(structural solvability x player skill), Backfire (ends turn), enemy attack/debuff, buffs.
"""
import random, statistics, sys
from dataclasses import dataclass, field

# ---------- Content (mirrors the design doc's tuning tables) ----------
# Commands: (name, energy)
COMMANDS = [("cast", 3), ("conjure", 4), ("summon", 4), ("invoke", 5), ("unleash", 6)]
COMMAND_W = [4, 3, 3, 2, 1]  # rarity weights
# Aspects: (name, add, mult, secondary(type, value))
ASPECTS = [
    ("quick", 1, 1.0, None), ("large", 2, 1.0, None), ("heavy", 3, 1.0, None),
    ("mighty", 0, 1.5, None), ("savage", 0, 2.0, None),
    ("warding", 0, 1.0, ("block", 3)), ("gentle", 0, 1.0, ("heal", 3)),
    ("sharpened", 1, 1.0, ("attack", 2)), ("stout", 1, 1.0, ("block", 2)),
]
ASPECT_W = [4, 3, 2, 3, 1, 2, 2, 2, 2]
ENTITIES = [("fireball", "attack"), ("bolt", "attack"), ("dagger", "attack"), ("barrier", "block"), ("potion", "heal")]
ENTITY_W = [3, 3, 2, 2, 2]

# Structural solvability by word length (ENABLE dictionary, from bind_sim.py)
SOLVABLE = {3: 1.0, 4: 0.999, 5: 0.977, 6: 0.925}
# Player skill: P(find a word within the timer | solvable), by word length
SKILL = {
    "novice":  {3: 0.95, 4: 0.80, 5: 0.55, 6: 0.30},
    "average": {3: 0.99, 4: 0.92, 5: 0.75, 6: 0.50},
    "expert":  {3: 1.00, 4: 0.98, 5: 0.92, 6: 0.80},
}

@dataclass
class Enemy:
    name: str; hp: int; atk_lo: int; atk_hi: int; debuff_p: float = 0.0; boss: bool = False
    big_atk: int = 0  # bosses: occasionally telegraph a big hit

# Chapter rosters (standard enemies + boss). Tuning target from the design doc.
CHAPTERS = {
    1: [Enemy("Cellar Rat", 18, 4, 6), Enemy("Bog Slime", 22, 4, 7), Enemy("Ink Imp", 25, 5, 8, 0.2), Enemy("Goblin Scribe", 28, 6, 8, 0.2),
        Enemy("BOSS Toad King", 40, 6, 9, 0.25, True, 14)],
    2: [Enemy("Moor Wolf", 32, 7, 10), Enemy("Word Bandit", 36, 8, 11, 0.25), Enemy("Marsh Wisp", 40, 8, 11, 0.3), Enemy("Clay Golem", 44, 9, 12),
        Enemy("BOSS Hedge Witch", 60, 8, 12, 0.3, True, 18)],
    3: [Enemy("Rusted Knight", 48, 9, 13), Enemy("Wyvern", 54, 10, 14, 0.25), Enemy("Lich Librarian", 58, 10, 14, 0.35), Enemy("Bridge Troll", 62, 11, 15),
        Enemy("BOSS Elder Wyrm", 90, 10, 14, 0.3, True, 24)],
}
MAX_FRAGS = {1: 3, 2: 4, 3: 5}

@dataclass
class Player:
    max_hp: int = 100
    power: float = 0.0     # +fraction
    armor: float = 0.0     # -fraction damage taken
    lifesteal: float = 0.0
    backfire_mult: float = 1.0

@dataclass
class Cfg:
    backfire_pct_per_frag: float = 0.03
    pool_c: int = 2; pool_a: int = 3; pool_e: int = 3
    policy: str = "adaptive"   # "safe" (always 3), "max" (always max), "adaptive"
    heal_below: float = 0.45

def wchoice(rng, items, weights): return rng.choices(items, weights)[0]

def refill(rng, pool):
    while len(pool["c"]) < CFG.pool_c: pool["c"].append(wchoice(rng, COMMANDS, COMMAND_W))
    while len(pool["a"]) < CFG.pool_a: pool["a"].append(wchoice(rng, ASPECTS, ASPECT_W))
    while len(pool["e"]) < CFG.pool_e: pool["e"].append(wchoice(rng, ENTITIES, ENTITY_W))

def spell_value(cmd, aspects, power):
    e = cmd[1] + sum(a[1] for a in aspects)
    for a in aspects: e *= a[2]
    e = round(e * (1 + power))
    sec = {"attack": 0, "block": 0, "heal": 0}
    for a in aspects:
        if a[3]: sec[a[3][0]] += a[3][1]
    return max(1, e), sec

def build_spell(rng, pool, hp, pmax, intent_dmg, max_frags, power, skill):
    """Greedy: pick entity by need, best command, then best aspects up to allowed count."""
    need_heal = hp / pmax < CFG.heal_below and any(e[1] == "heal" for e in pool["e"])
    if need_heal: ent = next(e for e in pool["e"] if e[1] == "heal")
    else:
        atks = [e for e in pool["e"] if e[1] == "attack"]
        ent = atks[0] if atks else (next((e for e in pool["e"] if e[1] == "block"), None) or pool["e"][0])
    cmd = max(pool["c"], key=lambda c: c[1])
    # choose number of aspects
    if CFG.policy == "safe": n_asp = 1
    elif CFG.policy == "max": n_asp = max_frags - 2
    else:  # adaptive: go big when healthy, safe when low
        n_asp = max_frags - 2 if hp / pmax > 0.5 else 1
    n_asp = min(n_asp, len(pool["a"]))
    # rank aspects by contribution
    ranked = sorted(pool["a"], key=lambda a: -(a[1] + (a[2] - 1) * 6 + (a[3][1] if a[3] else 0)))
    aspects = ranked[:n_asp]
    return cmd, aspects, ent

def fight(rng, enemy, player, chapter, skill):
    hp, ehp, block = player.max_hp, enemy.hp, 0
    pool = {"c": [], "a": [], "e": []}
    turns, backfires = 0, 0
    bleed = 0
    while hp > 0 and ehp > 0 and turns < 60:
        turns += 1
        refill(rng, pool)
        # enemy intent
        if enemy.boss and enemy.big_atk and rng.random() < 0.25: intent = ("big", enemy.big_atk)
        elif rng.random() < enemy.debuff_p: intent = ("debuff", 0)
        else: intent = ("attack", rng.randint(enemy.atk_lo, enemy.atk_hi))
        if bleed > 0: hp -= 3; bleed -= 1
        cmd, aspects, ent = build_spell(rng, pool, hp, player.max_hp, intent[1], MAX_FRAGS[chapter], player.power, skill)
        n = 2 + len(aspects)
        pool["c"].remove(cmd); pool["e"].remove(ent)
        for a in aspects: pool["a"].remove(a)
        p_ok = SOLVABLE[n] * SKILL[skill][n]
        if rng.random() < p_ok:
            e, sec = spell_value(cmd, aspects, player.power)
            dmg = (e if ent[1] == "attack" else 0) + sec["attack"]
            heal = (e if ent[1] == "heal" else 0) + sec["heal"]
            blk = (e if ent[1] == "block" else 0) + sec["block"]
            ehp -= dmg
            hp = min(player.max_hp, hp + heal + round(dmg * player.lifesteal))
            block = blk
        else:
            backfires += 1
            hp -= max(1, round(player.max_hp * CFG.backfire_pct_per_frag * n * player.backfire_mult))
            block = 0
        if ehp <= 0 or hp <= 0: break
        # enemy acts
        if intent[0] == "debuff": bleed = 2
        else:
            d = round(intent[1] * (1 - player.armor))
            absorbed = min(block, d); d -= absorbed
            hp -= d
        block = 0
    return hp > 0, hp, turns, backfires

def run_chapter(chapter, player, skill, trials=2000, seed=0):
    rng = random.Random(seed)
    rows = []
    for enemy in CHAPTERS[chapter]:
        res = [fight(rng, enemy, player, chapter, skill) for _ in range(trials)]
        wr = sum(r[0] for r in res) / trials
        hp_left = statistics.mean(r[1] for r in res if r[0]) if wr > 0 else 0
        turns = statistics.mean(r[2] for r in res)
        bf = statistics.mean(r[3] for r in res)
        rows.append((enemy.name, wr, hp_left, turns, bf))
    return rows

CFG = Cfg()

def player_at(stage):
    """Expected permanent buffs by stage (one buff per family, levels I-V)."""
    p = Player()
    if stage >= 1:  # after ch1 (~6 wins): Power II, Vitality I, Armor I
        p.power, p.max_hp, p.armor = 0.2, 110, 0.1
    if stage >= 2:  # after ch2: Power III, Vitality III, Armor II, Lifesteal I
        p.power, p.max_hp, p.armor, p.lifesteal = 0.3, 130, 0.2, 0.1
    return p

if __name__ == "__main__":
    policy = sys.argv[1] if len(sys.argv) > 1 else "adaptive"
    CFG.policy = policy
    print(f"policy={policy}, backfire={CFG.backfire_pct_per_frag*100:.0f}%/frag of max HP, backfire ends turn")
    for chapter in (1, 2, 3):
        player = player_at(chapter - 1)
        print(f"\n--- Chapter {chapter} (max {MAX_FRAGS[chapter]} fragments; player HP {player.max_hp}, power +{player.power:.0%}, armor {player.armor:.0%}) ---")
        print(f"{'enemy':14s} | " + " | ".join(f"{s:^28s}" for s in SKILL))
        print(f"{'':14s} | " + " | ".join(f"{'win%':>5s} {'hpLeft':>6s} {'turns':>5s} {'bkf':>4s}    " for s in SKILL))
        per_skill = {s: run_chapter(chapter, player, s) for s in SKILL}
        for i, enemy in enumerate(CHAPTERS[chapter]):
            cells = []
            for s in SKILL:
                name, wr, hpl, t, bf = per_skill[s][i]
                cells.append(f"{wr*100:5.0f} {hpl:6.0f} {t:5.1f} {bf:4.2f}    ")
            print(f"{enemy.name:14s} | " + " | ".join(cells))
