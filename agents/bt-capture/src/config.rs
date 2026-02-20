//! Configuration management

use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};
use std::fs;

use crate::hardware::HardwareType;

/// Agent configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    /// Hardware type
    pub hardware_type: HardwareType,
    
    /// Device ID (for USB devices)
    pub device_id: String,
    
    /// Buffer size (number of packets)
    pub buffer_size: usize,
    
    /// Upload endpoint URL
    pub upload_endpoint: String,
    
    /// Upload batch size
    pub upload_batch_size: usize,
    
    /// Enable adaptive channel hopping
    pub adaptive_hopping: bool,
    
    /// Channel hop interval (milliseconds)
    pub hop_interval_ms: u64,
    
    /// Enable RF fingerprinting
    pub rf_fingerprinting: bool,
    
    /// Enable local packet storage
    pub local_storage: bool,
    
    /// Local storage path
    pub storage_path: String,
    
    /// Maximum local storage size (MB)
    pub max_storage_mb: usize,
}

impl Default for Config {
    fn default() -> Self {
        Self {
            hardware_type: HardwareType::UsbDongle,
            device_id: String::from("auto"),
            buffer_size: 100000,
            upload_endpoint: String::from("http://localhost:8080/ingest"),
            upload_batch_size: 100,
            adaptive_hopping: true,
            hop_interval_ms: 100,
            rf_fingerprinting: true,
            local_storage: true,
            storage_path: String::from("./data"),
            max_storage_mb: 1024,
        }
    }
}

impl Config {
    /// Load configuration from file
    pub fn load(path: &str) -> Result<Self> {
        let contents = fs::read_to_string(path)
            .context("Failed to read config file")?;
        
        let config: Config = toml::from_str(&contents)
            .context("Failed to parse config file")?;
        
        Ok(config)
    }

    /// Save configuration to file
    pub fn save(&self, path: &str) -> Result<()> {
        let contents = toml::to_string_pretty(self)
            .context("Failed to serialize config")?;
        
        fs::write(path, contents)
            .context("Failed to write config file")?;
        
        Ok(())
    }

    /// Validate configuration
    pub fn validate(&self) -> Result<()> {
        if self.buffer_size == 0 {
            anyhow::bail!("Buffer size must be greater than 0");
        }

        if self.upload_batch_size == 0 {
            anyhow::bail!("Upload batch size must be greater than 0");
        }

        if self.upload_batch_size > self.buffer_size {
            anyhow::bail!("Upload batch size cannot exceed buffer size");
        }

        if self.hop_interval_ms == 0 {
            anyhow::bail!("Hop interval must be greater than 0");
        }

        Ok(())
    }
}

// Implement Serialize/Deserialize for HardwareType
impl Serialize for HardwareType {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: serde::Serializer,
    {
        let s = match self {
            HardwareType::UsbDongle => "usb_dongle",
            HardwareType::NrfSniffer => "nrf_sniffer",
            HardwareType::Ubertooth => "ubertooth",
            HardwareType::HackRF => "hackrf",
        };
        serializer.serialize_str(s)
    }
}

impl<'de> Deserialize<'de> for HardwareType {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        let s = String::deserialize(deserializer)?;
        match s.as_str() {
            "usb_dongle" => Ok(HardwareType::UsbDongle),
            "nrf_sniffer" => Ok(HardwareType::NrfSniffer),
            "ubertooth" => Ok(HardwareType::Ubertooth),
            "hackrf" => Ok(HardwareType::HackRF),
            _ => Err(serde::de::Error::custom(format!("Unknown hardware type: {}", s))),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_default_config() {
        let config = Config::default();
        assert!(config.validate().is_ok());
    }

    #[test]
    fn test_config_validation() {
        let mut config = Config::default();
        
        config.buffer_size = 0;
        assert!(config.validate().is_err());
        
        config.buffer_size = 100;
        config.upload_batch_size = 200;
        assert!(config.validate().is_err());
    }
}
