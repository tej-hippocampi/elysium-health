# Twilio (SMS) and Email Setup for CareGuide

The **Send to Patient** action in the doctor portal sends the patient dashboard link by **SMS** (Twilio) and **email** (SendGrid Web API preferred, or SMTP fallback). Configure one or both so doctors can deliver recovery resources to patients.

---

## 1. SendGrid — Email (recommended)

The app uses the **SendGrid Web API** when `SENDGRID_API_KEY` is set. Otherwise it falls back to SMTP.

### 1.1 Set environment variables

In `backend/.env`:

```bash
SENDGRID_API_KEY=SG.your_api_key_here
SENDGRID_FROM_EMAIL=noreply@archangelhealth.ai
SENDGRID_FROM_NAME=Archangel Health
```

- **SENDGRID_FROM_EMAIL** must be a verified sender in SendGrid (e.g. from Domain Authentication for archangelhealth.ai).
- Restart the backend after adding the key.

### 1.2 Install dependency

From the repo root: `pip install sendgrid` (or `cd backend && pip install -r requirements.txt`).

---

## 2. Twilio — SMS

### 1.1 Create a Twilio account

1. Go to [twilio.com](https://www.twilio.com) and sign up (free trial is fine).
2. Complete phone verification if prompted.

### 1.2 Get your credentials

1. In the [Twilio Console](https://console.twilio.com), note:
   - **Account SID** (starts with `AC...`)
   - **Auth Token** (click “Show” to reveal)
2. Go to **Phone Numbers → Manage → Buy a number** (or use a trial number).
   - Choose a number that can send SMS (e.g. US number with SMS capability).
   - Trial accounts can send only to **verified** recipient numbers until you upgrade.

### 1.3 Set environment variables

In `backend/.env` (copy from `.env.example` if needed):

```bash
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_FROM_NUMBER=+15551234567
```

- Use your real Account SID, Auth Token, and the Twilio phone number you bought (E.164 format, e.g. `+15551234567`).

### 1.4 How it’s used

- When a doctor clicks **“Send to Patient”** and the patient has a **phone number** on file, the backend sends an SMS via Twilio with the dashboard link.
- If Twilio is not configured, the UI will show something like “SMS: Twilio not configured” and no SMS is sent.

---

## 3. Email — SMTP (fallback)

Email is sent using standard **SMTP** (no Twilio SendGrid API in code). You can use any provider that gives you SMTP credentials.

### 2.1 Option A: Gmail

1. Use a Gmail account (or Google Workspace).
2. Turn on **2-Step Verification** for the account: [Google Account Security](https://myaccount.google.com/security).
3. Create an **App Password**:
   - Go to [App Passwords](https://myaccount.google.com/apppasswords) (or search “App passwords” in your Google account).
   - Create a new app password for “Mail” / “Other (CareGuide)”.
   - Copy the 16-character password (no spaces).
4. In `backend/.env`:

```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=xxxx xxxx xxxx xxxx
```

Use the app password as `SMTP_PASS`, not your normal Gmail password.

### 2.2 Option B: SendGrid (SMTP)

1. Sign up at [sendgrid.com](https://sendgrid.com).
2. Create an API key or use **SMTP Relay** credentials from the SendGrid dashboard.
3. In SendGrid: **Settings → Sender Authentication** — verify your domain or single sender (required for production).
4. In `backend/.env`:

```bash
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASS=SG.xxxxxxxxxxxxxxxxxxxxxxxx
```

Use your SendGrid API key as `SMTP_PASS`; `SMTP_USER` must be the literal word `apikey`.

### 2.3 Option C: Other SMTP (Outlook, Mailgun, etc.)

Use your provider’s SMTP host, port (usually 587 for TLS), and username/password:

```bash
SMTP_HOST=smtp.your-provider.com
SMTP_PORT=587
SMTP_USER=your-username
SMTP_PASS=your-password
```

### 2.4 How it’s used

- When a doctor clicks **“Send to Patient”** and the patient has an **email** on file, the backend sends an HTML email with the dashboard link using the SMTP settings above.
- If SMTP is not configured, the UI will show “Email: SMTP not configured” and no email is sent.

---

## 4. Quick checklist

| Goal              | What to set in `backend/.env` |
|-------------------|------------------------------|
| SMS only          | `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM_NUMBER` |
| Email only        | `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS` |
| SMS + Email       | All of the above             |

- Restart the backend after changing `.env`:  
  `cd backend && python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload`
- Patient records must have a **phone** and/or **email** (from “Add Patient”) for send to work; the button is disabled when there’s no contact info.

---

## 5. Troubleshooting

- **SMS not sending**
  - Confirm the “To” number is in E.164 format (e.g. `+15551234567`).
  - On a Twilio trial, the recipient must be a [verified number](https://console.twilio.com/us1/develop/phone-numbers/manage/verified).
- **Email not sending**
  - Gmail: use an **App Password**, not your normal password; 2-Step Verification must be on.
  - SendGrid: use `SMTP_USER=apikey` and your API key as `SMTP_PASS`; ensure sender/domain is verified.
  - Check backend logs for `[send] Email error: ...` or Twilio/SMTP errors.
