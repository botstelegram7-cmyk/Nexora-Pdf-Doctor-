# 🤖 PDF Doctor Bot
> **GitHub:** [@SerenaXdev](https://github.com/SerenaXdev)

An all-in-one Telegram PDF toolkit bot with premium plans, OCR, handwriting styles, and much more!

---

## ✨ Features

| Feature | Free | Basic | Pro |
|---------|------|-------|-----|
| All PDF Tools | ✅ (3/day) | ✅ Unlimited | ✅ Unlimited |
| Compress PDF | ✅ | ✅ | ✅ |
| Split / Merge PDFs | ✅ | ✅ | ✅ |
| Lock / Unlock PDF | ✅ | ✅ | ✅ |
| Repair Corrupted PDF | ✅ | ✅ | ✅ |
| Watermark (Text/Logo/Invisible) | ✅ | ✅ | ✅ |
| Dark Mode / BG Changer | ✅ | ✅ | ✅ |
| PDF → Excel | ✅ | ✅ | ✅ |
| PDF ↔ Images | ✅ | ✅ | ✅ |
| Page Numbers | ✅ | ✅ | ✅ |
| Handwritten PDF (6 fonts!) | ✅ | ✅ | ✅ |
| OCR (Image/PDF → Text) | ✅ | ✅ | ✅ |

---

## 🚀 Deployment on Render

### 1. Fork & Setup
```bash
git clone https://github.com/SerenaXdev/pdf-doctor-bot
cd pdf-doctor-bot
```

### 2. Create Bot
- Go to [@BotFather](https://t.me/BotFather) on Telegram
- Send `/newbot` and follow the steps
- Copy your **BOT_TOKEN**

### 3. Get Your User ID
- Message [@userinfobot](https://t.me/userinfobot)
- Copy your **User ID** (this will be your OWNER_ID)

### 4. Deploy on Render
1. Create a [Render](https://render.com) account
2. Click **New → Web Service**
3. Connect your GitHub repo
4. Render auto-detects `render.yaml`
5. Set the environment variables in Render dashboard:

| Variable | Required | Description |
|----------|----------|-------------|
| `BOT_TOKEN` | ✅ | From @BotFather |
| `OWNER_ID` | ✅ | Your Telegram User ID |
| `UPI_ID` | ❌ | Your UPI ID (e.g. name@paytm) |
| `UPI_QR_URL` | ❌ | URL to your UPI QR image |
| `START_IMAGE` | ❌ | URL/file_id for welcome image |
| `MONGODB_URL` | ❌ | MongoDB URL (SQLite used if empty) |

6. Click **Deploy!** 🚀

---

## 💰 Premium System

### Granting Premium (Owner Only)
```
/givepremium <user_id> basic    → 1 Month Basic
/givepremium <user_id> pro      → 1 Year Pro
```

### Payment Flow
1. User clicks **Buy Premium**
2. Bot shows UPI ID + QR code
3. User pays and sends screenshot
4. Screenshot forwarded to owner
5. Owner verifies and runs `/givepremium`

---

## 🛠️ Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Install Tesseract OCR
# Ubuntu: sudo apt install tesseract-ocr
# Mac: brew install tesseract

# Setup env
cp .env.example .env
# Edit .env with your values

# Run
python main.py
```

---

## 📋 Commands Reference

| Command | Description |
|---------|-------------|
| `/start` | Main menu |
| `/help` | All commands |
| `/account` | My account & plan |
| `/premium` | View/buy premium |
| `/compress` | Compress PDF |
| `/split` | Split PDF pages |
| `/merge` | Merge multiple PDFs |
| `/lock` | Password protect PDF |
| `/unlock` | Remove PDF password |
| `/repair` | Fix corrupted PDF |
| `/watermark` | Add watermark |
| `/darkmode` | Convert to dark mode |
| `/pagenos` | Add page numbers |
| `/pdf2img` | PDF to images |
| `/img2pdf` | Images to PDF |
| `/excel` | PDF to Excel |
| `/bgchange` | Change background color |
| `/handwrite` | Handwritten style PDF |
| `/ocr` | Extract text from image/PDF |

---

## 🏗️ Tech Stack

- **Language:** Python 3.11
- **Bot Framework:** python-telegram-bot 20.x
- **PDF Engine:** PyMuPDF + pikepdf + pdfplumber
- **OCR:** pytesseract + Tesseract
- **Database:** SQLite (default) / MongoDB (optional)
- **Web Server:** aiohttp (Render health checks)
- **Deployment:** Docker + Render

---

## 📜 License
MIT License — Made with ❤️ by [@SerenaXdev](https://github.com/SerenaXdev)
