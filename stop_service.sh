#!/bin/bash
# EgoZone 服务停止脚本

echo "🛑 停止 EgoZone 服务..."

# 检查 PID 文件是否存在
if [ -f "egozone_server.pid" ]; then
    SERVER_PID=$(cat egozone_server.pid)

    # 检查进程是否还在运行
    if ps -p $SERVER_PID > /dev/null; then
        echo "🔄 发送终止信号到 PID: $SERVER_PID"
        kill $SERVER_PID

        # 等待进程结束
        sleep 2

        # 如果进程仍在运行，则强制终止
        if ps -p $SERVER_PID > /dev/null; then
            echo "💥 强制终止进程 PID: $SERVER_PID"
            kill -9 $SERVER_PID
        fi

        # 删除 PID 文件
        rm egozone_server.pid
        echo "✅ 服务已停止"
    else
        echo "⚠️  进程 PID $SERVER_PID 不存在"
        rm egozone_server.pid
    fi
else
    echo "🔍 未找到 PID 文件，搜索相关进程..."
    PIDS=$(ps aux | grep -E "uvicorn.*main" | grep -v grep | awk '{print $2}')

    if [ ! -z "$PIDS" ]; then
        echo "🔄 停止找到的 EgoZone 进程: $PIDS"
        kill $PIDS 2>/dev/null || kill -9 $PIDS 2>/dev/null
        echo "✅ 服务已停止"
    else
        echo "✅ 未找到正在运行的 EgoZone 服务"
    fi
fi