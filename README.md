# 🗼 WatchTower

> An on-premises monitoring, security, and automation platform built for educational and SMB environments. WatchTower unifies server health, network metrics, security logs, and automated remediation into a single visual dashboard — no cloud dependency, no expensive licenses.

---

## 💡 The Problem

Sysadmins and students managing networks often juggle **multiple disconnected tools** — one for metrics, one for logs, one for alerts, another for backups. WatchTower solves this by centralizing everything into one platform you fully own and control.

---

## 🎯 Objectives

- Build a fully functional and secure virtual infrastructure on Proxmox VE
- Centralize system performance, logs, and security alerts in a single visual panel
- Detect failures and potential threats in **real time**
- Automate administration tasks with Ansible to reduce manual work
- Protect data with automated backups (local + optional cloud)

---

## 🧱 Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Hypervisor** | Proxmox VE | Hosts all virtual machines |
| **Firewall / VPN** | pfSense | VLAN segmentation, firewall rules, OpenVPN |
| **DNS / DHCP** | Pi-hole v6 | Internal DNS (`.home.arpa`), DHCP monitoring |
| **Metrics** | Prometheus + Grafana | Scraping, dashboards, and alerting |
| **Log Analysis** | Elastic Stack (ELK) | Log ingestion, search, and visualization |
| **Automation** | Ansible | Playbooks for config management and auto-remediation |
| **Backend** | FastAPI (Python) | Receives Grafana webhooks → triggers Ansible playbooks |
| **Backups** | Rclone + HDD | Scheduled backups with retention (local + Google Drive) |
| **Notifications** | Telegram Bot / Discord Bot | Real-time alert delivery |

---

## 🌐 Network Architecture

WatchTower runs across **segmented VLANs** on a single Proxmox host:

| VLAN | Name | Subnet | Services |
|------|------|--------|----------|
| 10 | MGMT | 192.168.10.0/24 | Management access |
| 20 | MONITOR | 192.168.20.0/24 | Prometheus + Grafana |
| 30 | LOGGING | 192.168.30.0/24 | ELK Stack |
| 40 | AUTO | 192.168.40.0/24 | Ansible + FastAPI |
| 50 | INFRA | 192.168.50.0/24 | Pi-hole DNS |
| 60 | BACKUP | 192.168.60.0/24 | Backup VM |
| 80 | DMZ | 192.168.80.0/24 | HAProxy reverse proxy |

HAProxy in the DMZ exposes **Grafana**, **Kibana**, and **FastAPI** securely.

---

## ⚙️ How Auto-Remediation Works

```
Prometheus detects anomaly
       ↓
Grafana fires alert webhook
       ↓
FastAPI validates the request
       ↓
FastAPI triggers Ansible playbook
       ↓
Service restarted / backup triggered automatically
       ↓
Action logged to database (PostgreSQL)
```

---

## 👥 Team — Tim Berners-Lee (ICA001.S1)

| Member | Individual Module |
|--------|------------------|
| **Chadric Hans Masangkay** | mini dashboard using Telegram Bot commands |
| **David Yang** | Automation modules — Ansible playbooks, alert-triggered remediation |
| **Gabriel Cabrera i Noguero** | Ethical hacking / Red-Blue Team — Suricata IDS, Metasploit, ELK integration |

---

## 🚀 Getting Started

```bash
# Clone the repo
git clone https://github.com/CHM-bot-blip/WatchTower.git
cd WatchTower

# Set up environment variables
cp .env.example .env
# Edit .env with your credentials

# Start all services
docker compose up -d
```

> ⚠️ Requires a Proxmox environment with the VLANs configured. See [`deployment.md`](./deployment.md) for full setup.

---

## 📁 Project Structure

```
WatchTower/
├── src/                  # FastAPI backend
├── frontend/             # Dashboard UI
├── telegram-bot/         # Telegram alert integration
├── discord-bot/          # Discord alert integration
├── compose.yml           # Docker Compose
├── deployment.md         # Full production deployment guide
├── development.md        # Local dev environment setup
└── README.md
```

---

## 📊 Compared to Alternatives

| Tool | Type | Key Difference |
|------|------|----------------|
| Datadog | SaaS | Cloud-managed, expensive, no on-prem control |
| Splunk | Enterprise SIEM | Powerful but complex and costly |
| Wazuh | Open-source XDR | Great for SIEM, but no custom auto-remediation flow |
| **WatchTower** | On-prem | Fully self-hosted, modular, built for education/SMB |

---

## 📄 License

See [`LICENSE`](./LICENSE) for details.


## 🙏 Credits

- **FastAPI** by Sebastián Ramírez (@tiangolo) — the backend framework
  powering WatchTower's API and auto-remediation engine.
