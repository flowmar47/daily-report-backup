#!/usr/bin/env python3
"""
Unit tests for SecureSessionManager
"""

import unittest
import tempfile
import shutil
import os
from pathlib import Path
import json
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from secure_session_manager import SecureSessionManager


class TestSecureSessionManager(unittest.TestCase):
    """Test SecureSessionManager functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.session_dir = Path(self.test_dir) / "sessions"
        self.session_dir.mkdir(exist_ok=True)
        self.manager = SecureSessionManager(self.session_dir)
        
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir)
        
    def test_initialization(self):
        """Test SecureSessionManager initialization"""
        self.assertEqual(self.manager.session_dir, self.session_dir)
        self.assertTrue(self.session_dir.exists())
        self.assertEqual(oct(self.session_dir.stat().st_mode)[-3:], '700')
        
    def test_save_encrypted_session(self):
        """Test saving encrypted session data"""
        session_data = {
            "cookies": [{"name": "test", "value": "cookie"}],
            "localStorage": {"key": "value"},
            "sessionStorage": {"session": "data"}
        }
        
        # Save session
        session_file = self.manager.save_encrypted_session("test_site", session_data)
        
        # Verify file exists and is encrypted
        self.assertTrue(session_file.exists())
        self.assertEqual(oct(session_file.stat().st_mode)[-3:], '600')
        
        # Verify content is encrypted (not readable as JSON)
        with open(session_file, 'rb') as f:
            content = f.read()
            self.assertGreater(len(content), 0)
            # Should not be valid JSON
            with self.assertRaises(json.JSONDecodeError):
                json.loads(content)
                
    def test_load_encrypted_session(self):
        """Test loading encrypted session data"""
        original_data = {
            "cookies": [{"name": "test", "value": "cookie"}],
            "localStorage": {"key": "value"},
            "sessionStorage": {"session": "data"}
        }
        
        # Save and load session
        self.manager.save_encrypted_session("test_site", original_data)
        loaded_data = self.manager.load_encrypted_session("test_site")
        
        # Verify loaded data matches original
        self.assertEqual(loaded_data, original_data)
        
    def test_load_nonexistent_session(self):
        """Test loading non-existent session"""
        result = self.manager.load_encrypted_session("nonexistent")
        self.assertIsNone(result)
        
    def test_clear_session(self):
        """Test clearing session data"""
        # Save a session
        session_data = {"test": "data"}
        self.manager.save_encrypted_session("test_site", session_data)
        
        # Verify it exists
        session_file = self.session_dir / "test_site_session.enc"
        self.assertTrue(session_file.exists())
        
        # Clear it
        self.manager.clear_session("test_site")
        
        # Verify it's gone
        self.assertFalse(session_file.exists())
        
    def test_clear_all_sessions(self):
        """Test clearing all sessions"""
        # Save multiple sessions
        for i in range(3):
            self.manager.save_encrypted_session(f"site_{i}", {"data": i})
            
        # Verify they exist
        sessions = list(self.session_dir.glob("*.enc"))
        self.assertEqual(len(sessions), 3)
        
        # Clear all
        self.manager.clear_all_sessions()
        
        # Verify all are gone
        sessions = list(self.session_dir.glob("*.enc"))
        self.assertEqual(len(sessions), 0)
        
    @patch('playwright.async_api.async_playwright')
    async def test_restore_browser_session(self, mock_playwright):
        """Test restoring browser session"""
        # Mock browser context
        mock_context = MagicMock()
        mock_context.add_cookies = MagicMock()
        mock_page = MagicMock()
        mock_context.new_page = MagicMock(return_value=mock_page)
        
        # Mock session data
        session_data = {
            "cookies": [{"name": "test", "value": "cookie"}],
            "localStorage": {"key": "value"},
            "sessionStorage": {"session": "data"}
        }
        
        # Save session
        self.manager.save_encrypted_session("test_site", session_data)
        
        # Restore session
        restored = await self.manager.restore_browser_session(
            mock_context, "test_site", "https://test.com"
        )
        
        # Verify restoration
        self.assertTrue(restored)
        mock_context.add_cookies.assert_called_once_with(session_data["cookies"])
        
    def test_session_rotation(self):
        """Test session rotation after threshold"""
        # Save sessions up to rotation threshold
        for i in range(10):  # Default threshold is 10
            data = {"cookies": [{"name": f"cookie_{i}", "value": str(i)}]}
            self.manager.save_encrypted_session("test_site", data)
            
        # Verify only the latest session exists
        sessions = list(self.session_dir.glob("test_site_*.enc"))
        self.assertEqual(len(sessions), 1)
        
        # Load and verify it's the latest
        loaded = self.manager.load_encrypted_session("test_site")
        self.assertEqual(loaded["cookies"][0]["name"], "cookie_9")
        
    def test_get_session_age(self):
        """Test getting session age"""
        # Save a session
        self.manager.save_encrypted_session("test_site", {"data": "test"})
        
        # Get age
        age = self.manager.get_session_age("test_site")
        
        # Should be very recent (less than 1 second)
        self.assertIsNotNone(age)
        self.assertLess(age, 1.0)
        
    def test_is_session_valid(self):
        """Test session validity check"""
        # Save a session
        self.manager.save_encrypted_session("test_site", {"data": "test"})
        
        # Should be valid (default max age is 7 days)
        self.assertTrue(self.manager.is_session_valid("test_site"))
        
        # Test with very short max age
        self.assertFalse(self.manager.is_session_valid("test_site", max_age_hours=0))
        
    def test_list_sessions(self):
        """Test listing all sessions"""
        # Save multiple sessions
        sites = ["site1", "site2", "site3"]
        for site in sites:
            self.manager.save_encrypted_session(site, {"data": site})
            
        # List sessions
        sessions = self.manager.list_sessions()
        
        # Verify all are listed
        self.assertEqual(len(sessions), 3)
        session_sites = [s["site"] for s in sessions]
        self.assertEqual(sorted(session_sites), sorted(sites))
        
        # Verify session info
        for session in sessions:
            self.assertIn("site", session)
            self.assertIn("file", session)
            self.assertIn("age_hours", session)
            self.assertIn("size_kb", session)


if __name__ == '__main__':
    unittest.main()