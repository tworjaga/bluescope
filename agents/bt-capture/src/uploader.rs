//! Uploader - Secure packet upload to ingest gateway

use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};
use tracing::{info, warn, error};

use crate::capture::BluetoothPacket;

/// Packet batch for upload
#[derive(Debug, Serialize, Deserialize)]
pub struct PacketBatch {
    pub agent_id: String,
    pub timestamp: i64,
    pub packets: Vec<SerializedPacket>,
}

/// Serialized packet for transmission
#[derive(Debug, Serialize, Deserialize)]
pub struct SerializedPacket {
    pub timestamp: i64,
    pub channel: u8,
    pub rssi: i8,
    pub phy: u8,
    pub crc_valid: bool,
    pub access_address: u32,
    pub data: Vec<u8>,
}

impl From<&BluetoothPacket> for SerializedPacket {
    fn from(packet: &BluetoothPacket) -> Self {
        Self {
            timestamp: packet.metadata.timestamp,
            channel: packet.metadata.channel,
            rssi: packet.metadata.rssi,
            phy: packet.metadata.phy,
            crc_valid: packet.metadata.crc_valid,
            access_address: packet.metadata.access_address,
            data: packet.data.clone(),
        }
    }
}

/// Packet uploader
pub struct Uploader {
    endpoint: String,
    batch_size: usize,
    agent_id: String,
    client: reqwest::Client,
}

impl Uploader {
    /// Create new uploader
    pub fn new(endpoint: String, batch_size: usize) -> Result<Self> {
        let agent_id = format!("agent-{}", uuid::Uuid::new_v4());
        
        let client = reqwest::Client::builder()
            .timeout(std::time::Duration::from_secs(30))
            .build()
            .context("Failed to create HTTP client")?;

        Ok(Self {
            endpoint,
            batch_size,
            agent_id,
            client,
        })
    }

    /// Upload batch of packets
    pub async fn upload_batch(&self, packets: &[BluetoothPacket]) -> Result<()> {
        if packets.is_empty() {
            return Ok(());
        }

        // Convert packets to serializable format
        let serialized: Vec<SerializedPacket> = packets
            .iter()
            .map(SerializedPacket::from)
            .collect();

        // Create batch
        let batch = PacketBatch {
            agent_id: self.agent_id.clone(),
            timestamp: chrono::Utc::now().timestamp(),
            packets: serialized,
        };

        // Upload via HTTP POST
        match self.upload_http(&batch).await {
            Ok(_) => {
                info!("Uploaded {} packets", packets.len());
                Ok(())
            }
            Err(e) => {
                error!("Failed to upload batch: {}", e);
                Err(e)
            }
        }
    }

    /// Upload via HTTP
    async fn upload_http(&self, batch: &PacketBatch) -> Result<()> {
        let response = self.client
            .post(&self.endpoint)
            .json(batch)
            .send()
            .await
            .context("Failed to send HTTP request")?;

        if !response.status().is_success() {
            anyhow::bail!("Upload failed with status: {}", response.status());
        }

        Ok(())
    }

    /// Get agent ID
    pub fn agent_id(&self) -> &str {
        &self.agent_id
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::capture::PacketMetadata;

    #[test]
    fn test_packet_serialization() {
        let packet = BluetoothPacket {
            metadata: PacketMetadata {
                timestamp: 1234567890,
                channel: 37,
                rssi: -70,
                phy: 1,
                crc_valid: true,
                access_address: 0x8E89BED6,
            },
            data: vec![0x42, 0x04, 0x01, 0x02],
        };

        let serialized = SerializedPacket::from(&packet);
        
        assert_eq!(serialized.channel, 37);
        assert_eq!(serialized.rssi, -70);
        assert_eq!(serialized.data.len(), 4);
    }
}
