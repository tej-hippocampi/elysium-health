# Cloudflare DNS import – archangelhealth.com

## File to import

Use: **`cloudflare-dns-import-archangelhealth.com.txt`**

In Cloudflare: **DNS** → **Records** → **Import** → choose that file.

---

## Proxy imported DNS records?

**Leave the checkbox UNCHECKED.** Do **not** proxy these records.

After import, make sure every **SendGrid** record (the 6 records: url5867, 60597807, em6318, s1._domainkey, s2._domainkey, _dmarc) is **DNS only** (grey cloud). If any are proxied (orange cloud), click the cloud to turn them grey.

---

## What’s in the file

1. **Cloudflare recommended**
   - **Root (A)** – `archangelhealth.com` → `192.0.2.1`  
     **Update this** to your real website IP or replace with a CNAME to your host (e.g. Vercel/Netlify).
   - **www (CNAME)** – `www.archangelhealth.com` → `archangelhealth.com`  
     So `www` works when root is correct.
   - **MX** – priority 10 → `mail.archangelhealth.com`  
     **Update this** if you receive email at `@archangelhealth.com` (point to your real mail server, e.g. Google Workspace, Microsoft 365, or your ESP).
   - **SPF (TXT at root)** – `v=spf1 include:sendgrid.net ~all`  
     Allows SendGrid to send as `@archangelhealth.com`.

2. **SendGrid (all 6)**
   - Link/tracking: url5867, 60597807, em6318 → SendGrid.
   - DKIM: s1._domainkey, s2._domainkey → SendGrid.
   - DMARC: _dmarc → `v=DMARC1; p=none;`

---

## After import

1. Set all **SendGrid** records to **DNS only** (grey cloud).
2. Edit the **root A record**: change `192.0.2.1` to your real site IP or replace with the CNAME your host gives you.
3. If you receive mail at this domain, edit the **MX** record to your real mail host.
4. Wait 5–10 minutes, then in SendGrid run **Verify** again.
