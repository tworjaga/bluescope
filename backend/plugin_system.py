"""
Plugin System - Extensible plugin architecture for BlueScope
Allows third-party extensions and custom protocol handlers
"""

import os
import sys
import json
import logging
import importlib
import importlib.util
from typing import Dict, Any, List, Optional, Callable, Type
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


@dataclass
class PluginInfo:
    """Plugin metadata"""
    name: str
    version: str
    description: str
    author: str
    entry_point: str
    dependencies: List[str] = field(default_factory=list)
    enabled: bool = True
    loaded: bool = False
    load_time: Optional[datetime] = None
    error: Optional[str] = None


class PluginInterface(ABC):
    """Base interface for all plugins"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Plugin name"""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """Plugin version"""
        pass
    
    @abstractmethod
    def initialize(self, context: Dict[str, Any]) -> bool:
        """Initialize plugin with context"""
        pass
    
    @abstractmethod
    def shutdown(self):
        """Shutdown plugin"""
        pass


class ProtocolPlugin(PluginInterface):
    """Plugin for custom protocol support"""
    
    @abstractmethod
    def can_decode(self, data: bytes) -> bool:
        """Check if this plugin can decode the data"""
        pass
    
    @abstractmethod
    def decode(self, data: bytes, channel: int, rssi: int) -> Optional[Dict[str, Any]]:
        """Decode protocol data"""
        pass


class AnalyzerPlugin(PluginInterface):
    """Plugin for custom analysis"""
    
    @abstractmethod
    def analyze(self, data: Any) -> Dict[str, Any]:
        """Analyze data and return results"""
        pass


class ExporterPlugin(PluginInterface):
    """Plugin for custom export formats"""
    
    @abstractmethod
    def get_format_name(self) -> str:
        """Get export format name"""
        pass
    
    @abstractmethod
    def export(self, data: Any, filepath: str) -> bool:
        """Export data to file"""
        pass


class PluginManager:
    """
    Plugin manager for BlueScope
    Handles plugin discovery, loading, and lifecycle
    """
    
    PLUGIN_DIR = "plugins"
    PLUGIN_MANIFEST = "plugin.json"
    
    def __init__(self):
        self.plugins: Dict[str, PluginInfo] = {}
        self.instances: Dict[str, PluginInterface] = {}
        self.hooks: Dict[str, List[Callable]] = {}
        self.context: Dict[str, Any] = {}
        
        # Plugin directories
        self.plugin_dirs: List[Path] = [
            Path(__file__).parent.parent / self.PLUGIN_DIR,
            Path.home() / ".bluescope" / "plugins",
        ]
        
        logger.info("PluginManager initialized")
    
    def set_context(self, context: Dict[str, Any]):
        """Set global context for plugins"""
        self.context = context
    
    def discover_plugins(self) -> List[PluginInfo]:
        """
        Discover available plugins
        
        Returns:
            List of plugin info objects
        """
        discovered = []
        
        for plugin_dir in self.plugin_dirs:
            if not plugin_dir.exists():
                continue
            
            for plugin_path in plugin_dir.iterdir():
                if not plugin_path.is_dir():
                    continue
                
                manifest_path = plugin_path / self.PLUGIN_MANIFEST
                if not manifest_path.exists():
                    continue
                
                try:
                    with open(manifest_path) as f:
                        manifest = json.load(f)
                    
                    info = PluginInfo(
                        name=manifest.get("name", plugin_path.name),
                        version=manifest.get("version", "0.0.1"),
                        description=manifest.get("description", ""),
                        author=manifest.get("author", "Unknown"),
                        entry_point=manifest.get("entry_point", "plugin.py"),
                        dependencies=manifest.get("dependencies", []),
                        enabled=manifest.get("enabled", True),
                    )
                    
                    discovered.append(info)
                    logger.debug(f"Discovered plugin: {info.name}")
                    
                except Exception as e:
                    logger.warning(f"Failed to load manifest from {plugin_path}: {e}")
        
        return discovered
    
    def load_plugin(self, name: str) -> bool:
        """
        Load a plugin by name
        
        Args:
            name: Plugin name
        
        Returns:
            True if loaded successfully
        """
        # Check if already loaded
        if name in self.instances:
            logger.warning(f"Plugin {name} already loaded")
            return True
        
        # Find plugin
        plugin_info = None
        plugin_path = None
        
        for plugin_dir in self.plugin_dirs:
            if not plugin_dir.exists():
                continue
            
            for p in plugin_dir.iterdir():
                if p.is_dir() and p.name == name:
                    plugin_path = p
                    break
            
            if plugin_path:
                break
        
        if not plugin_path:
            logger.error(f"Plugin {name} not found")
            return False
        
        # Load manifest
        manifest_path = plugin_path / self.PLUGIN_MANIFEST
        try:
            with open(manifest_path) as f:
                manifest = json.load(f)
            
            plugin_info = PluginInfo(
                name=manifest.get("name", name),
                version=manifest.get("version", "0.0.1"),
                description=manifest.get("description", ""),
                author=manifest.get("author", "Unknown"),
                entry_point=manifest.get("entry_point", "plugin.py"),
                dependencies=manifest.get("dependencies", []),
                enabled=manifest.get("enabled", True),
            )
            
        except Exception as e:
            logger.error(f"Failed to load manifest for {name}: {e}")
            return False
        
        # Check dependencies
        for dep in plugin_info.dependencies:
            if not self._check_dependency(dep):
                logger.error(f"Plugin {name} missing dependency: {dep}")
                plugin_info.error = f"Missing dependency: {dep}"
                self.plugins[name] = plugin_info
                return False
        
        # Load plugin module
        entry_file = plugin_path / plugin_info.entry_point
        if not entry_file.exists():
            logger.error(f"Entry point not found: {entry_file}")
            return False
        
        try:
            spec = importlib.util.spec_from_file_location(
                f"bluescope_plugin_{name}",
                entry_file
            )
            module = importlib.util.module_from_spec(spec)
            sys.modules[f"bluescope_plugin_{name}"] = module
            spec.loader.exec_module(module)
            
            # Find plugin class
            plugin_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and 
                    issubclass(attr, PluginInterface) and 
                    attr != PluginInterface):
                    plugin_class = attr
                    break
            
            if not plugin_class:
                logger.error(f"No plugin class found in {name}")
                return False
            
            # Instantiate plugin
            instance = plugin_class()
            
            # Initialize
            if not instance.initialize(self.context):
                logger.error(f"Plugin {name} initialization failed")
                return False
            
            # Store
            self.instances[name] = instance
            plugin_info.loaded = True
            plugin_info.load_time = datetime.now()
            self.plugins[name] = plugin_info
            
            logger.info(f"Plugin {name} v{plugin_info.version} loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load plugin {name}: {e}")
            plugin_info.error = str(e)
            self.plugins[name] = plugin_info
            return False
    
    def unload_plugin(self, name: str) -> bool:
        """
        Unload a plugin
        
        Args:
            name: Plugin name
        
        Returns:
            True if unloaded successfully
        """
        if name not in self.instances:
            logger.warning(f"Plugin {name} not loaded")
            return False
        
        try:
            instance = self.instances[name]
            instance.shutdown()
            
            del self.instances[name]
            self.plugins[name].loaded = False
            self.plugins[name].load_time = None
            
            logger.info(f"Plugin {name} unloaded")
            return True
            
        except Exception as e:
            logger.error(f"Error unloading plugin {name}: {e}")
            return False
    
    def load_all_plugins(self) -> Dict[str, bool]:
        """
        Load all discovered plugins
        
        Returns:
            Dict of plugin name -> success status
        """
        discovered = self.discover_plugins()
        results = {}
        
        for info in discovered:
            if info.enabled:
                results[info.name] = self.load_plugin(info.name)
            else:
                results[info.name] = False
                logger.info(f"Plugin {info.name} is disabled")
        
        return results
    
    def get_plugin(self, name: str) -> Optional[PluginInterface]:
        """Get loaded plugin instance"""
        return self.instances.get(name)
    
    def get_plugin_info(self, name: str) -> Optional[PluginInfo]:
        """Get plugin info"""
        return self.plugins.get(name)
    
    def list_plugins(self) -> List[PluginInfo]:
        """List all plugins"""
        return list(self.plugins.values())
    
    def register_hook(self, event: str, callback: Callable):
        """Register a hook for an event"""
        if event not in self.hooks:
            self.hooks[event] = []
        self.hooks[event].append(callback)
    
    def trigger_hook(self, event: str, *args, **kwargs):
        """Trigger all hooks for an event"""
        for callback in self.hooks.get(event, []):
            try:
                callback(*args, **kwargs)
            except Exception as e:
                logger.error(f"Hook error for {event}: {e}")
    
    def _check_dependency(self, dependency: str) -> bool:
        """Check if a dependency is available"""
        try:
            importlib.import_module(dependency)
            return True
        except ImportError:
            return False
    
    def get_protocol_plugins(self) -> List[ProtocolPlugin]:
        """Get all loaded protocol plugins"""
        return [
            p for p in self.instances.values() 
            if isinstance(p, ProtocolPlugin)
        ]
    
    def get_analyzer_plugins(self) -> List[AnalyzerPlugin]:
        """Get all loaded analyzer plugins"""
        return [
            p for p in self.instances.values()
            if isinstance(p, AnalyzerPlugin)
        ]
    
    def get_exporter_plugins(self) -> List[ExporterPlugin]:
        """Get all loaded exporter plugins"""
        return [
            p for p in self.instances.values()
            if isinstance(p, ExporterPlugin)
        ]


# Global plugin manager instance
_plugin_manager: Optional[PluginManager] = None


def get_plugin_manager() -> PluginManager:
    """Get or create global plugin manager"""
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager()
    return _plugin_manager


def test_plugin_system():
    """Test plugin system"""
    print("\n" + "="*60)
    print("Plugin System Test")
    print("="*60)
    
    manager = get_plugin_manager()
    
    # Test 1: Discover plugins
    print("\n1. Testing plugin discovery:")
    discovered = manager.discover_plugins()
    print(f"  Discovered {len(discovered)} plugins")
    
    # Test 2: List plugins
    print("\n2. Testing plugin list:")
    plugins = manager.list_plugins()
    for p in plugins:
        status = "" if p.loaded else ""
        print(f"  {status} {p.name} v{p.version}")
    
    # Test 3: Plugin info
    print("\n3. Testing plugin info retrieval:")
    for p in plugins:
        info = manager.get_plugin_info(p.name)
        if info:
            print(f"   {info.name}: {info.description[:50]}...")
    
    print("\n Plugin system tests completed")
    return True


if __name__ == "__main__":
    test_plugin_system()
