"""Tests for interactive mode."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path

from injekt.cli.interactive import InteractiveMode
from injekt.cli.input import InputHandler
from injekt.cli.output import OutputFormatter


class TestInteractiveMode:
    """Test suite for InteractiveMode class."""
    
    @pytest.fixture
    def mock_input_handler(self):
        """Create a mock input handler."""
        return Mock(spec=InputHandler)
    
    @pytest.fixture
    def mock_output_formatter(self):
        """Create a mock output formatter."""
        formatter = Mock(spec=OutputFormatter)
        formatter.console = Mock()
        return formatter
    
    @pytest.fixture
    def mock_commands(self):
        """Create mock command instances."""
        commands = {}
        for cmd_name in ["list", "install", "verify", "uninstall", "info", 
                        "report", "rollback", "update", "profile_list", 
                        "profile_switch", "export", "import"]:
            mock_cmd = Mock()
            mock_cmd.execute = Mock(return_value=0)
            commands[cmd_name] = mock_cmd
        return commands
    
    @pytest.fixture
    def interactive_mode(self, mock_input_handler, mock_output_formatter, mock_commands):
        """Create an InteractiveMode instance."""
        return InteractiveMode(
            input_handler=mock_input_handler,
            output_formatter=mock_output_formatter,
            commands=mock_commands
        )
    
    def test_initialization(self, interactive_mode, mock_input_handler, 
                           mock_output_formatter, mock_commands):
        """Test that InteractiveMode initializes correctly."""
        assert interactive_mode.input_handler == mock_input_handler
        assert interactive_mode.output_formatter == mock_output_formatter
        assert interactive_mode.commands == mock_commands
        assert interactive_mode.console == mock_output_formatter.console
    
    def test_run_exits_on_exit_choice(self, interactive_mode, mock_input_handler):
        """Test that run() exits when user selects Exit."""
        # Mock user selecting Exit immediately
        mock_input_handler.prompt_for_choice.return_value = "Exit"
        
        exit_code = interactive_mode.run()
        
        assert exit_code == 0
        mock_input_handler.prompt_for_choice.assert_called_once()
    
    def test_run_executes_list_action(self, interactive_mode, mock_input_handler, mock_commands):
        """Test that run() executes list packages action."""
        # Mock user selecting List packages then Exit
        mock_input_handler.prompt_for_choice.side_effect = ["List packages", "Exit"]
        mock_input_handler.prompt_for_confirmation.return_value = True
        
        exit_code = interactive_mode.run()
        
        assert exit_code == 0
        mock_commands["list"].execute.assert_called_once()
    
    def test_run_executes_install_action(self, interactive_mode, mock_input_handler, mock_commands):
        """Test that run() executes install package action with prompts."""
        # Mock user selecting Install package then Exit
        mock_input_handler.prompt_for_choice.side_effect = ["Install package", "Exit"]
        mock_input_handler.prompt_for_input.return_value = "test-package"
        mock_input_handler.prompt_for_confirmation.side_effect = [True, True]  # Confirm install, then continue
        
        exit_code = interactive_mode.run()
        
        assert exit_code == 0
        mock_commands["install"].execute.assert_called_once_with("test-package")
    
    def test_run_executes_verify_action(self, interactive_mode, mock_input_handler, mock_commands):
        """Test that run() executes verify installation action."""
        # Mock user selecting Verify installation then Exit
        mock_input_handler.prompt_for_choice.side_effect = ["Verify installation", "Exit"]
        mock_input_handler.prompt_for_input.return_value = "test-package"
        mock_input_handler.prompt_for_confirmation.return_value = True
        
        exit_code = interactive_mode.run()
        
        assert exit_code == 0
        mock_commands["verify"].execute.assert_called_once_with("test-package")
    
    def test_run_executes_uninstall_action(self, interactive_mode, mock_input_handler, mock_commands):
        """Test that run() executes uninstall package action."""
        # Mock user selecting Uninstall package then Exit
        mock_input_handler.prompt_for_choice.side_effect = ["Uninstall package", "Exit"]
        mock_input_handler.prompt_for_input.return_value = "test-package"
        mock_input_handler.prompt_for_confirmation.side_effect = [True, True]  # Confirm uninstall, then continue
        
        exit_code = interactive_mode.run()
        
        assert exit_code == 0
        mock_commands["uninstall"].execute.assert_called_once_with("test-package")
    
    def test_run_executes_info_action(self, interactive_mode, mock_input_handler, mock_commands):
        """Test that run() executes show package info action."""
        # Mock user selecting Show package info then Exit
        mock_input_handler.prompt_for_choice.side_effect = ["Show package info", "Exit"]
        mock_input_handler.prompt_for_input.return_value = "test-package"
        mock_input_handler.prompt_for_confirmation.return_value = True
        
        exit_code = interactive_mode.run()
        
        assert exit_code == 0
        mock_commands["info"].execute.assert_called_once_with("test-package")
    
    def test_run_executes_report_action(self, interactive_mode, mock_input_handler, mock_commands):
        """Test that run() executes generate report action."""
        # Mock user selecting Generate report then Exit
        mock_input_handler.prompt_for_choice.side_effect = ["Generate report", "Exit"]
        mock_input_handler.prompt_for_confirmation.return_value = True
        
        exit_code = interactive_mode.run()
        
        assert exit_code == 0
        mock_commands["report"].execute.assert_called_once()
    
    def test_run_executes_rollback_action(self, interactive_mode, mock_input_handler, mock_commands):
        """Test that run() executes rollback configuration action."""
        # Mock user selecting Rollback configuration then Exit
        mock_input_handler.prompt_for_choice.side_effect = ["Rollback configuration", "Exit"]
        mock_input_handler.prompt_for_confirmation.return_value = True
        
        exit_code = interactive_mode.run()
        
        assert exit_code == 0
        mock_commands["rollback"].execute.assert_called_once()
    
    def test_run_executes_update_action(self, interactive_mode, mock_input_handler, mock_commands):
        """Test that run() executes update package action."""
        # Mock user selecting Update package then Exit
        mock_input_handler.prompt_for_choice.side_effect = ["Update package", "Exit"]
        mock_input_handler.prompt_for_input.return_value = "test-package"
        mock_input_handler.prompt_for_confirmation.return_value = True
        
        exit_code = interactive_mode.run()
        
        assert exit_code == 0
        mock_commands["update"].execute.assert_called_once_with("test-package")
    
    def test_run_executes_profile_list_action(self, interactive_mode, mock_input_handler, mock_commands):
        """Test that run() executes profile list action."""
        # Mock user selecting Manage profiles -> List profiles then Exit
        mock_input_handler.prompt_for_choice.side_effect = [
            "Manage profiles",
            "List profiles",
            "Exit"
        ]
        mock_input_handler.prompt_for_confirmation.return_value = True
        
        exit_code = interactive_mode.run()
        
        assert exit_code == 0
        mock_commands["profile_list"].execute.assert_called_once()
    
    def test_run_executes_profile_switch_action(self, interactive_mode, mock_input_handler, mock_commands):
        """Test that run() executes profile switch action."""
        # Mock user selecting Manage profiles -> Switch profile then Exit
        mock_input_handler.prompt_for_choice.side_effect = [
            "Manage profiles",
            "Switch profile",
            "Exit"
        ]
        mock_input_handler.prompt_for_input.return_value = "performance"
        mock_input_handler.prompt_for_confirmation.return_value = True
        
        exit_code = interactive_mode.run()
        
        assert exit_code == 0
        mock_commands["profile_switch"].execute.assert_called_once_with("performance")
    
    def test_run_executes_export_action(self, interactive_mode, mock_input_handler, mock_commands):
        """Test that run() executes export configuration action."""
        # Mock user selecting Export configuration then Exit
        mock_input_handler.prompt_for_choice.side_effect = ["Export configuration", "Exit"]
        mock_input_handler.prompt_for_path.return_value = Path("/tmp/export")
        mock_input_handler.prompt_for_confirmation.side_effect = [True, True]  # Confirm export, then continue
        
        exit_code = interactive_mode.run()
        
        assert exit_code == 0
        mock_commands["export"].execute.assert_called_once_with(Path("/tmp/export"))
    
    def test_run_executes_import_action(self, interactive_mode, mock_input_handler, mock_commands):
        """Test that run() executes import configuration action."""
        # Mock user selecting Import configuration then Exit
        mock_input_handler.prompt_for_choice.side_effect = ["Import configuration", "Exit"]
        mock_input_handler.prompt_for_path.return_value = Path("/tmp/import")
        mock_input_handler.prompt_for_confirmation.side_effect = [True, True]  # Confirm import, then continue
        
        exit_code = interactive_mode.run()
        
        assert exit_code == 0
        mock_commands["import"].execute.assert_called_once_with(Path("/tmp/import"))
    
    def test_run_handles_keyboard_interrupt_continue(self, interactive_mode, mock_input_handler, mock_commands):
        """Test that run() handles KeyboardInterrupt and continues to menu."""
        # Mock user triggering KeyboardInterrupt, then choosing to continue, then Exit
        mock_input_handler.prompt_for_choice.side_effect = ["List packages", "Exit"]
        mock_commands["list"].execute.side_effect = KeyboardInterrupt()
        mock_input_handler.prompt_for_confirmation.side_effect = [True, True]  # Return to menu, then continue
        
        exit_code = interactive_mode.run()
        
        assert exit_code == 0
    
    def test_run_handles_keyboard_interrupt_exit(self, interactive_mode, mock_input_handler, mock_commands):
        """Test that run() handles KeyboardInterrupt and exits."""
        # Mock user triggering KeyboardInterrupt, then choosing to exit
        mock_input_handler.prompt_for_choice.return_value = "List packages"
        mock_commands["list"].execute.side_effect = KeyboardInterrupt()
        mock_input_handler.prompt_for_confirmation.return_value = False  # Don't return to menu
        
        exit_code = interactive_mode.run()
        
        assert exit_code == 0
    
    def test_run_handles_command_errors(self, interactive_mode, mock_input_handler, 
                                       mock_commands, mock_output_formatter):
        """Test that run() handles command errors gracefully."""
        # Mock user selecting action that fails, then Exit
        mock_input_handler.prompt_for_choice.side_effect = ["List packages", "Exit"]
        mock_commands["list"].execute.return_value = 1  # Error exit code
        mock_input_handler.prompt_for_confirmation.return_value = True
        
        exit_code = interactive_mode.run()
        
        assert exit_code == 0  # Interactive mode itself succeeds
        mock_output_formatter.format_warning.assert_called()
    
    def test_install_action_cancelled_by_user(self, interactive_mode, mock_input_handler, mock_commands):
        """Test that install action can be cancelled by user."""
        # Mock user selecting Install package, entering name, then cancelling
        mock_input_handler.prompt_for_choice.side_effect = ["Install package", "Exit"]
        mock_input_handler.prompt_for_input.return_value = "test-package"
        mock_input_handler.prompt_for_confirmation.side_effect = [False, True]  # Cancel install, then continue
        
        exit_code = interactive_mode.run()
        
        assert exit_code == 0
        mock_commands["install"].execute.assert_not_called()
    
    def test_uninstall_action_cancelled_by_user(self, interactive_mode, mock_input_handler, mock_commands):
        """Test that uninstall action can be cancelled by user."""
        # Mock user selecting Uninstall package, entering name, then cancelling
        mock_input_handler.prompt_for_choice.side_effect = ["Uninstall package", "Exit"]
        mock_input_handler.prompt_for_input.return_value = "test-package"
        mock_input_handler.prompt_for_confirmation.side_effect = [False, True]  # Cancel uninstall, then continue
        
        exit_code = interactive_mode.run()
        
        assert exit_code == 0
        mock_commands["uninstall"].execute.assert_not_called()
    
    def test_export_action_cancelled_by_user(self, interactive_mode, mock_input_handler, mock_commands):
        """Test that export action can be cancelled by user."""
        # Mock user selecting Export configuration, entering path, then cancelling
        mock_input_handler.prompt_for_choice.side_effect = ["Export configuration", "Exit"]
        mock_input_handler.prompt_for_path.return_value = Path("/tmp/export")
        mock_input_handler.prompt_for_confirmation.side_effect = [False, True]  # Cancel export, then continue
        
        exit_code = interactive_mode.run()
        
        assert exit_code == 0
        mock_commands["export"].execute.assert_not_called()
    
    def test_import_action_cancelled_by_user(self, interactive_mode, mock_input_handler, mock_commands):
        """Test that import action can be cancelled by user."""
        # Mock user selecting Import configuration, entering path, then cancelling
        mock_input_handler.prompt_for_choice.side_effect = ["Import configuration", "Exit"]
        mock_input_handler.prompt_for_path.return_value = Path("/tmp/import")
        mock_input_handler.prompt_for_confirmation.side_effect = [False, True]  # Cancel import, then continue
        
        exit_code = interactive_mode.run()
        
        assert exit_code == 0
        mock_commands["import"].execute.assert_not_called()
    
    def test_profile_management_back_to_menu(self, interactive_mode, mock_input_handler, mock_commands):
        """Test that profile management can return to main menu."""
        # Mock user selecting Manage profiles -> Back to main menu -> Exit
        mock_input_handler.prompt_for_choice.side_effect = [
            "Manage profiles",
            "Back to main menu",
            "Exit"
        ]
        mock_input_handler.prompt_for_confirmation.return_value = True
        
        exit_code = interactive_mode.run()
        
        assert exit_code == 0
        mock_commands["profile_list"].execute.assert_not_called()
        mock_commands["profile_switch"].execute.assert_not_called()
