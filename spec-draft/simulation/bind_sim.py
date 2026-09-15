"""
Binding puzzle solvability simulation.
For n fragments (1 command, n-2 aspects, 1 entity), count dictionary words of length n
whose i-th letter appears in fragment i. Reports P(solvable) and solution-count stats.
"""
import random, statistics, sys
from collections import defaultdict
from vocab import COMMANDS, ASPECTS, ENTITIES

COMMON2 = set("""am an as at be by do go he hi if in is it me my no of oh on or ox so to up us we
ah ad ax pi lo""".split())

def load(path):
    return [w.strip().lower() for w in open(path) if w.strip().isalpha()]

enable = set(load("enable1.txt"))
w20k = set(load("words20k.txt"))
w10k = set(load("google10k.txt"))

DICTS = {
    "ENABLE (172k, permissive)": enable,
    "20k common": {w for w in w20k if len(w) >= 3} | (w20k & COMMON2),
    "ENABLE, 2-letter restricted": {w for w in enable if len(w) >= 3} | COMMON2,
    "ENABLE ∩ 20k, 2-letter restricted": ({w for w in enable if len(w) >= 3} & w20k) | COMMON2,
}

def by_len(d):
    out = defaultdict(list)
    for w in d: out[len(w)].append(w)
    return out

def solutions(frags, words_n):
    sets = [set(f) for f in frags]
    return [w for w in words_n if all(c in s for c, s in zip(w, sets))]

def sample_spell(n, rng, shroud_vowel_drop=0):
    frags = [rng.choice(COMMANDS)] + rng.sample(ASPECTS, n - 2) + [rng.choice(ENTITIES)]
    return frags

def run(dname, d, trials=3000, seed=1, banned=None, max_n=6):
    bl = by_len(d)
    rng = random.Random(seed)
    print(f"\n== Dictionary: {dname} ==")
    print(f"{'n':>2} {'P(solv)':>8} {'P(>=3 sol)':>10} {'median':>7} {'p10':>5} {'p25':>5} {'mean':>7}")
    for n in range(2, max_n + 1):
        counts = []
        for _ in range(trials):
            frags = sample_spell(n, rng)
            sols = solutions(frags, bl[n])
            if banned:
                sols = [w for w in sols if banned not in w]
            counts.append(len(sols))
        solv = sum(c > 0 for c in counts) / trials
        solv3 = sum(c >= 3 for c in counts) / trials
        cs = sorted(counts)
        print(f"{n:>2} {solv:>8.3f} {solv3:>10.3f} {statistics.median(cs):>7.0f} {cs[len(cs)//10]:>5} {cs[len(cs)//4]:>5} {statistics.mean(cs):>7.1f}")

if __name__ == "__main__":
    for name, d in DICTS.items():
        run(name, d)
    print("\n### With banned letter 'e' (Oath-style restriction), ENABLE 2-letter restricted")
    run("ENABLE 2-restricted, ban e", DICTS["ENABLE, 2-letter restricted"], banned="e")
    print("\n### Example spells and their solutions (ENABLE ∩ 20k):")
    bl = by_len(DICTS["ENABLE ∩ 20k, 2-letter restricted"])
    rng = random.Random(7)
    for n in (2, 3, 4, 5):
        for _ in range(3):
            frags = sample_spell(n, rng)
            sols = solutions(frags, bl[n])
            print(f"  {' + '.join(f.upper() for f in frags):45s} -> {len(sols):3d} sols: {', '.join(sols[:8])}")
