# Cloudflare DNS import – archangelhealth.ai

## File to import

**`cloudflare-dns-import-archangelhealth.ai.txt`**

In Cloudflare: **DNS** → **Records** → **Import** → choose that file.

---

## Proxy imported DNS records?

**Leave the checkbox UNCHECKED.** Do not proxy these records.

After import, set every **SendGrid** record (url9174, 60597807, em5385, s1._domainkey, s2._domainkey, _dmarc) to **DNS only** (grey cloud).

---

## What’s in the file

### Cloudflare recommended steps

1. **Root (A)** – `archangelhealth.ai` → `192.0.2.1`  
   **Update** to your real site IP or replace with CNAME to your host (e.g. Vercel/Netlify).

2. **www (CNAME)** – `www.archangelhealth.ai` → `archangelhealth.ai`  
   So `www` resolves when root is correct.

3. **MX** – priority 10 → `mail.archangelhealth.ai`  
   **Update** if you receive email at `@archangelhealth.ai` (point to your real mail server).

4. **SPF (TXT at root)** – `v=spf1 include:sendgrid.net ~all`  
   Allows SendGrid to send as `@archangelhealth.ai`.

### SendGrid (all 6 from SendGrid)

- **Link/tracking:** url9174, 60597807, em5385 → SendGrid
- **DKIM:** s1._domainkey, s2._domainkey → SendGrid
- **DMARC:** _dmarc → `v=DMARC1; p=none;`

---

## After import

1. Set all **SendGrid** records to **DNS only** (grey cloud).
2. Edit **root A**: change `192.0.2.1` to your site IP or your host’s CNAME.
3. If you receive mail at this domain, edit **MX** to your real mail host.
4. Wait 5–10 minutes, then run **Verify** in SendGrid.
