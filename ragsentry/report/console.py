from __future__ import annotations

from ragsentry.diff import RunDiff


def format_diff_console(diff: RunDiff) -> str:
    """Format a RunDiff into a human-readable terminal report."""
    lines: list[str] = []

    lines.append("=" * 78)
    lines.append("                        RAGSENTRY RUN DIFF REPORT")
    lines.append("=" * 78)
    lines.append(f"Baseline Run:  {diff.baseline_run_id} ({diff.baseline_timestamp})")
    lines.append(f"Candidate Run: {diff.candidate_run_id} ({diff.candidate_timestamp})")
    lines.append("-" * 78)

    # Summary Counts
    counts = diff.summary.get("counts", {})
    lines.append("Status Breakdown:")
    lines.append(
        f"  Total: {diff.summary.get('total_questions', 0)} | "
        f"Improved: {counts.get('improved', 0)} | "
        f"Regressed: {counts.get('regressed', 0)} | "
        f"Unchanged: {counts.get('unchanged', 0)} | "
        f"New: {counts.get('new', 0)} | "
        f"Removed: {counts.get('removed', 0)}"
    )
    lines.append("-" * 78)

    # Average Metric Shifts
    avg_deltas = diff.summary.get("average_deltas", {})
    if avg_deltas:
        lines.append("Overall Metric Shifts:")
        for metric, data in avg_deltas.items():
            b_val = f"{data['baseline']:.4f}" if data.get("baseline") is not None else "N/A"
            c_val = f"{data['candidate']:.4f}" if data.get("candidate") is not None else "N/A"
            delta = data.get("delta")
            if delta is not None:
                sign = "+" if delta > 0 else ""
                delta_str = f"{sign}{delta:.4f}"
            else:
                delta_str = "N/A"
            lines.append(f"  - {metric:<20}: {b_val} -> {c_val} ({delta_str})")
        lines.append("-" * 78)

    # Per-Question Breakdown Table
    lines.append(
        f"{'Question ID':<12} {'Status':<11} {'Metric':<18} {'Base':<8} {'Cand':<8} {'Delta':<8}"
    )
    lines.append("-" * 78)

    for row in diff.rows:
        if not row.metric_deltas:
            lines.append(f"{row.id:<12} {row.status.upper():<11} {'(no scores)':<18} {'-':<8} {'-':<8} {'-':<8}")
            continue

        first = True
        for m_name, m_delta in row.metric_deltas.items():
            qid = row.id if first else ""
            status = row.status.upper() if first else ""
            b_str = f"{m_delta.baseline:.4f}" if m_delta.baseline is not None else "N/A"
            c_str = f"{m_delta.candidate:.4f}" if m_delta.candidate is not None else "N/A"
            if m_delta.delta is not None:
                sign = "+" if m_delta.delta > 0 else ""
                d_str = f"{sign}{m_delta.delta:.4f}"
            else:
                d_str = "N/A"

            lines.append(f"{qid:<12} {status:<11} {m_name:<18} {b_str:<8} {c_str:<8} {d_str:<8}")
            first = False

    lines.append("=" * 78)
    return "\n".join(lines)
