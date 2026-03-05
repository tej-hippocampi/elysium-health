# SendGrid DNS Records for archangelhealth.com

Add these records **where your domain’s DNS is managed** (e.g. GoDaddy, Namecheap, Cloudflare, Google Domains, Vercel, etc.). That’s usually your domain registrar or your hosting/DNS provider.

---

## Step 1: Open DNS settings

1. Log in to the place where you bought or manage **archangelhealth.com**.
2. Find **DNS**, **DNS Management**, **DNS Records**, or **Manage Domain**.
3. Open the DNS records page for **archangelhealth.com**.

---

## Step 2: Add these 6 records

Add each row below as a **new record**. Use the exact **Type**, **Host**, and **Value**.

**Host note:** Some providers want only the **subdomain** (e.g. `url5867`), others want the **full name** (e.g. `url5867.archangelhealth.com`). If a field is labeled “Name” or “Host”, try the subdomain first; if it doesn’t work, use the full name. Leave “blank” or “@” only when the instructions say “leave default”.

| # | Type | Host (Name) | Value (Points to / Content) |
|---|------|-------------|-----------------------------|
| 1 | **CNAME** | `url5867` | `sendgrid.net` |
| 2 | **CNAME** | `60597807` | `sendgrid.net` |
| 3 | **CNAME** | `em6318` | `u60597807.wl058.sendgrid.net` |
| 4 | **CNAME** | `s1._domainkey` | `s1.domainkey.u60597807.wl058.sendgrid.net` |
| 5 | **CNAME** | `s2._domainkey` | `s2.domainkey.u60597807.wl058.sendgrid.net` |
| 6 | **TXT** | `_dmarc` | `v=DMARC1; p=none;` |

- **TTL:** Leave default (e.g. 3600 or 1 hour) unless your provider requires something else.
- **Proxy/CDN:** If you use Cloudflare, set the orange cloud to **DNS only (grey)** for these records so they don’t get proxied.

---

## Step 3: Save and wait

- Save all records.
- DNS can take from a few minutes up to **24–48 hours** to propagate.
- In SendGrid, use **Verify** or **Check DNS**; it may take a couple of tries once propagation is done.

---

## If your provider asks for “full hostname”

Some panels want the full hostname in the Host/Name field. In that case use:

| Type | Host (full) | Value |
|------|-------------|--------|
| CNAME | `url5867.archangelhealth.com` | `sendgrid.net` |
| CNAME | `60597807.archangelhealth.com` | `sendgrid.net` |
| CNAME | `em6318.archangelhealth.com` | `u60597807.wl058.sendgrid.net` |
| CNAME | `s1._domainkey.archangelhealth.com` | `s1.domainkey.u60597807.wl058.sendgrid.net` |
| CNAME | `s2._domainkey.archangelhealth.com` | `s2.domainkey.u60597807.wl058.sendgrid.net` |
| TXT | `_dmarc.archangelhealth.com` | `v=DMARC1; p=none;` |

---

## Quick reference by provider

- **Cloudflare:** DNS → Records → Add record → choose CNAME or TXT.
- **GoDaddy:** My Products → DNS → Add → choose record type.
- **Namecheap:** Domain List → Manage → Advanced DNS → Add New Record.
- **Google Domains / Cloud Identity:** DNS → Custom records → Create.
- **Vercel:** Project → Settings → Domains → DNS for your domain (or use the registrar’s DNS).

After the records are in place and verified in SendGrid, you can send from addresses like `noreply@archangelhealth.com` and improve deliverability.
