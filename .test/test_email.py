import pytest
import sys
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
from db import adduser

def test_validate_email_format():
    # Test valid email
    valid_email = "test.email@example.com"
    try:
        adduser("Test User", "25", "1234567890", valid_email, "password123")
        assert False, "Expected ValueError for valid email"
    except ValueError:
        pass

    # Test invalid email (missing domain)
    invalid_email_missing_domain = "test.email@example"
    try:
        adduser("Test User", "25", "1234567890", invalid_email_missing_domain, "password123")
        assert False, "Expected ValueError for invalid email (missing domain)"
    except ValueError:
        pass

    # Test invalid email (missing @ symbol)
    invalid_email_missing_at = "test.email.example.com"
    try:
        adduser("Test User", "25", "1234567890", invalid_email_missing_at, "password123")
        assert False, "Expected ValueError for invalid email (missing @ symbol)"
    except ValueError:
        pass

    # Test invalid email (missing top-level domain)
    invalid_email_missing_tld = "test.email@example"
    try:
        adduser("Test User", "25", "1234567890", invalid_email_missing_tld, "password123")
        assert False, "Expected ValueError for invalid email (missing top-level domain)"
    except ValueError:
        pass