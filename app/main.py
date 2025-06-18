import os
import os
import logging
import threading
from flask import Flask, request, jsonify
from werkzeug.exceptions import BadRequest
from datetime import datetime

# Setup project path
from utils.common import setup_project_path, setup_logging, validate_project_name, create_response_dict
setup_project_path()

from config.settings import Config
from services.slack_service import SlackService
from services.process_service import ProcessService
from services.report_service import ReportService
from constants import DEFAULT_PORT, LOGS_DIR

# Initialize Flask app
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

# Initialize configuration
config = Config()
config.validate()

# Initialize services
slack_service = SlackService()
process_service = ProcessService()
report_service = ReportService()

# Setup logging
logger = setup_logging(__name__, config.LOG_LEVEL, config.LOG_FILE)

# Application metadata
APP_VERSION = "2.0.0"
START_TIME = datetime.now()

class SlackBotAPI:
    """Main Slack Bot API class"""
    
    def __init__(self):
        # TEMPORARILY COMMENTED - SUPPORTED_PROJECTS causing errors
        # self.supported_projects = Config.SUPPORTED_PROJECTS
        self.supported_projects = []  # Temporarily empty to avoid errors
    
    def validate_project(self, project: str) -> tuple[bool, str]:
        """Validate project name
        
        Args:
            project: Project name to validate
            
        Returns:
            tuple: (is_valid, error_message)
        """
        return validate_project_name(project)
    
    def send_response(self, message: str, ephemeral: bool = False) -> tuple[dict, int]:
        """Send response to Slack
        
        Args:
            message: Message to send
            ephemeral: Whether message should be ephemeral
            
        Returns:
            tuple: (response_dict, status_code)
        """
        try:
            success = slack_service.send_message(message, ephemeral)
            if success:
                return {}, 200
            else:
                return {"error": "Failed to send message"}, 500
        except Exception as e:
            logger.error(f"Error sending response: {str(e)}")
            return {"error": "Internal server error"}, 500
    
    def get_help_message(self) -> str:
        """Get help message
        
        Returns:
            str: Help message
        """
        # TEMPORARILY COMMENTED - supported_projects causing errors
        # projects_list = ", ".join(self.supported_projects)
        projects_list = "mlm, vkyc, edpadmin, edpdob"  # Hardcoded temporarily
        return f"""
🤖 **SLACK BOT AUTOMATION - HƯỚNG DẪN SỬ DỤNG**

📋 **Danh sách lệnh:**
• `/run <project>` - Chạy test project
• `/report <project>` - Xem báo cáo mới nhất
• `/stop <project>` - Dừng project đang chạy
• `/deploy <image>` - Pull Docker image
• `/help` - Hiển thị hướng dẫn này

🎯 **Projects được hỗ trợ:** {projects_list}

💡 **Ví dụ sử dụng:**
• `/run mlm` - Chạy MLM project
• `/report vkyc` - Xem báo cáo VKYC
• `/stop edpadmin` - Dừng EDP Admin

⚠️ **Lưu ý:** Các lệnh có thể mất vài phút để hoàn thành.
        """.strip()

bot_api = SlackBotAPI()

@app.route("/bot-slack/help", methods=["POST"])
def help_command():
    """Handle help command"""
    try:
        help_message = bot_api.get_help_message()
        return bot_api.send_response(help_message)
    except Exception as e:
        logger.error(f"Error in help command: {str(e)}")
        return bot_api.send_response("❌ Lỗi hệ thống khi hiển thị help", ephemeral=True)

@app.route("/bot-slack/run", methods=["POST"])
def run_command():
    """Handle run command"""
    try:
        project = request.form.get("text", "").strip().lower()
        
        # Validate project
        is_valid, error_message = bot_api.validate_project(project)
        if not is_valid:
            return jsonify({
                "response_type": "ephemeral",
                "text": error_message
            }), 200
        
        # Send immediate response
        slack_service.send_message(f"🚀 Đang khởi động project {project}...")
        
        # Run project in background
        def run_background():
            try:
                result = process_service.run_batch_file(project)
                if result["success"]:
                    slack_service.send_message(f"✅ Project {project} đã hoàn thành thành công!")
                else:
                    slack_service.send_message(result["message"])
            except Exception as e:
                logger.error(f"Background run error for {project}: {str(e)}")
                slack_service.send_message(f"❌ Lỗi khi chạy project {project}: {str(e)}")
        
        threading.Thread(target=run_background, daemon=True).start()
        return "", 200
        
    except Exception as e:
        logger.error(f"Error in run command: {str(e)}")
        return jsonify({
            "response_type": "ephemeral",
            "text": "❌ Lỗi hệ thống khi chạy project"
        }), 200

@app.route("/bot-slack/report", methods=["POST"])
def report_command():
    """Handle report command"""
    try:
        project = request.form.get("text", "").strip().lower()
        
        # Validate project
        is_valid, error_message = bot_api.validate_project(project)
        if not is_valid:
            return jsonify({
                "response_type": "ephemeral",
                "text": error_message
            }), 200
        
        # Generate report
        result = report_service.generate_report_message(project)
        return bot_api.send_response(result["message"])
        
    except Exception as e:
        logger.error(f"Error in report command: {str(e)}")
        return jsonify({
            "response_type": "ephemeral",
            "text": "❌ Lỗi hệ thống khi tạo báo cáo"
        }), 200

@app.route("/bot-slack/stop", methods=["POST"])
def stop_command():
    """Handle stop command"""
    try:
        project = request.form.get("text", "").strip().lower()
        
        # Validate project
        is_valid, error_message = bot_api.validate_project(project)
        if not is_valid:
            return jsonify({
                "response_type": "ephemeral",
                "text": error_message
            }), 200
        
        # Stop containers and processes
        container_result = process_service.stop_containers_by_name(project)
        process_result = process_service.stop_project(project)
        
        # Combine messages
        messages = []
        if container_result["success"]:
            messages.append(container_result["message"])
        if process_result["success"]:
            messages.append(process_result["message"])
        
        if not messages:
            message = f"❌ Không thể dừng project {project}"
        else:
            message = "\n".join(messages)
        
        return bot_api.send_response(message)
        
    except Exception as e:
        logger.error(f"Error in stop command: {str(e)}")
        return jsonify({
            "response_type": "ephemeral",
            "text": "❌ Lỗi hệ thống khi dừng project"
        }), 200

@app.route("/bot-slack/deploy", methods=["POST"])
def deploy_command():
    """Handle deploy command"""
    try:
        image = request.form.get("text", "").strip()
        
        if not image:
            return jsonify({
                "response_type": "ephemeral",
                "text": "❌ Tên image không được để trống"
            }), 200
        
        # Send immediate response
        slack_service.send_message(f"🐳 Đang pull Docker image: {image}...")
        
        # Pull image in background
        def pull_background():
            try:
                result = process_service.pull_docker_image(image)
                slack_service.send_message(result["message"])
            except Exception as e:
                logger.error(f"Background pull error for {image}: {str(e)}")
                slack_service.send_message(f"❌ Lỗi khi pull image {image}: {str(e)}")
        
        threading.Thread(target=pull_background, daemon=True).start()
        return "", 200
        
    except Exception as e:
        logger.error(f"Error in deploy command: {str(e)}")
        return jsonify({
            "response_type": "ephemeral",
            "text": "❌ Lỗi hệ thống khi deploy"
        }), 200

@app.route("/bot-slack/status", methods=["GET"])
def status_command():
    """Handle status command"""
    try:
        running_projects = process_service.get_running_projects()
        
        if running_projects:
            message = f"🔄 **Projects đang chạy:** {', '.join(running_projects)}"
        else:
            message = "✅ **Không có project nào đang chạy**"
        
        return jsonify({"status": "ok", "message": message}), 200
        
    except Exception as e:
        logger.error(f"Error in status command: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring"""
    try:
        uptime = datetime.now() - START_TIME
        health_data = {
            "status": "healthy",
            "version": APP_VERSION,
            "uptime": str(uptime),
            "timestamp": datetime.now().isoformat(),
            "services": {
                "slack": "connected" if slack_service else "disconnected",
                "process": "running" if process_service else "stopped",
                "report": "available" if report_service else "unavailable"
            }
        }
        return jsonify(health_data), 200
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 503

@app.route('/metrics', methods=['GET'])
def metrics():
    """Basic metrics endpoint"""
    try:
        import psutil
        metrics_data = {
            "system": {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent if os.name != 'nt' else psutil.disk_usage('C:').percent
            },
            "application": {
                "version": APP_VERSION,
                "uptime": str(datetime.now() - START_TIME),
                "active_processes": len(process_service.running_processes) if hasattr(process_service, 'running_processes') else 0
            }
        }
        return jsonify(metrics_data), 200
    except Exception as e:
        logger.error(f"Metrics error: {e}")
        return jsonify({"error": "Metrics unavailable"}), 500

@app.errorhandler(400)
def bad_request(error):
    """Handle bad request errors"""
    return jsonify({"error": "Bad request"}), 400

@app.errorhandler(404)
def not_found(error):
    """Handle not found errors"""
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle internal server errors"""
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({"error": "Internal server error"}), 500

def initialize_app():
    """Initialize application"""
    try:
        # Validate configuration
        Config.validate()
        logger.info("Configuration validated successfully")
        
        # Test Slack connection
        test_result = slack_service.send_message("🤖 Slack Bot đã khởi động thành công!")
        if test_result:
            logger.info("Slack connection test successful")
        else:
            logger.warning("Slack connection test failed")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize app: {str(e)}")
        return False

if __name__ == "__main__":
    # Initialize application
    if initialize_app():
        logger.info(f"Starting Slack Bot API server v{APP_VERSION}...")
        app.run(
            debug=False,
            host="0.0.0.0",
            port=int(os.getenv("PORT", 5000)),
            threaded=True
        )
    else:
        logger.error("Failed to start application")
        sys.exit(1)