from __future__ import annotations

from ragsentry.ci import CIGateResult


def format_pr_comment(gate_result: CIGateResult) -> str:
    """Format a CI gate result into a GitHub PR comment markdown string."""
    cand = gate_result.candidate_run
    base = gate_result.baseline_run
    diff = gate_result.diff

    status_icon = ":white_check_mark:" if gate_result.passed else ":x:"
    status_text = "PASSED" if gate_result.passed else "FAILED"

    lines: list[str] = []
    lines.append(f"## {status_icon} RagSentry Quality Gate {status_text}\n")

    if cand:
        lines.append(f"**Run ID:** `{cand.run_id}` | **Adapter:** `{cand.adapter}` | **Timestamp:** `{cand.timestamp}`\n")

    # Violations Alert
    if not gate_result.passed:
        lines.append("> [!CAUTION]")
        lines.append("> **Quality Gate Breaches:**")
        for v in gate_result.violations:
            lines.append(f"> - {v}")
        lines.append("")

    # Summary Metrics Table
    lines.append("### Metric Summary\n")
    if diff:
        lines.append("| Metric | Baseline | Candidate | Delta | Threshold |")
        lines.append("| :--- | :--- | :--- | :--- | :--- |")
        avg_deltas = diff.summary.get("average_deltas", {})
        for metric, d_info in avg_deltas.items():
            b_val = f"{d_info['baseline']:.4f}" if d_info.get("baseline") is not None else "-"
            c_val = f"{d_info['candidate']:.4f}" if d_info.get("candidate") is not None else "-"
            delta = d_info.get("delta")
            if delta is not None:
                sign = "+" if delta > 0 else ""
                d_str = f"**{sign}{delta:.4f}**"
            else:
                d_str = "-"
            thresh_val = f">= {gate_result.thresholds[metric]:.4f}" if metric in gate_result.thresholds else "-"
            lines.append(f"| **{metric}** | {b_val} | {c_val} | {d_str} | {thresh_val} |")
    elif cand:
        lines.append("| Metric | Candidate Score | Threshold |")
        lines.append("| :--- | :--- | :--- |")
        avg_scores = cand.summary.get("average_scores", {})
        for metric, score in avg_scores.items():
            thresh_val = f">= {gate_result.thresholds[metric]:.4f}" if metric in gate_result.thresholds else "-"
            lines.append(f"| **{metric}** | {score:.4f} | {thresh_val} |")
    lines.append("")

    # Question Breakdown (Collapsible)
    if diff and diff.rows:
        counts = diff.summary.get("counts", {})
        lines.append(
            f"**Breakdown:** {counts.get('improved', 0)} improved, "
            f"{counts.get('regressed', 0)} regressed, "
            f"{counts.get('unchanged', 0)} unchanged.\n"
        )
        lines.append("<details>")
        lines.append("<summary><b>View Per-Question Details</b></summary>\n")
        lines.append("| Question ID | Status | Metric | Base | Candidate | Delta |")
        lines.append("| :--- | :--- | :--- | :--- | :--- | :--- |")

        for row in diff.rows:
            if not row.metric_deltas:
                lines.append(f"| `{row.id}` | {row.status.upper()} | - | - | - | - |")
                continue
            first = True
            for m_name, m_delta in row.metric_deltas.items():
                qid = f"`{row.id}`" if first else ""
                stat = row.status.upper() if first else ""
                b_str = f"{m_delta.baseline:.4f}" if m_delta.baseline is not None else "-"
                c_str = f"{m_delta.candidate:.4f}" if m_delta.candidate is not None else "-"
                if m_delta.delta is not None:
                    sign = "+" if m_delta.delta > 0 else ""
                    d_str = f"{sign}{m_delta.delta:.4f}"
                else:
                    d_str = "-"
                lines.append(f"| {qid} | {stat} | {m_name} | {b_str} | {c_str} | {d_str} |")
                first = False

        lines.append("\n</details>\n")

    lines.append("----\n*Generated automatically by [RagSentry](https://github.com/OmarMul/RagSentry)*")
    return "\n".join(lines)
