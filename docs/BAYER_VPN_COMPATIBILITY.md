# Bayer Network: VPN Compatibility Guide

## Overview

AutoGraph v3 is fully compatible with Bayer's corporate VPN infrastructure. This document describes the network configuration, VPN requirements, and troubleshooting steps for accessing AutoGraph through Bayer's VPN.

## Bayer VPN Requirements

### Supported VPN Solutions

- **Cisco AnyConnect** (Primary - Recommended)
- **FortiClient VPN** (Secondary)
- **GlobalProtect** (Palo Alto Networks)
- **Zscaler Private Access** (ZPA)

### VPN Configuration

#### Connection Details

```
VPN Gateway: vpn.bayer.com
Port: 443 (HTTPS)
Protocol: SSL/TLS
Authentication: Azure AD (Bayer SSO)
MFA: Required
```

#### Network Access

After connecting to Bayer VPN, AutoGraph is accessible at:

```
Production: https://diagrams.bayer.com
Staging: https://diagrams-staging.bayer.com
Development: https://diagrams-dev.bayer.com
```

## Network Architecture

### VPN Integration

```
[User Device] 
    ↓ VPN Tunnel (TLS 1.3)
[Bayer VPN Gateway] (vpn.bayer.com)
    ↓ Internal Network
[Bayer Firewall] (Application Gateway)
    ↓ Subnet: 10.0.0.0/16
[AutoGraph Load Balancer] (10.0.1.10)
    ↓
[AutoGraph Services]
    ├─ Frontend (10.0.1.20)
    ├─ API Gateway (10.0.1.30)
    └─ Backend Services (10.0.1.40-50)
```

### IP Whitelisting

AutoGraph only accepts connections from Bayer IP ranges:

```
Bayer Corporate Network: 10.0.0.0/8
Bayer VPN Pool: 172.16.0.0/12
Bayer Europe: 192.168.0.0/16
Bayer Americas: 10.1.0.0/16
Bayer APAC: 10.2.0.0/16
```

## VPN Connection Guide

### Windows (Cisco AnyConnect)

1. **Install Cisco AnyConnect**
   - Download from Bayer IT Portal: https://it.bayer.com/vpn
   - Run installer as Administrator
   - Accept Bayer IT security policy

2. **Configure Connection**
   ```
   Server: vpn.bayer.com
   Group: BayerEmployees
   Username: firstname.lastname@bayer.com
   ```

3. **Connect**
   - Launch Cisco AnyConnect
   - Enter credentials
   - Approve MFA push notification
   - Wait for "Connected" status

4. **Verify Connection**
   ```powershell
   # Check VPN interface
   ipconfig /all | findstr "Cisco AnyConnect"
   
   # Test connectivity
   ping diagrams.bayer.com
   curl https://diagrams.bayer.com/health
   ```

### macOS (Cisco AnyConnect)

1. **Install Cisco AnyConnect**
   ```bash
   # Download from Bayer IT Portal
   open https://it.bayer.com/vpn
   
   # Install package
   sudo installer -pkg CiscoAnyConnect.pkg -target /
   ```

2. **Configure and Connect**
   ```bash
   # Open AnyConnect
   open /Applications/Cisco/Cisco\ AnyConnect\ Secure\ Mobility\ Client.app
   ```
   
   Same configuration as Windows

3. **Verify Connection**
   ```bash
   # Check VPN status
   /opt/cisco/anyconnect/bin/vpn state
   
   # Test connectivity
   ping diagrams.bayer.com
   curl https://diagrams.bayer.com/health
   ```

### Linux (OpenConnect)

```bash
# Install OpenConnect (Cisco AnyConnect compatible)
sudo apt-get install openconnect

# Connect to Bayer VPN
sudo openconnect --protocol=anyconnect vpn.bayer.com

# Enter credentials when prompted
Username: firstname.lastname@bayer.com
Password: ********

# Verify connection
ping diagrams.bayer.com
curl https://diagrams.bayer.com/health
```

## Split Tunnel Configuration

### Enabled Routes (Through VPN)

Only Bayer internal resources route through VPN:

```
10.0.0.0/8         # Bayer corporate network
172.16.0.0/12      # Bayer VPN pool
192.168.0.0/16     # Bayer Europe
diagrams.bayer.com # AutoGraph production
*.bayer.com        # All Bayer internal domains
```

### Direct Routes (Bypass VPN)

Public internet traffic bypasses VPN:

```
0.0.0.0/0 except above  # Direct to internet
```

### Benefits

- Faster internet access for non-Bayer sites
- Reduced VPN bandwidth consumption
- Better user experience
- Compliance with data routing policies

## Firewall Rules

### Inbound (From VPN)

```
Port 443 (HTTPS) → AutoGraph Load Balancer
    Allow from: Bayer VPN Pool (172.16.0.0/12)
    Protocol: TCP
    TLS Version: 1.3 minimum
    
Port 80 (HTTP) → Redirect to 443
    Action: Redirect to HTTPS
```

### Outbound (From AutoGraph)

```
Port 443 (HTTPS) → External APIs
    Allow to: Azure AD, MGA API, Azure DevOps
    Protocol: TCP
    
Port 587 (SMTP) → Email Server
    Allow to: smtp.bayer.com
    Protocol: TCP with TLS
```

### Service-to-Service (Internal)

```
All internal services communicate on private subnet (10.0.1.0/24)
No firewall rules needed between services
```

## Network Performance

### Latency Requirements

| Connection Type | Target Latency | Maximum Acceptable |
|----------------|----------------|-------------------|
| VPN → Load Balancer | < 20ms | < 50ms |
| Load Balancer → Frontend | < 5ms | < 10ms |
| Frontend → API Gateway | < 5ms | < 10ms |
| API Gateway → Backend | < 5ms | < 10ms |
| Backend → Database | < 2ms | < 5ms |

### Bandwidth Requirements

| User Activity | Bandwidth | Notes |
|--------------|-----------|-------|
| View diagram | 100 KB/s | Initial load |
| Edit diagram | 50 KB/s | Real-time updates |
| Export PNG | 500 KB/s | One-time download |
| Video tutorial | 2 MB/s | Streaming |

### Optimization

- **CDN**: Static assets cached at edge locations
- **Compression**: Gzip/Brotli for all text content
- **WebSocket**: Persistent connection for real-time collaboration
- **HTTP/2**: Multiplexing for parallel requests

## Troubleshooting

### Cannot Connect to VPN

**Problem**: Cisco AnyConnect fails to connect

**Solutions**:
1. Check credentials: `firstname.lastname@bayer.com`
2. Approve MFA push notification within 60 seconds
3. Verify VPN client is up to date
4. Contact Bayer IT Help Desk: +49-123-456-7890

### VPN Connected but Cannot Access AutoGraph

**Problem**: VPN shows "Connected" but diagrams.bayer.com unreachable

**Solutions**:
1. Verify DNS resolution:
   ```bash
   nslookup diagrams.bayer.com
   # Should return: 10.0.1.10
   ```

2. Check routing table:
   ```bash
   # Windows
   route print | findstr "10.0.0.0"
   
   # macOS/Linux
   netstat -rn | grep 10.0.0.0
   ```

3. Ping load balancer:
   ```bash
   ping 10.0.1.10
   ```

4. Test HTTPS:
   ```bash
   curl -v https://diagrams.bayer.com/health
   ```

5. If still failing, contact Network Operations: network-ops@bayer.com

### Slow Performance on VPN

**Problem**: AutoGraph is slow when connected via VPN

**Solutions**:
1. Check VPN latency:
   ```bash
   ping -c 10 10.0.1.10
   # Target: < 50ms average
   ```

2. Check bandwidth:
   ```bash
   speedtest-cli --server bayer-internal
   # Target: > 10 Mbps download, > 5 Mbps upload
   ```

3. Try different VPN gateway:
   - Europe: `vpn-eu.bayer.com`
   - Americas: `vpn-us.bayer.com`
   - APAC: `vpn-ap.bayer.com`

4. Disable split tunnel (route all traffic through VPN):
   - May be slower for internet but faster for AutoGraph
   - Configure in Cisco AnyConnect preferences

### SSL/TLS Certificate Errors

**Problem**: Browser shows certificate warning

**Solutions**:
1. Install Bayer root CA certificate:
   - Download from: https://it.bayer.com/certificates
   - Import to system trust store

2. Windows:
   ```powershell
   certutil -addstore -f "Root" BayerRootCA.crt
   ```

3. macOS:
   ```bash
   sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain BayerRootCA.crt
   ```

4. Linux:
   ```bash
   sudo cp BayerRootCA.crt /usr/local/share/ca-certificates/
   sudo update-ca-certificates
   ```

## Security Considerations

### Network Segmentation

AutoGraph is deployed in isolated subnet with strict firewall rules:
- Only VPN users can access
- No direct internet access
- All traffic encrypted (TLS 1.3)
- Network logs sent to Bayer SIEM

### Data in Transit

All data encrypted:
- VPN tunnel: TLS 1.3
- AutoGraph ↔ Browser: TLS 1.3
- Service ↔ Service: mTLS (mutual TLS)
- Database connections: TLS 1.3

### Monitoring

Network traffic monitored 24/7:
- Intrusion Detection System (IDS)
- Data Loss Prevention (DLP)
- Anomaly detection
- Automated alerts to SOC

## VPN Alternatives

### For External Partners

External partners without Bayer VPN access can use:

1. **Azure Virtual Desktop (AVD)**
   - Managed virtual desktop with AutoGraph access
   - No VPN required
   - Contact: avd-support@bayer.com

2. **Temporary VPN Access**
   - Short-term VPN credentials
   - Requires approval from Bayer sponsor
   - Contact: vpn-access@bayer.com

3. **Zero Trust Network Access (ZTNA)**
   - Device posture check
   - Conditional access
   - Contact: ztna-support@bayer.com

## Support Contacts

| Issue Type | Contact | Email | Phone |
|-----------|---------|-------|-------|
| VPN Connection | Bayer IT Help Desk | helpdesk@bayer.com | +49-123-456-7890 |
| Network Issues | Network Operations | network-ops@bayer.com | +49-123-456-7891 |
| AutoGraph Access | AutoGraph Support | autograph-support@bayer.com | +49-123-456-7892 |
| Security Issues | IT Security | itsecurity@bayer.com | +49-123-456-7893 |

## Appendix

### Network Diagram

```
                                  Internet
                                      ↓
                         [Bayer Corporate Firewall]
                                      ↓
                         [VPN Gateway Cluster]
                          (vpn.bayer.com)
                                      ↓
                         [Internal DNS Servers]
                                      ↓
                    [Application Gateway / WAF]
                                      ↓
                      [AutoGraph Load Balancer]
                         (10.0.1.10)
                                      ↓
                    ┌─────────────────┴─────────────────┐
                    ↓                                   ↓
              [Frontend Nodes]                  [API Gateway Nodes]
               10.0.1.20-25                      10.0.1.30-35
                    ↓                                   ↓
                    └─────────────────┬─────────────────┘
                                      ↓
                           [Backend Services]
                            10.0.1.40-50
                                      ↓
                    ┌─────────────────┼─────────────────┐
                    ↓                 ↓                 ↓
              [PostgreSQL]        [Redis]           [MinIO]
               10.0.1.60         10.0.1.70         10.0.1.80
```

### VPN Configuration File

For advanced users, VPN configuration can be automated:

```xml
<!-- Cisco AnyConnect Profile -->
<AnyConnectProfile>
  <ServerList>
    <HostEntry>
      <HostName>Bayer VPN</HostName>
      <HostAddress>vpn.bayer.com</HostAddress>
    </HostEntry>
  </ServerList>
  <EnableSplitTunnel>true</EnableSplitTunnel>
  <SplitTunnelNetworkList>
    <RouteList>
      <Route>10.0.0.0/8</Route>
      <Route>172.16.0.0/12</Route>
      <Route>192.168.0.0/16</Route>
    </RouteList>
  </SplitTunnelNetworkList>
</AnyConnectProfile>
```

---

**Document Version**: 1.0  
**Last Updated**: 2025-12-24  
**Author**: AutoGraph DevOps Team  
**Approved By**: Bayer IT Network Team
