# Setup project path
from utils.common import setup_project_path, setup_logging, handle_exceptions
setup_project_path()

from bs4 import BeautifulSoup
from datetime import datetime
from config.settings import Config

logger = setup_logging(__name__)

PROJECT_CONFIG = {
    "mlm": {
        "file_path": Config.REPORT_PATHS.get("mlm", ""),
        "report_link": "https://10.10.10.10:8080/job/MLM_AUTOMATION/HTML_20Report/"
    },
    "edpadmin": {
        "file_path": Config.REPORT_PATHS.get("edpadmin", ""),
        "report_link": "https://10.10.10.10:8080/job/EDP_ADMIN_AUTOMATION/HTML_20Report/"
    },
    "edpdob": {
        "file_path": Config.REPORT_PATHS.get("edpdob", ""),
        "report_link": "https://10.10.10.10:8080/job/EDP_DOB_AUTOMATION/HTML_20Report/"
    },
    "vkyc": {
        "file_path": Config.REPORT_PATHS.get("vkyc", ""),
        "report_link": "https://10.10.10.10:8080/job/VKYC_AUTOMATION/HTML_20Report/"
    }
}

@handle_exceptions(default_return="❌ Lỗi không xác định khi tạo báo cáo")
def gen_mess(project):
    """Generate report message for a project
    
    Args:
        project: Project name
        
    Returns:
        str: Formatted report message
    """
    if project not in PROJECT_CONFIG:
        return f"❌ Project '{project}' không được hỗ trợ"
    
    config = PROJECT_CONFIG[project]
    file_path = config["file_path"]
    
    if not file_path:
        return f"❌ Đường dẫn báo cáo cho project '{project}' chưa được cấu hình"
    
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
        soup = BeautifulSoup(content, 'html.parser')
        
        # Extract report data
        execution_date = extract_execution_date(soup)
        total, passed, failed, error = extract_test_results(soup)
        
        # Format message
        message = format_report_message(
            project.upper(),
            execution_date,
            total,
            passed,
            failed,
            error,
            config["report_link"]
        )

def format_report_message(display_name, execution_date, total, passed, failed, error, report_url):
    """Format the report message
    
    Args:
        display_name: Project display name
        execution_date: Test execution date
        total: Total test count
        passed: Passed test count
        failed: Failed test count
        error: Error test count
        report_url: URL for report
        
    Returns:
        str: Formatted message
    """
    # Create shortened link
    report_link = shorten_link(report_url, "Xem báo cáo")
    
    message = (
        f"====== REPORT {display_name} ======\n"
        f"Execution time: {execution_date}\n"
        f"Total: {total}\n"
        f"Passed: {passed}\n"
        f"Failed: {failed}\n"
        f"Error: {error}\n"
        f"Report: {report_link}\n"
    )
    
    return message

def extract_test_results(soup):
    """Extract test results from HTML soup
    
    Args:
        soup: BeautifulSoup object
        
    Returns:
        tuple: (total, passed, failed, error)
    """
    def get_count_text(class_name):
        span = soup.find("span", class_=class_name)
        if span:
            text = span.get_text(strip=True)
            return int(text) if text.isdigit() else 0
        return 0
    
    total = get_total_tests(str(soup))
    passed = get_count_text("success-badge")
    failed = get_count_text("failure-badge")
    error = get_count_text("error-badge")
    
    return total, passed, failed, error

def extract_execution_date(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    td = soup.find("td", class_="overview")
    if not td:
        return None

    spans = td.find_all("span")
    if len(spans) < 2:
        return None

    raw_date_text = spans[1].get_text(strip=True)

    try:
        cleaned_date_text = " ".join(raw_date_text.split()[1:])
        dt = datetime.strptime(cleaned_date_text, "%B %d %Y at %H:%M")
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None

def get_total_tests(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    overview = soup.select_one("td.overview")
    if overview:
        spans = overview.find_all("span")
        if spans:
            parts = spans[0].get_text().split()
            if len(parts) > 0:
                return parts[0]
    return "N/A"

def read_summary_report_html(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    soup = BeautifulSoup(content, "html.parser")

    def get_count_text(class_name):
        span = soup.find("span", class_=class_name)
        if span:
            text = span.get_text(strip=True)
            return int(text) if text.isdigit() else 0
        return 0

    execution_date = extract_execution_date(content)
    total = get_total_tests(content)
    passed = get_count_text("success-badge")
    failed = get_count_text("failure-badge")
    error = get_count_text("error-badge")

    return execution_date, total, passed, failed, error

def shorten_link(long_url: str, name_url: str) -> str:
    return f"<{long_url}|{name_url}>"
