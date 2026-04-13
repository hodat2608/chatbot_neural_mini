# NeuralChat — AI Chat Web App

Ứng dụng web chat AI đầy đủ tính năng, tích hợp API GPT-4o.

## 🚀 Cài đặt & Chạy

```bash
# 1. Cài dependencies
pip install -r requirements.txt

# 2. Chạy server
python app.py

# 3. Truy cập
http://localhost:5000
```

## ✨ Tính năng

- 💬 **Chat AI real-time** với streaming (SSE)
- 📁 **Lưu trữ lịch sử** cuộc trò chuyện (SQLite)
- 🗑️ **Xóa cuộc trò chuyện** hoặc xóa tin nhắn
- ✏️ **Đổi tên** cuộc trò chuyện
- 🤖 **Chọn model**: GPT-4o, GPT-4o Mini, GPT-4 Turbo, GPT-3.5
- 📝 **Markdown rendering** với syntax highlighting
- 📋 **Copy code** button trên code blocks
- ⌨️ **Shift+Enter** để xuống dòng
- 📱 **Responsive** — hoạt động trên mobile

## 📁 Cấu trúc

```
ai-chat/
├── app.py              # Flask backend + API routes
├── requirements.txt    # Python dependencies
├── chat.db             # SQLite database (tự tạo khi chạy)
└── templates/
    └── index.html      # Frontend (HTML/CSS/JS all-in-one)
```

## 🔌 API Endpoints

| Method | Route | Mô tả |
|--------|-------|-------|
| GET | `/api/conversations` | Lấy danh sách cuộc trò chuyện |
| POST | `/api/conversations` | Tạo cuộc trò chuyện mới |
| GET | `/api/conversations/<id>` | Lấy chi tiết + tin nhắn |
| DELETE | `/api/conversations/<id>` | Xóa cuộc trò chuyện |
| PATCH | `/api/conversations/<id>/rename` | Đổi tên |
| POST | `/api/conversations/<id>/clear` | Xóa tin nhắn |
| POST | `/api/chat` | Gửi tin nhắn (SSE streaming) |

## 🔧 Cấu hình

Thay API key trong `app.py`:
```python
client = OpenAI(
    api_key="YOUR_API_KEY",
    base_url="https://api.llmapi.ai/v1"
)
```
