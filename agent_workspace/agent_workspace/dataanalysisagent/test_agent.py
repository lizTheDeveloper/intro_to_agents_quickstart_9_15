import pytest
from pathlib import Path
import json

# Add these tests below in test_agent.py
def test_data_analysis_agent():
    # Test 1: Verify the agent can process local datasets
    result = analyze_data(
        analysis_technique="descriptive statistics",
        data_source="test.csv",
        output_file="output/test_stats.txt"
    )
    assert result.startswith("Analysis complete:")
    assert Path("output/test_stats.txt").exists()

    # Test 2: Validate linear regression functionality
    result = analyze_data(
        analysis_technique="linear_regression",
        data_source="test.csv",
        output_file="output/test_regression.txt"
    )
    assert Path("output/test_regression.txt").exists()
    with open("output/test_regression.txt") as f:
        data = json.loads(f.read())
        assert "R_squared" in data
        assert 0 <= data["R_squared"] <= 1

    # Test 3: Verify web dataset processing
    result = analyze_data(
        analysis_technique="time series forecasting",
        data_source="https://example.com/synthetic-time-series.csv",
        output_file="output/test_web_analysis.txt"
    )
    assert "Analysis error" not in result

    # Test 4: Validate audit logging
    assert Path("analysis_log.txt").exists()
    log_content = Path("analysis_log.txt").read_text()
    assert "Started analysis" in log_content
    assert "Analysis completed" in log_content

    # Test 5: File management operations
    assert Path("methodology.txt").exists()
    assert "Data Validation" in Path("methodology.txt").read_text()

    # Clean up test files
    for f in Path("output").glob("*.txt"):
        f.unlink()
    
    assert not any(Path("output").glob("*.txt"))