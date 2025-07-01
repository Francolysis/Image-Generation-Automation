import streamlit as st
import pandas as pd
import openai
import os
import time
import requests
from datetime import datetime
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

# --- PAGE CONFIG ---
st.set_page_config(page_title="AI Image Generator", layout="centered")
st.title("🖼️ AI Image Generator + Google Drive Upload")
st.markdown("Upload an Excel file with prompts, styles, and sizes to generate images using OpenAI DALL·E 3.")

# --- INPUTS ---
openai_key = st.text_input("🔑 Enter your OpenAI API Key", type="password")
uploaded_file = st.file_uploader("📁 Upload Excel File (.xlsx)", type=["xlsx"])

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

            # Create session folder
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

                    # Create/find style subfolder in session folder
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

                    # Upload to style folder under session
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

            # Save and upload log
            log_df = pd.DataFrame(log_data)
            log_file = "upload_log.csv"
            log_df.to_csv(log_file, index=False)
            st.success("✅ All images generated and uploaded!")
            st.download_button("📥 Download Upload Log", data=log_df.to_csv(index=False), file_name="upload_log.csv")

            # Upload log to session folder
            log_drive = drive.CreateFile({
                'title': log_file,
                'parents': [{'id': session_folder_id}]
            })
            log_drive.SetContentFile(log_file)
            log_drive.Upload()
            st.info(f"Log also uploaded to: {session_name}")

    except Exception as e:
        st.error(f"❌ Something went wrong: {e}")
