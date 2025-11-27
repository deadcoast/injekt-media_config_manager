"""Tests for InputHandler."""

from pathlib import Path
from io import StringIO
from unittest.mock import patch, MagicMock
from rich.console import Console

from injekt.cli.input import InputHandler


def test_prompt_for_input_basic():
    """Test basic input prompting."""
    handler = InputHandler()
    
    with patch('rich.prompt.Prompt.ask', return_value="test input"):
        result = handler.prompt_for_input("Enter value")
        assert result == "test input"


def test_prompt_for_input_with_default():
    """Test input prompting with default value."""
    handler = InputHandler()
    
    with patch('rich.prompt.Prompt.ask', return_value="default"):
        result = handler.prompt_for_input("Enter value", default="default")
        assert result == "default"


def test_prompt_for_input_with_validation():
    """Test input prompting with validation."""
    handler = InputHandler()
    
    def validator(value: str) -> bool:
        return len(value) > 3
    
    # Mock to return invalid then valid input
    with patch('rich.prompt.Prompt.ask', side_effect=["ab", "abcd"]):
        result = handler.prompt_for_input(
            "Enter value",
            validator=validator,
            error_message="Too short"
        )
        assert result == "abcd"


def test_prompt_for_confirmation_yes():
    """Test confirmation prompt with yes response."""
    handler = InputHandler()
    
    with patch('rich.prompt.Confirm.ask', return_value=True):
        result = handler.prompt_for_confirmation("Proceed?")
        assert result is True


def test_prompt_for_confirmation_no():
    """Test confirmation prompt with no response."""
    handler = InputHandler()
    
    with patch('rich.prompt.Confirm.ask', return_value=False):
        result = handler.prompt_for_confirmation("Proceed?", default=False)
        assert result is False


def test_prompt_for_path_basic(tmp_path):
    """Test path prompting with existing path."""
    handler = InputHandler()
    test_dir = tmp_path / "test"
    test_dir.mkdir()
    
    with patch('rich.prompt.Prompt.ask', return_value=str(test_dir)):
        result = handler.prompt_for_path("Enter path", must_exist=True)
        assert result == test_dir


def test_prompt_for_path_must_be_dir(tmp_path):
    """Test path prompting requiring directory."""
    handler = InputHandler()
    test_dir = tmp_path / "test"
    test_dir.mkdir()
    test_file = tmp_path / "file.txt"
    test_file.write_text("test")
    
    # First return file (invalid), then directory (valid)
    with patch('rich.prompt.Prompt.ask', side_effect=[str(test_file), str(test_dir)]):
        result = handler.prompt_for_path("Enter path", must_exist=True, must_be_dir=True)
        assert result == test_dir


def test_prompt_for_path_must_be_file(tmp_path):
    """Test path prompting requiring file."""
    handler = InputHandler()
    test_file = tmp_path / "file.txt"
    test_file.write_text("test")
    
    with patch('rich.prompt.Prompt.ask', return_value=str(test_file)):
        result = handler.prompt_for_path("Enter path", must_exist=True, must_be_file=True)
        assert result == test_file


def test_prompt_for_choice_by_number():
    """Test choice prompting with number selection."""
    handler = InputHandler()
    choices = ["option1", "option2", "option3"]
    
    with patch('rich.prompt.Prompt.ask', return_value="2"):
        result = handler.prompt_for_choice("Select option", choices)
        assert result == "option2"


def test_prompt_for_choice_by_name():
    """Test choice prompting with name selection."""
    handler = InputHandler()
    choices = ["option1", "option2", "option3"]
    
    with patch('rich.prompt.Prompt.ask', return_value="option1"):
        result = handler.prompt_for_choice("Select option", choices)
        assert result == "option1"


def test_prompt_for_choice_invalid_then_valid():
    """Test choice prompting with invalid then valid input."""
    handler = InputHandler()
    choices = ["option1", "option2"]
    
    # First invalid (out of range), then valid
    with patch('rich.prompt.Prompt.ask', side_effect=["5", "1"]):
        result = handler.prompt_for_choice("Select option", choices)
        assert result == "option1"


def test_prompt_for_choice_with_default():
    """Test choice prompting with default value."""
    handler = InputHandler()
    choices = ["option1", "option2"]
    
    with patch('rich.prompt.Prompt.ask', return_value="option1"):
        result = handler.prompt_for_choice("Select option", choices, default="option1")
        assert result == "option1"
