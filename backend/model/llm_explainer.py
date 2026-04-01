def generate_explanation(reasons):
    if not reasons:
        return "No strong reasons identified."

    reasons = [r for r in reasons if abs(r["impact"]) > 0.05]

    if not reasons:
        return "No significant factors influencing churn."

    reasons = sorted(reasons, key=lambda x: abs(x["impact"]), reverse=True)
    important_features = [r["feature"] for r in reasons]

    explanation = (
        f"Customer churn prediction is mainly influenced by "
        f"{', '.join(important_features)}. "
        f"These factors have the strongest impact on the model's decision. "
        f"Recommended actions: Analyze pricing and service value, "
        f"improve customer engagement, and provide better support and retention offers."
    )
    return explanation