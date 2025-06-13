from bs4 import BeautifulSoup
from datetime import datetime
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config import settings as rc

# TEMPORARILY COMMENTED - REPORT_PATH causing errors
# Cấu hình dự án: đường dẫn file báo cáo, tên hiển thị và link báo cáo
# PROJECT_CONFIG = {
#     "mlm": {
#         "file_path": rc.REPORT_PATH_MLM, 
#         "display_name": "MLM AUTO",
#         "detail": rc.DEFAULT_URL_REPORT + "/mlm/",
#         "summary": rc.DEFAULT_URL_REPORT + "/mlm/serenity-summary.html"
#     },
#     "edpadmin": {
#         "file_path": rc.REPORT_PATH_ADMIN,
#         "display_name": "EDP Admin Project",
#         "detail": rc.DEFAULT_URL_REPORT + "/edpadmin/",
#         "summary": rc.DEFAULT_URL_REPORT + "/edpadmin/serenity-summary.html"
#     },
#     "edpdob": {
#         "file_path": rc.REPORT_PATH_DOB,
#         "display_name": "EDP DOB AUTO",
#         "detail": rc.DEFAULT_URL_REPORT  + "/edpdob/",
#         "summary": rc.DEFAULT_URL_REPORT  + "/edpdob/serenity-summary.html"
#     },
#     "vkyc": {
#         "file_path": rc.REPORT_PATH_VKYC,
#         "display_name": "VKYC AUTO",
#         "detail": rc.DEFAULT_URL_REPORT  + "/vkyc/",
#         "summary": rc.DEFAULT_URL_REPORT + "/vkyc/serenity-summary.html"
#     }
# }

# Temporarily empty to avoid errors
PROJECT_CONFIG = {}

def gen_mess(project):
    # TEMPORARILY COMMENTED - PROJECT_CONFIG causing errors
    # if project not in PROJECT_CONFIG:
    #     return f"❌ Project '{project}' không tồn tại!"
    # 
    # config = PROJECT_CONFIG[project]
    # 
    # try:
    #     execution_date, total, passed, failed, error = read_summary_report_html(config["file_path"])
    # except Exception as e:
    #     return f"❌ Lỗi khi đọc báo cáo dự án '{config['display_name']}': {e}"
    # 
    # # Tạo link báo cáo chi tiết và tóm tắt (giả định dùng cùng base url + tên file)
    # report_detail = shorten_link(config["detail"] , "Tại đây")
    # report_summary = shorten_link(config["summary"], "Tại đây")
    # 
    # mess = (
    #     f"====== REPORT {config['display_name'].upper()} ======\n"
    #     f"Execution time: {execution_date}\n"
    #     f"Total: {total}\n"
    #     f"Passed: {passed}\n"
    #     f"Failed: {failed}\n"
    #     f"Error: {error}\n"
    #     f"Report detail: {report_detail}\n"
    #     f"Report summary: {report_summary}\n"
    # )
    # return mess
    
    return f"❌ Chức năng báo cáo tạm thời bị vô hiệu hóa do lỗi cấu hình đường dẫn cho project '{project}'"

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
