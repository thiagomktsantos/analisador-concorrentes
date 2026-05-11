-- ============================================================
-- CI Dashboard — Supabase Setup
-- Execute este script no SQL Editor do seu projeto Supabase
-- ============================================================

-- 1. Tabela principal de dados por usuário
CREATE TABLE IF NOT EXISTS ci_dados (
    id            UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id       UUID NOT NULL UNIQUE REFERENCES auth.users(id) ON DELETE CASCADE,
    minha_empresa JSONB DEFAULT '{}'::jsonb,
    concorrentes  JSONB DEFAULT '[]'::jsonb,
    metricas_redes JSONB DEFAULT '{}'::jsonb,
    created_at    TIMESTAMPTZ DEFAULT NOW(),
    updated_at    TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Índice para lookup rápido por user_id
CREATE INDEX IF NOT EXISTS idx_ci_dados_user_id ON ci_dados(user_id);

-- 3. Trigger para atualizar updated_at automaticamente
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS set_updated_at ON ci_dados;
CREATE TRIGGER set_updated_at
    BEFORE UPDATE ON ci_dados
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- 4. Row Level Security (RLS) — cada usuário só acessa seus próprios dados
ALTER TABLE ci_dados ENABLE ROW LEVEL SECURITY;

-- Política: usuário autenticado pode ler seus próprios dados
CREATE POLICY "select_own_data" ON ci_dados
    FOR SELECT USING (auth.uid() = user_id);

-- Política: usuário autenticado pode inserir seus próprios dados
CREATE POLICY "insert_own_data" ON ci_dados
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Política: usuário autenticado pode atualizar seus próprios dados
CREATE POLICY "update_own_data" ON ci_dados
    FOR UPDATE USING (auth.uid() = user_id);

-- Política: usuário autenticado pode deletar seus próprios dados
CREATE POLICY "delete_own_data" ON ci_dados
    FOR DELETE USING (auth.uid() = user_id);

-- ============================================================
-- PRONTO! Configure os secrets do Streamlit:
--
-- [secrets]
-- SUPABASE_URL  = "https://<seu-projeto>.supabase.co"
-- SUPABASE_KEY  = "<sua-anon-key>"
-- GEMINI_API_KEY = "<sua-chave-gemini>"
-- ============================================================
