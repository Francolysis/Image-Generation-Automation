# 🖼️ AI Image Generator + Google Drive Uploader

This Streamlit app lets you:

✅ Generate images using OpenAI's DALL·E 3 API  
✅ Organize outputs by style into session-based Google Drive folders  
✅ Upload and log results in a downloadable CSV  
✅ Share images and logs with collaborators — perfect for content creators, designers, and AI teams

---

## 📁 Folder Structure

```
.
├── app.py                # Streamlit application
├── requirements.txt      # Dependencies
└── prompts.xlsx          # Sample Excel input file
```

---

## 📄 prompts.xlsx Format

| Prompt                                | Style               | Size        |
|---------------------------------------|---------------------|-------------|
| A lion wearing a crown in the desert  | oil painting        | 1024x1024   |
| Futuristic African city at dusk       | cyberpunk concept art | 1024x1792   |
| A robot watering flowers in a garden  | watercolor sketch   | 1792x1024   |

---

## 🚀 How to Run It Locally

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the app:
```bash
streamlit run app.py
```

3. Enter your OpenAI API key and upload your Excel file.

---

## ☁️ How to Deploy to Streamlit Cloud

1. Fork or upload this repo to GitHub.
2. Go to [streamlit.io/cloud](https://streamlit.io/cloud)
3. Connect your GitHub and deploy!

---

## 📦 Optional: Convert to a Standalone Desktop App

You can use `pyinstaller` to package it into a .exe:
```bash
pip install pyinstaller
echo import os\nos.system("streamlit run app.py") > run.py
pyinstaller --noconfirm --onefile run.py
```

---

## 🧠 Requirements

- Python 3.8+
- OpenAI API Key
- Google account to authenticate with Google Drive

---

Built with ❤️ by [Your Name]
