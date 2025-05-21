"""Test cases for the workflow module."""
import json
import os
import unittest
from unittest.mock import patch, MagicMock

import pytest

from workflow import (
    whisper_transcribe,
    _chat,
    node_replace,
    node_speaker_separation,
    node_company_check,
    node_approach_check,
    node_longcall_check,
    node_customer_reaction,
    node_manner_check,
    node_to_json,
    run_workflow,
    run_pipeline
)


class TestWorkflow(unittest.TestCase):
    """Test cases for workflow module functions."""

    @patch('workflow.openai.audio.transcriptions.create')
    def test_whisper_transcribe(self, mock_whisper):
        """Test the whisper_transcribe function."""
        # モックの戻り値を設定
        mock_response = MagicMock()
        mock_response.text = "これはテスト文字起こしです。"
        mock_whisper.return_value = mock_response

        # テスト
        result = whisper_transcribe(b'dummy_audio_bytes')
        
        # 検証
        mock_whisper.assert_called_once()
        self.assertEqual(result, "これはテスト文字起こしです。")

    @patch('workflow.openai.chat.completions.create')
    def test_chat(self, mock_chat):
        """Test the _chat function."""
        # モックの戻り値を設定
        mock_response = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "テスト応答"
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_chat.return_value = mock_response

        # テスト
        result = _chat("システムプロンプト", "ユーザープロンプト")
        
        # 検証
        mock_chat.assert_called_once()
        self.assertEqual(result, "テスト応答")

    @patch('workflow.run_workflow')
    @patch('workflow.whisper_transcribe')
    def test_run_pipeline(self, mock_whisper, mock_workflow):
        """Test the run_pipeline function."""
        # モックの戻り値を設定
        mock_whisper.return_value = "テスト文字起こし"
        mock_workflow.return_value = {"評価": "A"}

        # テスト
        result = run_pipeline(b'dummy_audio_bytes')
        
        # 検証
        mock_whisper.assert_called_once_with(b'dummy_audio_bytes')
        mock_workflow.assert_called_once_with("テスト文字起こし")
        self.assertEqual(result, {"評価": "A"})


@pytest.mark.parametrize(
    "node_func,expected_result",
    [
        (node_replace, "整形されたテキスト"),
        (node_speaker_separation, "営業担当: テスト\nお客様: 返答"),
        (node_company_check, '{"自社名明示": true}'),
        (node_approach_check, '{"ニーズ把握": 4}'),
        (node_longcall_check, '{"通話時間の適切さ": "適切"}'),
        (node_customer_reaction, '{"興味レベル": "高"}'),
        (node_manner_check, '{"敬語": 5}'),
    ]
)
@patch('workflow._chat')
def test_node_functions(mock_chat, node_func, expected_result):
    """Test all node functions with parameterization."""
    # モックの戻り値を設定
    mock_chat.return_value = expected_result
    
    # テスト
    result = node_func("テスト入力")
    
    # 検証
    assert result == expected_result
    mock_chat.assert_called_once()


if __name__ == '__main__':
    unittest.main() 