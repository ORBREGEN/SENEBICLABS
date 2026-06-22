# Hosting Label Studio on a Google Cloud VM (free during the trial)

Goal: an always-on, HTTPS Label Studio at `https://annotate.senebiclabs.com` that a
remote clinician can use without you, with data on your own VM.

Run the `gcloud` commands in Cloud Shell (project already set to `senebiclabs`).

---

## 1. Reserve a static IP (so DNS never breaks)
```bash
gcloud compute addresses create senebiclabs-ls-ip --region=us-central1
gcloud compute addresses describe senebiclabs-ls-ip --region=us-central1 --format='value(address)'
```
Note the IP it prints — you'll point DNS at it in step 4.

## 2. Create the VM
```bash
gcloud compute instances create senebiclabs-ls \
  --zone=us-central1-a \
  --machine-type=e2-small \
  --image-family=ubuntu-2204-lts --image-project=ubuntu-os-cloud \
  --boot-disk-size=30GB \
  --address=senebiclabs-ls-ip \
  --tags=http-server,https-server
```
(`e2-small` = 2 GB RAM, comfortable, covered by your trial credit. To stay in the
*always-free* tier instead, use `--machine-type=e2-micro` — tighter, add swap below.)

## 3. Open the firewall for web traffic
```bash
gcloud compute firewall-rules create allow-http  --allow=tcp:80  --target-tags=http-server  2>/dev/null || true
gcloud compute firewall-rules create allow-https --allow=tcp:443 --target-tags=https-server 2>/dev/null || true
```

## 4. Point DNS at the VM
In your domain's DNS (wherever senebiclabs.com is managed), add an **A record**:
```
annotate   A   <the static IP from step 1>
```
Wait a couple of minutes for it to resolve (`ping annotate.senebiclabs.com`).

## 5. SSH in and install Docker
```bash
gcloud compute ssh senebiclabs-ls --zone=us-central1-a
```
Then on the VM:
```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER && newgrp docker
# (optional, recommended on e2-micro) add 2 GB swap:
sudo fallocate -l 2G /swapfile && sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile
```

## 6. Get this folder onto the VM and configure
```bash
git clone https://github.com/ORBREGEN/SENEBICLABS.git
cd SENEBICLABS/docker/labelstudio-vm
cp .env.example .env
nano .env          # set LS_DOMAIN + strong passwords
```

## 7. Launch
```bash
docker compose up -d
docker compose logs -f caddy   # watch it obtain the HTTPS cert (Ctrl-C when done)
```
Visit **https://annotate.senebiclabs.com** — Label Studio, on HTTPS, always on.
Log in with the `LS_ADMIN_EMAIL` / `LS_ADMIN_PASSWORD` you set.

## 8. Wire it to the rest of the platform
- Get a **legacy API token**: Label Studio → Account & Settings → enable Legacy Tokens → copy the 40-char hex token.
- On **Cloud Run** (and your local `.env`), set:
  ```
  LS_URL=https://annotate.senebiclabs.com
  LS_TOKEN=<the 40-char token>
  ```
  Now "Send to Label Studio" / "Pull results" work against the hosted instance.

## 9. Add your clinician
Label Studio → the project → **Settings → Members → Add** (or invite by email).
Send them `https://annotate.senebiclabs.com` and their login. They can label any time.

---

### Costs / lifecycle
- During the GCP free trial: **$0** (covered by credit). A pilot finishes long before the
  90-day trial ends, so no mid-pilot disruption.
- After the trial: an `e2-small` is ~$13/mo. Once the first pilot pays, either keep it or
  move the same `docker-compose` to a $6/mo VM (Hetzner/DigitalOcean). Nothing changes but the host.

### To pause billing later
```bash
gcloud compute instances stop senebiclabs-ls --zone=us-central1-a   # stop (keeps data)
gcloud compute instances start senebiclabs-ls --zone=us-central1-a  # resume
```
