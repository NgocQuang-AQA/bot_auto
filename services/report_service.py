import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from bs4 import BeautifulSoup
# Setup project path
from utils.common import setup_project_path, setup_logging, handle_exceptions
setup_project_path()

from config.settings import Config
from services.slack_service import SlackService

logger = setup_logging(__name__)

class ReportService:
    """Service for handling test reports"""
    
    def __init__(self):
        self.project_config = {
            "mlm": {
                "display_name": "MLM AUTO",
                "detail_url": f"{Config.DEFAULT_URL_REPORT}/mlm/",
                "summary_url": f"{Config.DEFAULT_URL_REPORT}/mlm/serenity-summary.html"
            },
            "edpadmin": {
                "display_name": "EDP Admin Project",
                "detail_url": f"{Config.DEFAULT_URL_REPORT}/edpadmin/",
                "summary_url": f"{Config.DEFAULT_URL_REPORT}/edpadmin/serenity-summary.html"
            },
            "edpdob": {
                "display_name": "EDP DOB AUTO",
                "detail_url": f"{Config.DEFAULT_URL_REPORT}/edpdob/",
                "summary_url": f"{Config.DEFAULT_URL_REPORT}/edpdob/serenity-summary.html"
            },
            "vkyc": {
                "display_name": "VKYC AUTO",
                "detail_url": f"{Config.DEFAULT_URL_REPORT}/vkyc/",
                "summary_url": f"{Config.DEFAULT_URL_REPORT}/vkyc/serenity-summary.html"
            }
        }
    
    @handle_exceptions(default_return={"success": False, "message": "❌ Lỗi không xác định khi tạo báo cáo"})
    def generate_report_message(self, project: str) -> Dict[str, Any]:
        """Generate report message for a project
        
        Args:
            project: Project name
            
        Returns:
            dict: Result with status and message
        """
        if project not in Config.SUPPORTED_PROJECTS:
            return {
                "success": False,
                "message": f"❌ Project '{project}' không được hỗ trợ"
            }
        
        if project not in self.project_config:
            return {
                "success": False,
                "message": f"❌ Cấu hình báo cáo cho project '{project}' không tồn tại"
            }
        
        config = self.project_config[project]
        report_path = Config.REPORT_PATHS.get(project)
        
        if not report_path:
            return {
                "success": False,
                "message": f"❌ Đường dẫn báo cáo cho project '{project}' chưa được cấu hình"
            }
        
        report_data = self._parse_html_report(report_path)
        if not report_data["success"]:
            return report_data
        
        execution_date, total, passed, failed, error = report_data["data"]
        
        # Create formatted message
        message = self._format_report_message(
            config["display_name"],
            execution_date,
            total,
            passed,
            failed,
            error,
            config["detail_url"],
            config["summary_url"]
        )
        
        return {
            "success": True,
            "message": message
        }
    
    def _parse_html_report(self, file_path: str) -> Dict[str, Any]:
        """Parse HTML report file
        
        Args:
            file_path: Path to HTML report file
            
        Returns:
            dict: Parsed report data or error
        """
        try:
            if not os.path.exists(file_path):
                return {
                    "success": False,
                    "message": f"❌ File báo cáo không tồn tại: {file_path}"
                }
            
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract execution date
            execution_date = self._extract_execution_date(soup)
            
            # Extract test statistics
            stats = self._extract_test_statistics(soup)
            
            return {
                "success": True,
                "data": (execution_date, stats["total"], stats["passed"], stats["failed"], stats["error"])
            }
            
        except Exception as e:
            logger.error(f"Error parsing HTML report {file_path}: {str(e)}")
            return {
                "success": False,
                "message": f"❌ Lỗi khi đọc file báo cáo: {str(e)}"
            }
    
    def _extract_execution_date(self, soup: BeautifulSoup) -> str:
        """Extract execution date from HTML
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            str: Formatted execution date
        """
        try:
            # Try multiple selectors for execution date
            date_selectors = [
                '.execution-date',
                '.test-date',
                '[data-test="execution-date"]',
                'time'
            ]
            
            for selector in date_selectors:
                date_element = soup.select_one(selector)
                if date_element:
                    return date_element.get_text(strip=True)
            
            # Fallback to current date if not found
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
        except Exception:
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def _extract_test_statistics(self, soup: BeautifulSoup) -> Dict[str, int]:
        """Extract test statistics from HTML
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            dict: Test statistics
        """
        stats = {"total": 0, "passed": 0, "failed": 0, "error": 0}
        
        try:
            # Try to find statistics in common locations
            stat_selectors = {
                "total": ['.total-tests', '[data-test="total"]', '.test-count-total'],
                "passed": ['.passed-tests', '[data-test="passed"]', '.test-count-passed'],
                "failed": ['.failed-tests', '[data-test="failed"]', '.test-count-failed'],
                "error": ['.error-tests', '[data-test="error"]', '.test-count-error']
            }
            
            for stat_type, selectors in stat_selectors.items():
                for selector in selectors:
                    element = soup.select_one(selector)
                    if element:
                        try:
                            stats[stat_type] = int(element.get_text(strip=True))
                            break
                        except ValueError:
                            continue
            
            # If no specific selectors found, try to parse from summary tables
            if stats["total"] == 0:
                self._parse_summary_table(soup, stats)
            
        except Exception as e:
            logger.warning(f"Error extracting test statistics: {str(e)}")
        
        return stats
    
    def _parse_summary_table(self, soup: BeautifulSoup, stats: Dict[str, int]):
        """Parse statistics from summary table
        
        Args:
            soup: BeautifulSoup object
            stats: Statistics dictionary to update
        """
        try:
            # Look for summary tables
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        label = cells[0].get_text(strip=True).lower()
                        value_text = cells[1].get_text(strip=True)
                        
                        try:
                            value = int(value_text)
                            if 'total' in label:
                                stats['total'] = value
                            elif 'pass' in label:
                                stats['passed'] = value
                            elif 'fail' in label:
                                stats['failed'] = value
                            elif 'error' in label:
                                stats['error'] = value
                        except ValueError:
                            continue
        except Exception as e:
            logger.warning(f"Error parsing summary table: {str(e)}")
    
    def _format_report_message(self, display_name: str, execution_date: str, 
                              total: int, passed: int, failed: int, error: int,
                              detail_url: str, summary_url: str) -> str:
        """Format report message
        
        Args:
            display_name: Project display name
            execution_date: Execution date
            total: Total tests
            passed: Passed tests
            failed: Failed tests
            error: Error tests
            detail_url: Detail report URL
            summary_url: Summary report URL
            
        Returns:
            str: Formatted message
        """
        # Calculate success rate
        success_rate = (passed / total * 100) if total > 0 else 0
        
        # Determine status emoji
        if failed == 0 and error == 0:
            status_emoji = "✅"
        elif failed > 0 or error > 0:
            status_emoji = "❌"
        else:
            status_emoji = "⚠️"
        
        message = f"""
====== REPORT {display_name.upper()} ======
{status_emoji} Execution time: {execution_date}
📊 **Test Summary:**
• Total: {total}
• Passed: {passed} ✅
• Failed: {failed} ❌
• Error: {error} ⚠️
• Success Rate: {success_rate:.1f}%

🔗 **Links:**
• [Chi tiết báo cáo]({detail_url})
• [Tóm tắt báo cáo]({summary_url})
==========================================
        """.strip()
        
        return message
    
    def get_available_projects(self) -> list:
        """Get list of available projects for reporting
        
        Returns:
            list: List of project names
        """
        return list(self.project_config.keys())