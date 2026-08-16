-- Script de inicialización de base de datos PostgreSQL
-- Auto-generado desde modelos SQLAlchemy
-- Crea todas las tablas necesarias para la API REST

-- ============================================================================
-- USERS TABLE - Autenticación y gestión de usuarios
-- ============================================================================
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    phone VARCHAR(20),
    country VARCHAR(100),
    professional_title VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    is_verified BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    last_login TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);

-- ============================================================================
-- IDENTITY TABLE - Perfil profesional (IKIGAI, diferenciadores)
-- ============================================================================
CREATE TABLE IF NOT EXISTS identity (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    ikigai_passion TEXT,
    ikigai_profession TEXT,
    ikigai_vocation TEXT,
    ikigai_mission TEXT,
    key_differentiators TEXT,
    unique_value_proposition TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_identity_user_id ON identity(user_id);

-- ============================================================================
-- COMPETENCIES TABLE - Competencias (técnicas, transferibles, negocio)
-- ============================================================================
CREATE TABLE IF NOT EXISTS competencies (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    type VARCHAR(50) NOT NULL,
    level VARCHAR(50),
    proficiency_score INTEGER,
    years_of_experience INTEGER,
    endorsements INTEGER DEFAULT 0,
    is_highlighted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_competencies_user_id ON competencies(user_id);
CREATE INDEX IF NOT EXISTS idx_competencies_type ON competencies(type);

-- ============================================================================
-- EVIDENCE TABLE - Evidencia (proyectos, cargos, logros, STAR cases)
-- ============================================================================
CREATE TABLE IF NOT EXISTS evidence (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    company VARCHAR(255),
    position VARCHAR(255),
    start_date DATE,
    end_date DATE,
    url VARCHAR(500),
    is_featured BOOLEAN DEFAULT FALSE,
    star_situation TEXT,
    star_task TEXT,
    star_action TEXT,
    star_result TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_evidence_user_id ON evidence(user_id);
CREATE INDEX IF NOT EXISTS idx_evidence_type ON evidence(type);

-- ============================================================================
-- JOB_STRATEGY TABLE - Estrategia de búsqueda de empleo
-- ============================================================================
CREATE TABLE IF NOT EXISTS job_strategy (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    target_role VARCHAR(255),
    target_industries TEXT,
    target_companies TEXT,
    salary_expectations VARCHAR(255),
    employment_type VARCHAR(50),
    remote_preference VARCHAR(50),
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_job_strategy_user_id ON job_strategy(user_id);
CREATE INDEX IF NOT EXISTS idx_job_strategy_status ON job_strategy(status);

-- ============================================================================
-- VACANCY TABLE - Ofertas de empleo seguidas
-- ============================================================================
CREATE TABLE IF NOT EXISTS vacancy (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    company VARCHAR(255),
    url VARCHAR(500),
    description TEXT,
    salary_range VARCHAR(255),
    location VARCHAR(255),
    employment_type VARCHAR(50),
    status VARCHAR(50) DEFAULT 'saved',
    applied_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_vacancy_user_id ON vacancy(user_id);
CREATE INDEX IF NOT EXISTS idx_vacancy_status ON vacancy(status);

-- ============================================================================
-- NETWORKING_CONTACT TABLE - Contactos de networking
-- ============================================================================
CREATE TABLE IF NOT EXISTS networking_contact (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    title VARCHAR(255),
    company VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(20),
    linkedin_url VARCHAR(500),
    relationship_type VARCHAR(50),
    contact_status VARCHAR(50) DEFAULT 'active',
    last_contact_date TIMESTAMP WITH TIME ZONE,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_networking_contact_user_id ON networking_contact(user_id);
CREATE INDEX IF NOT EXISTS idx_networking_contact_status ON networking_contact(contact_status);

-- ============================================================================
-- INTERVIEW TABLE - Seguimiento de entrevistas
-- ============================================================================
CREATE TABLE IF NOT EXISTS interview (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    vacancy_id INTEGER REFERENCES vacancy(id) ON DELETE SET NULL,
    company VARCHAR(255) NOT NULL,
    position VARCHAR(255),
    interview_type VARCHAR(50),
    interview_round VARCHAR(50),
    scheduled_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    interviewer_name VARCHAR(255),
    interviewer_email VARCHAR(255),
    interview_format VARCHAR(50),
    duration_minutes INTEGER,
    feedback TEXT,
    feedback_rating INTEGER,
    status VARCHAR(50) DEFAULT 'scheduled',
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_interview_user_id ON interview(user_id);
CREATE INDEX IF NOT EXISTS idx_interview_vacancy_id ON interview(vacancy_id);
CREATE INDEX IF NOT EXISTS idx_interview_status ON interview(status);

-- ============================================================================
-- REFRESH_TOKEN TABLE - Tokens de refresco para JWT
-- ============================================================================
CREATE TABLE IF NOT EXISTS refresh_token (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(500) UNIQUE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_revoked BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_refresh_token_user_id ON refresh_token(user_id);
CREATE INDEX IF NOT EXISTS idx_refresh_token_token ON refresh_token(token);
CREATE INDEX IF NOT EXISTS idx_refresh_token_expires_at ON refresh_token(expires_at);

-- ============================================================================
-- FILE_UPLOAD TABLE - Archivos subidos (CVs, cover letters, etc)
-- ============================================================================
CREATE TABLE IF NOT EXISTS file_upload (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(50),
    file_size INTEGER,
    file_path VARCHAR(500),
    s3_url VARCHAR(500),
    is_public BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_file_upload_user_id ON file_upload(user_id);
CREATE INDEX IF NOT EXISTS idx_file_upload_file_type ON file_upload(file_type);

-- ============================================================================
-- METRICS TABLE - Métricas de carrera y seguimiento
-- ============================================================================
CREATE TABLE IF NOT EXISTS metrics (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    metric_type VARCHAR(100) NOT NULL,
    value DECIMAL(10, 2),
    period VARCHAR(50),
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_metrics_user_id ON metrics(user_id);
CREATE INDEX IF NOT EXISTS idx_metrics_metric_type ON metrics(metric_type);
CREATE INDEX IF NOT EXISTS idx_metrics_calculated_at ON metrics(calculated_at);

-- ============================================================================
-- EVENT TABLE - Registro de eventos del usuario
-- ============================================================================
CREATE TABLE IF NOT EXISTS event (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    event_type VARCHAR(100) NOT NULL,
    event_data TEXT,
    ip_address VARCHAR(50),
    user_agent VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_event_user_id ON event(user_id);
CREATE INDEX IF NOT EXISTS idx_event_type ON event(event_type);
CREATE INDEX IF NOT EXISTS idx_event_created_at ON event(created_at);

-- ============================================================================
-- AUDIT_LOG TABLE - Registro de auditoría (admin)
-- ============================================================================
CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(100),
    entity_id INTEGER,
    changes TEXT,
    ip_address VARCHAR(50),
    user_agent VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_action ON audit_log(action);
CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON audit_log(created_at);

-- ============================================================================
-- USER_SESSION TABLE - Rastreo de sesiones activas
-- ============================================================================
CREATE TABLE IF NOT EXISTS user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(500) UNIQUE NOT NULL,
    session_hash VARCHAR(255) NOT NULL,
    device_type VARCHAR(100),
    device_os VARCHAR(100),
    browser_name VARCHAR(100),
    browser_version VARCHAR(50),
    ip_address VARCHAR(50) NOT NULL,
    user_agent VARCHAR(500),
    country VARCHAR(100),
    city VARCHAR(100),
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    ended_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    was_secure BOOLEAN DEFAULT FALSE NOT NULL,
    page_views INTEGER DEFAULT 0 NOT NULL,
    api_calls INTEGER DEFAULT 0 NOT NULL,
    requests_count INTEGER DEFAULT 0 NOT NULL,
    session_duration_seconds INTEGER,
    notes VARCHAR(500)
);

CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_is_active ON user_sessions(is_active);
CREATE INDEX IF NOT EXISTS idx_user_sessions_started_at ON user_sessions(started_at);

-- ============================================================================
-- TRIGGERS - Actualizar updated_at automáticamente
-- ============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Aplicar trigger a todas las tablas con updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_identity_updated_at BEFORE UPDATE ON identity FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_competencies_updated_at BEFORE UPDATE ON competencies FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_evidence_updated_at BEFORE UPDATE ON evidence FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_job_strategy_updated_at BEFORE UPDATE ON job_strategy FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_vacancy_updated_at BEFORE UPDATE ON vacancy FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_networking_contact_updated_at BEFORE UPDATE ON networking_contact FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_interview_updated_at BEFORE UPDATE ON interview FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_file_upload_updated_at BEFORE UPDATE ON file_upload FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- INITIAL DATA - Usuario de prueba
-- ============================================================================

-- Insertar usuario de prueba
-- Username: usuario
-- Password: password123
-- Hash generado con bcrypt (cost factor 12)
INSERT INTO users (
    username,
    email,
    password_hash,
    full_name,
    professional_title,
    is_active,
    is_verified
)
VALUES (
    'usuario',
    'usuario@example.com',
    '$2b$12$KIX7Zh3v5QXMhXY5nZj5VOZLmqP8h6u1yWJZ5sJZwLqxN5vYqJWLq',
    'Usuario Ejemplo',
    'Desarrollador Full Stack',
    TRUE,
    TRUE
)
ON CONFLICT (username) DO NOTHING;

-- ============================================================================
-- CONFIRMATION MESSAGE
-- ============================================================================
DO $$
BEGIN
    RAISE NOTICE 'Database schema initialized successfully';
    RAISE NOTICE 'Test user created: username=usuario, password=password123';
    RAISE NOTICE 'Tables created: users, identity, competencies, evidence, job_strategy, vacancy, networking_contact, interview, refresh_token, file_upload, metrics, event, audit_log, user_sessions';
END $$;
