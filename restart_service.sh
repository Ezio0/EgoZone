#!/bin/bash
# EgoZone 服务重启脚本

echo "🔄 重启 EgoZone 服务..."

# 首先停止服务
echo "🛑 正在停止现有服务..."
./stop_service.sh

# 等待一段时间确保服务完全停止
sleep 3

# 启动服务
echo "🚀 正在启动新服务..."
./start_service.sh