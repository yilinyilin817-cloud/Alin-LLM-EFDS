# LLM-EFDS - 基于大模型的设备故障诊断系统

基于大语言模型（LLM）和检索增强生成（RAG）技术的智能设备故障诊断系统。

## 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        Vue3 前端                                │
│   首页 | 智能诊断 | 知识库管理 | 案例管理 | 设备档案 | 智能问答   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI 网关                                │
├──────────┬───────────┬───────────┬───────────┬────────────────┤
│ 用户服务  │ 故障诊断   │ 知识库    │ RAG服务   │ LLM服务        │
└──────────┴───────────┴───────────┴───────────┴────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
        ┌──────────┐   ┌──────────┐   ┌──────────┐
        │  Milvus  │   │  MySQL   │   │  LLM API │
        │ (向量库)  │   │ (关系库)  │   │ (GPT等)  │
        └──────────┘   └──────────┘   └──────────┘
```

## 功能特性

- **智能诊断**: 基于AI的设备故障智能诊断，快速定位问题
- **RAG检索**: 结合知识库进行检索增强生成，提高诊断准确性
- **知识库管理**: 支持文档上传、自动分块、向量化存储
- **案例管理**: 历史故障案例积累与复用
- **设备档案**: 设备信息管理，维护记录追踪
- **智能问答**: AI助手实时对话，专业问题解答

## 技术栈

### 后端
- FastAPI - 高性能Web框架
- SQLAlchemy - ORM数据库访问
- MySQL - 关系型数据库
- Milvus - 向量数据库
- Sentence Transformers - 文本向量化
- OpenAI API - 大语言模型

### 前端
- Vue 3 - 渐进式JavaScript框架
- TypeScript - 类型安全
- Tailwind CSS - 原子化CSS框架
- Vue Router - 路由管理
- Pinia - 状态管理

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- MySQL 8.0+
- Milvus 2.3+
- Docker (可选)

### 方式一：Docker部署（推荐）

```bash
# 克隆项目
git clone <repository-url>
cd LLM-EFDS

# 设置环境变量
export LLM_API_KEY="your-openai-api-key"

# 启动所有服务
docker-compose up -d

# 访问应用
# 前端: http://localhost:5173
# 后端API: http://localhost:8000
# API文档: http://localhost:8000/docs
```

### 方式二：本地开发

#### 1. 后端设置

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填写必要的配置

# 初始化数据库
mysql -u root -p < init.sql

# 启动后端服务
uvicorn app.main:app --reload
```

#### 2. 前端设置

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

## 项目结构

```
LLM-EFDS/
├── backend/
│   ├── app/
│   │   ├── api/           # API路由
│   │   │   ├── user_router.py
│   │   │   ├── diagnosis_router.py
│   │   │   ├── knowledge_router.py
│   │   │   └── chat_router.py
│   │   ├── database/      # 数据库连接和模型
│   │   │   ├── mysql.py
│   │   │   ├── milvus.py
│   │   │   └── models.py
│   │   ├── services/      # 业务逻辑服务
│   │   │   ├── llm_service.py
│   │   │   ├── rag_service.py
│   │   │   ├── user_service.py
│   │   │   ├── knowledge_service.py
│   │   │   └── diagnosis_service.py
│   │   ├── utils/         # 工具函数
│   │   │   ├── embedding.py
│   │   │   └── text_processor.py
│   │   ├── config.py      # 配置管理
│   │   └── main.py        # 应用入口
│   ├── tests/             # 测试文件
│   ├── requirements.txt   # Python依赖
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   │   ├── pages/         # 页面组件
│   │   ├── components/    # 公共组件
│   │   ├── router/        # 路由配置
│   │   └── App.vue        # 根组件
│   ├── package.json
│   └── Dockerfile
│
├── docker-compose.yml     # Docker编排
└── README.md
```

## API文档

启动后端服务后，访问 http://localhost:8000/docs 查看完整的API文档。

### 主要接口

| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/users/register` | POST | 用户注册 |
| `/api/users/login` | POST | 用户登录 |
| `/api/diagnosis/diagnose` | POST | 故障诊断 |
| `/api/diagnosis/chat` | POST | AI对话 |
| `/api/knowledge/upload` | POST | 上传文档 |
| `/api/knowledge/documents` | GET | 获取文档列表 |
| `/api/chat/conversations` | GET | 获取对话列表 |

## 测试

### 后端测试

```bash
cd backend
pytest tests/ -v
```

### 前端测试

```bash
cd frontend
npm run test
```

### E2E测试

```bash
cd frontend
npx playwright test
```

## 配置说明

### 后端配置 (.env)

```env
# 数据库配置
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=llm_efds

# 向量数据库配置
MILVUS_HOST=localhost
MILVUS_PORT=19530

# LLM配置
LLM_API_KEY=your_openai_api_key
LLM_API_BASE=https://api.openai.com/v1
LLM_MODEL=gpt-3.5-turbo

# Embedding配置
EMBEDDING_MODEL=shibing624/text2vec-base-chinese
```

## 故障排除

### 常见问题

1. **Milvus连接失败**
   - 确保Milvus服务已启动
   - 检查端口19530是否可用

2. **LLM调用失败**
   - 检查API密钥是否正确
   - 确认网络连接正常

3. **文档向量化失败**
   - 检查Embedding模型下载状态
   - 确认向量维度配置正确

## 许可证

MIT License

## 贡献指南

欢迎提交Issue和Pull Request！
