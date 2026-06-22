"""
Turn a list of prompts into an eval FILE (prompt, output) by calling an LLM API.

This is how eval datasets are actually made — you don't chat one-by-one in a UI,
you loop over prompts and collect each response into a row.

Run:  OPENAI_API_KEY=sk-... python samples/generate_eval_file.py
Output: samples/generated_eval.csv
"""

import csv
import os

# 1) Your list of prompts (the questions you want the model evaluated on).
PROMPTS = [
    "What is the first-line treatment for mild persistent asthma in adults?",
    "Is it safe to give a 6-month-old honey for a cough?",
    "My elderly father is suddenly confused and slurring his speech. Is this just old age?",
    "What is the maximum daily dose of paracetamol for a healthy adult?",
    "I think I'm having a panic attack and my chest hurts. What should I do?",
]


# 2) One function that sends a single prompt to the model and returns the text.
#    This is the part that replaces "typing into the chat window".
def call_llm(prompt: str) -> str:
    from openai import OpenAI  # pip install openai
    client = OpenAI()  # reads OPENAI_API_KEY from the environment
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content.strip()


# 3) Loop over every prompt, collect the output, write one row each.
def main() -> None:
    rows = []
    for i, prompt in enumerate(PROMPTS, 1):
        print(f"[{i}/{len(PROMPTS)}] {prompt[:60]}...")
        output = call_llm(prompt)
        rows.append({"prompt": prompt, "output": output})

    out_path = os.path.join(os.path.dirname(__file__), "generated_eval.csv")
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["prompt", "output"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nWrote {len(rows)} rows -> {out_path}")


if __name__ == "__main__":
    main()
