# Slack Bot Automation Service

🤖 **Service tự động hóa cho Slack Bot** - Quản lý và điều khiển các project testing thông qua Slack commands.

## 📋 Tổng quan

Dự án này cung cấp một Slack Bot service để:
- Chạy các project testing tự động
- Quản lý Docker containers
- Xem báo cáo test results
- Deploy Docker images
- Điều khiển processes thông qua Slack commands

## 🏗️ Kiến trúc

```
bot_auto/
├── app.py                 # Main Flask application
├── config.py             # Configuration management
├── services/
│   ├── slack_service.py  # Slack API interactions
│   ├── process_service.py # Process & Docker management
│   └── report_service.py # Report generation
├── requirements.txt      # Python dependencies
├── .env                 # Environment variables
└── README.md           # This file
```

## 🚀 Cài đặt

### 1. Clone repository
```bash
git clone <repository-url>
cd bot_auto
```

### 2. Tạo virtual environment
```bash
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
```

### 3. Cài đặt dependencies
```bash
pip install -r requirements.txt
```

### 4. Cấu hình environment variables
Tạo file `.env` với nội dung:
```env
# Slack Configuration
TOKEN_SLACK=xoxb-your-slack-bot-token
GROUP_ID_SLACK=your-slack-channel-id

# Report Configuration
DEFAULT_URL_REPORT=https://your-report-domain.com
REPORT_PATH_MLM=path/to/mlm/report.html
REPORT_PATH_ADMIN=path/to/admin/report.html
REPORT_PATH_DOB=path/to/dob/report.html
REPORT_PATH_VKYC=path/to/vkyc/report.html

# Batch File Paths
RUN_MLM_BAT=path/to/mlm_run.bat
RUN_VKYC_BAT=path/to/vkyc_run.bat
RUN_EDP_ADMIN_BAT=path/to/edp_admin_run.bat
RUN_EDP_DOB_BAT=path/to/edp_dob_run.bat

# Optional
LOG_LEVEL=INFO
PORT=5000
```

### 5. Chạy application
```bash
python app.py
```

## 🎯 Slack Commands

### Các lệnh có sẵn:

| Command | Mô tả | Ví dụ |
|---------|-------|-------|
| `/help` | Hiển thị hướng dẫn | `/help` |
| `/run <project>` | Chạy test project | `/run mlm` |
| `/report <project>` | Xem báo cáo mới nhất | `/report vkyc` |
| `/stop <project>` | Dừng project đang chạy | `/stop edpadmin` |
| `/deploy <image>` | Pull Docker image | `/deploy nginx:latest` |

### Projects được hỗ trợ:
- `mlm` - MLM Auto Testing
- `vkyc` - VKYC Auto Testing  
- `edpadmin` - EDP Admin Testing
- `edpdob` - EDP DOB Testing

## 🔧 Cấu hình Slack App

### 1. Tạo Slack App
1. Truy cập [Slack API](https://api.slack.com/apps)
2. Tạo "New App" → "From scratch"
3. Nhập tên app và chọn workspace

### 2. Cấu hình Bot Token
1. Vào **OAuth & Permissions**
2. Thêm Bot Token Scopes:
   - `chat:write`
   - `commands`
   - `channels:read`
3. Install App to Workspace
4. Copy **Bot User OAuth Token**

### 3. Tạo Slash Commands
Vào **Slash Commands** và tạo:

| Command | Request URL | Description |
|---------|-------------|-------------|
| `/help` | `https://your-domain.com/bot-slack/help` | Hiển thị help |
| `/run` | `https://your-domain.com/bot-slack/run` | Chạy project |
| `/report` | `https://your-domain.com/bot-slack/report` | Xem báo cáo |
| `/stop` | `https://your-domain.com/bot-slack/stop` | Dừng project |
| `/deploy` | `https://your-domain.com/bot-slack/deploy` | Deploy image |

### 4. Event Subscriptions (Optional)
Nếu muốn nhận events:
1. Enable Events: `https://your-domain.com/slack/events`
2. Subscribe to bot events: `message.channels`

## 🛠️ Development

### Cấu trúc Services

#### SlackService
- Quản lý Slack API interactions
- Gửi messages và formatted blocks
- Error handling cho Slack API

#### ProcessService
- Quản lý Docker containers
- Chạy batch files
- Thread-safe process management
- Background monitoring

#### ReportService
- Parse HTML reports
- Generate formatted messages
- Extract test statistics

### Logging
Application sử dụng Python logging với các levels:
- `INFO`: General information
- `WARNING`: Warning messages
- `ERROR`: Error messages
- `DEBUG`: Debug information (khi LOG_LEVEL=DEBUG)

### Error Handling
- Comprehensive exception handling
- Graceful degradation
- User-friendly error messages
- Proper HTTP status codes

## 🔒 Security

### Best Practices được áp dụng:
- Environment variables cho sensitive data
- Input validation cho tất cả commands
- Process timeout để tránh hanging
- Thread-safe operations
- Proper error handling

### Khuyến nghị bổ sung:
- Sử dụng HTTPS cho production
- Implement Slack request verification
- Rate limiting cho API endpoints
- Monitor và log security events

## 📊 Monitoring

### Health Check
```bash
GET /bot-slack/status
```

### Logs
Logs được output ra console và có thể redirect:
```bash
python app.py > app.log 2>&1
```

### Metrics
- Process status
- Running projects
- Error rates
- Response times

## 🚀 Deployment

### Docker (Khuyến nghị)
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["python", "app.py"]
```

### Systemd Service
```ini
[Unit]
Description=Slack Bot Automation Service
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/bot_auto
Environment=PATH=/path/to/venv/bin
ExecStart=/path/to/venv/bin/python app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

### Nginx Reverse Proxy
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location /bot-slack/ {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 🐛 Troubleshooting

### Common Issues

1. **Slack Token Invalid**
   - Kiểm tra TOKEN_SLACK trong .env
   - Verify bot permissions

2. **Batch Files Not Found**
   - Kiểm tra đường dẫn trong .env
   - Verify file permissions

3. **Docker Commands Fail**
   - Kiểm tra Docker daemon running
   - Verify user permissions

4. **Report Files Not Found**
   - Kiểm tra REPORT_PATH_* trong .env
   - Verify file exists và readable

### Debug Mode
```bash
LOG_LEVEL=DEBUG python app.py
```

## 📝 Changelog

### v2.0.0 (Current)
- ✅ Refactored architecture với services
- ✅ Improved error handling
- ✅ Thread-safe operations
- ✅ Better configuration management
- ✅ Comprehensive logging
- ✅ Input validation
- ✅ Health check endpoint

### v1.0.0 (Legacy)
- Basic Slack bot functionality
- Simple process management
- Basic report generation

## 🤝 Contributing

1. Fork repository
2. Create feature branch
3. Make changes
4. Add tests
5. Submit pull request

## 📄 License

MIT License - see LICENSE file for details.

## 📞 Support

Nếu có vấn đề hoặc câu hỏi:
1. Check troubleshooting section
2. Review logs
3. Create issue on repository
4. Contact team lead

---

**Made with ❤️ for automation testing team**
