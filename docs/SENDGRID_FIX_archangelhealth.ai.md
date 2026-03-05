# Fix SendGrid verification for archangelhealth.ai

SendGrid is checking for **different hostnames and targets** than what you had. Here’s what to change in Cloudflare so validation passes.

---

## What’s wrong

| SendGrid expects | You had | Fix |
|------------------|---------|-----|
| **u9174** → sendgrid.net | url9174 → sendgrid.net | Use host **u9174** (no "rl") |
| **em6318** → u0597807.u1058.sendgrid.net | em5385 → u60597807.wl058... | Use host **em6318** and target **u0597807.u1058.sendgrid.net** |
| s1._domainkey → s1.domainkey.**u0597807.u1058**.sendgrid.net | ...u60597807.wl058... | Change target to **u0597807.u1058** |
| s2._domainkey → s2.domainkey.**u0597807.u1058**.sendgrid.net | ...u60597807.wl058... | Same as above |
| _dmarc → "v=DMARC1; p=none" | "v=DMARC1; p=none;" | Optional: remove trailing semicolon |

---

## What to do in Cloudflare

### 1. First link (link branding)

- **Delete** the CNAME record whose name is **url9174**.
- **Add** a new CNAME:
  - **Name:** `u9174`
  - **Target:** `sendgrid.net`
  - **Proxy:** DNS only (grey cloud)

### 2. Link tracking host

- **Edit** the CNAME whose name is **em5385**:
  - Change **Name** to **em6318** (leave the zone as archangelhealth.ai).
  - Change **Target** to **u0597807.u1058.sendgrid.net**
  - **Proxy:** DNS only (grey cloud)

(If your provider only allows editing target, delete em5385 and create a new record with Name **em6318** and Target **u0597807.u1058.sendgrid.net**.)

### 3. DKIM (s1 and s2)

- **s1._domainkey**  
  Edit the CNAME and set **Target** to:  
  `s1.domainkey.u0597807.u1058.sendgrid.net`  
  (DNS only.)

- **s2._domainkey**  
  Edit the CNAME and set **Target** to:  
  `s2.domainkey.u0597807.u1058.sendgrid.net`  
  (DNS only.)

### 4. DMARC (optional)

- ** _dmarc**  
  If validation still fails for DMARC, edit the TXT and set **Content** to exactly:  
  `v=DMARC1; p=none`  
  (no semicolon at the end.)

### 5. 60597807

- Leave as is (already **60597807** → sendgrid.net).

---

## Checklist

- [ ] CNAME **u9174** → sendgrid.net (not url9174)
- [ ] CNAME **60597807** → sendgrid.net
- [ ] CNAME **em6318** → u0597807.u1058.sendgrid.net (not em5385)
- [ ] CNAME **s1._domainkey** → s1.domainkey.u0597807.u1058.sendgrid.net
- [ ] CNAME **s2._domainkey** → s2.domainkey.u0597807.u1058.sendgrid.net
- [ ] TXT **_dmarc** → v=DMARC1; p=none
- [ ] All six above set to **DNS only** (grey cloud)

Wait 5–10 minutes, then click **Verify** again in SendGrid.
