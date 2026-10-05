"""
test_mcq.py - tests for MC compiler + gate.
"""

from __future__ import annotations

import sys, os, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "tools"))

import mcq
from mcq import MCQuestion, question_hash, ingest_csv, ingest_php_test_page
import gate
from gate import gate, gate_course, gate_question


def test_t1_question_hash_deterministic():
    h1 = question_hash("What is 2+2?", "4", "test.csv:1")
    h2 = question_hash("What is 2+2?", "4", "test.csv:1")
    h4 = question_hash("What is 2+2?", "5", "test.csv:1")
    assert h1 == h2 and h1 != h4
    print("T1: ok")


def test_t2_mcquestion_canonical():
    h = question_hash("stem", "A", "src")
    q = MCQuestion(
        question_id=h, stem="stem", choices=("A", "B"), answer="A",
        source="src", subject_area="math", level="k-12",
    )
    c = q.canonical()
    assert c["stem"] == "stem" and c["answer"] == "A" and c["subject_area"] == "math"
    print("T2: ok")


def test_t3_gate_passes_valid_question():
    h = question_hash("s", "A", "src")
    q = MCQuestion(question_id=h, stem="the stem", choices=("A", "B"), answer="A",
                   source="src", subject_area="math", level="k-12")
    ok, reason = gate(q.canonical())
    assert ok, reason
    print(f"T3: ok ({reason})")


def test_t4_gate_rejects_no_answer():
    h = question_hash("s", "A", "src")
    q = MCQuestion(question_id=h, stem="the stem", choices=("A", "B"), answer="",
                   source="src")
    ok, reason = gate(q.canonical())
    assert not ok and reason == "no_answer"
    print("T4: ok")


def test_t5_gate_rejects_unknown_subject():
    h = question_hash("s", "A", "src")
    q = MCQuestion(question_id=h, stem="the stem", choices=("A", "B"), answer="A",
                   source="src", subject_area="astrology", level="k-12")
    ok, reason = gate(q.canonical())
    assert not ok and "unknown_subject_area" in reason
    print("T5: ok")


def test_t6_gate_course_passes():
    course = {"name": "AP English", "subject_area": "humanities", "level": "ap-high",
              "duration_hours": 20, "voice": "awg/didactic", "sheet": "ap-stiff/standard",
              "pedagogy": "socratic", "refuses": []}
    ok, reason = gate_course(course)
    assert ok, reason
    print(f"T6: ok")


def test_t7_gate_course_rejects_refuses():
    course = {"name": "Bad", "subject_area": "medicine", "level": "professional",
              "duration_hours": 10, "voice": "v1", "sheet": "s1", "pedagogy": "didactic",
              "refuses": ["homeopathy"], "description": "This covers homeopathy in detail."}
    ok, reason = gate_course(course)
    assert not ok and "refuses_violated" in reason
    print("T7: ok")


def test_t8_gate_course_no_voice():
    course = {"name": "X", "subject_area": "math", "level": "k-12",
              "duration_hours": 10, "voice": "", "sheet": "s1", "pedagogy": "socratic"}
    ok, reason = gate_course(course)
    assert not ok and reason == "no_voice"
    print("T8: ok")


def test_t9_ingest_csv():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write("question,A,B,C,D,answer,explanation\n")
        f.write("What is 2+2?,2,3,4,5,C,addition\n")
        f.write("Capital of France?,London,Paris,Berlin,Madrid,B,country\n")
        path = f.name
    try:
        qs = ingest_csv(path, subject_area="math", level="k-12")
        assert len(qs) == 2
        assert qs[0].answer == "C"
        assert qs[0].question_id != qs[1].question_id
        print(f"T9: ok ({len(qs)} questions)")
    finally:
        os.unlink(path)


def test_t10_ingest_php():
    path = HERE / "examples" / "AP-English-test-1.php"
    if not path.is_file():
        print(f"T10: skip (no sample PHP at {path})")
        return
    qs = ingest_php_test_page(str(path))
    assert len(qs) >= 5, f"expected >= 5 questions, got {len(qs)}"
    for q in qs:
        assert q.answer in ["A", "B", "C", "D"]
    print(f"T10: ok ({len(qs)} questions)")


def main():
    test_t1_question_hash_deterministic()
    test_t2_mcquestion_canonical()
    test_t3_gate_passes_valid_question()
    test_t4_gate_rejects_no_answer()
    test_t5_gate_rejects_unknown_subject()
    test_t6_gate_course_passes()
    test_t7_gate_course_rejects_refuses()
    test_t8_gate_course_no_voice()
    test_t9_ingest_csv()
    test_t10_ingest_php()
    print("\nALL FAR_COURSES TESTS PASS (T1..T10)")


if __name__ == "__main__":
    main()
