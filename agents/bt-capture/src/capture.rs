//! Capture Engine - Core packet capture functionality

use anyhow::{Context, Result};
use std::sync::Arc;
use tokio::sync::mpsc;
use tracing::{info, warn, error, debug};
use chrono::Utc;

use crate::hardware::{HardwareInterface, HardwareType};
use crate::buffer::RingBuffer;
use crate::uploader::Uploader;
use crate::config::Config;
use crate::metrics::MetricsCollector;

/// Bluetooth packet metadata
#[derive(Debug, Clone)]
pub struct PacketMetadata {
    pub timestamp: i64,
    pub channel: u8,
    pub rssi: i8,
    pub phy: u8,
    pub crc_valid: bool,
    pub access_address: u32,
}

/// Captured Bluetooth packet
#[derive(Debug, Clone)]
pub struct BluetoothPacket {
    pub metadata: PacketMetadata,
    pub data: Vec<u8>,
}

/// Capture statistics
#[derive(Debug, Clone, Default)]
pub struct CaptureStats {
    pub packets_captured: u64,
    pub bytes_captured: u64,
    pub packets_dropped: u64,
    pub crc_errors: u64,
    pub uptime_seconds: u64,
}

/// Main capture engine
pub struct CaptureEngine {
    config: Config,
    hardware: Box<dyn HardwareInterface>,
    buffer: Arc<RingBuffer<BluetoothPacket>>,
    uploader: Arc<Uploader>,
    metrics: Arc<MetricsCollector>,
    stats: CaptureStats,
    is_running: bool,
}

impl CaptureEngine {
    /// Create new capture engine
    pub async fn new(
        config: Config,
        metrics: Arc<MetricsCollector>,
    ) -> Result<Self> {
        info!("Initializing capture engine");

        // Initialize hardware interface
        let hardware = Self::initialize_hardware(&config).await?;
        
        // Create ring buffer
        let buffer = Arc::new(RingBuffer::new(config.buffer_size));
        
        // Create uploader
        let uploader = Arc::new(Uploader::new(
            config.upload_endpoint.clone(),
            config.upload_batch_size,
        )?);

        Ok(Self {
            config,
            hardware,
            buffer,
            uploader,
            metrics,
            stats: CaptureStats::default(),
            is_running: false,
        })
    }

    /// Initialize hardware interface based on configuration
    async fn initialize_hardware(config: &Config) -> Result<Box<dyn HardwareInterface>> {
        use crate::hardware::*;

        match config.hardware_type {
            HardwareType::UsbDongle => {
                info!("Initializing USB Bluetooth dongle");
                Ok(Box::new(UsbDongle::new(config.device_id.clone()).await?))
            }
            HardwareType::NrfSniffer => {
                info!("Initializing nRF Sniffer");
                Ok(Box::new(NrfSniffer::new(config.device_id.clone()).await?))
            }
            HardwareType::Ubertooth => {
                info!("Initializing Ubertooth One");
                Ok(Box::new(Ubertooth::new().await?))
            }
            HardwareType::HackRF => {
                info!("Initializing HackRF One");
                Ok(Box::new(HackRF::new().await?))
            }
        }
    }

    /// Start packet capture
    pub async fn start(&mut self) -> Result<()> {
        if self.is_running {
            warn!("Capture already running");
            return Ok(());
        }

        info!("Starting packet capture");

        // Start hardware
        self.hardware.start().await
            .context("Failed to start hardware")?;

        // Start channel hopping if enabled
        if self.config.adaptive_hopping {
            self.start_channel_hopping().await?;
        }

        // Start capture loop
        self.is_running = true;
        self.start_capture_loop().await?;

        // Start upload loop
        self.start_upload_loop().await?;

        info!("Packet capture started successfully");

        Ok(())
    }

    /// Stop packet capture
    pub async fn stop(&mut self) -> Result<()> {
        if !self.is_running {
            return Ok(());
        }

        info!("Stopping packet capture");

        self.is_running = false;

        // Stop hardware
        self.hardware.stop().await
            .context("Failed to stop hardware")?;

        // Flush remaining packets
        self.flush_buffer().await?;

        info!("Packet capture stopped");

        Ok(())
    }

    /// Start capture loop
    async fn start_capture_loop(&mut self) -> Result<()> {
        let hardware = self.hardware.clone_interface();
        let buffer = self.buffer.clone();
        let metrics = self.metrics.clone();
        let mut stats = self.stats.clone();

        tokio::spawn(async move {
            info!("Capture loop started");

            loop {
                match hardware.receive_packet().await {
                    Ok(packet) => {
                        // Update statistics
                        stats.packets_captured += 1;
                        stats.bytes_captured += packet.data.len() as u64;

                        if !packet.metadata.crc_valid {
                            stats.crc_errors += 1;
                        }

                        // Update metrics
                        metrics.record_packet_captured(packet.data.len());
                        metrics.record_rssi(packet.metadata.rssi);
                        metrics.record_channel(packet.metadata.channel);

                        // Add to buffer
                        if !buffer.push(packet) {
                            stats.packets_dropped += 1;
                            metrics.record_packet_dropped();
                            warn!("Buffer full, packet dropped");
                        }
                    }
                    Err(e) => {
                        error!("Error receiving packet: {}", e);
                        tokio::time::sleep(tokio::time::Duration::from_millis(100)).await;
                    }
                }
            }
        });

        Ok(())
    }

    /// Start upload loop
    async fn start_upload_loop(&self) -> Result<()> {
        let buffer = self.buffer.clone();
        let uploader = self.uploader.clone();
        let batch_size = self.config.upload_batch_size;

        tokio::spawn(async move {
            info!("Upload loop started");

            loop {
                // Collect batch of packets
                let mut batch = Vec::with_capacity(batch_size);
                
                for _ in 0..batch_size {
                    if let Some(packet) = buffer.pop() {
                        batch.push(packet);
                    } else {
                        break;
                    }
                }

                if !batch.is_empty() {
                    // Upload batch
                    match uploader.upload_batch(&batch).await {
                        Ok(_) => {
                            debug!("Uploaded {} packets", batch.len());
                        }
                        Err(e) => {
                            error!("Failed to upload batch: {}", e);
                            
                            // Put packets back in buffer
                            for packet in batch {
                                buffer.push(packet);
                            }
                        }
                    }
                }

                // Sleep before next batch
                tokio::time::sleep(tokio::time::Duration::from_secs(1)).await;
            }
        });

        Ok(())
    }

    /// Start adaptive channel hopping
    async fn start_channel_hopping(&self) -> Result<()> {
        let hardware = self.hardware.clone_interface();
        let hop_interval = self.config.hop_interval_ms;

        tokio::spawn(async move {
            info!("Channel hopping started");

            let channels = [37, 38, 39, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
            let mut channel_idx = 0;

            loop {
                let channel = channels[channel_idx];
                
                if let Err(e) = hardware.set_channel(channel).await {
                    error!("Failed to set channel {}: {}", channel, e);
                }

                channel_idx = (channel_idx + 1) % channels.len();

                tokio::time::sleep(tokio::time::Duration::from_millis(hop_interval)).await;
            }
        });

        Ok(())
    }

    /// Flush buffer to uploader
    async fn flush_buffer(&self) -> Result<()> {
        info!("Flushing buffer");

        let mut packets = Vec::new();
        
        while let Some(packet) = self.buffer.pop() {
            packets.push(packet);
        }

        if !packets.is_empty() {
            self.uploader.upload_batch(&packets).await
                .context("Failed to flush buffer")?;
            
            info!("Flushed {} packets", packets.len());
        }

        Ok(())
    }

    /// Get capture statistics
    pub fn get_stats(&self) -> CaptureStats {
        self.stats.clone()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_capture_engine_creation() {
        let config = Config::default();
        let metrics = Arc::new(MetricsCollector::new());
        
        let result = CaptureEngine::new(config, metrics).await;
        assert!(result.is_ok());
    }
}
