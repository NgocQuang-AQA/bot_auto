from flask import Flask, request, jsonify
from flask import Flask, request, jsonify
import threading

# Setup project path
from utils.common import setup_project_path, setup_logging, validate_project_name
setup_project_path()

from services import legacy_service as service 
from utils import report_reader as readReport
from config import settings as rc
from constants import SUPPORTED_PROJECTS

app = Flask(__name__)
logger = setup_logging(__name__)

@app.route("/bot-slack/help", methods=["POST"])
def send_guid():
    help_message = """
    Danh sách các lệnh
    */run <project>*: Thực thi test project (edpadmin, edpdob, mlm, vkyc)
    */report <project>*: Xem kết quả mới nhất (edpadmin, edpdob, mlm, vkyc)
    */stop <project>*: Dừng project đang chạy (edpadmin, edpdob, mlm, vkyc)
    */help*: Hiển thị danh sách lệnh.
    """
    service.send_mess(help_message)
    return "", 200

@app.route("/bot-slack/run", methods=["POST"])
def run():
    project = request.form.get("text", "").strip().lower()
    is_valid, error_msg = validate_project_name(project)
    
    if not is_valid:
        return jsonify({
            "response_type": "ephemeral",
            "text": error_msg
        }), 200
    
    service.send_mess(f"✅ Đang chạy project {project}...")
    # Gửi phản hồi NGAY cho Slack (tránh timeout)
    threading.Thread(target=run_background_project, args=(project,)).start()
    return "", 200

@app.route("/bot-slack/report", methods=["POST"])
def report():
    project = request.form.get("text", "").strip().lower()
    is_valid, error_msg = validate_project_name(project)

    if not is_valid:
        return jsonify({
            "response_type": "ephemeral",
            "text": error_msg
        }), 200

    mess = readReport.gen_mess(project)

    service.send_mess(mess)

    return "", 200

@app.route("/bot-slack/stop", methods=["POST"])
def stop():

    project = request.form.get("text", "").strip().lower()

    if not project or project not in PROJECT_LST:
        return jsonify({
            "response_type": "ephemeral",
            "text": "❌ Project không tồn tại!"
        }), 200
    
    service.stop_containers_by_partial_name(project)

    return "", 200

@app.route("/bot-slack/deploy", methods=["POST"])
def deploy():

    image = request.form.get("image", "").strip().lower()
    
    service.pull_image(image)

    return "", 200



def run_background_project(project):
    try:
        service.run_project_with_batch(project)
    except Exception as e:
        return jsonify({
            "response_type": "ephemeral",
            "text": "❗️ Lỗi dừng project"
        }), 200

if __name__ == "__main__":
    app.run(debug=True, port=5000)