
# AI Image Generator App
import streamlit as st
import pandas as pd
import openai
import os
import time
import requests
import zipfile
from io import BytesIO
from datetime import datetime
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import smtplib
from email.message import EmailMessage

st.set_page_config(page_title="AI Image Generator", layout="centered")
st.title("🖼️ AI Image Generator + Google Drive Upload")
st.markdown("Upload an Excel file with prompts, styles, and sizes to generate images using OpenAI DALL·E 3.")

# Inputs
openai_key = st.text_input("🔑 Enter your OpenAI API Key", type="password")
uploaded_file = st.file_uploader("📁 Upload Excel File (.xlsx)", type=["xlsx"])
project_name = st.text_input("📝 Enter a name for your image zip file", value="generated_images")
email_recipient = st.text_input("📧 Enter email(s) to receive ZIP (comma-separated)")
email_subject = st.text_input("✉️ Email Subject", value="Your Generated Images ZIP")
email_message = st.text_area("📝 Email Message", value="Here is your image zip file and upload log.")
include_log = st.checkbox("📎 Attach upload log CSV to email", value=True)
preview_email = st.checkbox("👁️ Preview email before sending", value=True)

def send_zip_email(recipients, zip_bytes, log_path, zip_filename, subject, message, attach_log):
    try:
        for email in recipients:
            msg = EmailMessage()
            msg['Subject'] = subject
            msg['From'] = 'your_email@gmail.com'
            msg['To'] = email
            msg.set_content(message)

            msg.add_attachment(zip_bytes.read(), maintype='application', subtype='zip', filename=zip_filename)
            zip_bytes.seek(0)

            if attach_log:
                with open(log_path, "rb") as log_file:
                    msg.add_attachment(log_file.read(), maintype='text', subtype='csv', filename='upload_log.csv')

            if preview_email:
                st.info(f"Previewing email to: {email}\nSubject: {subject}\nMessage: {message}")

            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login('your_email@gmail.com', 'your_app_password')  # Use app password
                smtp.send_message(msg)
        return True
    except Exception as e:
        st.error(f"❌ Failed to send email: {e}")
        return False

if uploaded_file and openai_key:
    try:
        openai.api_key = openai_key
        df = pd.read_excel(uploaded_file)
        df = df.dropna(subset=["Prompt"])
        st.success(f"Loaded {len(df)} prompts.")
        st.dataframe(df)

        if st.button("🚀 Generate and Upload Images"):
            st.info("Authenticating with Google Drive...")
            gauth = GoogleAuth()
            gauth.LocalWebserverAuth()
            drive = GoogleDrive(gauth)

            session_name = datetime.now().strftime("Session_%Y-%m-%d_%H%M")
            session_folder_metadata = {
                'title': session_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            session_folder = drive.CreateFile(session_folder_metadata)
            session_folder.Upload()
            session_folder_id = session_folder['id']
            st.success(f"Created session folder: {session_name}")

            local_folder = "generated_images"
            os.makedirs(local_folder, exist_ok=True)
            style_folders = {}
            log_data = []
            image_paths = []
            progress = st.progress(0)

            for i, row in df.iterrows():
                try:
                    prompt = str(row["Prompt"]).strip()
                    style = str(row.get("Style", "Uncategorized")).strip()
                    size = str(row.get("Size", "1024x1024")).strip()
                    full_prompt = f"{prompt}, {style}" if style.lower() not in prompt.lower() else prompt

                    response = openai.Image.create(prompt=full_prompt, n=1, size=size)
                    image_url = response["data"][0]["url"]
                    image_data = requests.get(image_url).content

                    filename = f"image_{i+1}.png"
                    local_path = os.path.join(local_folder, filename)
                    with open(local_path, "wb") as f:
                        f.write(image_data)

                    image_paths.append(local_path)

                    if style not in style_folders:
                        folder_metadata = {
                            'title': style,
                            'mimeType': 'application/vnd.google-apps.folder',
                            'parents': [{'id': session_folder_id}]
                        }
                        folder = drive.CreateFile(folder_metadata)
                        folder.Upload()
                        style_folders[style] = folder['id']
                    style_folder_id = style_folders[style]

                    file_drive = drive.CreateFile({
                        'title': filename,
                        'parents': [{'id': style_folder_id}]
                    })
                    file_drive.SetContentFile(local_path)
                    file_drive.Upload()
                    file_url = f"https://drive.google.com/uc?id={file_drive['id']}"

                    log_data.append({
                        "Prompt": prompt,
                        "Style": style,
                        "Size": size,
                        "Filename": filename,
                        "Drive URL": file_url
                    })

                    progress.progress((i+1)/len(df))
                    st.image(local_path, caption=prompt, width=400)
                    time.sleep(2)

                except Exception as e:
                    st.error(f"Error with prompt {i+1}: {e}")

            log_df = pd.DataFrame(log_data)
            log_file = "upload_log.csv"
            log_df.to_csv(log_file, index=False)

            log_drive = drive.CreateFile({
                'title': log_file,
                'parents': [{'id': session_folder_id}]
            })
            log_drive.SetContentFile(log_file)
            log_drive.Upload()

            st.success("✅ All images generated and uploaded!")
            st.download_button("📥 Download Upload Log", data=log_df.to_csv(index=False), file_name="upload_log.csv")

            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zipf:
                for path in image_paths:
                    zipf.write(path, os.path.basename(path))
            zip_buffer.seek(0)
            zip_filename = f"{project_name}.zip"

            st.download_button("📦 Download All Images as ZIP", data=zip_buffer, file_name=zip_filename)

            if email_recipient:
                recipient_list = [e.strip() for e in email_recipient.split(",") if e.strip()]
                st.info("Sending ZIP file and optional log to email(s)...")
                if send_zip_email(recipient_list, zip_buffer, log_file, zip_filename, email_subject, email_message, include_log):
                    st.success("✅ Email(s) sent successfully!")

    except Exception as e:
        st.error(f"❌ Something went wrong: {e}")
