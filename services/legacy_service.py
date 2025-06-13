import subprocess
from flask import jsonify
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config import settings as rc

# Biến toàn cục giữ tiến trình đang chạy
current_process = None

RUN_PROJECT = {
    "mlm": rc.RUN_MLM_BAT,
    "vkyc": rc.RUN_VKYC_BAT,
    "edpadmin": rc.RUN_EDP_ADMIN_BAT,
    "edpdob": rc.RUN_EDP_DOB_BAT
}
# ---------------------------
# STOP CONTAINER BY NAME
# ---------------------------
def stop_containers_by_partial_name(keyword):
    mess = ""
    stopped = []
    errors = []

    try:
        # Lấy danh sách container đang chạy
        list_cmd = ["docker", "ps", "--format", "{{.ID}} {{.Names}}"]
        result = subprocess.run(list_cmd, capture_output=True, text=True)

        if result.returncode != 0:
            mess = "❌ Không thể lấy danh sách container."
            return jsonify({"message": mess})

        containers = result.stdout.strip().split("\n")

        for line in containers:
            if not line.strip():
                continue

            container_id, container_name = line.strip().split(maxsplit=1)

            if keyword.lower() in container_name.lower():
                stop_cmd = ["docker", "stop", container_id]
                stop_result = subprocess.run(stop_cmd, capture_output=True, text=True)

                if stop_result.returncode == 0:
                    stopped.append(container_name)
                else:
                    errors.append(
                        f"❌ Lỗi khi dừng {container_name}: {stop_result.stderr.strip()}"
                    )

        if not stopped and not errors:
            mess = f"⚠️ Project '{keyword}' đang không chạy."
        elif stopped:
            mess = f"✅ Đã dừng project {', '.join(stopped)}"
            if errors:
                mess += "\nMột số lỗi khi dừng project:\n" + "\n".join(errors)
        else:
            mess = "\n".join(errors)

    except Exception as e:
        mess = f"❌ Lỗi hệ thống: {str(e)}"
    send_mess(mess)

# ---------------------------
# RUN .BAT FILE
# ---------------------------
def run_project_with_batch(project):
    global current_process
    filePath = RUN_PROJECT[project]
    try:
        current_process = subprocess.Popen(
            filePath,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        # Đọc log và in log chạy projectproject
        # for line in current_process.stdout:
        #     print(f"[Batch Output] {line.strip()}")

        current_process.wait()

        exit_code = current_process.returncode

        if exit_code == 0:
            print("Chạy thành công")
        else:
            print("Chạy không thành công")

    except Exception as e:
        print("Lỗi")


# ---------------------------
# STOP CURRENT PROCESS
# ---------------------------
def stop_current_process():
    global current_process

    if current_process and current_process.poll() is None:
        current_process.terminate()
        try:
            current_process.wait(timeout=5)
            print("✅ Process đã được dừng.")
        except subprocess.TimeoutExpired:
            current_process.kill()
            print("❌ Process bị kill do không phản hồi.")
    else:
        print("⚠️ Không có process nào đang chạy.")


# ---------------------------
# RUN COMMAND (Docker or CLI)
# ---------------------------

def pull_image(image_name):
    message = ""
    try:
        # Tạo câu lệnh pull
        cmd = f"docker pull {image_name}"

        # Chạy lệnh
        current_process = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        output_lines = []
        for line in current_process.stdout:
            print(f"[Docker Output] {line.strip()}")
            output_lines.append(line.strip())

        current_process.wait()
        exit_code = current_process.returncode

        if exit_code == 0:
            message = f"✅ Deploy thành công image: {image_name}"
        else:
            message = f"❌ Lỗi khi deploy image: {image_name}\nChi tiết: {' | '.join(output_lines)}"
    except Exception as e:
        message = f"❌ Lỗi hệ thống: {str(e)}"

    send_mess(message)

# ---------------------------
# GỬI TIN NHẮN SLACK
# ---------------------------
def send_mess(mess):
    client = WebClient(token=rc.TOKEN_SLACK)
    try:
        client.chat_postMessage(channel=rc.GROUP_ID_SLACK, text=mess)
    except SlackApiError as e:
        print(f"❌ Gửi tin nhắn thất bại: {e.response['error']}")
    except Exception as e:
        print(f"❌ Lỗi không xác định: {str(e)}")


# ---------------------------
# TEST TRỰC TIẾP
# ---------------------------
if __name__ == "__main__":
    # Ví dụ test
    stop_containers_by_partial_name("mlm")
    # run_project_with_batch("start.bat")
