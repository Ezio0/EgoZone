#!/bin/bash
# EgoZone 本地开发服务启动脚本

echo "🚀 启动 EgoZone 本地开发服务..."

# 检查虚拟环境是否存在
if [ ! -d "venv" ]; then
    echo "❌ 虚拟环境不存在，请先运行: python -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# 检查是否有服务正在运行
if lsof -ti:8000; then
    echo "⚠️  端口 8000 已被占用，尝试停止现有服务..."
    lsof -ti:8000 | xargs kill -9 2>/dev/null || echo "未找到占用端口 8000 的进程"
fi

# 激活虚拟环境并启动服务
echo "🔌 激活虚拟环境..."
source venv/bin/activate

echo "⚡ 启动 FastAPI 服务..."
# 启动服务并将输出重定向到日志文件
nohup uvicorn main:app --host 127.0.0.1 --port 8000 --reload > service_output.log 2>&1 &

SERVER_PID=$!
echo "✅ 服务已启动，PID: $SERVER_PID"
echo "🌐 访问地址: http://127.0.0.1:8000"

# 写入 PID 到文件，以便将来停止服务
echo $SERVER_PID > egozone_server.pid

echo "📝 日志文件: service_output.log"
echo "📌 要停止服务，请运行: ./stop_service.sh"