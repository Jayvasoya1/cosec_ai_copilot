from app.core.question_engine import generate_question

def build_response(results):
    final = []

    for r in results:

        if "need_input" in r:
            question = generate_question(r["missing"])
            return {
                "status": "need_input",
                "message": question,
                "partial": r["partial"]
            }

        if "error" in r:
            final.append(f"❌ {r['error']}")

        else:
            final.append(f"✅ {r.get('message', 'Done')}")

    return {
        "status": "success",
        "message": "\n".join(final),
        "details": results
    }