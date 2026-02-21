def classify_risk_with_history(reaction, hospitalized, previous_high_risk_count):

    score = 0

    if hospitalized:
        score += 5

    if "breathing" in reaction.lower():
        score += 4

    if "rash" in reaction.lower():
        score += 3

    if previous_high_risk_count >= 3:
        score += 2

    if score >= 5:
        return "HIGH RISK"

    return "LOW RISK"
