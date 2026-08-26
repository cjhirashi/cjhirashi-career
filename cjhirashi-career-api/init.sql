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
-- CAREER DOMAIN SCHEMA (v2) - 30 tablas, validadas contra la bóveda real
-- Reemplaza el dominio de carrera anterior (identity/competencies/evidence/
-- job_strategy/vacancy/networking_contact/interview) que nunca tuvo datos.
-- Ver docs/09-DECISIONS para el ADR correspondiente.
-- ============================================================================

-- ---------------------------------------------------------------------------
-- DOMINIO 1: IDENTIDAD PROFESIONAL
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS differentiators (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    pillar_name VARCHAR(255) NOT NULL,
    pillar_description TEXT,
    strengths TEXT,
    evidence TEXT,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_differentiators_user_id ON differentiators(user_id);

CREATE TABLE IF NOT EXISTS identity (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    professional_tagline VARCHAR(255),
    bio_summary TEXT,
    unique_value_proposition TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_identity_user_id ON identity(user_id);

CREATE TABLE IF NOT EXISTS identity_reflections (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    dimension VARCHAR(50) NOT NULL CHECK (dimension IN ('passion', 'profession', 'vocation', 'mission')),
    content TEXT,
    tags TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    UNIQUE (user_id, dimension)
);
CREATE INDEX IF NOT EXISTS idx_identity_reflections_user_id ON identity_reflections(user_id);

CREATE TABLE IF NOT EXISTS competencies (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL CHECK (type IN ('technical', 'transferable', 'business')),
    category VARCHAR(100),
    level VARCHAR(50),
    years_of_experience DECIMAL(4, 2),
    practice_start_date DATE,
    context_libraries JSONB,
    depth_description TEXT,
    market_gaps TEXT,
    honesty_note TEXT,
    aligned_differentiator_ids JSONB,
    proficiency_score INTEGER,
    is_highlighted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_competencies_user_id ON competencies(user_id);
CREATE INDEX IF NOT EXISTS idx_competencies_type ON competencies(type);

CREATE TABLE IF NOT EXISTS certifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    institution VARCHAR(255),
    year INTEGER,
    description TEXT,
    syllabus TEXT,
    document_url VARCHAR(1000),
    status VARCHAR(30) DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed')),
    related_competency_id INTEGER REFERENCES competencies(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_certifications_status ON certifications(status);
CREATE INDEX IF NOT EXISTS idx_certifications_user_id ON certifications(user_id);

CREATE TABLE IF NOT EXISTS target_roles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_name VARCHAR(255) NOT NULL,
    priority_order INTEGER CHECK (priority_order BETWEEN 1 AND 3),
    salary_median INTEGER,
    salary_min INTEGER,
    salary_max INTEGER,
    years_experience_required INTEGER,
    description TEXT,
    market_active_vacancies INTEGER,
    market_validated_at DATE,
    market_sources JSONB,
    current_accessibility VARCHAR(100),
    key_requirements TEXT,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_target_roles_user_id ON target_roles(user_id);
CREATE INDEX IF NOT EXISTS idx_target_roles_priority ON target_roles(priority_order);

CREATE TABLE IF NOT EXISTS work_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    company VARCHAR(255) NOT NULL,
    role_title VARCHAR(255) NOT NULL,
    start_date DATE,
    end_date DATE,
    people_managed VARCHAR(100),
    description TEXT,
    narrative TEXT,
    key_metrics JSONB,
    learnings TEXT,
    contract_type VARCHAR(50),
    industry_sector VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_work_history_user_id ON work_history(user_id);
CREATE INDEX IF NOT EXISTS idx_work_history_start_date ON work_history(start_date);

CREATE TABLE IF NOT EXISTS achievements (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    work_history_id INTEGER REFERENCES work_history(id) ON DELETE SET NULL,
    context JSONB,
    challenge TEXT,
    solution TEXT,
    impact_metrics JSONB,
    evidence_type VARCHAR(30) CHECK (evidence_type IN ('direct_account', 'public_backed')),
    documentation_urls TEXT,
    executive_storytelling TEXT,
    demonstrated_competency_ids JSONB,
    visible_on_cv BOOLEAN DEFAULT TRUE,
    visible_in_interview BOOLEAN DEFAULT TRUE,
    visible_on_portal BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_achievements_user_id ON achievements(user_id);
CREATE INDEX IF NOT EXISTS idx_achievements_work_history_id ON achievements(work_history_id);

CREATE TABLE IF NOT EXISTS star_stories (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    duration_seconds INTEGER CHECK (duration_seconds BETWEEN 60 AND 90),
    narrative TEXT,
    key_points TEXT,
    achievement_id INTEGER REFERENCES achievements(id) ON DELETE SET NULL,
    cross_pattern VARCHAR(255),
    role_application TEXT,
    times_practiced INTEGER DEFAULT 0,
    active_in_interviews BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_star_stories_user_id ON star_stories(user_id);
CREATE INDEX IF NOT EXISTS idx_star_stories_active ON star_stories(active_in_interviews);

CREATE TABLE IF NOT EXISTS career_reviews (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    review_date DATE,
    review_type VARCHAR(50) CHECK (review_type IN ('gap_analysis', 'transition_decision', 'quarterly_review')),
    context TEXT,
    decision_or_finding TEXT,
    result_or_learning TEXT,
    action_items TEXT,
    tracking_status VARCHAR(30) DEFAULT 'active' CHECK (tracking_status IN ('active', 'completed', 'paused')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_career_reviews_user_id ON career_reviews(user_id);

CREATE TABLE IF NOT EXISTS role_gap_analysis (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    target_role_id INTEGER NOT NULL REFERENCES target_roles(id) ON DELETE CASCADE,
    gap_name VARCHAR(255) NOT NULL,
    severity VARCHAR(20) CHECK (severity IN ('critical', 'high', 'medium', 'low')),
    market_requirement TEXT,
    closing_plan TEXT,
    viability VARCHAR(30) CHECK (viability IN ('viable', 'viable_with_caveats', 'not_viable')),
    closure_status VARCHAR(30) DEFAULT 'not_started' CHECK (closure_status IN ('not_started', 'in_progress', 'completed', 'paused')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_role_gap_analysis_user_id ON role_gap_analysis(user_id);
CREATE INDEX IF NOT EXISTS idx_role_gap_analysis_role_id ON role_gap_analysis(target_role_id);

CREATE TABLE IF NOT EXISTS projects (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    category VARCHAR(50),
    industry VARCHAR(100),
    year INTEGER,
    card_summary VARCHAR(500),
    detailed_summary TEXT,
    problem TEXT,
    solution TEXT,
    architecture TEXT,
    tech_stack TEXT,
    metrics JSONB,
    approach_steps TEXT,
    results JSONB,
    github_url VARCHAR(500),
    demo_url VARCHAR(500),
    repo_structure TEXT,
    evidence_sources TEXT,
    releases JSONB,
    status VARCHAR(30) DEFAULT 'active' CHECK (status IN ('active', 'in_development', 'archived')),
    is_featured BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_projects_user_id ON projects(user_id);
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
CREATE INDEX IF NOT EXISTS idx_projects_featured ON projects(is_featured);

-- ---------------------------------------------------------------------------
-- DOMINIO 2: OPERATIVA DE BÚSQUEDA
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS fit_scoring_factors (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    factor_name VARCHAR(100) NOT NULL,
    weight_percentage INTEGER,
    scoring_guide TEXT,
    display_order INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_fit_scoring_factors_user_id ON fit_scoring_factors(user_id);

CREATE TABLE IF NOT EXISTS market_segments (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    market_type VARCHAR(20) CHECK (market_type IN ('visible', 'hidden')),
    channel_name VARCHAR(255),
    channel_type VARCHAR(50),
    strategy_text TEXT,
    applications_made INTEGER DEFAULT 0,
    responses_received INTEGER DEFAULT 0,
    interviews_achieved INTEGER DEFAULT 0,
    priority INTEGER CHECK (priority BETWEEN 1 AND 10),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_market_segments_user_id ON market_segments(user_id);

CREATE TABLE IF NOT EXISTS role_narratives (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    target_role_id INTEGER REFERENCES target_roles(id) ON DELETE SET NULL,
    title VARCHAR(255) NOT NULL,
    usage_context VARCHAR(100),
    full_narrative TEXT,
    key_points TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_role_narratives_user_id ON role_narratives(user_id);
CREATE INDEX IF NOT EXISTS idx_role_narratives_context ON role_narratives(usage_context);

CREATE TABLE IF NOT EXISTS search_plans (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    period_start DATE,
    period_end DATE,
    target_role_id INTEGER REFERENCES target_roles(id) ON DELETE SET NULL,
    weekly_targets JSONB,
    primary_channels TEXT,
    target_cvs_sent INTEGER,
    target_interviews INTEGER,
    target_offers INTEGER,
    plan_status VARCHAR(30) DEFAULT 'not_started' CHECK (plan_status IN ('not_started', 'in_progress', 'paused', 'completed', 'cancelled')),
    completion_percentage INTEGER DEFAULT 0,
    lessons_learned TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_search_plans_user_id ON search_plans(user_id);

CREATE TABLE IF NOT EXISTS networking_contacts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    role_title VARCHAR(255),
    company_or_specialty VARCHAR(255),
    linkedin_url VARCHAR(500),
    email VARCHAR(255),
    role_category VARCHAR(50) CHECK (role_category IN ('data_director', 'automation_ai_peer', 'manager_team_lead', 'specialized_recruiter', 'target_company_lead')),
    contact_status VARCHAR(30) DEFAULT 'pending' CHECK (contact_status IN ('pending', 'contacted', 'following_up', 'converted')),
    how_originated TEXT,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_networking_contacts_user_id ON networking_contacts(user_id);
CREATE INDEX IF NOT EXISTS idx_networking_contacts_category ON networking_contacts(role_category);
CREATE INDEX IF NOT EXISTS idx_networking_contacts_status ON networking_contacts(contact_status);

CREATE TABLE IF NOT EXISTS target_companies (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    company_name VARCHAR(255) NOT NULL,
    tier INTEGER,
    best_fit_role_id INTEGER REFERENCES target_roles(id) ON DELETE SET NULL,
    company_size VARCHAR(50),
    salary_estimate VARCHAR(100),
    work_modality VARCHAR(100),
    target_market VARCHAR(100),
    weak_tie_contact_id INTEGER REFERENCES networking_contacts(id) ON DELETE SET NULL,
    priority VARCHAR(10),
    status VARCHAR(30),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_target_companies_user_id ON target_companies(user_id);
CREATE INDEX IF NOT EXISTS idx_target_companies_tier ON target_companies(tier);

CREATE TABLE IF NOT EXISTS vacancies (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    order_number INTEGER,
    company VARCHAR(255) NOT NULL,
    exact_role VARCHAR(255) NOT NULL,
    vacancy_url VARCHAR(500) UNIQUE,
    source VARCHAR(50),
    found_date DATE,
    fit_percentage INTEGER CHECK (fit_percentage BETWEEN 0 AND 100),
    track_category VARCHAR(50),
    recommended_cv_version VARCHAR(100),
    analysis_notes TEXT,
    evaluation VARCHAR(30) DEFAULT 'pending_review' CHECK (evaluation IN ('apply', 'do_not_apply', 'pending_review')),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_vacancies_user_id ON vacancies(user_id);
CREATE INDEX IF NOT EXISTS idx_vacancies_fit ON vacancies(fit_percentage DESC);
CREATE INDEX IF NOT EXISTS idx_vacancies_evaluation ON vacancies(evaluation);

-- file_upload_id referencia a file_uploads (plural), creada por el modelo
-- SQLAlchemy activo (api/src/models/file_upload.py), no por este script.
-- Sin FK a nivel de init.sql por eso (no existe file_uploads en este punto
-- en un deploy nuevo) — la integridad referencial se agrega manualmente
-- después del primer arranque de api_rest, ver docs/09-DECISIONS.
CREATE TABLE IF NOT EXISTS cv_versions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    target_role_id INTEGER REFERENCES target_roles(id) ON DELETE SET NULL,
    title VARCHAR(255) NOT NULL,
    length_pages INTEGER,
    status VARCHAR(30) DEFAULT 'draft' CHECK (status IN ('draft', 'approved', 'final')),
    content TEXT,
    target_vacancy_ids JSONB,
    file_upload_id INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_cv_versions_user_id ON cv_versions(user_id);
CREATE INDEX IF NOT EXISTS idx_cv_versions_status ON cv_versions(status);

CREATE TABLE IF NOT EXISTS cover_letter_versions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    target_role_id INTEGER REFERENCES target_roles(id) ON DELETE SET NULL,
    title VARCHAR(255) NOT NULL,
    status VARCHAR(30) DEFAULT 'draft' CHECK (status IN ('draft', 'approved', 'final')),
    body_content TEXT,
    target_vacancy_id INTEGER REFERENCES vacancies(id) ON DELETE SET NULL,
    file_upload_id INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_cover_letter_versions_user_id ON cover_letter_versions(user_id);
CREATE INDEX IF NOT EXISTS idx_cover_letter_versions_status ON cover_letter_versions(status);

CREATE TABLE IF NOT EXISTS applications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    vacancy_id INTEGER NOT NULL REFERENCES vacancies(id) ON DELETE CASCADE,
    applied_at TIMESTAMP WITH TIME ZONE,
    cv_version_id INTEGER REFERENCES cv_versions(id) ON DELETE SET NULL,
    cover_letter_version_id INTEGER REFERENCES cover_letter_versions(id) ON DELETE SET NULL,
    current_status VARCHAR(30) DEFAULT 'applied' CHECK (current_status IN ('applied', 'in_process', 'offer', 'rejected', 'archived')),
    recruiter_contact_id INTEGER REFERENCES networking_contacts(id) ON DELETE SET NULL,
    final_result VARCHAR(30) CHECK (final_result IN ('offer_accepted', 'offer_rejected', 'rejected', 'negotiating')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_applications_user_id ON applications(user_id);
CREATE INDEX IF NOT EXISTS idx_applications_vacancy_id ON applications(vacancy_id);
CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(current_status);

CREATE TABLE IF NOT EXISTS application_interactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    application_id INTEGER NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    interaction_at TIMESTAMP WITH TIME ZONE,
    channel VARCHAR(50),
    content_sent TEXT,
    response_received TEXT,
    status VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_application_interactions_app_id ON application_interactions(application_id);

CREATE TABLE IF NOT EXISTS interviews (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    application_id INTEGER NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    interview_type VARCHAR(50),
    scheduled_at TIMESTAMP WITH TIME ZONE,
    interviewers TEXT,
    questions_asked TEXT,
    answers_given TEXT,
    feedback_received TEXT,
    overall_impression VARCHAR(20) CHECK (overall_impression IN ('very_positive', 'positive', 'neutral', 'negative')),
    narrative_used_id INTEGER REFERENCES role_narratives(id) ON DELETE SET NULL,
    interview_result VARCHAR(30) CHECK (interview_result IN ('pending', 'advanced', 'rejected', 'under_consideration')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_interviews_user_id ON interviews(user_id);
CREATE INDEX IF NOT EXISTS idx_interviews_application_id ON interviews(application_id);

CREATE TABLE IF NOT EXISTS contact_interactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    contact_id INTEGER NOT NULL REFERENCES networking_contacts(id) ON DELETE CASCADE,
    interaction_at TIMESTAMP WITH TIME ZONE,
    channel VARCHAR(50),
    content_sent TEXT,
    response_received TEXT,
    status VARCHAR(50),
    generated_opportunity BOOLEAN DEFAULT FALSE,
    related_vacancy_id INTEGER REFERENCES vacancies(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_contact_interactions_contact_id ON contact_interactions(contact_id);

CREATE TABLE IF NOT EXISTS networking_activities (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category VARCHAR(30) CHECK (category IN ('give_value_70', 'share_learning_20', 'talk_about_you_10')),
    activity_type VARCHAR(255) NOT NULL,
    concrete_action TEXT,
    example TEXT,
    frequency_description VARCHAR(100),
    times_completed INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_networking_activities_user_id ON networking_activities(user_id);
CREATE INDEX IF NOT EXISTS idx_networking_activities_category ON networking_activities(category);

-- ---------------------------------------------------------------------------
-- DOMINIO 3: PRESENCIA DIGITAL
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS digital_platforms (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    platform_name VARCHAR(50) CHECK (platform_name IN ('linkedin', 'github', 'kaggle', 'portfolio_web', 'medium', 'twitter', 'other')),
    profile_url VARCHAR(500),
    profile_status VARCHAR(30),
    platform_strategy TEXT,
    followers_count INTEGER,
    is_active_in_search BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_digital_platforms_user_id ON digital_platforms(user_id);

CREATE TABLE IF NOT EXISTS content_pieces (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    slug VARCHAR(255),
    excerpt VARCHAR(500),
    body_content TEXT,
    content_type VARCHAR(50),
    thematic_pillar VARCHAR(100),
    tags TEXT,
    status VARCHAR(30) DEFAULT 'draft' CHECK (status IN ('draft', 'scheduled', 'published')),
    reading_minutes INTEGER,
    featured_on_home BOOLEAN DEFAULT FALSE,
    scheduled_publish_at TIMESTAMP WITH TIME ZONE,
    related_project_id INTEGER REFERENCES projects(id) ON DELETE SET NULL,
    related_achievement_id INTEGER REFERENCES achievements(id) ON DELETE SET NULL,
    related_competency_id INTEGER REFERENCES competencies(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_content_pieces_user_id ON content_pieces(user_id);
CREATE INDEX IF NOT EXISTS idx_content_pieces_status ON content_pieces(status);
CREATE UNIQUE INDEX IF NOT EXISTS idx_content_pieces_slug ON content_pieces(user_id, slug);

CREATE TABLE IF NOT EXISTS publications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content_piece_id INTEGER NOT NULL REFERENCES content_pieces(id) ON DELETE CASCADE,
    platform_id INTEGER NOT NULL REFERENCES digital_platforms(id) ON DELETE CASCADE,
    published_title VARCHAR(255),
    publication_url VARCHAR(500),
    published_at TIMESTAMP WITH TIME ZONE,
    full_content TEXT,
    char_length INTEGER,
    hashtags_used TEXT,
    views INTEGER,
    likes_reactions INTEGER,
    comments INTEGER,
    shares INTEGER,
    content_status VARCHAR(30) DEFAULT 'draft' CHECK (content_status IN ('draft', 'scheduled', 'published')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_publications_content_piece_id ON publications(content_piece_id);
CREATE INDEX IF NOT EXISTS idx_publications_platform_id ON publications(platform_id);

-- ---------------------------------------------------------------------------
-- DOMINIO 4: SOPORTE
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS tags (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tag_name VARCHAR(100) NOT NULL,
    entity_type VARCHAR(100),
    color_hex VARCHAR(7),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    UNIQUE (user_id, tag_name)
);
CREATE INDEX IF NOT EXISTS idx_tags_user_id ON tags(user_id);

-- ============================================================================
-- NOTA: refresh_tokens, file_uploads, events, audit_logs
-- ============================================================================
-- Estas 4 tablas NO se declaran aquí. Sus modelos SQLAlchemy activos
-- (api/src/models/refresh_token.py, file_upload.py, event.py, audit_log.py)
-- usan __tablename__ en plural y se crean vía Base.metadata.create_all()
-- en cada arranque de api_rest (ver api/src/database.py:init_db()).
-- Antes vivían aquí duplicadas en singular (refresh_token, file_upload,
-- event, audit_log) sin que el código real las usara jamás — se eliminaron
-- por confundir el schema real con tablas huérfanas. Si algún día se migra
-- todo a init.sql como fuente única, hacerlo para las 4 a la vez.

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
CREATE TRIGGER update_file_upload_updated_at BEFORE UPDATE ON file_upload FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Dominio de carrera (v2)
CREATE TRIGGER update_differentiators_updated_at BEFORE UPDATE ON differentiators FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_identity_updated_at BEFORE UPDATE ON identity FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_identity_reflections_updated_at BEFORE UPDATE ON identity_reflections FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_competencies_updated_at BEFORE UPDATE ON competencies FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_target_roles_updated_at BEFORE UPDATE ON target_roles FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_role_narratives_updated_at BEFORE UPDATE ON role_narratives FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_search_plans_updated_at BEFORE UPDATE ON search_plans FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_networking_contacts_updated_at BEFORE UPDATE ON networking_contacts FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_target_companies_updated_at BEFORE UPDATE ON target_companies FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_cv_versions_updated_at BEFORE UPDATE ON cv_versions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_cover_letter_versions_updated_at BEFORE UPDATE ON cover_letter_versions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_certifications_updated_at BEFORE UPDATE ON certifications FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_work_history_updated_at BEFORE UPDATE ON work_history FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_achievements_updated_at BEFORE UPDATE ON achievements FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_star_stories_updated_at BEFORE UPDATE ON star_stories FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_career_reviews_updated_at BEFORE UPDATE ON career_reviews FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_role_gap_analysis_updated_at BEFORE UPDATE ON role_gap_analysis FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_fit_scoring_factors_updated_at BEFORE UPDATE ON fit_scoring_factors FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_market_segments_updated_at BEFORE UPDATE ON market_segments FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_vacancies_updated_at BEFORE UPDATE ON vacancies FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_applications_updated_at BEFORE UPDATE ON applications FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_application_interactions_updated_at BEFORE UPDATE ON application_interactions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_interviews_updated_at BEFORE UPDATE ON interviews FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_contact_interactions_updated_at BEFORE UPDATE ON contact_interactions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_networking_activities_updated_at BEFORE UPDATE ON networking_activities FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_digital_platforms_updated_at BEFORE UPDATE ON digital_platforms FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_content_pieces_updated_at BEFORE UPDATE ON content_pieces FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_publications_updated_at BEFORE UPDATE ON publications FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_tags_updated_at BEFORE UPDATE ON tags FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- INITIAL DATA - Usuario administrador
-- ============================================================================

-- Insertar usuario administrador (Carlos Jiménez Hirashi)
-- Username: cjhirashi
-- Password: admin (cambiar tras el primer login vía /change-password)
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
    'cjhirashi',
    'cjhirashi@gmail.com',
    '$2b$12$QXklZt7u/l18bzPqC/vRQO2H5pJFsVaiTFQot7j6QsLi3n/cJBhD.',
    'Carlos Jiménez Hirashi',
    'Arquitecto de Soluciones',
    TRUE,
    TRUE
)
ON CONFLICT (username) DO NOTHING;

-- ============================================================================
-- VISTAS - Métricas de búsqueda calculadas (nunca capturadas a mano)
-- ============================================================================

CREATE OR REPLACE VIEW search_metrics_view AS
SELECT
    a.user_id,
    date_trunc('week', a.applied_at)::date AS week_start,
    COUNT(*) AS applications_sent,
    COUNT(*) FILTER (WHERE a.current_status <> 'applied') AS responses_received,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE a.current_status <> 'applied') / NULLIF(COUNT(*), 0),
        2
    ) AS response_rate_percentage,
    COUNT(DISTINCT i.id) AS interviews_scheduled,
    COUNT(*) FILTER (WHERE a.current_status = 'offer') AS offers,
    COUNT(*) FILTER (WHERE a.current_status = 'rejected') AS rejections
FROM applications a
LEFT JOIN interviews i ON i.application_id = a.id
GROUP BY a.user_id, date_trunc('week', a.applied_at);

-- ============================================================================
-- CONFIRMATION MESSAGE
-- ============================================================================
DO $$
BEGIN
    RAISE NOTICE 'Database schema initialized successfully';
    RAISE NOTICE 'Admin user created: username=cjhirashi';
    RAISE NOTICE 'Career domain (v2): differentiators, identity, identity_reflections, competencies, certifications, target_roles, work_history, achievements, star_stories, career_reviews, role_gap_analysis, projects, fit_scoring_factors, market_segments, role_narratives, search_plans, networking_contacts, target_companies, vacancies, cv_versions, cover_letter_versions, applications, application_interactions, interviews, contact_interactions, networking_activities, digital_platforms, content_pieces, publications, tags';
    RAISE NOTICE 'System tables: users, refresh_token, file_upload, metrics, event, audit_log, user_sessions';
    RAISE NOTICE 'Views: search_metrics_view';
END $$;
