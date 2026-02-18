# EgoZone 信任设备管理指南

## 功能说明

为了在安全性与便利性之间取得平衡，EgoZone 实现了信任设备功能：

1. **安全增强**：重新启用了密码验证功能，确保每次非信任设备访问都需要验证密码
2. **便利性保持**：对信任设备（如家里的电脑、公司的电脑和手机）提供免密码登录

## 如何使用

### 1. 首次登录并信任设备

1. 在您信任的设备（如家里的电脑）上访问 EgoZone
2. 使用正确的管理员密码或公共访问密码登录
3. 在登录界面勾选"信任此设备"选项
4. 系统会记录该设备的信息并将其加入信任列表

### 2. 查看信任设备

您可以随时通过 API 端点查看当前的信任设备列表：
```
GET /api/auth/trusted-devices
```

### 3. 移除信任设备

如果某个设备不再可信，您可以通过以下 API 端点移除它：
```
DELETE /api/auth/trusted-devices/{device_fingerprint}
```

### 4. 命令行管理工具

我们还提供了命令行工具来管理信任设备：

#### 初始化信任设备列表
```bash
python manage_trusted_devices.py init
```

#### 列出所有信任设备
```bash
python manage_trusted_devices.py list
```

#### 手动添加信任设备
```bash
python manage_trusted_devices.py add --fingerprint <设备指纹> --name "<设备名称>"
```

#### 移除信任设备
```bash
python manage_trusted_devices.py remove --fingerprint <设备指纹>
```

## 技术细节

### 设备指纹生成

系统通过以下信息生成唯一的设备指纹：
- User-Agent 头部信息
- IP 地址
- 其他请求头信息

### 数据存储

信任设备信息存储在 `data/trusted_devices.json` 文件中，包含：
- 设备指纹
- 设备名称
- 添加时间
- 最后使用时间
- User-Agent 信息

## 安全提示

1. 定期检查信任设备列表，移除不再使用的设备
2. 在公共或共享设备上不要选择"信任此设备"
3. 如果怀疑信任设备被入侵，请立即移除其信任状态
4. 定期更换管理员和访问密码

## API 变更

以下 API 端点已更新以支持信任设备功能：

### 登录端点
- `POST /api/auth/login` - 支持 `trust_device` 参数
- `POST /api/auth/access-login` - 支持 `trust_device` 参数

### 设备管理端点
- `GET /api/auth/trusted-devices` - 获取信任设备列表
- `DELETE /api/auth/trusted-devices/{device_fingerprint}` - 移除信任设备
- `POST /api/auth/trust-device` - 手动添加信任设备