from typing import List, Dict, Any, Tuple
from backend.precedent.storage.schema import Incident, MatchResult, ConsistencyReport, DifferentiatingFactor
from backend.precedent.features.vectorizer import FEATURE_LABELS, FEATURE_NAMES

FIA_GUIDELINES_MAP = {
    "overlap_pct": "FIA Driving Standards Guidelines (Art 2.1 - Overtaking on Inside): Attacker must have front axle alongside defender'\''s cockpit by corner apex to earn racing room.",
    "had_inside_line": "FIA Driving Standards Guidelines (Art 2.2 - Defending/Line Rights): Car establishing inside line before braking phase has primary rights to apex curvature.",
    "closing_speed_norm": "FIA International Sporting Code (Appendix L, Chapter IV): Excessive closing speed indicating out-of-control braking nullifies overlap rights.",
    "contact_occurred": "FIA Sporting Regulations Art 33.3: Maneuvers with direct wheel/sidepod contact are heavily scrutinized unless mutual racing room was respected."
}


def analyze_consistency(
    target: Incident,
    matches: List[MatchResult],
    novelty_threshold: float = 0.85,
    top_n_eval: int = 2
) -> ConsistencyReport:
    """
    Evaluates precedent consistency across matched incidents.
    Categorizes into Clean Match ('consistent'), Inconsistent Precedent ('split'), or 'novel'.
    """
    if not matches:
        return ConsistencyReport(
            target_incident=target,
            matches=[],
            verdict_status="novel",
            majority_ruling="unknown",
            is_consistent=False,
            novelty_score=1.0,
            differentiating_factors=[],
            summary_verdict="No past precedents found.",
            fia_rules_reference="N/A"
        )

    closest_dist = matches[0].distance
    if closest_dist > novelty_threshold:
        return ConsistencyReport(
            target_incident=target,
            matches=matches,
            verdict_status="novel",
            majority_ruling=matches[0].precedent.ruling,
            is_consistent=False,
            novelty_score=round(closest_dist, 3),
            differentiating_factors=[],
            summary_verdict=f"Novel racing scenario. Closest historical incident ({matches[0].precedent.name}) is geometrically distant (L2 distance {closest_dist:.2f} > threshold {novelty_threshold}). No direct precedent exists.",
            fia_rules_reference="FIA International Sporting Code Art 11.9.3.a (Discretionary Powers of Stewards in Novel Circumstances)."
        )

    # Evaluate the top N immediate geometric neighbors
    eval_matches = matches[:top_n_eval]
    rulings = [m.precedent.ruling for m in eval_matches]

    # Check consistency: all top neighbors must share the target ruling
    is_split = any(r != target.ruling for r in rulings)
    status = "split" if is_split else "consistent"
    is_consistent = (status == "consistent")
    majority_ruling = target.ruling if is_consistent else eval_matches[0].precedent.ruling

    factors: List[DifferentiatingFactor] = []
    top_factor_name = "overlap_pct"

    if status == "split":
        # Find the immediate precedent with differing ruling
        differing_match = next((m for m in eval_matches if m.precedent.ruling != target.ruling), eval_matches[0])
        precedent_inc = differing_match.precedent

        # Compare physical/geometric fields
        comparisons = [
            ("overlap_pct", "Overlap % at Apex", f"{int(target.overlap_pct_at_apex * 100)}%", f"{int(precedent_inc.overlap_pct_at_apex * 100)}%", abs(target.overlap_pct_at_apex - precedent_inc.overlap_pct_at_apex)),
            ("closing_speed_norm", "Closing Speed Delta", f"{target.closing_speed_delta:.1f} km/h", f"{precedent_inc.closing_speed_delta:.1f} km/h", abs(target.closing_speed_delta - precedent_inc.closing_speed_delta) / 50.0),
            ("had_inside_line", "Held Inside Line", "Yes" if target.had_inside_line else "No", "Yes" if precedent_inc.had_inside_line else "No", abs(target.had_inside_line - precedent_inc.had_inside_line)),
            ("contact_occurred", "Physical Collision", "Yes" if target.contact_occurred else "No", "Yes" if precedent_inc.contact_occurred else "No", abs(target.contact_occurred - precedent_inc.contact_occurred))
        ]

        # Sort by delta descending
        comparisons.sort(key=lambda x: x[4], reverse=True)

        for feat, label, t_val, p_val, delta in comparisons:
            if delta > 0.05:
                expl = f"{label} differed: Target had {t_val} vs Precedent ({precedent_inc.name}) had {p_val}."
                factors.append(DifferentiatingFactor(
                    feature_name=feat,
                    display_name=label,
                    target_value=t_val,
                    precedent_value=p_val,
                    delta=round(delta, 3),
                    explanation=expl
                ))

        if factors:
            top_factor_name = factors[0].feature_name

        summary = (
            f"Precedent Split Detected: Despite matching corner geometry (distance {differing_match.distance:.3f}), "
            f"target was ruled '{target.ruling}', whereas precedent '{differing_match.precedent.name}' was ruled '{differing_match.precedent.ruling}'. "
            f"Primary distinguishing metric: {factors[0].display_name if factors else 'Apex Overlap'}."
        )
    else:
        names = " and ".join([f"'{m.precedent.name}'" for m in eval_matches])
        summary = (
            f"Consistent Precedent: Top geometric precedents ({names}) "
            f"were uniformly ruled '{majority_ruling}'. Target decision is fully consistent with established precedent."
        )

    fia_ref = FIA_GUIDELINES_MAP.get(top_factor_name, "FIA Driving Standards Guidelines (Art 2: Overtaking & Defending).")

    return ConsistencyReport(
        target_incident=target,
        matches=matches,
        verdict_status=status,
        majority_ruling=majority_ruling,
        is_consistent=is_consistent,
        novelty_score=round(closest_dist, 3),
        differentiating_factors=factors,
        summary_verdict=summary,
        fia_rules_reference=fia_ref
    )
