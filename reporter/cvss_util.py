from cvss import CVSS3

def vector_to_score(vector):
    return CVSS3(vector).scores()[2]

def score_to_severity(score):
    if not isinstance(score, float):
        score = float(score)
    if score == 0.0:
        return "none"
    elif 0.1 <= score < 4.0:
        return "low"
    elif 4.0 <= score < 7.0:
        return "medium"
    elif 7.0 <= score < 9.0:
        return "high"
    else:
        return "critical"
