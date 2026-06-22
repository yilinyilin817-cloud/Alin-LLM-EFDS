const http = require('http');
const fs = require('fs');
const path = require('path');
const { URL } = require('url');

const PORT = 8000;
const UPLOAD_DIR = path.join(__dirname, 'uploads', 'knowledge');

if (!fs.existsSync(UPLOAD_DIR)) {
  fs.mkdirSync(UPLOAD_DIR, { recursive: true });
}

let documents = [];
let devices = [];
let conversations = [];
let modelProviders = [];
let operationLogs = [];
let systemSettings = { rag_top_k: 5, similarity_threshold: 0.7 };
let docIdCounter = 1;
let deviceIdCounter = 1;

let users = [
  { id: 1, username: 'admin', email: 'admin@example.com', password: 'admin123', role: 'admin', is_active: true, created_at: new Date().toISOString() }
];
let userIdCounter = 2;
let convIdCounter = 1;
let msgIdCounter = 1;
let providerIdCounter = 1;
let logIdCounter = 1;

function addLog(action, detail) {
  operationLogs.unshift({
    id: logIdCounter++,
    user: 'admin',
    action,
    detail: detail || '',
    ip: '127.0.0.1',
    time: new Date().toLocaleString('zh-CN'),
  });
  if (operationLogs.length > 200) operationLogs.length = 200;
}

function detectEncoding(buffer) {
  if (buffer.length >= 3 && buffer[0] === 0xEF && buffer[1] === 0xBB && buffer[2] === 0xBF) return 'utf8';
  if (buffer.length >= 2 && ((buffer[0] === 0xFF && buffer[1] === 0xFE) || (buffer[0] === 0xFE && buffer[1] === 0xFF))) return 'utf16';
  let hasHighBytes = false, isUtf8 = true, i = 0;
  while (i < buffer.length) {
    if (buffer[i] <= 0x7F) { i++; }
    else if (buffer[i] >= 0xC0 && buffer[i] <= 0xDF) {
      if (i + 1 >= buffer.length || buffer[i + 1] < 0x80 || buffer[i + 1] > 0xBF) { isUtf8 = false; break; }
      i += 2; hasHighBytes = true;
    } else if (buffer[i] >= 0xE0 && buffer[i] <= 0xEF) {
      if (i + 2 >= buffer.length || buffer[i + 1] < 0x80 || buffer[i + 1] > 0xBF || buffer[i + 2] < 0x80 || buffer[i + 2] > 0xBF) { isUtf8 = false; break; }
      i += 3; hasHighBytes = true;
    } else if (buffer[i] >= 0xF0 && buffer[i] <= 0xF7) {
      if (i + 3 >= buffer.length || buffer[i + 1] < 0x80 || buffer[i + 1] > 0xBF || buffer[i + 2] < 0x80 || buffer[i + 2] > 0xBF || buffer[i + 3] < 0x80 || buffer[i + 3] > 0xBF) { isUtf8 = false; break; }
      i += 4; hasHighBytes = true;
    } else { isUtf8 = false; break; }
  }
  if (isUtf8 && hasHighBytes) return 'utf8';
  if (!hasHighBytes) return 'utf8';
  let gbkScore = 0;
  for (let j = 0; j < buffer.length - 1; j++) {
    if (buffer[j] >= 0x81 && buffer[j] <= 0xFE) {
      if (buffer[j + 1] >= 0x40 && buffer[j + 1] <= 0xFE && buffer[j + 1] !== 0x7F) { gbkScore++; j++; }
    }
  }
  return gbkScore > 10 ? 'gbk' : 'utf8';
}

function readFileWithEncoding(filePath) {
  const buffer = fs.readFileSync(filePath);
  const encoding = detectEncoding(buffer);
  try { return new TextDecoder(encoding === 'gbk' ? 'gbk' : 'utf-8', { fatal: true }).decode(buffer); }
  catch {
    try { return new TextDecoder('gbk', { fatal: true }).decode(buffer); }
    catch { return buffer.toString('utf-8'); }
  }
}

function parseMultipart(buffer, boundary) {
  const parts = {};
  const boundaryBuffer = Buffer.from(`--${boundary}`);
  let start = buffer.indexOf(boundaryBuffer) + boundaryBuffer.length + 2;
  while (start < buffer.length) {
    const end = buffer.indexOf(boundaryBuffer, start);
    if (end === -1) break;
    const partBuffer = buffer.slice(start, end - 2);
    const headerEnd = partBuffer.indexOf('\r\n\r\n');
    if (headerEnd !== -1) {
      const header = partBuffer.slice(0, headerEnd).toString('utf-8');
      const body = partBuffer.slice(headerEnd + 4);
      const nameMatch = header.match(/name="([^"]+)"/);
      const filenameMatch = header.match(/filename="([^"]+)"/);
      if (filenameMatch) {
        const enc = detectEncoding(body);
        let content;
        try { content = new TextDecoder(enc === 'gbk' ? 'gbk' : 'utf-8').decode(body); } catch { content = body.toString('utf-8'); }
        parts.filename = filenameMatch[1]; parts.content = content; parts.encoding = enc; parts.rawBuffer = body;
      } else if (nameMatch) { parts[nameMatch[1]] = body.toString('utf-8'); }
    }
    start = end + boundaryBuffer.length + 2;
  }
  return parts;
}

const MOCK_RESPONSES = {
  default: `感谢您的提问。基于您描述的情况，我来进行分析：

**初步分析**

针对您提到的问题，需要从以下几个维度进行排查：

1. **设备运行状态检查**：确认设备运行参数是否在正常范围内
2. **历史维护记录**：查看近期是否进行过维修或更换部件
3. **环境因素**：温度、湿度、粉尘等环境条件是否异常

**建议操作**

- 首先进行设备巡检，记录关键参数
- 查阅设备维护手册中的故障排查流程
- 如有需要，可以使用专业检测工具进一步诊断

> 请提供更多详细的故障现象描述，我可以给出更精确的诊断建议。`,
  振动: `针对**设备异常振动**问题，以下是详细的诊断分析：

**常见振动原因**

1. **机械不平衡**：旋转部件质量分布不均
2. **不对中**：联轴器连接的两轴中心线偏差
3. **轴承故障**：磨损、润滑不良或损坏
4. **松动**：基础螺栓或部件连接松动

**诊断方法**

- 使用**振动分析仪**采集振动信号
- 分析频谱图中的特征频率
- 结合时域波形判断故障类型

**推荐工具**

| 检测项目 | 推荐工具 | 精度要求 |
|---------|---------|---------|
| 振动测量 | 便携式测振仪 | ±5% |
| 温度监测 | 红外测温仪 | ±1°C |
| 对中校正 | 激光对中仪 | 0.01mm |

需要我针对具体设备类型提供更详细的方案吗？`,
  温度: `关于**设备温度异常**的问题，分析如下：

**温度升高的可能原因**

1. **摩擦增大**：润滑不良或部件磨损
2. **散热不足**：冷却系统故障或散热器堵塞
3. **过载运行**：实际负载超过额定值
4. **电气故障**：绕组绝缘下降、接触不良

**处理建议**

- 立即检查冷却系统工作状态
- 监测温度变化趋势，记录温升速率
- 如温度持续上升，建议降负荷或停机检查

> **安全提示**：电机轴承温度超过95°C或绕组温度超过绝缘等级允许值时，必须立即停机。`,
};

function getMockResponse(query) {
  for (const [keyword, response] of Object.entries(MOCK_RESPONSES)) {
    if (keyword !== 'default' && query.includes(keyword)) return response;
  }
  return MOCK_RESPONSES.default;
}

const SUPPORTED_PROVIDERS = {
  third_party: [
    { name: 'openai', label: 'OpenAI', default_base: 'https://api.openai.com/v1' },
    { name: 'deepseek', label: 'DeepSeek', default_base: 'https://api.deepseek.com/v1' },
    { name: 'zhipu', label: '智谱AI (ChatGLM)', default_base: 'https://open.bigmodel.cn/api/paas/v4' },
    { name: 'qwen', label: '通义千问', default_base: 'https://dashscope.aliyuncs.com/compatible-mode/v1' },
    { name: 'moonshot', label: 'Moonshot (Kimi)', default_base: 'https://api.moonshot.cn/v1' },
    { name: 'baichuan', label: '百川智能', default_base: 'https://api.baichuan-ai.com/v1' },
    { name: 'yi', label: '零一万物 (Yi)', default_base: 'https://api.lingyiwanwu.com/v1' },
    { name: 'minimax', label: 'MiniMax', default_base: 'https://api.minimax.chat/v1' },
    { name: 'spark', label: '讯飞星火', default_base: 'https://spark-api-open.xf-yun.com/v1' },
    { name: 'doubao', label: '豆包 (火山引擎)', default_base: 'https://ark.cn-beijing.volces.com/api/v3' },
    { name: 'openai_compatible', label: 'OpenAI兼容接口', default_base: '' },
  ],
  local: [
    { name: 'ollama', label: 'Ollama', default_base: 'http://localhost:11434/v1' },
    { name: 'vllm', label: 'vLLM', default_base: 'http://localhost:8000/v1' },
    { name: 'lmstudio', label: 'LM Studio', default_base: 'http://localhost:1234/v1' },
    { name: 'text_generation', label: 'text-generation-webui', default_base: 'http://localhost:5000/v1' },
    { name: 'local_compatible', label: '本地OpenAI兼容接口', default_base: 'http://localhost:8000/v1' },
  ]
};

const server = http.createServer((req, res) => {
  const url = new URL(req.url, `http://${req.headers.host}`);
  const pathname = url.pathname;
  const method = req.method;

  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  res.setHeader('Content-Type', 'application/json; charset=utf-8');

  if (method === 'OPTIONS') { res.writeHead(200); res.end(); return; }

  const sendJson = (data, status = 200) => {
    res.writeHead(status, { 'Content-Type': 'application/json; charset=utf-8' });
    res.end(JSON.stringify(data));
  };

  const getBody = () => new Promise((resolve) => {
    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', () => { try { resolve(JSON.parse(body)); } catch { resolve({}); } });
  });

  // Health
  if (pathname === '/' || pathname === '/health') { sendJson({ status: 'healthy', version: '1.0.0' }); return; }

  // Users
  if (pathname === '/api/users/login' && method === 'POST') {
    getBody().then(data => {
      const { username, password } = data;
      const user = users.find(u => u.username === username && u.password === password);
      if (user) {
        sendJson({ access_token: `token-${user.id}-${Date.now()}`, token_type: 'bearer', user: { id: user.id, username: user.username, role: user.role } });
      } else {
        sendJson({ detail: '用户名或密码错误' }, 401);
      }
    });
    return;
  }

  if (pathname === '/api/users/register' && method === 'POST') {
    getBody().then(data => {
      const { username, email, password } = data;
      if (!username || !email || !password) {
        sendJson({ detail: '请填写所有必填字段' }, 400);
        return;
      }
      if (password.length < 6) {
        sendJson({ detail: '密码长度至少6位' }, 400);
        return;
      }
      if (users.find(u => u.username === username)) {
        sendJson({ detail: '用户名已存在' }, 400);
        return;
      }
      if (users.find(u => u.email === email)) {
        sendJson({ detail: '邮箱已被注册' }, 400);
        return;
      }
      const newUser = {
        id: userIdCounter++,
        username,
        email,
        password,
        role: 'user',
        is_active: true,
        created_at: new Date().toISOString()
      };
      users.push(newUser);
      addLog('创建用户', `用户名: ${username}`);
      sendJson({ id: newUser.id, username: newUser.username, email: newUser.email, is_active: newUser.is_active, role: newUser.role });
    });
    return;
  }

  if (pathname === '/api/users/me' && method === 'GET') {
    sendJson({ id: 1, username: 'admin', email: 'admin@example.com', is_active: true, role: 'admin' });
    return;
  }

  if (pathname === '/api/users/list' && method === 'GET') {
    sendJson(users.map(u => ({ id: u.id, username: u.username, email: u.email, is_active: u.is_active, role: u.role, created_at: u.created_at })));
    return;
  }

  if (pathname.match(/^\/api\/users\/\d+$/) && method === 'PUT') {
    const id = parseInt(pathname.split('/').pop());
    const user = users.find(u => u.id === id);
    if (!user) { sendJson({ detail: '用户不存在' }, 404); return; }
    getBody().then(data => {
      if (data.email) user.email = data.email;
      if (data.role) user.role = data.role;
      if (data.is_active !== undefined) user.is_active = data.is_active;
      addLog('更新用户', `用户ID: ${id}`);
      sendJson({ id: user.id, username: user.username, email: user.email, is_active: user.is_active, role: user.role });
    });
    return;
  }

  if (pathname.match(/^\/api\/users\/\d+$/) && method === 'DELETE') {
    const id = parseInt(pathname.split('/').pop());
    const index = users.findIndex(u => u.id === id);
    if (index === -1) { sendJson({ detail: '用户不存在' }, 404); return; }
    if (users[index].role === 'admin') { sendJson({ detail: '不能删除管理员账户' }, 400); return; }
    users.splice(index, 1);
    addLog('删除用户', `用户ID: ${id}`);
    sendJson({ message: '用户删除成功' });
    return;
  }

  if (pathname.match(/^\/api\/users\/\d+\/password$/) && method === 'PUT') {
    const id = parseInt(pathname.split('/')[4]);
    const user = users.find(u => u.id === id);
    if (!user) { sendJson({ detail: '用户不存在' }, 404); return; }
    getBody().then(data => {
      if (!data.password || data.password.length < 6) {
        sendJson({ detail: '密码长度至少6位' }, 400);
        return;
      }
      user.password = data.password;
      addLog('重置密码', `用户ID: ${id}`);
      sendJson({ message: '密码重置成功' });
    });
    return;
  }

  // Model providers
  if (pathname === '/api/models/providers/supported' && method === 'GET') { sendJson(SUPPORTED_PROVIDERS); return; }

  if (pathname === '/api/models/' && method === 'GET') { sendJson(modelProviders); return; }
  if (pathname === '/api/models/active' && method === 'GET') { sendJson(modelProviders.filter(p => p.is_active)); return; }

  if (pathname === '/api/models/' && method === 'POST') {
    getBody().then(data => {
      const provider = {
        id: providerIdCounter++,
        name: data.name || '未命名',
        provider_type: data.provider_type || 'third_party',
        provider_name: data.provider_name || '',
        api_base: data.api_base || '',
        api_key: data.api_key ? data.api_key.slice(0, 4) + '****' + data.api_key.slice(-4) : '',
        model_name: data.model_name || '',
        temperature: data.temperature ?? 0.7,
        max_tokens: data.max_tokens ?? 2048,
        is_default: data.is_default || false,
        is_active: data.is_active !== false,
        extra_config: data.extra_config || null,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
      if (provider.is_default) modelProviders.forEach(p => p.is_default = false);
      modelProviders.push(provider);
      addLog('创建模型配置', `名称: ${provider.name}`);
      sendJson(provider);
    });
    return;
  }

  if (pathname.match(/^\/api\/models\/\d+$/) && method === 'GET') {
    const id = parseInt(pathname.split('/').pop());
    const p = modelProviders.find(x => x.id === id);
    if (p) sendJson(p); else sendJson({ detail: '模型配置不存在' }, 404);
    return;
  }

  if (pathname.match(/^\/api\/models\/\d+$/) && method === 'PUT') {
    const id = parseInt(pathname.split('/').pop());
    const p = modelProviders.find(x => x.id === id);
    if (!p) { sendJson({ detail: '模型配置不存在' }, 404); return; }
    getBody().then(data => {
      if (data.name !== undefined) p.name = data.name;
      if (data.provider_type !== undefined) p.provider_type = data.provider_type;
      if (data.provider_name !== undefined) p.provider_name = data.provider_name;
      if (data.api_base !== undefined) p.api_base = data.api_base;
      if (data.api_key) p.api_key = data.api_key.slice(0, 4) + '****' + data.api_key.slice(-4);
      if (data.model_name !== undefined) p.model_name = data.model_name;
      if (data.temperature !== undefined) p.temperature = data.temperature;
      if (data.max_tokens !== undefined) p.max_tokens = data.max_tokens;
      if (data.is_default !== undefined) {
        if (data.is_default) modelProviders.forEach(x => x.is_default = false);
        p.is_default = data.is_default;
      }
      if (data.is_active !== undefined) p.is_active = data.is_active;
      p.updated_at = new Date().toISOString();
      addLog('更新模型配置', `ID: ${id}`);
      sendJson(p);
    });
    return;
  }

  if (pathname.match(/^\/api\/models\/\d+$/) && method === 'DELETE') {
    const id = parseInt(pathname.split('/').pop());
    const idx = modelProviders.findIndex(x => x.id === id);
    if (idx === -1) { sendJson({ detail: '模型配置不存在' }, 404); return; }
    const name = modelProviders[idx].name;
    modelProviders.splice(idx, 1);
    addLog('删除模型配置', `名称: ${name}`);
    sendJson({ message: '模型配置已删除' });
    return;
  }

  if (pathname.match(/^\/api\/models\/\d+\/toggle$/) && method === 'POST') {
    const id = parseInt(pathname.split('/')[3]);
    const p = modelProviders.find(x => x.id === id);
    if (!p) { sendJson({ detail: '模型配置不存在' }, 404); return; }
    p.is_active = !p.is_active;
    addLog(`${p.is_active ? '启用' : '禁用'}模型配置`, `名称: ${p.name}`);
    sendJson({ message: `模型配置已${p.is_active ? '启用' : '禁用'}`, is_active: p.is_active });
    return;
  }

  if (pathname.match(/^\/api\/models\/\d+\/set-default$/) && method === 'POST') {
    const id = parseInt(pathname.split('/')[3]);
    const p = modelProviders.find(x => x.id === id);
    if (!p) { sendJson({ detail: '模型配置不存在' }, 404); return; }
    modelProviders.forEach(x => x.is_default = false);
    p.is_default = true;
    addLog('设置默认模型', `名称: ${p.name}`);
    sendJson({ message: `已将 ${p.name} 设为默认模型` });
    return;
  }

  // Chat conversations
  if (pathname === '/api/chat/conversations' && method === 'GET') {
    sendJson(conversations.map(c => ({
      id: c.id,
      title: c.title,
      created_at: c.created_at,
      updated_at: c.updated_at,
    })));
    return;
  }

  if (pathname === '/api/chat/conversations' && method === 'POST') {
    getBody().then(data => {
      const conv = {
        id: convIdCounter++,
        title: data.title || '新对话',
        messages: [],
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
      conversations.unshift(conv);
      sendJson(conv);
    });
    return;
  }

  if (pathname.match(/^\/api\/chat\/conversations\/\d+$/) && method === 'GET') {
    const id = parseInt(pathname.split('/').pop());
    const c = conversations.find(x => x.id === id);
    if (!c) { sendJson({ detail: '对话不存在' }, 404); return; }
    sendJson(c.messages.map(m => ({
      id: m.id, role: m.role, content: m.content, metadata: m.metadata,
      created_at: m.created_at,
    })));
    return;
  }

  if (pathname.match(/^\/api\/chat\/conversations\/\d+\/messages$/) && method === 'GET') {
    const id = parseInt(pathname.split('/')[4]);
    const c = conversations.find(x => x.id === id);
    if (!c) { sendJson({ detail: '对话不存在' }, 404); return; }
    sendJson(c.messages.map(m => ({
      id: m.id, role: m.role, content: m.content, metadata: m.metadata,
      created_at: m.created_at,
    })));
    return;
  }

  if (pathname.match(/^\/api\/chat\/conversations\/\d+\/messages$/) && method === 'POST') {
    const id = parseInt(pathname.split('/')[4]);
    const c = conversations.find(x => x.id === id);
    if (!c) { sendJson({ detail: '对话不存在' }, 404); return; }
    getBody().then(data => {
      const userMsg = { id: msgIdCounter++, role: 'user', content: data.content, metadata: null, created_at: new Date().toISOString() };
      c.messages.push(userMsg);
      if (c.title === '新对话') c.title = data.content.slice(0, 50);

      const knowledgeRefs = [];
      for (const doc of documents) {
        if (data.content && doc.content && doc.content.toLowerCase().includes(data.content.slice(0, 10).toLowerCase())) {
          knowledgeRefs.push({ index: knowledgeRefs.length + 1, content: doc.content.slice(0, 200), score: 0.85 + Math.random() * 0.15, document_id: doc.id });
        }
      }

      const response = getMockResponse(data.content);
      const meta = knowledgeRefs.length > 0 ? { knowledge_refs: knowledgeRefs } : null;
      const assistantMsg = {
        id: msgIdCounter++, role: 'assistant', content: response,
        metadata: meta ? JSON.stringify(meta) : null,
        created_at: new Date().toISOString(),
      };
      c.messages.push(assistantMsg);
      c.updated_at = new Date().toISOString();
      sendJson({ id: assistantMsg.id, role: 'assistant', content: response, metadata: meta, created_at: assistantMsg.created_at });
    });
    return;
  }

  if (pathname.match(/^\/api\/chat\/conversations\/\d+\/stream$/) && method === 'POST') {
    const id = parseInt(pathname.split('/')[4]);
    const c = conversations.find(x => x.id === id);
    if (!c) { sendJson({ detail: '对话不存在' }, 404); return; }
    getBody().then(data => {
      const userMsg = { id: msgIdCounter++, role: 'user', content: data.content, metadata: null, created_at: new Date().toISOString() };
      c.messages.push(userMsg);
      if (c.title === '新对话') c.title = data.content.slice(0, 50);

      const knowledgeRefs = [];
      for (const doc of documents) {
        if (data.content && doc.content && doc.content.toLowerCase().includes(data.content.slice(0, 10).toLowerCase())) {
          knowledgeRefs.push({ index: knowledgeRefs.length + 1, content: doc.content.slice(0, 200), score: 0.85 + Math.random() * 0.15, document_id: doc.id });
        }
      }

      const fullResponse = getMockResponse(data.content);
      const chunks = fullResponse.split('');

      res.writeHead(200, {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Access-Control-Allow-Origin': '*',
      });

      if (knowledgeRefs.length > 0) {
        res.write(`data: ${JSON.stringify({ type: 'knowledge_refs', refs: knowledgeRefs })}\n\n`);
      }

      let idx = 0;
      const interval = setInterval(() => {
        if (idx >= chunks.length) {
          clearInterval(interval);
          const meta = knowledgeRefs.length > 0 ? { knowledge_refs: knowledgeRefs } : null;
          const msgId = msgIdCounter++;
          const assistantMsg = {
            id: msgId, role: 'assistant', content: fullResponse,
            metadata: meta ? JSON.stringify(meta) : null,
            created_at: new Date().toISOString(),
          };
          c.messages.push(assistantMsg);
          c.updated_at = new Date().toISOString();
          res.write(`data: ${JSON.stringify({ type: 'done', message_id: msgId })}\n\n`);
          res.end();
          return;
        }
        const chunkSize = Math.floor(Math.random() * 3) + 1;
        const chunk = chunks.slice(idx, idx + chunkSize).join('');
        idx += chunkSize;
        res.write(`data: ${JSON.stringify({ type: 'content', content: chunk })}\n\n`);
      }, 20);
    });
    return;
  }

  if (pathname.match(/^\/api\/chat\/conversations\/\d+$/) && method === 'DELETE') {
    const id = parseInt(pathname.split('/').pop());
    const idx = conversations.findIndex(x => x.id === id);
    if (idx === -1) { sendJson({ detail: '对话不存在' }, 404); return; }
    conversations.splice(idx, 1);
    sendJson({ message: '对话删除成功' });
    return;
  }

  if (pathname.match(/^\/api\/chat\/conversations\/\d+$/) && method === 'PUT') {
    const id = parseInt(pathname.split('/').pop());
    const c = conversations.find(x => x.id === id);
    if (!c) { sendJson({ detail: '对话不存在' }, 404); return; }
    getBody().then(data => {
      if (data.title) c.title = data.title;
      c.updated_at = new Date().toISOString();
      sendJson({ id: c.id, title: c.title, created_at: c.created_at, updated_at: c.updated_at });
    });
    return;
  }

  // Knowledge
  if (pathname === '/api/knowledge/documents' && method === 'GET') { sendJson({ documents, total: documents.length }); return; }

  if (pathname.match(/^\/api\/knowledge\/documents\/\d+$/) && method === 'GET') {
    const id = parseInt(pathname.split('/').pop());
    const doc = documents.find(d => d.id === id);
    if (doc) sendJson(doc); else sendJson({ detail: '文档不存在' }, 404);
    return;
  }

  if (pathname.match(/^\/api\/knowledge\/documents\/\d+\/content$/) && method === 'GET') {
    const id = parseInt(pathname.split('/')[4]);
    const doc = documents.find(d => d.id === id);
    if (!doc) { sendJson({ detail: '文档不存在' }, 404); return; }
    let content = doc.content || '';
    if (!content && doc.file_path && fs.existsSync(doc.file_path)) {
      try { content = readFileWithEncoding(doc.file_path); doc.content = content; } catch { content = '[无法读取文件内容]'; }
    }
    sendJson({ id, content, title: doc.title, encoding: doc.encoding || 'utf-8' });
    return;
  }

  if (pathname.match(/^\/api\/knowledge\/documents\/\d+\/content$/) && method === 'PUT') {
    const id = parseInt(pathname.split('/')[4]);
    const doc = documents.find(d => d.id === id);
    if (!doc) { sendJson({ detail: '文档不存在' }, 404); return; }
    getBody().then(data => {
      doc.content = data.content;
      doc.updated_at = new Date().toISOString();
      doc.chunk_count = Math.max(1, Math.floor((data.content || '').length / 500));
      if (doc.file_path && fs.existsSync(doc.file_path)) {
        try { fs.writeFileSync(doc.file_path, data.content, 'utf-8'); doc.encoding = 'utf-8'; } catch (e) { sendJson({ detail: `保存文件失败: ${e.message}` }, 500); return; }
      }
      sendJson(doc);
    });
    return;
  }

  if (pathname.match(/^\/api\/knowledge\/documents\/\d+$/) && method === 'PUT') {
    const id = parseInt(pathname.split('/').pop());
    const doc = documents.find(d => d.id === id);
    if (!doc) { sendJson({ detail: '文档不存在' }, 404); return; }
    getBody().then(data => {
      if (data.title) doc.title = data.title;
      if (data.content !== undefined) { doc.content = data.content; doc.chunk_count = Math.max(1, Math.floor((data.content || '').length / 500)); }
      doc.updated_at = new Date().toISOString();
      sendJson(doc);
    });
    return;
  }

  if (pathname.match(/^\/api\/knowledge\/documents\/\d+$/) && method === 'DELETE') {
    const id = parseInt(pathname.split('/').pop());
    const idx = documents.findIndex(d => d.id === id);
    if (idx === -1) { sendJson({ detail: '文档不存在' }, 404); return; }
    const doc = documents[idx];
    if (doc.file_path && fs.existsSync(doc.file_path)) { try { fs.unlinkSync(doc.file_path); } catch {} }
    documents.splice(idx, 1);
    sendJson({ message: '文档删除成功' });
    return;
  }

  if (pathname.match(/^\/api\/knowledge\/documents\/\d+\/reprocess$/) && method === 'POST') {
    const id = parseInt(pathname.split('/')[4]);
    const doc = documents.find(d => d.id === id);
    if (!doc) { sendJson({ detail: '文档不存在' }, 404); return; }
    if (doc.file_path && fs.existsSync(doc.file_path)) {
      try { doc.content = readFileWithEncoding(doc.file_path); doc.chunk_count = Math.max(1, Math.floor((doc.content || '').length / 500)); } catch {}
    }
    doc.status = 'completed'; doc.error_message = null; doc.updated_at = new Date().toISOString();
    sendJson(doc);
    return;
  }

  if (pathname === '/api/knowledge/search' && method === 'GET') {
    const query = url.searchParams.get('query') || '';
    const results = documents
      .filter(d => d.title.toLowerCase().includes(query.toLowerCase()) || (d.content || '').toLowerCase().includes(query.toLowerCase()))
      .map(d => ({ document_id: d.id, content: (d.content || '').substring(0, 200) + ((d.content || '').length > 200 ? '...' : ''), score: 0.85 + Math.random() * 0.15 }));
    sendJson({ documents: results });
    return;
  }

  if (pathname === '/api/knowledge/upload' && method === 'POST') {
    const contentType = req.headers['content-type'] || '';
    if (!contentType.includes('multipart/form-data')) { sendJson({ detail: '无效的请求格式' }, 400); return; }
    let body = [];
    req.on('data', chunk => body.push(chunk));
    req.on('end', () => {
      const buffer = Buffer.concat(body);
      const boundary = contentType.split('boundary=')[1];
      const parts = parseMultipart(buffer, boundary);
      if (!parts.filename) { sendJson({ detail: '未找到上传文件' }, 400); return; }
      const ext = path.extname(parts.filename).toLowerCase();
      const allowedExts = ['.txt', '.pdf', '.doc', '.docx', '.xlsx', '.xls', '.csv', '.md'];
      if (!allowedExts.includes(ext)) { sendJson({ detail: `不支持的文件格式: ${ext}` }, 400); return; }
      const newFilename = `${Date.now()}_${parts.filename}`;
      const filePath = path.join(UPLOAD_DIR, newFilename);
      try { fs.writeFileSync(filePath, parts.rawBuffer || parts.content, parts.rawBuffer ? undefined : 'utf-8'); } catch (e) { sendJson({ detail: `保存文件失败: ${e.message}` }, 500); return; }
      const doc = {
        id: docIdCounter++, title: path.parse(parts.filename).name, file_path: filePath, file_type: ext,
        content: parts.content || '', encoding: parts.encoding || 'utf-8',
        chunk_count: Math.max(1, Math.floor((parts.content || '').length / 500)),
        status: 'completed', error_message: null, created_at: new Date().toISOString(), updated_at: new Date().toISOString(),
      };
      documents.push(doc);
      sendJson(doc);
    });
    return;
  }

  // Diagnosis
  if (pathname === '/api/diagnosis/diagnose' && method === 'POST') {
    getBody().then(data => {
      sendJson({
        possible_causes: ['轴承磨损或损坏', '转子不平衡', '润滑不足或润滑脂变质', '电机安装不当，地脚松动'],
        repair_suggestions: ['检查轴承状况，必要时更换轴承', '进行动平衡校正', '更换润滑脂，确保润滑充分', '检查并紧固地脚螺栓'],
        preventive_measures: ['建立定期巡检制度', '制定设备润滑保养计划', '安装振动监测传感器'],
        severity: 'high',
        similar_cases: [
          { content: '某型号三相异步电机运行3个月后出现异常振动', score: 0.92 },
          { content: '液压泵站电机温度异常升高，原因为润滑脂干涸', score: 0.87 }
        ]
      });
    });
    return;
  }

  if (pathname === '/api/diagnosis/chat' && method === 'POST') {
    getBody().then(data => {
      const query = data.query || '';
      sendJson({ conversation_id: data.conversation_id || Date.now(), response: getMockResponse(query) });
    });
    return;
  }

  // Devices
  if (pathname === '/api/devices/' && method === 'GET') { sendJson(devices); return; }
  if (pathname === '/api/devices/' && method === 'POST') {
    getBody().then(data => {
      const device = { id: deviceIdCounter++, ...data, status: 'normal', installation_date: new Date().toISOString(), created_at: new Date().toISOString(), updated_at: new Date().toISOString() };
      devices.push(device);
      sendJson(device);
    });
    return;
  }

  // System settings
  if (pathname === '/api/system/settings' && method === 'GET') { sendJson(systemSettings); return; }
  if (pathname === '/api/system/settings' && method === 'PUT') {
    getBody().then(data => {
      Object.assign(systemSettings, data);
      addLog('更新系统设置', JSON.stringify(data));
      sendJson({ message: '设置已更新' });
    });
    return;
  }

  // Operation logs
  if (pathname === '/api/system/logs' && method === 'GET') {
    const skip = parseInt(url.searchParams.get('skip') || '0');
    const limit = parseInt(url.searchParams.get('limit') || '50');
    sendJson(operationLogs.slice(skip, skip + limit));
    return;
  }

  sendJson({ detail: '未找到请求的资源' }, 404);
});

server.listen(PORT, '0.0.0.0', () => {
  console.log(`\n  LLM-EFDS Backend Server`);
  console.log(`  Running on: http://localhost:${PORT}`);
  console.log(`  Health check: http://localhost:${PORT}/health`);
  console.log(`  Supported encodings: UTF-8, GBK, GB2312, UTF-16\n`);
});
