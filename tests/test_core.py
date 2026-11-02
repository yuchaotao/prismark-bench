from prismark.generate.generator import SPLITS, _iban_check, _luhn_complete, generate
from prismark.generate.llm_templates import check_patterns, check_syntax
from prismark.metrics import Prediction, redact_with_spans, score, value_leaked
from prismark.schema import Example, Span
from prismark.taxonomy import LABELS, NEGATIVE_LABELS


def test_generated_spans_are_exact_and_labeled():
    examples = generate(n_per_template=3, seed=1)
    assert examples
    for ex in examples:
        for s in ex.spans:
            assert s.label in LABELS
            assert not ex.text[s.start : s.end].lower().startswith(("a ", "an ", "the "))
            assert ex.text[s.start : s.end] and ex.text[s.start : s.end] == ex.text[s.start : s.end].strip()
        for s in ex.negatives:
            assert s.label in NEGATIVE_LABELS


def test_generation_is_deterministic():
    a = [e.to_dict() for e in generate(n_per_template=2, seed=7)]
    b = [e.to_dict() for e in generate(n_per_template=2, seed=7)]
    assert a == b


def test_splits_share_no_templates():
    ids = {split: {e.id.rsplit("-", 1)[0] for e in generate(split, n_per_template=1)} for split in SPLITS}
    assert ids["dev"] and ids["test"]
    assert not ids["dev"] & ids["test"]


def test_llm_template_validators():
    assert check_syntax("Hi {PERSON_NAME}, your {HEALTH} results are in.", ["PERSON_NAME"]) is None
    assert check_syntax("Hi {PERSON_NAME}, from {FOO}.", []) == "unknown slot FOO"
    assert check_syntax("Hi {PERSON_NAME} and {PERSON_NAME@2}.", ["PERSON_NAME@2"]) is None
    assert check_syntax("Hi {PERSON_NAME}.", []) == "fewer than two private slots"
    assert check_syntax("Hi {PERSON_NAME, {HEALTH}.", []) == "malformed braces"
    assert check_syntax("{PERSON_NAME} is a {POLITICAL}.", []) == "article before a phrase slot"
    assert check_syntax("{PERSON_NAME} has no {CRIMINAL} record.", []) == "article before a phrase slot"
    assert check_patterns("Call {FIRST_NAME} at 555-123-4567 about {HEALTH}.") == "literal PHONE"
    assert check_patterns("Order {!ORDER_ID} for {PERSON_NAME}.") is None
    assert check_patterns("{PERSON_NAME} applied for 123 Main Street.") == "literal street address"
    assert check_syntax("{FIRST_NAME}@2 met {PERSON_NAME}.", []) == "malformed braces"


def test_luhn():
    assert _luhn_complete("411111111111111") == "4111111111111111"


def test_iban_check_digits():
    # Example IBAN from the ISO 13616 / ECBS documentation.
    assert _iban_check("DE", "370400440532013000") == "89"


def _example():
    text = "Call Avery Okafor at 555-0100 about order 123-456-7890."
    return Example(
        id="x",
        text=text,
        spans=[Span(5, 17, "PERSON_NAME"), Span(21, 29, "PHONE")],
        negatives=[Span(42, 54, "DECOY_NUMBER")],
    )


def test_perfect_prediction():
    ex = _example()
    s = score([ex], {"x": Prediction(spans=list(ex.spans))})
    assert s["protected_recall"] == 1.0
    assert s["char_precision"] == 1.0
    assert s["negative_fp_rate"] == 0.0
    assert s["leakage_rate"] == 0.0
    assert s["utility"] == 1.0


def test_partial_name_is_not_protected():
    ex = _example()
    s = score([ex], {"x": Prediction(spans=[Span(5, 10, "PERSON_NAME"), Span(21, 29, "PHONE")])})
    assert s["protected_recall"] == 0.5
    assert s["overlap_recall"] == 1.0
    assert s["leakage_rate"] == 0.0  # the full name no longer appears verbatim...
    assert s["fragment_leakage_rate"] == 0.5  # ...but the surname does
    assert s["by_label"]["PERSON_NAME"] == 0.0


def test_over_redaction_hits_negatives():
    ex = _example()
    s = score([ex], {"x": Prediction(spans=list(ex.spans) + [Span(42, 54, "PHONE")])})
    assert s["negative_fp_rate"] == 1.0
    assert s["negative_keep"] == 0.0


def test_leak_detection_handles_reformatting():
    assert value_leaked("123-45-6789", "ssn is 123 45 6789")
    assert not value_leaked("HIV", "he lives in Ohio")
    assert redact_with_spans("ab cd", [Span(0, 2, "X")]) == "<PII> cd"
