use std::net::SocketAddr;
use std::time::Duration;

use serde::{Deserialize, Serialize};
use tokio::net::UdpSocket;
use tokio::time;

/// Default UDP port for LAN discovery broadcasts.
pub const DISCOVERY_PORT: u16 = 7778;

/// How often the host sends a broadcast beacon (seconds).
pub const BEACON_INTERVAL: Duration = Duration::from_secs(2);

/// Maximum size of a discovery packet in bytes.
const MAX_PACKET_SIZE: usize = 512;

/// A discovery beacon broadcast by the game host.
///
/// ## Rust concept: small structs for wire formats
///
/// This struct is intentionally minimal — just enough data for a joining
/// player to see the game and connect. The `Serialize`/`Deserialize`
/// derives let us convert it to/from JSON with one call, and the small
/// size fits comfortably in a single UDP datagram.
///
/// UDP has no guaranteed delivery or ordering, so beacons are sent
/// repeatedly. If a client misses one, it'll catch the next.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct DiscoveryBeacon {
    /// Protocol identifier so we don't confuse our beacons with other
    /// UDP traffic on the same port.
    pub game: String,
    /// Display name of the host player.
    pub host_name: String,
    /// TCP port the game server is listening on.
    pub port: u16,
    /// Number of players currently connected.
    pub player_count: u8,
    /// Maximum number of players allowed.
    pub max_players: u8,
}

impl DiscoveryBeacon {
    /// Create a new beacon for advertising a game.
    pub fn new(host_name: String, port: u16, player_count: u8, max_players: u8) -> DiscoveryBeacon {
        DiscoveryBeacon {
            game: "4AD".to_string(),
            host_name,
            port,
            player_count,
            max_players,
        }
    }

    /// Check if this is a valid 4AD beacon (not random UDP noise).
    pub fn is_valid(&self) -> bool {
        self.game == "4AD" && self.port > 0 && self.max_players > 0
    }

    /// Serialize to JSON bytes for UDP transmission.
    pub fn to_bytes(&self) -> Option<Vec<u8>> {
        serde_json::to_vec(self).ok()
    }

    /// Deserialize from JSON bytes received via UDP.
    pub fn from_bytes(data: &[u8]) -> Option<DiscoveryBeacon> {
        serde_json::from_slice(data).ok()
    }
}

/// A discovered game on the LAN, combining the beacon data with the
/// source address so the client knows where to connect.
#[derive(Debug, Clone)]
pub struct DiscoveredGame {
    /// The host's IP address (from the UDP packet source).
    pub addr: SocketAddr,
    /// The beacon data (host name, TCP port, player count).
    pub beacon: DiscoveryBeacon,
}

impl DiscoveredGame {
    /// The address to connect to via TCP (host IP + game port).
    pub fn connect_addr(&self) -> String {
        format!("{}:{}", self.addr.ip(), self.beacon.port)
    }
}

/// Broadcast a discovery beacon on the LAN.
///
/// ## Rust concept: UDP broadcast
///
/// `UdpSocket::set_broadcast(true)` enables sending to the broadcast
/// address `255.255.255.255`. Every device on the LAN receives the
/// packet (unless firewalled). This is the simplest LAN discovery
/// mechanism — no multicast groups, no DNS-SD, just raw broadcast.
///
/// The function sends a single beacon packet. Call it in a loop with
/// a sleep interval to keep broadcasting.
///
/// ## Rust concept: `tokio::net::UdpSocket`
///
/// Like `TcpStream`, tokio's `UdpSocket` is async. `.send_to().await`
/// doesn't block the thread — if the kernel buffer is full, the task
/// yields and other tasks run. In practice, UDP sends almost never
/// block (datagrams are fire-and-forget).
pub async fn send_beacon(socket: &UdpSocket, beacon: &DiscoveryBeacon) -> std::io::Result<()> {
    if let Some(data) = beacon.to_bytes() {
        let broadcast_addr = format!("255.255.255.255:{}", DISCOVERY_PORT);
        socket.send_to(&data, &broadcast_addr).await?;
    }
    Ok(())
}

/// Run the beacon broadcaster in a loop (meant to be `tokio::spawn`ed).
///
/// Sends a beacon every `BEACON_INTERVAL` until the task is cancelled.
pub async fn run_beacon(beacon: DiscoveryBeacon) -> std::io::Result<()> {
    let socket = UdpSocket::bind("0.0.0.0:0").await?;
    socket.set_broadcast(true)?;

    let mut interval = time::interval(BEACON_INTERVAL);
    loop {
        interval.tick().await;
        send_beacon(&socket, &beacon).await?;
    }
}

/// Listen for discovery beacons on the LAN.
///
/// Returns discovered games through a channel. Meant to be spawned as
/// a background task while the join screen is displayed.
///
/// ## Rust concept: `tokio::select!` alternative
///
/// We could use `tokio::select!` to combine the UDP recv with a
/// cancellation signal. For simplicity, we just run this as a spawned
/// task and abort it when the user leaves the join screen.
pub async fn listen_for_beacons(
    tx: tokio::sync::mpsc::Sender<DiscoveredGame>,
) -> std::io::Result<()> {
    let socket = UdpSocket::bind(format!("0.0.0.0:{}", DISCOVERY_PORT)).await?;

    let mut buf = [0u8; MAX_PACKET_SIZE];
    loop {
        let (len, addr) = socket.recv_from(&mut buf).await?;
        if let Some(beacon) = DiscoveryBeacon::from_bytes(&buf[..len]) {
            if beacon.is_valid() {
                let game = DiscoveredGame { addr, beacon };
                if tx.send(game).await.is_err() {
                    break; // Receiver dropped
                }
            }
        }
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    // --- Beacon serialization tests ---

    #[test]
    fn beacon_serializes_to_json() {
        let beacon = DiscoveryBeacon::new("Alice".to_string(), 7777, 1, 4);
        let bytes = beacon.to_bytes();
        assert!(bytes.is_some());
        let json = String::from_utf8(bytes.unwrap()).unwrap();
        assert!(json.contains("4AD"));
        assert!(json.contains("Alice"));
        assert!(json.contains("7777"));
    }

    #[test]
    fn beacon_roundtrips_through_bytes() {
        let beacon = DiscoveryBeacon::new("Bob".to_string(), 9999, 2, 4);
        let bytes = beacon.to_bytes().unwrap();
        let restored = DiscoveryBeacon::from_bytes(&bytes).unwrap();
        assert_eq!(restored, beacon);
    }

    #[test]
    fn beacon_is_valid_for_correct_data() {
        let beacon = DiscoveryBeacon::new("Host".to_string(), 7777, 1, 4);
        assert!(beacon.is_valid());
    }

    #[test]
    fn beacon_is_invalid_for_wrong_game() {
        let mut beacon = DiscoveryBeacon::new("Host".to_string(), 7777, 1, 4);
        beacon.game = "OTHER".to_string();
        assert!(!beacon.is_valid());
    }

    #[test]
    fn beacon_is_invalid_for_zero_port() {
        let beacon = DiscoveryBeacon::new("Host".to_string(), 0, 1, 4);
        assert!(!beacon.is_valid());
    }

    #[test]
    fn beacon_is_invalid_for_zero_max_players() {
        let beacon = DiscoveryBeacon::new("Host".to_string(), 7777, 1, 0);
        assert!(!beacon.is_valid());
    }

    #[test]
    fn from_bytes_returns_none_for_garbage() {
        let garbage = b"this is not json";
        assert!(DiscoveryBeacon::from_bytes(garbage).is_none());
    }

    #[test]
    fn discovered_game_connect_addr_uses_beacon_port() {
        let beacon = DiscoveryBeacon::new("Host".to_string(), 8080, 1, 4);
        let game = DiscoveredGame {
            addr: "192.168.1.100:7778".parse().unwrap(),
            beacon,
        };
        // Should use the beacon's TCP port, not the UDP discovery port
        assert_eq!(game.connect_addr(), "192.168.1.100:8080");
    }

    // --- UDP integration test ---

    #[tokio::test]
    async fn beacon_send_and_receive_over_udp() {
        // Bind a receiver first on a random port
        let receiver = UdpSocket::bind("127.0.0.1:0").await.unwrap();
        let recv_port = receiver.local_addr().unwrap().port();

        // Bind a sender
        let sender = UdpSocket::bind("127.0.0.1:0").await.unwrap();

        let beacon = DiscoveryBeacon::new("TestHost".to_string(), 7777, 1, 4);
        let data = beacon.to_bytes().unwrap();

        // Send directly to the receiver (not broadcast, since loopback
        // doesn't support broadcast on all systems)
        sender
            .send_to(&data, format!("127.0.0.1:{}", recv_port))
            .await
            .unwrap();

        // Receive and parse
        let mut buf = [0u8; MAX_PACKET_SIZE];
        let (len, _addr) = receiver.recv_from(&mut buf).await.unwrap();
        let received = DiscoveryBeacon::from_bytes(&buf[..len]).unwrap();
        assert_eq!(received.host_name, "TestHost");
        assert_eq!(received.port, 7777);
    }
}
