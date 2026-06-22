# LLM-EFDS 测试方案

## 1. 测试概述

本测试方案涵盖基于大模型的设备故障诊断系统的后端API测试、前端组件测试以及集成测试。

## 2. 后端API测试

### 2.1 用户服务测试

```bash
# 测试用户注册
curl -X POST "http://localhost:8000/api/users/register" \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@example.com","password":"test123456"}'

# 测试用户登录
curl -X POST "http://localhost:8000/api/users/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=test123456"

# 测试获取当前用户信息
curl -X GET "http://localhost:8000/api/users/me" \
  -H "Authorization: Bearer <token>"
```

### 2.2 故障诊断服务测试

```bash
# 测试故障诊断
curl -X POST "http://localhost:8000/api/diagnosis/diagnose" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"fault_phenomenon":"电机运行时出现异常振动和温度升高"}'

# 测试AI对话
curl -X POST "http://localhost:8000/api/diagnosis/chat" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"query":"电机温度过高怎么办？"}'
```

### 2.3 知识库服务测试

```bash
# 测试上传文档
curl -X POST "http://localhost:8000/api/knowledge/upload" \
  -H "Authorization: Bearer <token>" \
  -F "file=@/path/to/document.pdf" \
  -F "title=电机维护手册"

# 测试获取文档列表
curl -X GET "http://localhost:8000/api/knowledge/documents" \
  -H "Authorization: Bearer <token>"

# 测试搜索文档
curl -X GET "http://localhost:8000/api/knowledge/search?query=轴承" \
  -H "Authorization: Bearer <token>"
```

### 2.4 对话服务测试

```bash
# 获取对话列表
curl -X GET "http://localhost:8000/api/chat/conversations" \
  -H "Authorization: Bearer <token>"

# 获取对话消息
curl -X GET "http://localhost:8000/api/chat/conversations/1/messages" \
  -H "Authorization: Bearer <token>"
```

## 3. 前端测试

### 3.1 页面功能测试

| 页面 | 测试项 | 预期结果 |
|------|--------|----------|
| 首页 | 功能导航点击 | 正确跳转到对应页面 |
| 首页 | 最近案例点击 | 正确跳转到案例详情 |
| 诊断页 | 输入故障现象 | 显示诊断结果 |
| 诊断页 | 示例点击 | 自动填充输入框 |
| 知识库 | 上传文档 | 显示上传进度和状态 |
| 知识库 | 搜索文档 | 正确过滤显示结果 |
| 案例页 | 筛选状态 | 正确过滤案例列表 |
| 案例页 | 查看详情 | 弹出详情弹窗 |
| 设备页 | 设备卡片点击 | 弹出设备详情 |
| 对话页 | 发送消息 | AI正确回复 |
| 登录页 | 注册登录 | 正确流程完成 |

### 3.2 浏览器自动化测试

```bash
# 使用agent-browser进行E2E测试
agent-browser open http://localhost:5173
agent-browser wait --load networkidle
agent-browser screenshot homepage.png

# 测试登录流程
agent-browser open http://localhost:5173/login
agent-browser snapshot -i
agent-browser fill @e1 "testuser"
agent-browser fill @e2 "password123"
agent-browser click @e3
agent-browser wait --url "**/"
```

## 4. 集成测试

### 4.1 RAG流程测试

1. 上传测试文档到知识库
2. 等待文档处理完成（状态变为completed）
3. 使用相关关键词进行诊断
4. 验证返回结果包含知识库内容

### 4.2 LLM集成测试

1. 配置LLM API密钥
2. 测试诊断接口
3. 验证返回JSON格式正确
4. 测试流式响应（如果启用）

## 5. 性能测试

### 5.1 并发测试

```bash
# 使用wrk进行压力测试
wrk -t4 -c100 -d30s http://localhost:8000/health
```

### 5.2 响应时间测试

| 接口 | 目标响应时间 | 最大响应时间 |
|------|--------------|--------------|
| /health | < 100ms | 500ms |
| /api/users/login | < 500ms | 2s |
| /api/diagnosis/diagnose | < 5s | 10s |
| /api/knowledge/upload | < 10s | 30s |

## 6. 安全测试

### 6.1 认证测试

- 未登录访问受保护接口应返回401
- 使用无效token应返回401
- 使用过期token应返回401

### 6.2 权限测试

- 普通用户不能访问管理员接口
- 用户只能访问自己的对话记录

## 7. 测试脚本

### 7.1 后端测试脚本 (backend/tests/run_tests.py)

```python
import pytest
import requests
import time

BASE_URL = "http://localhost:8000"

def test_health():
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_user_registration():
    response = requests.post(
        f"{BASE_URL}/api/users/register",
        json={
            "username": f"testuser_{int(time.time())}",
            "email": f"test_{int(time.time())}@example.com",
            "password": "test123456"
        }
    )
    assert response.status_code == 200

def test_user_login():
    # 先注册
    username = f"testuser_{int(time.time())}"
    requests.post(
        f"{BASE_URL}/api/users/register",
        json={
            "username": username,
            "email": f"{username}@example.com",
            "password": "test123456"
        }
    )
    # 再登录
    response = requests.post(
        f"{BASE_URL}/api/users/login",
        data={"username": username, "password": "test123456"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

### 7.2 前端测试脚本 (frontend/tests/e2e.test.ts)

```typescript
import { test, expect } from '@playwright/test';

test.describe('LLM-EFDS E2E Tests', () => {
  test('homepage loads correctly', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('h1')).toContainText('LLM-EFDS');
  });

  test('navigation works', async ({ page }) => {
    await page.goto('/');
    await page.click('text=智能诊断');
    await expect(page).toHaveURL('/diagnosis');
  });

  test('diagnosis form submission', async ({ page }) => {
    await page.goto('/diagnosis');
    await page.fill('textarea', '电机运行时出现异常振动');
    await page.click('button:has-text("开始智能诊断")');
    await expect(page.locator('text=诊断结果')).toBeVisible({ timeout: 10000 });
  });
});
```

## 8. 运行测试

### 8.1 后端测试

```bash
cd backend
pip install pytest requests
pytest tests/test_api.py -v
```

### 8.2 前端测试

```bash
cd frontend
npm install -D @playwright/test
npx playwright test
```

## 9. 测试报告

测试完成后，生成以下报告：
- API测试报告 (backend/tests/report.html)
- 前端E2E测试报告 (frontend/test-results/)
- 性能测试报告 (performance-report.txt)
