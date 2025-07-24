#!/usr/bin/env python3
"""
Test script for the YouTube downloader app
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import validate_url, format_duration, format_number, sanitize_filename

def test_validation():
    """Test URL validation function"""
    print("Testing URL validation...")
    
    test_cases = [
        ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", True, "video"),
        ("https://youtu.be/dQw4w9WgXcQ", True, "video"),
        ("https://www.youtube.com/playlist?list=PLXxxx", True, "playlist"),
        ("https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=PLXxxx", True, "playlist"),
        ("https://invalid-url.com", False, None),
        ("", False, None),
    ]
    
    for url, expected_valid, expected_type in test_cases:
        is_valid, message, url_type = validate_url(url)
        assert is_valid == expected_valid, f"Failed for {url}: expected {expected_valid}, got {is_valid}"
        if expected_valid:
            assert url_type == expected_type, f"Failed type for {url}: expected {expected_type}, got {url_type}"
        print(f"✅ {url[:50]}... - {message}")

def test_formatters():
    """Test formatting functions"""
    print("\nTesting formatting functions...")
    
    # Test duration formatting
    assert format_duration(3661) == "1h 1m 1s"
    assert format_duration(61) == "1m 1s"
    assert format_duration(30) == "30s"
    assert format_duration(0) == "Unknown"
    print("✅ Duration formatting works")
    
    # Test number formatting
    assert format_number(1500) == "1.5K"
    assert format_number(1500000) == "1.5M"
    assert format_number(1500000000) == "1.5B"
    assert format_number(500) == "500"
    print("✅ Number formatting works")
    
    # Test filename sanitization
    problematic_name = 'Test<>:"/\\|?*Video'
    sanitized = sanitize_filename(problematic_name)
    assert "<" not in sanitized and ">" not in sanitized
    print("✅ Filename sanitization works")

def test_imports():
    """Test that all required packages are available"""
    print("\nTesting imports...")
    
    try:
        import streamlit
        print("✅ Streamlit available")
    except ImportError:
        print("❌ Streamlit not available")
        return False
    
    try:
        import yt_dlp
        print("✅ yt-dlp available")
    except ImportError:
        print("❌ yt-dlp not available")
        return False
    
    return True

if __name__ == "__main__":
    print("🧪 Running tests for YouTube Downloader App\n")
    
    # Test imports first
    if not test_imports():
        print("\n❌ Some required packages are missing!")
        sys.exit(1)
    
    # Run other tests
    try:
        test_validation()
        test_formatters()
        print("\n🎉 All tests passed!")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
