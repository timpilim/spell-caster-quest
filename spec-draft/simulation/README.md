# Balance simulations

Two small, dependency-free Python 3 scripts backing the numbers in `SpellCastGame v2.0.md` §10.

| Script | What it answers |
|--------|-----------------|
| `bind_sim.py` | How often a random N-fragment spell has a valid binding word, and how many (per dictionary). |
| `combat_sim.py` | Win rates, fight length, HP left and Backfire counts per chapter, enemy, player skill and drafting policy. |
| `vocab.py` | Fragment vocabulary shared by both scripts. |

## Setup

`bind_sim.py` needs two word lists in this folder (not committed, ~2 MB):

```bash
curl -sSL -o enable1.txt https://raw.githubusercontent.com/dolph/dictionary/master/enable1.txt
curl -sSL -o words20k.txt https://raw.githubusercontent.com/first20hours/google-10000-english/master/20k.txt
curl -sSL -o google10k.txt https://raw.githubusercontent.com/first20hours/google-10000-english/master/google-10000-english-no-swears.txt
```

## Run

```bash
python3 bind_sim.py
python3 combat_sim.py adaptive   # or: safe | max
```

`combat_sim.py` mirrors the GDD tables: fragment stats (Appendix A), enemy roster (§8.3), chapter rules (§5.3), expected buffs per chapter and the Backfire rule (3% of Max HP per fragment, turn-ending). Edit the constants at the top of the file to test a change, then update the GDD tables if the change is kept.
