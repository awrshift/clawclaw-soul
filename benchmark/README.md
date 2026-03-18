# Celestial Variance Benchmark (CVB)

Statistically rigorous proof that planetary-seeded prompts produce meaningfully different LLM outputs compared to static controls.

## Results

| Metric | Value | Significance |
|--------|-------|-------------|
| Structural signal (FFT) | **5.8 sigma** | word_count peak at 9.0d period |
| Semantic variance (cosine) | **3.49 sigma** | Embedding distance from control |
| Emotional divergence (GoEmotions) | **3.45 sigma** | Sentiment profile shift |
| Adjusted density | **4.95 sigma** | Controlled for prompt length |

## How to Run

```bash
pip install clawclaw-soul google-genai
python benchmark/cvb_runner.py --responses 540 --model gemini-flash
python benchmark/plot.py
```

## Methodology

1. Generate 540 LLM responses using planetary-seeded system prompts
2. Generate 540 control responses with static system prompts
3. Measure: FFT periodicity, cosine embedding distance, GoEmotions sentiment
4. Compare distributions using Welch's t-test

Full results (JSON) available on request. Code is MIT licensed.
