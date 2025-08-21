#!/usr/bin/env python3
"""
Enhanced Secure Session Manager
Advanced session management with intelligent caching, encryption, and rotation
"""

import os
import json
import logging
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import hashlib
import sys

# Add parent directory to path for SecureConfigManager
sys.path.append(str(Path(__file__).parent.parent))
from secure_config_manager import SecureConfigManager
from intelligent_cache import IntelligentCache, CacheEntryType, get_cache

logger = logging.getLogger(__name__)

class SessionInfo:
    """Session information and metadata"""
    
    def __init__(self, session_name: str, data: Dict[str, Any]):
        self.session_name = session_name
        self.data = data
        self.created_at = datetime.now()
        self.last_used = datetime.now()
        self.use_count = 0
        self.version = 1
        self.checksum = self._calculate_checksum(data)
    
    def _calculate_checksum(self, data: Dict[str, Any]) -> str:
        """Calculate checksum for session data integrity"""
        data_str = json.dumps(data, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(data_str.encode()).hexdigest()[:16]
    
    def mark_used(self):
        """Mark session as used"""
        self.last_used = datetime.now()
        self.use_count += 1
    
    def is_expired(self, max_age_hours: int = 24) -> bool:
        """Check if session has expired"""
        age = datetime.now() - self.created_at
        return age > timedelta(hours=max_age_hours)
    
    def needs_rotation(self, max_uses: int = 50) -> bool:
        """Check if session needs rotation"""
        return self.use_count >= max_uses
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'session_name': self.session_name,
            'data': self.data,
            'created_at': self.created_at.isoformat(),
            'last_used': self.last_used.isoformat(),
            'use_count': self.use_count,
            'version': self.version,
            'checksum': self.checksum
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionInfo':
        """Create SessionInfo from dictionary"""
        session_info = cls(data['session_name'], data['data'])
        session_info.created_at = datetime.fromisoformat(data['created_at'])
        session_info.last_used = datetime.fromisoformat(data['last_used'])
        session_info.use_count = data.get('use_count', 0)
        session_info.version = data.get('version', 1)
        session_info.checksum = data.get('checksum', session_info.checksum)
        return session_info

class EnhancedSessionManager:
    """Advanced session manager with caching, encryption, and intelligent rotation"""
    
    def __init__(self, session_dir: str = "browser_sessions", config: Dict[str, Any] = None):
        self.session_dir = Path(session_dir)
        self.session_dir.mkdir(exist_ok=True)
        
        self.config = config or {}
        
        # Session configuration
        self.max_session_age_hours = self.config.get('max_session_age_hours', 24)
        self.max_session_uses = self.config.get('max_session_uses', 50)
        self.session_rotation_threshold = self.config.get('rotation_threshold', 0.8)  # 80%
        self.max_cached_sessions = self.config.get('max_cached_sessions', 10)
        
        # Initialize secure config manager for session encryption
        self.secure_manager = SecureConfigManager(self.session_dir)
        
        # Initialize intelligent cache
        cache_config = {
            'max_memory_entries': self.config.get('cache_max_entries', 100),
            'max_memory_size_mb': self.config.get('cache_max_size_mb', 50),
            'session_ttl': self.config.get('session_cache_ttl', 3600),  # 1 hour in cache
            'cache_dir': str(self.session_dir / 'cache')
        }
        self.cache = get_cache(cache_config)
        
        # Session pool for rotation
        self.active_sessions: Dict[str, SessionInfo] = {}
        self.session_lock = asyncio.Lock()
        
        logger.info(f"🔐 Enhanced session manager initialized - Dir: {self.session_dir}")
    
    async def save_session_state(self, session_data: Dict[str, Any], 
                                session_name: str = "mymama_session") -> bool:
        """Save encrypted browser session state with caching"""
        try:
            async with self.session_lock:
                # Create session info
                session_info = SessionInfo(session_name, session_data)
                
                # Save to cache for fast access
                cache_key = f"session_{session_name}"
                await self.cache.set(
                    "sessions", 
                    cache_key, 
                    session_info.to_dict(),
                    entry_type=CacheEntryType.SESSION_DATA,
                    ttl=self.config.get('session_cache_ttl', 3600)
                )
                
                # Update active sessions
                self.active_sessions[session_name] = session_info
                
                # Encrypt and save to disk
                success = await self._save_encrypted_session(session_info)
                
                if success:
                    logger.info(f"✅ Session saved: {session_name} (version: {session_info.version})")
                    return True
                else:
                    # Remove from cache if disk save failed
                    await self.cache.delete("sessions", cache_key)
                    logger.error(f"❌ Failed to save session to disk: {session_name}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Error saving session {session_name}: {e}")
            return False
    
    async def load_session_state(self, session_name: str = "mymama_session") -> Optional[Dict[str, Any]]:
        """Load decrypted browser session state from cache or disk"""
        try:
            cache_key = f"session_{session_name}"
            
            # Try cache first
            cached_session = await self.cache.get("sessions", cache_key)
            if cached_session:
                session_info = SessionInfo.from_dict(cached_session)
                
                # Check if session is still valid
                if not session_info.is_expired(self.max_session_age_hours):
                    session_info.mark_used()
                    self.active_sessions[session_name] = session_info
                    
                    # Update cache with new usage stats
                    await self.cache.set(
                        "sessions",
                        cache_key,
                        session_info.to_dict(),
                        entry_type=CacheEntryType.SESSION_DATA,
                        ttl=self.config.get('session_cache_ttl', 3600)
                    )
                    
                    logger.debug(f"📦 Session loaded from cache: {session_name} (uses: {session_info.use_count})")
                    return session_info.data
                else:
                    # Remove expired session
                    await self._remove_session(session_name)
                    logger.info(f"🗑️ Removed expired session: {session_name}")
                    return None
            
            # Try loading from disk
            session_info = await self._load_encrypted_session(session_name)
            if session_info:
                # Check validity
                if not session_info.is_expired(self.max_session_age_hours):
                    session_info.mark_used()
                    
                    # Add to cache for future fast access
                    await self.cache.set(
                        "sessions",
                        cache_key,
                        session_info.to_dict(),
                        entry_type=CacheEntryType.SESSION_DATA,
                        ttl=self.config.get('session_cache_ttl', 3600)
                    )
                    
                    self.active_sessions[session_name] = session_info
                    logger.debug(f"💽 Session loaded from disk: {session_name}")
                    return session_info.data
                else:
                    # Remove expired session
                    await self._remove_session(session_name)
                    logger.info(f"🗑️ Removed expired disk session: {session_name}")
                    return None
            
            logger.debug(f"❌ Session not found: {session_name}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error loading session {session_name}: {e}")
            return None
    
    async def _save_encrypted_session(self, session_info: SessionInfo) -> bool:
        """Save session to encrypted disk storage"""
        try:
            session_subdir = self.session_dir / session_info.session_name
            session_subdir.mkdir(exist_ok=True)
            
            # Prepare session data with metadata
            session_data_with_metadata = {
                'session_data': session_info.data,
                'metadata': {
                    'created_at': session_info.created_at.isoformat(),
                    'last_used': session_info.last_used.isoformat(),
                    'use_count': session_info.use_count,
                    'version': session_info.version,
                    'checksum': session_info.checksum
                }
            }
            
            # Use a temporary secure manager for this session
            session_secure_manager = SecureConfigManager(session_subdir)
            success = session_secure_manager.encrypt_config(session_data_with_metadata)
            
            if success:
                # Move encrypted file to correct location
                encrypted_file = session_subdir / "config.enc"
                session_file = session_subdir / "session.enc"
                
                if encrypted_file.exists():
                    encrypted_file.rename(session_file)
                    
                    # Secure permissions
                    os.chmod(session_file, 0o600)
                    os.chmod(session_subdir, 0o700)
                    
                    # Remove old plaintext session if it exists
                    plaintext_session = session_subdir / "session.json"
                    if plaintext_session.exists():
                        plaintext_session.unlink()
                    
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error saving encrypted session: {e}")
            return False
    
    async def _load_encrypted_session(self, session_name: str) -> Optional[SessionInfo]:
        """Load session from encrypted disk storage"""
        try:
            session_subdir = self.session_dir / session_name
            session_file = session_subdir / "session.enc"
            
            if not session_file.exists():
                return None
            
            # Use a temporary secure manager for this session
            session_secure_manager = SecureConfigManager(session_subdir)
            decrypted_data = session_secure_manager.decrypt_config()
            
            if decrypted_data:
                # Extract session data and metadata
                session_data = decrypted_data.get('session_data', {})
                metadata = decrypted_data.get('metadata', {})
                
                # Create session info
                session_info = SessionInfo(session_name, session_data)
                
                # Restore metadata
                if metadata:
                    session_info.created_at = datetime.fromisoformat(metadata.get('created_at', session_info.created_at.isoformat()))
                    session_info.last_used = datetime.fromisoformat(metadata.get('last_used', session_info.last_used.isoformat()))
                    session_info.use_count = metadata.get('use_count', 0)
                    session_info.version = metadata.get('version', 1)
                    
                    # Verify checksum
                    expected_checksum = metadata.get('checksum', '')
                    if expected_checksum and expected_checksum != session_info.checksum:
                        logger.warning(f"⚠️ Session checksum mismatch for {session_name}")
                        return None
                
                return session_info
            
            return None
            
        except Exception as e:
            logger.error(f"Error loading encrypted session: {e}")
            return None
    
    async def rotate_session(self, session_name: str = "mymama_session") -> bool:
        """Rotate session by creating a new version"""
        try:
            async with self.session_lock:
                # Get current session
                current_session_data = await self.load_session_state(session_name)
                if not current_session_data:
                    logger.warning(f"⚠️ Cannot rotate non-existent session: {session_name}")
                    return False
                
                # Archive old session
                await self._archive_session(session_name)
                
                # Create new session with incremented version
                old_session = self.active_sessions.get(session_name)
                new_version = old_session.version + 1 if old_session else 1
                
                # Remove old session from cache and active sessions
                cache_key = f"session_{session_name}"
                await self.cache.delete("sessions", cache_key)
                if session_name in self.active_sessions:
                    del self.active_sessions[session_name]
                
                logger.info(f"🔄 Session rotated: {session_name} -> version {new_version}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error rotating session {session_name}: {e}")
            return False
    
    async def _archive_session(self, session_name: str):
        """Archive old session"""
        try:
            session_subdir = self.session_dir / session_name
            session_file = session_subdir / "session.enc"
            
            if session_file.exists():
                # Create archive with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                archive_file = session_subdir / f"session_archive_{timestamp}.enc"
                session_file.rename(archive_file)
                
                # Clean up old archives (keep only last 5)
                archives = sorted(session_subdir.glob("session_archive_*.enc"))
                for old_archive in archives[:-5]:
                    old_archive.unlink()
                
                logger.debug(f"📦 Archived session: {session_name}")
                
        except Exception as e:
            logger.warning(f"Error archiving session: {e}")
    
    async def _remove_session(self, session_name: str):
        """Remove session completely"""
        try:
            # Remove from cache
            cache_key = f"session_{session_name}"
            await self.cache.delete("sessions", cache_key)
            
            # Remove from active sessions
            if session_name in self.active_sessions:
                del self.active_sessions[session_name]
            
            # Remove from disk
            session_subdir = self.session_dir / session_name
            if session_subdir.exists():
                for file in session_subdir.glob("*"):
                    file.unlink()
                session_subdir.rmdir()
            
            logger.debug(f"🗑️ Removed session: {session_name}")
            
        except Exception as e:
            logger.warning(f"Error removing session: {e}")
    
    async def check_session_health(self, session_name: str = "mymama_session") -> Dict[str, Any]:
        """Check session health and recommend actions"""
        try:
            session_info = self.active_sessions.get(session_name)
            
            if not session_info:
                # Try to load from cache/disk
                await self.load_session_state(session_name)
                session_info = self.active_sessions.get(session_name)
            
            if not session_info:
                return {
                    'status': 'not_found',
                    'action': 'create_new',
                    'message': 'Session does not exist'
                }
            
            health_status = {
                'status': 'healthy',
                'action': 'none',
                'message': 'Session is healthy',
                'age_hours': (datetime.now() - session_info.created_at).total_seconds() / 3600,
                'use_count': session_info.use_count,
                'version': session_info.version,
                'last_used': session_info.last_used.isoformat()
            }
            
            # Check if expired
            if session_info.is_expired(self.max_session_age_hours):
                health_status.update({
                    'status': 'expired',
                    'action': 'rotate',
                    'message': f'Session expired (age: {health_status["age_hours"]:.1f}h)'
                })
            
            # Check if needs rotation
            elif session_info.needs_rotation(self.max_session_uses):
                health_status.update({
                    'status': 'overused',
                    'action': 'rotate',
                    'message': f'Session overused (uses: {session_info.use_count})'
                })
            
            # Check if approaching rotation threshold
            elif session_info.use_count >= (self.max_session_uses * self.session_rotation_threshold):
                health_status.update({
                    'status': 'warning',
                    'action': 'consider_rotation',
                    'message': f'Session approaching rotation threshold'
                })
            
            return health_status
            
        except Exception as e:
            logger.error(f"Error checking session health: {e}")
            return {
                'status': 'error',
                'action': 'investigate',
                'message': f'Error checking session: {str(e)}'
            }
    
    async def cleanup_expired_sessions(self) -> int:
        """Clean up all expired sessions"""
        cleaned_count = 0
        
        try:
            # Clean up active sessions
            expired_sessions = []
            for session_name, session_info in self.active_sessions.items():
                if session_info.is_expired(self.max_session_age_hours):
                    expired_sessions.append(session_name)
            
            for session_name in expired_sessions:
                await self._remove_session(session_name)
                cleaned_count += 1
            
            # Clean up disk sessions
            for session_dir in self.session_dir.iterdir():
                if session_dir.is_dir() and session_dir.name != 'cache':
                    session_file = session_dir / "session.enc"
                    if session_file.exists():
                        # Check file age
                        file_age_hours = (datetime.now().timestamp() - session_file.stat().st_mtime) / 3600
                        if file_age_hours > self.max_session_age_hours:
                            await self._remove_session(session_dir.name)
                            cleaned_count += 1
            
            if cleaned_count > 0:
                logger.info(f"🧹 Cleaned up {cleaned_count} expired sessions")
            
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error cleaning up sessions: {e}")
            return 0
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get session management statistics"""
        active_count = len(self.active_sessions)
        total_disk_sessions = sum(1 for d in self.session_dir.iterdir() if d.is_dir() and d.name != 'cache')
        
        # Calculate average age and usage
        if self.active_sessions:
            avg_age_hours = sum(
                (datetime.now() - s.created_at).total_seconds() / 3600 
                for s in self.active_sessions.values()
            ) / len(self.active_sessions)
            
            avg_uses = sum(s.use_count for s in self.active_sessions.values()) / len(self.active_sessions)
        else:
            avg_age_hours = 0
            avg_uses = 0
        
        return {
            'active_sessions': active_count,
            'total_disk_sessions': total_disk_sessions,
            'average_age_hours': round(avg_age_hours, 2),
            'average_uses': round(avg_uses, 1),
            'max_session_age_hours': self.max_session_age_hours,
            'max_session_uses': self.max_session_uses,
            'cache_stats': self.cache.get_stats()
        }

# Factory function
def create_enhanced_session_manager(session_dir: str = "browser_sessions", 
                                   config: Dict[str, Any] = None) -> EnhancedSessionManager:
    """Create enhanced session manager with optimized defaults"""
    default_config = {
        'max_session_age_hours': 24,
        'max_session_uses': 50,
        'rotation_threshold': 0.8,
        'session_cache_ttl': 3600,
        'cache_max_entries': 100,
        'cache_max_size_mb': 50
    }
    
    merged_config = {**default_config, **(config or {})}
    return EnhancedSessionManager(session_dir, merged_config)

async def main():
    """Test the enhanced session manager"""
    config = {
        'max_session_age_hours': 1,  # Short for testing
        'max_session_uses': 5,
        'session_cache_ttl': 60
    }
    
    manager = create_enhanced_session_manager("test_sessions", config)
    
    try:
        # Test session operations
        test_session_data = {
            'cookies': [{'name': 'test', 'value': 'value'}],
            'localStorage': {'token': 'abc123'}
        }
        
        # Save session
        await manager.save_session_state(test_session_data, "test_session")
        
        # Load session
        loaded_data = await manager.load_session_state("test_session")
        print(f"Loaded session: {loaded_data is not None}")
        
        # Check health
        health = await manager.check_session_health("test_session")
        print(f"Session health: {health}")
        
        # Get stats
        stats = manager.get_session_stats()
        print(f"Session stats: {json.dumps(stats, indent=2)}")
        
    finally:
        await manager.cache.stop()

if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())