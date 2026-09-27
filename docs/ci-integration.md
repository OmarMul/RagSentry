# CI/CD Integration Guide: "pytest for RAG"

**RagSentry** acts as an automated regression-testing and evaluation gate in your Continuous Integration (CI) pipelines. Just as `pytest` fails your build on broken unit tests, `ragsentry ci` fails your build on quality regressions, hallucination spikes, or retrieval degradation.

---

## 1. Core Concepts & Exit Codes

`ragsentry ci` is CI-provider-agnostic:
- **Exit Code `0`**: The quality gate **PASSED** (all thresholds met, no unacceptable regressions).
- **Exit Code `1`**: The quality gate **FAILED** (one or more metrics breached thresholds or regressed).

It supports two gating modes (which can be used together):
1. **Absolute Threshold Gating**: Ensures metrics meet a minimum acceptable standard (e.g., `faithfulness >= 0.85`).
2. **Baseline Regression Gating**: Compares the current PR against a stored baseline run (e.g., from `main` or production) to ensure recent changes didn't degrade existing capabilities.

---

## 2. Command Line Reference

```powershell
ragsentry ci [OPTIONS]
```

### Options

| Option | Shorthand | Description | Example |
| :--- | :--- | :--- | :--- |
| `--candidate` | `-c` | **(Required)** Path to the candidate evaluation run JSON file. | `-c runs/candidate.json` |
| `--baseline` | `-b` | Path to a baseline evaluation run JSON file to compare against. | `-b runs/baseline.json` |
| `--threshold` | `-t` | Minimum acceptable score for a metric. Repeatable. | `-t faithfulness=0.85 -t answer_relevancy=0.80` |
| `--max-regression` | | Maximum allowable drop in any average metric vs baseline. | `--max-regression 0.05` |
| `--max-regressed-questions` | | Max allowed count of individual questions that regressed. Default: `0`. | `--max-regressed-questions 0` |
| `--pr-comment-out` | | Output file path to write the formatted Markdown report. | `--pr-comment-out pr_comment.md` |

---

## 3. GitHub Actions Integration

### Complete Workflow (`.github/workflows/ragsentry.yml`)

The following workflow:
1. Runs evaluation against your RAG adapter.
2. Evaluates the run with `ragsentry ci`.
3. Displays the full report in the **GitHub Job Summary**.
4. Automatically posts or updates a comment on the Pull Request.

```yaml
name: RagSentry Quality Gate

on:
  pull_request:
    branches: [ main ]
  push:
    branches: [ main ]

jobs:
  rag-quality-gate:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write # Required if posting PR comments

    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install Dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e .

      - name: Run RAG Evaluation
        env:
          # Use your preferred judge provider key stored in GitHub Secrets
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          ragsentry run \
            --evalset evalset.jsonl \
            --adapter my_package.retriever:query \
            --judge-provider gemini \
            --out runs/

      - name: Identify Candidate Run File
        id: run_file
        run: |
          LATEST_RUN=$(ls -t runs/run_*.json | head -n 1)
          echo "path=$LATEST_RUN" >> $GITHUB_OUTPUT

      - name: Evaluate Quality Gate
        run: |
          ragsentry ci \
            --candidate "${{ steps.run_file.outputs.path }}" \
            --threshold faithfulness=0.80 \
            --threshold answer_relevancy=0.75 \
            --pr-comment-out pr_comment.md

      - name: Publish to GitHub Step Summary
        if: always()
        run: |
          if [ -f pr_comment.md ]; then
            cat pr_comment.md >> $GITHUB_STEP_SUMMARY
          fi

      - name: Post PR Comment
        if: always() && github.event_name == 'pull_request'
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          if [ -f pr_comment.md ]; then
            gh pr comment ${{ github.event.pull_request.number }} --body-file pr_comment.md
          fi
```

---

## 4. Comparing Against a Stored Baseline

To catch regressions against `main`:

1. Store the latest run from `main` in your repository or as a GitHub Actions Cache / Artifact.
2. In the PR workflow, pass both the candidate and the baseline:

```bash
ragsentry ci \
  --candidate runs/candidate.json \
  --baseline runs/baseline.json \
  --threshold faithfulness=0.85 \
  --max-regression 0.05 \
  --max-regressed-questions 0 \
  --pr-comment-out pr_comment.md
```

If the candidate score drops by more than `0.05` on any metric, or if any question regresses, the command exits with code `1` and highlights the regressed questions in the report.

---

## 5. GitLab CI / Bitbucket / Generic Pipelines

Because `ragsentry ci` uses standard exit codes and outputs Markdown to a file, it works out of the box in any CI engine.

### Example for GitLab CI (`.gitlab-ci.yml`)

```yaml
stages:
  - test

rag_gate:
  stage: test
  image: python:3.12
  script:
    - pip install -e .
    - ragsentry run -e evalset.jsonl -a "http://localhost:8000/query" -p gemini --out runs/
    - LATEST_RUN=$(ls -t runs/run_*.json | head -n 1)
    - ragsentry ci -c "$LATEST_RUN" -t faithfulness=0.80 --pr-comment-out report.md
  artifacts:
    when: always
    paths:
      - report.md
      - runs/
```

---

## 6. Recommended Best Practices

1. **Keep Golden Eval Sets Lean**: In CI, run a focused "smoke" eval set (15–30 questions) so your CI pipeline finishes in under 2 minutes. Reserve larger benchmarks (100–500 questions) for nightly builds.
2. **Store API Keys Securely**: Always inject your judge API key (`GEMINI_API_KEY`, `OPENROUTER_API_KEY`, etc.) through encrypted CI repository secrets.
3. **Inspect Collapsible Details**: When a build fails, click the **"View Per-Question Details"** dropdown in your PR comment to pinpoint which specific questions lost retrieval context or hallucinated.
