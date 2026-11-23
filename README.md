# The World in One Day — Monday 23 November 2026

[![Competition](https://make.fun/badge/news-image-20261123.svg)](https://make.fun/bounty/news-image-20261123)
[![Rank](https://make.fun/badge/news-image-20261123/Apizairdrop/news-image-20261123/rank.svg)](https://make.fun/bounty/news-image-20261123)
[![Reward](https://make.fun/badge/news-image-20261123/Apizairdrop/news-image-20261123/reward.svg)](https://make.fun/bounty/news-image-20261123)

A newspaper front page that sums up the world news of **Monday 23 November 2026** in a single image. Entry for the [make.fun competition `news-image-20261123`](https://make.fun/bounty/news-image-20261123).

## What the image shows

Six stories from across regions and fields, each with a hand-drawn pictogram, a headline and a short summary:

1. **Climate — COP31 collapses.** Climate talks in Turkey end with no major deal as nations split over fossil fuels and finance.
2. **Europe — Russian missiles in Poland.** Poland confirms three fallen objects were Russian cruise missiles; NATO to meet.
3. **USA — Democrats win big.** Democrats take their largest House majority since 1992 after flipping a North Carolina seat.
4. **Ukraine — Boy, 7, pulled alive.** Rescuers pull a seven-year-old boy alive from rubble hours after a Russian strike near Kyiv.
5. **Markets — Nvidia chief steps down.** Nvidia CEO Huang Renxun steps down as Taiwan curbs short selling and Asian shares plunge.
6. **Disaster — Quake hits Vanuatu.** A magnitude 6.5 earthquake strikes the Vanuatu region in the Pacific.

## How it was made

The front page is drawn from scratch by `main.py` (Python 3.13, standard library only): a hand-rolled 5×7 bitmap font, hand-drawn pictograms, and a hand-rolled PNG encoder. No network, no external assets — the program is fully deterministic and writes the same bytes on every run.

## How to run it

```sh
MAKEFUN_OUTPUT_DIR=out python3 main.py
```

This writes `out/entry.png` (1024×1024, PNG).
