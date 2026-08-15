-- Script de inicialización de base de datos PostgreSQL
-- Crea las tablas y usuario inicial de prueba

-- Crear tabla de usuarios
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Crear índices para usuarios
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Crear tabla de documentos
CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    title VARCHAR(255),
    data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Crear índices para documentos
CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(user_id);
CREATE INDEX IF NOT EXISTS idx_documents_type ON documents(type);

-- Crear trigger para actualizar updated_at automáticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_documents_updated_at
    BEFORE UPDATE ON documents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Insertar usuario de prueba
-- Username: usuario
-- Password: password123
-- Hash generado con bcrypt (cost factor 12)
INSERT INTO users (username, email, password_hash)
VALUES (
    'usuario',
    'usuario@example.com',
    '$2b$12$KIX7Zh3v5QXMhXY5nZj5VOZLmqP8h6u1yWJZ5sJZwLqxN5vYqJWLq'
)
ON CONFLICT (username) DO NOTHING;

-- Insertar documentos de ejemplo para el usuario de prueba
INSERT INTO documents (user_id, type, title, data)
SELECT
    u.id,
    'cv',
    'CV Ejemplo',
    '{"nombre": "Usuario Ejemplo", "email": "usuario@example.com", "telefono": "+34 600 000 000", "titulo_profesional": "Desarrollador Full Stack", "resumen": "Profesional con experiencia en desarrollo web", "experiencia": [{"empresa": "Tech Corp", "puesto": "Developer", "años": "2020-2024", "descripcion": "Desarrollo de aplicaciones web"}], "educacion": [{"institucion": "Universidad", "titulo": "Ingeniería Informática", "años": "2016-2020"}], "habilidades": ["Python", "JavaScript", "FastAPI", "React"]}'::jsonb
FROM users u
WHERE u.username = 'usuario'
ON CONFLICT DO NOTHING;

INSERT INTO documents (user_id, type, title, data)
SELECT
    u.id,
    'cover_letter',
    'Carta de Presentación Ejemplo',
    '{"nombre": "Usuario Ejemplo", "email": "usuario@example.com", "empresa": "Tech Corp", "puesto": "Senior Developer", "fecha": "2024-01-15", "contenido": "Estimado equipo de reclutamiento, me dirijo a ustedes para expresar mi interés en la posición de Senior Developer..."}'::jsonb
FROM users u
WHERE u.username = 'usuario'
ON CONFLICT DO NOTHING;

-- Mensaje de confirmación
DO $$
BEGIN
    RAISE NOTICE 'Database initialized successfully';
    RAISE NOTICE 'Test user created: username=usuario, password=password123';
END $$;
