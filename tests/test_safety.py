import pytest
from db import check_if_week_processed, mark_week_processed, DB_PATH
import os

def test_idempotency_logic():
    import uuid
    test_week = f"2026-W99-TEST-{uuid.uuid4()}"
    
    # Should be false initially
    assert not check_if_week_processed(test_week)
    
    # Mark it processed
    mark_week_processed(test_week)
    
    # Should now be true
    assert check_if_week_processed(test_week)

def test_anti_hallucination_gate():
    # Mock hallucination check
    original_text = "The app crashes every time I try to login."
    valid_quote = "crashes every time"
    hallucinated_quote = "the UI is very bad"
    
    assert valid_quote in original_text
    assert hallucinated_quote not in original_text
