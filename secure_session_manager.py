#!/usr/bin/env python3
"""
Secure Session Manager
Encrypts and manages browser session data securely
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import sys

# Add parent directory to path for SecureConfigManager
sys.path.append(str(Path(__file__).parent.parent))
from secure_config_manager import SecureConfigManager

logger = logging.getLogger(__name__)

class SecureSessionManager:
    """Manages encrypted browser session storage"""
    
    def __init__(self, session_dir: str = "browser_sessions"):
        self.session_dir = Path(session_dir)
        self.session_dir.mkdir(exist_ok=True)
        
        # Initialize secure config manager for session encryption
        self.secure_manager = SecureConfigManager(self.session_dir)
    
    def save_session_state(self, session_data: Dict[str, Any], session_name: str = "mymama_session") -> bool:
        """Save encrypted browser session state"""
        try:
            session_subdir = self.session_dir / session_name
            session_subdir.mkdir(exist_ok=True)
            
            # Encrypt and save session data
            session_file = session_subdir / "session.enc"
            success = self.secure_manager.encrypt_config(session_data)
            
            if success:
                # Move encrypted file to correct location
                encrypted_file = self.session_dir / "config.enc"
                if encrypted_file.exists():
                    encrypted_file.rename(session_file)
                    
                # Secure permissions
                os.chmod(session_file, 0o600)
                os.chmod(session_subdir, 0o700)
                
                # Remove old plaintext session if it exists
                old_session = session_subdir / "session.json"
                if old_session.exists():
                    old_session.unlink()
                    logger.info(f"Removed old plaintext session file: {old_session}")
                
                logger.info(f"✅ Session state encrypted and saved to {session_file}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to save encrypted session: {e}")
            return False
    
    def load_session_state(self, session_name: str = "mymama_session") -> Optional[Dict[str, Any]]:
        """Load encrypted browser session state"""
        try:
            session_subdir = self.session_dir / session_name
            session_file = session_subdir / "session.enc"
            
            if not session_file.exists():
                # Try to migrate existing plaintext session
                old_session = session_subdir / "session.json"
                if old_session.exists():
                    logger.info(f"Migrating plaintext session to encrypted format: {old_session}")
                    with open(old_session, 'r') as f:
                        session_data = json.load(f)
                    
                    if self.save_session_state(session_data, session_name):
                        return session_data
                
                logger.warning(f"No encrypted session found: {session_file}")
                return None
            
            # Temporarily move encrypted file for decryption
            temp_encrypted = self.session_dir / "config.enc"
            session_file.rename(temp_encrypted)
            
            try:
                session_data = self.secure_manager.decrypt_config()
                if session_data:
                    logger.info(f"✅ Session state decrypted successfully from {session_file}")
                    return session_data
            finally:
                # Move file back
                if temp_encrypted.exists():
                    temp_encrypted.rename(session_file)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to load encrypted session: {e}")
            return None
    
    def migrate_existing_sessions(self) -> bool:
        """Migrate all existing plaintext sessions to encrypted format"""
        try:
            migrated_count = 0
            
            for session_dir in self.session_dir.iterdir():
                if session_dir.is_dir():
                    plaintext_session = session_dir / "session.json"
                    encrypted_session = session_dir / "session.enc"
                    
                    if plaintext_session.exists() and not encrypted_session.exists():
                        logger.info(f"Migrating session: {session_dir.name}")
                        
                        with open(plaintext_session, 'r') as f:
                            session_data = json.load(f)
                        
                        if self.save_session_state(session_data, session_dir.name):
                            migrated_count += 1
                            logger.info(f"✅ Migrated {session_dir.name}")
                        else:
                            logger.error(f"❌ Failed to migrate {session_dir.name}")
            
            logger.info(f"Migration completed: {migrated_count} sessions migrated")
            return True
            
        except Exception as e:
            logger.error(f"Session migration failed: {e}")
            return False
    
    def secure_session_directory(self) -> bool:
        """Secure permissions on session directory and files"""
        try:
            # Secure main session directory
            os.chmod(self.session_dir, 0o700)
            
            # Secure all session subdirectories and files
            for session_dir in self.session_dir.iterdir():
                if session_dir.is_dir():
                    os.chmod(session_dir, 0o700)
                    
                    for session_file in session_dir.iterdir():
                        if session_file.is_file():
                            os.chmod(session_file, 0o600)
            
            logger.info(f"✅ Secured permissions for {self.session_dir}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to secure session directory: {e}")
            return False

def main():
    """CLI for managing encrypted sessions"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Secure Session Manager")
    parser.add_argument('--migrate', action='store_true', help="Migrate plaintext sessions to encrypted format")
    parser.add_argument('--secure', action='store_true', help="Secure session directory permissions")
    parser.add_argument('--session-dir', help="Session directory", default="browser_sessions")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    manager = SecureSessionManager(args.session_dir)
    
    if args.migrate:
        success = manager.migrate_existing_sessions()
        if success:
            print("✅ Session migration completed")
        else:
            print("❌ Session migration failed")
            return 1
    
    if args.secure:
        success = manager.secure_session_directory()
        if success:
            print("✅ Session directory secured")
        else:
            print("❌ Failed to secure session directory")
            return 1
    
    if not args.migrate and not args.secure:
        parser.print_help()
    
    return 0

if __name__ == "__main__":
    exit(main())