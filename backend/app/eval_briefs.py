from .brief_generator import get_generator

SAMPLES = [
    "We need a dashboard that exports our weekly sales pipeline to CSV.",
    "Can someone build an AI agent that automatically triages support tickets?",
    "fix the thing",
    "Our approval workflow for expense reports is too slow.",
]

def main():
    gen = get_generator()
    passed = 0
    for text in SAMPLES:
        brief = gen.generate(text)
        issues = []
        if len(brief.problem_summary) < 10: issues.append("summary too short")
        if not brief.likely_users: issues.append("no likely_users")
        if not brief.clarifying_questions: issues.append("no clarifying questions")
        if not brief.risks: issues.append("no risks")
        status = "PASS" if not issues else "FAIL"
        if not issues: passed += 1
        print(f"[{status}] {text[:50]!r}")
        for i in issues: print(f"    - {i}")
    print(f"\n{passed}/{len(SAMPLES)} passed.")

if __name__ == "__main__":
    main()