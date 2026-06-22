-- 初始化数据库表结构

CREATE DATABASE IF NOT EXISTS llm_efds CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE llm_efds;

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role ENUM('admin', 'user') DEFAULT 'user',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 设备表
CREATE TABLE IF NOT EXISTS devices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    model VARCHAR(100),
    manufacturer VARCHAR(100),
    category VARCHAR(50),
    location VARCHAR(200),
    installation_date TIMESTAMP,
    status VARCHAR(20) DEFAULT 'normal',
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 故障案例表
CREATE TABLE IF NOT EXISTS fault_cases (
    id INT AUTO_INCREMENT PRIMARY KEY,
    device_id INT,
    fault_type VARCHAR(50) NOT NULL,
    fault_phenomenon TEXT NOT NULL,
    fault_reason TEXT,
    solution TEXT,
    maintenance_record TEXT,
    severity VARCHAR(20),
    status VARCHAR(20) DEFAULT 'open',
    reported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE SET NULL
);

-- 知识文档表
CREATE TABLE IF NOT EXISTS knowledge_documents (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    file_path VARCHAR(500),
    file_type VARCHAR(20),
    content TEXT,
    chunk_count INT DEFAULT 0,
    status ENUM('pending', 'processing', 'completed', 'failed') DEFAULT 'pending',
    error_message TEXT,
    uploaded_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (uploaded_by) REFERENCES users(id) ON DELETE SET NULL
);

-- 对话表
CREATE TABLE IF NOT EXISTS conversations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    title VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 消息表
CREATE TABLE IF NOT EXISTS messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    conversation_id INT,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    metadata TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
);

-- 创建索引
CREATE INDEX idx_devices_category ON devices(category);
CREATE INDEX idx_devices_status ON devices(status);
CREATE INDEX idx_fault_cases_device_id ON fault_cases(device_id);
CREATE INDEX idx_fault_cases_status ON fault_cases(status);
CREATE INDEX idx_fault_cases_severity ON fault_cases(severity);
CREATE INDEX idx_knowledge_documents_status ON knowledge_documents(status);
CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);

-- 维护记录表
CREATE TABLE IF NOT EXISTS maintenance_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    device_id INT NOT NULL,
    maintenance_type VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    content TEXT,
    technician VARCHAR(100),
    cost FLOAT DEFAULT 0,
    parts_replaced TEXT,
    next_maintenance_date TIMESTAMP,
    status VARCHAR(20) DEFAULT 'completed',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE
);

-- 问题上报表
CREATE TABLE IF NOT EXISTS issue_reports (
    id INT AUTO_INCREMENT PRIMARY KEY,
    device_id INT,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    issue_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) DEFAULT 'medium',
    priority VARCHAR(20) DEFAULT 'normal',
    status VARCHAR(20) DEFAULT 'open',
    reporter_name VARCHAR(100) NOT NULL,
    reporter_department VARCHAR(100),
    assignee_name VARCHAR(100),
    assignee_department VARCHAR(100),
    location VARCHAR(200),
    attachment_url VARCHAR(500),
    progress_percent INT DEFAULT 0,
    due_date TIMESTAMP,
    resolved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE SET NULL
);

-- 工作进度表
CREATE TABLE IF NOT EXISTS work_progress (
    id INT AUTO_INCREMENT PRIMARY KEY,
    issue_id INT NOT NULL,
    user_name VARCHAR(100) NOT NULL,
    user_department VARCHAR(100),
    progress_note TEXT NOT NULL,
    progress_percent INT,
    status VARCHAR(20),
    action_taken TEXT,
    hours_spent FLOAT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (issue_id) REFERENCES issue_reports(id) ON DELETE CASCADE
);

-- 新表索引
CREATE INDEX idx_maintenance_records_device_id ON maintenance_records(device_id);
CREATE INDEX idx_maintenance_records_status ON maintenance_records(status);
CREATE INDEX idx_issue_reports_device_id ON issue_reports(device_id);
CREATE INDEX idx_issue_reports_status ON issue_reports(status);
CREATE INDEX idx_issue_reports_severity ON issue_reports(severity);
CREATE INDEX idx_issue_reports_reporter_dept ON issue_reports(reporter_department);
CREATE INDEX idx_issue_reports_assignee_dept ON issue_reports(assignee_department);
CREATE INDEX idx_work_progress_issue_id ON work_progress(issue_id);

-- 模型提供商配置表
CREATE TABLE IF NOT EXISTS model_providers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    provider_type ENUM('third_party', 'local') DEFAULT 'third_party',
    provider_name VARCHAR(50) NOT NULL,
    api_base VARCHAR(500) NOT NULL,
    api_key VARCHAR(500) DEFAULT '',
    model_name VARCHAR(100) NOT NULL,
    temperature FLOAT DEFAULT 0.7,
    max_tokens INT DEFAULT 2048,
    is_default BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    extra_config TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE INDEX idx_model_providers_type ON model_providers(provider_type);
CREATE INDEX idx_model_providers_active ON model_providers(is_active);
CREATE INDEX idx_model_providers_default ON model_providers(is_default);

-- 系统设置表
CREATE TABLE IF NOT EXISTS system_settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    `key` VARCHAR(100) UNIQUE NOT NULL,
    value TEXT,
    description VARCHAR(255),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 操作日志表
CREATE TABLE IF NOT EXISTS operation_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    username VARCHAR(50),
    action VARCHAR(255) NOT NULL,
    detail TEXT,
    ip_address VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_operation_logs_user_id ON operation_logs(user_id);
CREATE INDEX idx_operation_logs_created_at ON operation_logs(created_at);

-- 插入默认管理员用户 (密码: admin123)
INSERT INTO users (username, email, hashed_password, role) VALUES
('admin', 'admin@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.LLdAH.9gCQqK2W', 'admin');
