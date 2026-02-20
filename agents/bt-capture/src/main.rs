//! BlueScope Bluetooth Capture Agent
//! 
//! High-performance Bluetooth packet capture with support for:
//! - USB BT dongles (HCI)
//! - nRF Sniffer
//! - Ubertooth One
//! - HackRF One
//! - Multi-antenna SDR

use anyhow::{Context, Result};
use std::sync::Arc;
use tokio::sync::RwLock;
use tracing::{info, warn, error};

mod capture;
mod hardware;
mod buffer;
mod uploader;
mod config;
mod metrics;

use capture::CaptureEngine;
use config::Config;
use metrics::MetricsCollector;

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize tracing
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::from_default_env()
                .add_directive(tracing::Level::INFO.into())
        )
        .init();

    info!("BlueScope Bluetooth Capture Agent v{}", env!("CARGO_PKG_VERSION"));

    // Load configuration
    let config = Config::load("config.toml")
        .context("Failed to load configuration")?;
    
    info!("Configuration loaded: {:?}", config);

    // Initialize metrics collector
    let metrics = Arc::new(MetricsCollector::new());
    
    // Start metrics server
    let metrics_clone = metrics.clone();
    tokio::spawn(async move {
        if let Err(e) = metrics_clone.start_server(9090).await {
            error!("Metrics server error: {}", e);
        }
    });

    // Initialize capture engine
    let engine = Arc::new(RwLock::new(
        CaptureEngine::new(config.clone(), metrics.clone())
            .await
            .context("Failed to initialize capture engine")?
    ));

    info!("Capture engine initialized");

    // Start capture
    {
        let mut engine_guard = engine.write().await;
        engine_guard.start().await
            .context("Failed to start capture")?;
    }

    info!("Capture started successfully");

    // Wait for shutdown signal
    tokio::signal::ctrl_c().await
        .context("Failed to listen for shutdown signal")?;

    info!("Shutdown signal received, stopping capture...");

    // Stop capture
    {
        let mut engine_guard = engine.write().await;
        engine_guard.stop().await
            .context("Failed to stop capture")?;
    }

    info!("Capture agent stopped");

    Ok(())
}
