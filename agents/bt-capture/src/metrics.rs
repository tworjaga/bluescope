//! Metrics collection and export

use prometheus::{
    Counter, Gauge, Histogram, HistogramOpts, IntCounter, IntGauge, Opts, Registry,
};
use std::sync::Arc;
use tracing::{info, error};

/// Metrics collector
pub struct MetricsCollector {
    registry: Registry,
    
    // Counters
    packets_captured: IntCounter,
    packets_dropped: IntCounter,
    bytes_captured: Counter,
    crc_errors: IntCounter,
    
    // Gauges
    buffer_size: IntGauge,
    rssi_current: Gauge,
    channel_current: IntGauge,
    
    // Histograms
    packet_size_histogram: Histogram,
    rssi_histogram: Histogram,
}

impl MetricsCollector {
    /// Create new metrics collector
    pub fn new() -> Self {
        let registry = Registry::new();

        // Create counters
        let packets_captured = IntCounter::with_opts(
            Opts::new("bt_packets_captured_total", "Total packets captured")
        ).unwrap();
        
        let packets_dropped = IntCounter::with_opts(
            Opts::new("bt_packets_dropped_total", "Total packets dropped")
        ).unwrap();
        
        let bytes_captured = Counter::with_opts(
            Opts::new("bt_bytes_captured_total", "Total bytes captured")
        ).unwrap();
        
        let crc_errors = IntCounter::with_opts(
            Opts::new("bt_crc_errors_total", "Total CRC errors")
        ).unwrap();

        // Create gauges
        let buffer_size = IntGauge::with_opts(
            Opts::new("bt_buffer_size", "Current buffer size")
        ).unwrap();
        
        let rssi_current = Gauge::with_opts(
            Opts::new("bt_rssi_current", "Current RSSI value")
        ).unwrap();
        
        let channel_current = IntGauge::with_opts(
            Opts::new("bt_channel_current", "Current channel")
        ).unwrap();

        // Create histograms
        let packet_size_histogram = Histogram::with_opts(
            HistogramOpts::new("bt_packet_size_bytes", "Packet size distribution")
                .buckets(vec![10.0, 50.0, 100.0, 200.0, 500.0, 1000.0])
        ).unwrap();
        
        let rssi_histogram = Histogram::with_opts(
            HistogramOpts::new("bt_rssi_dbm", "RSSI distribution")
                .buckets(vec![-100.0, -90.0, -80.0, -70.0, -60.0, -50.0, -40.0])
        ).unwrap();

        // Register metrics
        registry.register(Box::new(packets_captured.clone())).unwrap();
        registry.register(Box::new(packets_dropped.clone())).unwrap();
        registry.register(Box::new(bytes_captured.clone())).unwrap();
        registry.register(Box::new(crc_errors.clone())).unwrap();
        registry.register(Box::new(buffer_size.clone())).unwrap();
        registry.register(Box::new(rssi_current.clone())).unwrap();
        registry.register(Box::new(channel_current.clone())).unwrap();
        registry.register(Box::new(packet_size_histogram.clone())).unwrap();
        registry.register(Box::new(rssi_histogram.clone())).unwrap();

        Self {
            registry,
            packets_captured,
            packets_dropped,
            bytes_captured,
            crc_errors,
            buffer_size,
            rssi_current,
            channel_current,
            packet_size_histogram,
            rssi_histogram,
        }
    }

    /// Record packet captured
    pub fn record_packet_captured(&self, size: usize) {
        self.packets_captured.inc();
        self.bytes_captured.inc_by(size as f64);
        self.packet_size_histogram.observe(size as f64);
    }

    /// Record packet dropped
    pub fn record_packet_dropped(&self) {
        self.packets_dropped.inc();
    }

    /// Record CRC error
    pub fn record_crc_error(&self) {
        self.crc_errors.inc();
    }

    /// Update buffer size
    pub fn update_buffer_size(&self, size: i64) {
        self.buffer_size.set(size);
    }

    /// Record RSSI
    pub fn record_rssi(&self, rssi: i8) {
        self.rssi_current.set(rssi as f64);
        self.rssi_histogram.observe(rssi as f64);
    }

    /// Record channel
    pub fn record_channel(&self, channel: u8) {
        self.channel_current.set(channel as i64);
    }

    /// Start metrics HTTP server
    pub async fn start_server(&self, port: u16) -> anyhow::Result<()> {
        use warp::Filter;

        info!("Starting metrics server on port {}", port);

        let registry = self.registry.clone();
        
        let metrics_route = warp::path!("metrics")
            .map(move || {
                use prometheus::Encoder;
                let encoder = prometheus::TextEncoder::new();
                let metric_families = registry.gather();
                let mut buffer = Vec::new();
                
                if let Err(e) = encoder.encode(&metric_families, &mut buffer) {
                    error!("Failed to encode metrics: {}", e);
                    return warp::reply::with_status(
                        "Error encoding metrics",
                        warp::http::StatusCode::INTERNAL_SERVER_ERROR,
                    );
                }
                
                warp::reply::with_status(
                    String::from_utf8(buffer).unwrap_or_default(),
                    warp::http::StatusCode::OK,
                )
            });

        warp::serve(metrics_route)
            .run(([0, 0, 0, 0], port))
            .await;

        Ok(())
    }

    /// Get registry for custom metrics
    pub fn registry(&self) -> &Registry {
        &self.registry
    }
}

impl Default for MetricsCollector {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_metrics_collector() {
        let collector = MetricsCollector::new();
        
        collector.record_packet_captured(100);
        collector.record_packet_dropped();
        collector.record_rssi(-70);
        collector.record_channel(37);
        
        // Metrics should be recorded without panicking
    }
}
