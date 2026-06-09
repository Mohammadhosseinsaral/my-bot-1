import os
import time
import requests
from urllib.parse import urlparse

TOKEN = "BGFFBA0CVBEMXGZGLLORZJFYSNUGBXKJVIHBSUHLZAQDJVKELOQYANKCOLXGBJJF"

OFFSET_FILE = "offset.txt"

LAST_MESSAGE_FILE = "last_message_id.txt"

def load_last_message_id():
    try:
        with open(LAST_MESSAGE_FILE, "r") as f:
            return f.read().strip()
    except:
        return None

def save_last_message_id(message_id):
    with open(LAST_MESSAGE_FILE, "w") as f:
        f.write(str(message_id))

def load_offset():
    try:
        with open(OFFSET_FILE, "r") as f:
            return f.read().strip()
    except:
        return None


def save_offset(offset):
    with open(OFFSET_FILE, "w") as f:
        f.write(offset)


def send_message(chat_id, text):
    try:
        requests.post(
            f"https://botapi.rubika.ir/v3/{TOKEN}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": text
            },
            timeout=30
        )
    except Exception as e:
        print("send_message error:", e)


def request_upload_url():
    r = requests.post(
        f"https://botapi.rubika.ir/v3/{TOKEN}/requestSendFile",
        json={
            "type": "File"
        },
        timeout=30
    ).json()

    return r["data"]["upload_url"]


def upload_file(upload_url, filepath):
    with open(filepath, "rb") as f:
        r = requests.post(
            upload_url,
            files={"file": f},
            timeout=300
        ).json()

    return r["data"]["file_id"]


def send_file(chat_id, file_id):
    r = requests.post(
        f"https://botapi.rubika.ir/v3/{TOKEN}/sendFile",
        json={
            "chat_id": chat_id,
            "file_id": file_id
        },
        timeout=30
    )

    return r.json()


def get_filename_from_url(url):
    path = urlparse(url).path
    filename = os.path.basename(path)

    if not filename:
        filename = "downloaded_file"

    return filename


def download_file(url):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    filename = get_filename_from_url(url)

    with requests.get(
        url,
        headers=headers,
        stream=True,
        timeout=60,
        allow_redirects=True
    ) as r:

        r.raise_for_status()

        with open(filename, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)

    return filename


def process_link(chat_id, url):

    filepath = None

    try:

        send_message(
            chat_id,
            "درحال دانلود فایل..."
        )

        filepath = download_file(url)

        send_message(
            chat_id,
            "درحال آپلود به روبیکا..."
        )

        upload_url = request_upload_url()

        file_id = upload_file(
            upload_url,
            filepath
        )

        send_file(
            chat_id,
            file_id
        )

        send_message(
            chat_id,
            "فایل با موفقیت ارسال شد."
        )

    except Exception as e:

        send_message(
            chat_id,
            f"خطا:\n{str(e)}"
        )

        print("ERROR:", e)

    finally:

        if filepath and os.path.exists(filepath):
            try:
                os.remove(filepath)
            except:
                pass


def main():

    print("Bot Started...")

    last_message_id = load_last_message_id()

    while True:

        try:

            r = requests.post(
                f"https://botapi.rubika.ir/v3/{TOKEN}/getUpdates",
                json={"limit": 100},
                timeout=30
            ).json()

            if "data" not in r:
                time.sleep(2)
                continue

            updates = r["data"]["updates"]

            # اولین اجرا: فقط آخرین پیام را ذخیره کن
            if last_message_id is None:

                newest_id = None

                for update in updates:

                    if update.get("type") != "NewMessage":
                        continue

                    msg = update.get("new_message", {})
                    mid = msg.get("message_id")

                    if mid:
                        newest_id = str(mid)

                if newest_id:
                    save_last_message_id(newest_id)
                    last_message_id = newest_id
                    print("Old messages skipped.")

                time.sleep(2)
                continue

            for update in updates:

                if update.get("type") != "NewMessage":
                    continue

                chat_id = update["chat_id"]

                msg = update.get("new_message", {})

                if msg.get("sender_type") != "User":
                    continue

                message_id = str(msg.get("message_id", ""))

                if not message_id:
                    continue

                if message_id <= str(last_message_id):
                    continue

                text = msg.get("text", "").strip()

                if not text:
                    continue

                print("MESSAGE:", text)

                if (
                    text.startswith("http://")
                    or text.startswith("https://")
                ):
                    process_link(chat_id, text)

                save_last_message_id(message_id)
                last_message_id = message_id

        except Exception as e:
            print("MAIN LOOP ERROR:", e)

        time.sleep(2)


if __name__ == "__main__":
    main()

