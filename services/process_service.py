import subprocess
import threading
import time
import logging
from typing import Optional, Dict, Any
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config.settings import Config

logger = logging.getLogger(__name__)

class ProcessService:
    """Service for managing processes and Docker containers"""
    
    def __init__(self):
        self._running_processes: Dict[str, subprocess.Popen] = {}
        self._process_lock = threading.Lock()
    
    def run_batch_file(self, project: str) -> Dict[str, Any]:
        """Run batch file for specified project
        
        Args:
            project: Project name
            
        Returns:
            dict: Result with status and message
        """
        # TEMPORARILY COMMENTED - BATCH_PATHS causing errors
        return {
            "success": False,
            "message": f"❌ Chức năng chạy batch file tạm thời bị vô hiệu hóa do lỗi cấu hình đường dẫn"
        }
        
        # if project not in Config.SUPPORTED_PROJECTS:
        #     return {
        #         "success": False,
        #         "message": f"❌ Project '{project}' không được hỗ trợ"
        #     }
        # 
        # batch_path = Config.BATCH_PATHS[project]
        # if not batch_path:
        #     return {
        #         "success": False,
        #         "message": f"❌ Không tìm thấy đường dẫn batch file cho project '{project}'"
        #     }
        
        # TEMPORARILY COMMENTED - Rest of batch file execution
        # try:
        #     with self._process_lock:
        #         # Stop existing process if running
        #         if project in self._running_processes:
        #             self._stop_process(project)
        #         
        #         # Start new process
        #         process = subprocess.Popen(
        #             batch_path,
        #             shell=True,
        #             stdout=subprocess.PIPE,
        #             stderr=subprocess.STDOUT,
        #             text=True,
        #             cwd=None
        #         )
        #         
        #         self._running_processes[project] = process
        #         logger.info(f"Started batch process for project: {project}")
        #     
        #     # Wait for process completion in background
        #     threading.Thread(
        #         target=self._monitor_process,
        #         args=(project, process),
        #         daemon=True
        #     ).start()
        #     
        #     return {
        #         "success": True,
        #         "message": f"✅ Đã bắt đầu chạy project {project}"
        #     }
        #     
        # except Exception as e:
        #     logger.error(f"Error running batch file for {project}: {str(e)}")
        #     return {
        #         "success": False,
        #         "message": f"❌ Lỗi khi chạy project {project}: {str(e)}"
        #     }
    
    def stop_containers_by_name(self, keyword: str) -> Dict[str, Any]:
        """Stop Docker containers by partial name match
        
        Args:
            keyword: Partial container name to match
            
        Returns:
            dict: Result with status and message
        """
        try:
            # Get running containers
            list_cmd = ["docker", "ps", "--format", "{{.ID}} {{.Names}}"]
            result = subprocess.run(list_cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                return {
                    "success": False,
                    "message": "❌ Không thể lấy danh sách container"
                }
            
            containers = result.stdout.strip().split("\n")
            stopped_containers = []
            errors = []
            
            for line in containers:
                if not line.strip():
                    continue
                
                parts = line.strip().split(maxsplit=1)
                if len(parts) < 2:
                    continue
                    
                container_id, container_name = parts
                
                if keyword.lower() in container_name.lower():
                    stop_result = subprocess.run(
                        ["docker", "stop", container_id],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    
                    if stop_result.returncode == 0:
                        stopped_containers.append(container_name)
                        logger.info(f"Stopped container: {container_name}")
                    else:
                        error_msg = f"❌ Lỗi khi dừng {container_name}: {stop_result.stderr.strip()}"
                        errors.append(error_msg)
                        logger.error(error_msg)
            
            if not stopped_containers and not errors:
                return {
                    "success": True,
                    "message": f"⚠️ Không tìm thấy container nào chứa '{keyword}' đang chạy"
                }
            elif stopped_containers:
                message = f"✅ Đã dừng container: {', '.join(stopped_containers)}"
                if errors:
                    message += "\n" + "\n".join(errors)
                return {
                    "success": True,
                    "message": message
                }
            else:
                return {
                    "success": False,
                    "message": "\n".join(errors)
                }
                
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "message": "❌ Timeout khi thực hiện lệnh Docker"
            }
        except Exception as e:
            logger.error(f"Error stopping containers: {str(e)}")
            return {
                "success": False,
                "message": f"❌ Lỗi hệ thống: {str(e)}"
            }
    
    def pull_docker_image(self, image_name: str) -> Dict[str, Any]:
        """Pull Docker image
        
        Args:
            image_name: Name of the Docker image
            
        Returns:
            dict: Result with status and message
        """
        try:
            cmd = ["docker", "pull", image_name]
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            
            if process.returncode == 0:
                logger.info(f"Successfully pulled image: {image_name}")
                return {
                    "success": True,
                    "message": f"✅ Đã pull thành công image: {image_name}"
                }
            else:
                error_msg = f"❌ Lỗi khi pull image {image_name}: {process.stderr}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "message": error_msg
                }
                
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "message": f"❌ Timeout khi pull image: {image_name}"
            }
        except Exception as e:
            logger.error(f"Error pulling image {image_name}: {str(e)}")
            return {
                "success": False,
                "message": f"❌ Lỗi hệ thống: {str(e)}"
            }
    
    def stop_project(self, project: str) -> Dict[str, Any]:
        """Stop running project process
        
        Args:
            project: Project name
            
        Returns:
            dict: Result with status and message
        """
        with self._process_lock:
            if project in self._running_processes:
                success = self._stop_process(project)
                if success:
                    return {
                        "success": True,
                        "message": f"✅ Đã dừng project {project}"
                    }
                else:
                    return {
                        "success": False,
                        "message": f"❌ Không thể dừng project {project}"
                    }
            else:
                return {
                    "success": True,
                    "message": f"⚠️ Project {project} không đang chạy"
                }
    
    def _stop_process(self, project: str) -> bool:
        """Stop a specific project process
        
        Args:
            project: Project name
            
        Returns:
            bool: Success status
        """
        if project not in self._running_processes:
            return True
        
        process = self._running_processes[project]
        
        try:
            if process.poll() is None:  # Process is still running
                process.terminate()
                try:
                    process.wait(timeout=5)
                    logger.info(f"Process for {project} terminated gracefully")
                except subprocess.TimeoutExpired:
                    process.kill()
                    logger.warning(f"Process for {project} was killed forcefully")
            
            del self._running_processes[project]
            return True
            
        except Exception as e:
            logger.error(f"Error stopping process for {project}: {str(e)}")
            return False
    
    def _monitor_process(self, project: str, process: subprocess.Popen):
        """Monitor process completion
        
        Args:
            project: Project name
            process: Process object
        """
        try:
            exit_code = process.wait()
            
            with self._process_lock:
                if project in self._running_processes:
                    del self._running_processes[project]
            
            if exit_code == 0:
                logger.info(f"Project {project} completed successfully")
            else:
                logger.warning(f"Project {project} completed with exit code: {exit_code}")
                
        except Exception as e:
            logger.error(f"Error monitoring process for {project}: {str(e)}")
    
    def get_running_projects(self) -> list:
        """Get list of currently running projects
        
        Returns:
            list: List of running project names
        """
        with self._process_lock:
            return list(self._running_processes.keys())