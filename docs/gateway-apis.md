# Gateway Client API 接口文档

## 基础信息

- **服务名称**: Gateway Client API
- **基础路径**: `/api/v1/gateway`
- **默认端口**: 2381

## API 接口

### 1. HTTP 服务接口

#### 1.1 注册 HTTP 服务

**接口**: `GET /api/v1/gateway/http/{service_name}`

**描述**: 注册指定服务的 HTTP 访问，自动配置 Kong 反向代理并返回访问地址。

**参数**:
- `service_name` (路径参数): 服务名称

**响应**:
```json
{
  "success": true,
  "message": "HTTP 服务注册成功",
  "data": {
    "http_endpoint": "myservice.example.com",
    "service_name": "myservice",
    "container_name": "myservice_container",
    "http_port": 8080
  }
}
```

**错误响应**:
```json
{
  "success": false,
  "message": "服务 myservice 不存在"
}
```

#### 1.2 删除 HTTP 服务

**接口**: `DELETE /api/v1/gateway/http/{service_name}`

**描述**: 删除指定服务的 HTTP 注册，清理 Kong 代理配置。

**参数**:
- `service_name` (路径参数): 服务名称

**响应**:
```json
{
  "success": true,
  "message": "HTTP 服务删除成功",
  "data": {
    "service_name": "myservice"
  }
}
```

### 2. SSH 服务接口

#### 2.1 注册 SSH 服务

**接口**: `GET /api/v1/gateway/ssh/{service_name}`

**描述**: 注册指定服务的 SSH 访问，自动配置 FRP TCP 转发并分配外部端口。

**参数**:
- `service_name` (路径参数): 服务名称

**响应**:
```json
{
  "success": true,
  "message": "SSH 服务注册成功",
  "data": {
    "ssh_endpoint": "connect.example.com:40001",
    "service_name": "myservice",
    "container_name": "myservice_container",
    "ssh_port": 40001
  }
}
```

**错误响应**:
```json
{
  "success": false,
  "message": "端口池分配失败: 无可用端口"
}
```

#### 2.2 删除 SSH 服务

**接口**: `DELETE /api/v1/gateway/ssh/{service_name}`

**描述**: 删除指定服务的 SSH 注册，清理 FRP 代理配置并释放端口。

**参数**:
- `service_name` (路径参数): 服务名称

**响应**:
```json
{
  "success": true,
  "message": "SSH 服务删除成功",
  "data": {
    "service_name": "myservice"
  }
}
```

### 3. 系统接口

#### 3.1 健康检查

**接口**: `GET /health`

**描述**: 检查服务健康状态。

**响应**:
```json
{
  "status": "healthy",
  "service": "gateway-client-api"
}
```

#### 3.2 根路径信息

**接口**: `GET /`

**描述**: 获取 API 基础信息和可用端点列表。

**响应**:
```json
{
  "message": "Gateway Client API",
  "version": "1.0.0",
  "endpoints": [
    "GET /api/v1/gateway/http/{service-name} - 注册HTTP服务",
    "DELETE /api/v1/gateway/http/{service-name} - 删除HTTP服务",
    "GET /api/v1/gateway/ssh/{service-name} - 注册SSH服务",
    "DELETE /api/v1/gateway/ssh/{service-name} - 删除SSH服务"
  ]
}
```

## 使用示例

### 1. 注册 HTTP 服务

```bash
# 注册名为 "web-app" 的 HTTP 服务
curl -X GET "http://localhost:2381/api/v1/gateway/http/web-app"

# 响应
{
  "success": true,
  "message": "HTTP 服务注册成功",
  "data": {
    "http_endpoint": "web-app.example.com",
    "service_name": "web-app",
    "container_name": "web-app_container",
    "http_port": 8080
  }
}

# 访问服务
curl -H "Host: web-app.example.com" http://example.com
```

### 2. 注册 SSH 服务

```bash
# 注册名为 "dev-env" 的 SSH 服务
curl -X GET "http://localhost:2381/api/v1/gateway/ssh/dev-env"

# 响应
{
  "success": true,
  "message": "SSH 服务注册成功",
  "data": {
    "ssh_endpoint": "connect.example.com:40001",
    "service_name": "dev-env",
    "container_name": "dev-env_container",
    "ssh_port": 40001
  }
}

# SSH 连接
ssh user@connect.example.com -p 40001
```

### 3. 删除服务

```bash
# 删除 HTTP 服务
curl -X DELETE "http://localhost:2381/api/v1/gateway/http/web-app"

# 删除 SSH 服务
curl -X DELETE "http://localhost:2381/api/v1/gateway/ssh/dev-env"
```

## 错误处理

### 常见错误码

- **服务不存在**: 当请求的服务在服务发现中不存在时返回
- **服务已注册**: 当服务已经注册且容器名称匹配时返回成功状态
- **端口分配失败**: SSH 服务端口池耗尽时返回
- **代理配置失败**: Kong 或 FRP 代理配置失败时返回
- **连接失败**: 无法连接到 etcd、Kong 或 FRP 服务时返回

### 错误响应格式

```json
{
  "success": false,
  "message": "具体错误信息描述"
}
```
