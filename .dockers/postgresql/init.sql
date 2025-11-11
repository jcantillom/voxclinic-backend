CREATE
EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE
EXTENSION IF NOT EXISTS pgcrypto;
CREATE
EXTENSION IF NOT EXISTS citext;

BEGIN;

-- ========= 0) Multi-tenant & seguridad =========
CREATE TABLE tenant
(
    id         uuid PRIMARY KEY     DEFAULT uuid_generate_v4(),
    code       text UNIQUE NOT NULL,
    name       text        NOT NULL,
    meta       jsonb       NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    deleted_at timestamptz
);

CREATE TABLE user_account
(
    id         uuid PRIMARY KEY     DEFAULT uuid_generate_v4(),
    tenant_id  uuid        NOT NULL REFERENCES tenant (id),
    email      citext      NOT NULL,
    full_name  text        NOT NULL,
    is_active  boolean     NOT NULL DEFAULT true,
    meta       jsonb       NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    deleted_at timestamptz,
    UNIQUE (tenant_id, email)
);
CREATE INDEX idx_user_account_tenant ON user_account (tenant_id);

CREATE TABLE role
(
    id          uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id   uuid  NOT NULL REFERENCES tenant (id),
    code        text  NOT NULL,
    name        text  NOT NULL,
    permissions jsonb NOT NULL   DEFAULT '[]'::jsonb,
    UNIQUE (tenant_id, code)
);
CREATE INDEX idx_role_tenant ON role (tenant_id);

CREATE TABLE user_role
(
    user_id uuid NOT NULL REFERENCES user_account (id),
    role_id uuid NOT NULL REFERENCES role (id),
    PRIMARY KEY (user_id, role_id)
);

CREATE TABLE provider
(
    id          uuid PRIMARY KEY     DEFAULT uuid_generate_v4(),
    tenant_id   uuid        NOT NULL REFERENCES tenant (id),
    npi         text, -- identificador profesional (opcional/local)
    full_name   text        NOT NULL,
    specialty   text,
    credentials text,
    meta        jsonb       NOT NULL DEFAULT '{}'::jsonb,
    created_at  timestamptz NOT NULL DEFAULT now(),
    updated_at  timestamptz NOT NULL DEFAULT now(),
    deleted_at  timestamptz,
    UNIQUE (tenant_id, npi)
);

CREATE TABLE facility
(
    id         uuid PRIMARY KEY     DEFAULT uuid_generate_v4(),
    tenant_id  uuid        NOT NULL REFERENCES tenant (id),
    code       text        NOT NULL,
    name       text        NOT NULL,
    address    text,
    meta       jsonb       NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    deleted_at timestamptz,
    UNIQUE (tenant_id, code)
);

CREATE TABLE department
(
    id          uuid PRIMARY KEY     DEFAULT uuid_generate_v4(),
    tenant_id   uuid        NOT NULL REFERENCES tenant (id),
    facility_id uuid REFERENCES facility (id),
    code        text        NOT NULL,
    name        text        NOT NULL,
    meta        jsonb       NOT NULL DEFAULT '{}'::jsonb,
    created_at  timestamptz NOT NULL DEFAULT now(),
    updated_at  timestamptz NOT NULL DEFAULT now(),
    deleted_at  timestamptz,
    UNIQUE (tenant_id, code)
);

CREATE TABLE audit_log
(
    id            bigserial PRIMARY KEY,
    tenant_id     uuid        NOT NULL REFERENCES tenant (id),
    actor_user_id uuid REFERENCES user_account (id),
    action        text        NOT NULL, -- e.g. "REPORT_SIGN", "DICTATION_UPLOAD"
    entity_type   text        NOT NULL, -- e.g. "report", "patient"
    entity_id     uuid,
    before_state  jsonb,
    after_state   jsonb,
    ip            inet,
    created_at    timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_audit_tenant_time ON audit_log (tenant_id, created_at DESC);

-- ========= 1) Pacientes & atención =========
CREATE TABLE patient
(
    id          uuid PRIMARY KEY     DEFAULT uuid_generate_v4(),
    tenant_id   uuid        NOT NULL REFERENCES tenant (id),
    mrn         text,                                     -- medical record number
    first_name  text        NOT NULL,
    last_name   text        NOT NULL,
    dob         date,
    sex         text,                                     -- M/F/X/Unknown (o catálogo)
    phone       text,
    email       citext,
    identifiers jsonb       NOT NULL DEFAULT '[]'::jsonb, -- otros IDs
    address     jsonb,                                    -- calle/ciudad/etc.
    meta        jsonb       NOT NULL DEFAULT '{}'::jsonb,
    created_at  timestamptz NOT NULL DEFAULT now(),
    updated_at  timestamptz NOT NULL DEFAULT now(),
    deleted_at  timestamptz,
    UNIQUE (tenant_id, mrn)
);
CREATE INDEX idx_patient_name ON patient (tenant_id, last_name, first_name);

CREATE TABLE encounter
(
    id            uuid PRIMARY KEY     DEFAULT uuid_generate_v4(),
    tenant_id     uuid        NOT NULL REFERENCES tenant (id),
    patient_id    uuid        NOT NULL REFERENCES patient (id),
    facility_id   uuid REFERENCES facility (id),
    department_id uuid REFERENCES department (id),
    started_at    timestamptz,
    ended_at      timestamptz,
    type          text, -- ambulatorio, emergencia, etc.
    meta          jsonb       NOT NULL DEFAULT '{}'::jsonb,
    created_at    timestamptz NOT NULL DEFAULT now(),
    updated_at    timestamptz NOT NULL DEFAULT now(),
    deleted_at    timestamptz
);
CREATE INDEX idx_encounter_patient ON encounter (tenant_id, patient_id, started_at DESC);

CREATE TABLE "order"
(
    id                   uuid PRIMARY KEY     DEFAULT uuid_generate_v4(),
    tenant_id            uuid        NOT NULL REFERENCES tenant (id),
    encounter_id         uuid REFERENCES encounter (id),
    patient_id           uuid        NOT NULL REFERENCES patient (id),
    ordering_provider_id uuid REFERENCES provider (id),
    code                 text        NOT NULL,                  -- LOINC/SNOMED/local
    description          text        NOT NULL,
    priority             text,
    status               text        NOT NULL DEFAULT 'PLACED', -- PLACED|SCHEDULED|IN_PROGRESS|COMPLETED|CANCELLED
    meta                 jsonb       NOT NULL DEFAULT '{}'::jsonb,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now(),
    deleted_at           timestamptz
);
CREATE INDEX idx_order_patient ON "order" (tenant_id, patient_id, created_at DESC);

CREATE TABLE study
(
    id           uuid PRIMARY KEY     DEFAULT uuid_generate_v4(),
    tenant_id    uuid        NOT NULL REFERENCES tenant (id),
    order_id     uuid REFERENCES "order" (id),
    accession_no text,                                   -- clave radiología
    modality     text,                                   -- CT/MR/CR/US/etc.
    performed_at timestamptz,
    meta         jsonb       NOT NULL DEFAULT '{}'::jsonb,
    status       text        NOT NULL DEFAULT 'PENDING', -- PENDING|READING|REPORTED|AMENDED
    created_at   timestamptz NOT NULL DEFAULT now(),
    updated_at   timestamptz NOT NULL DEFAULT now(),
    deleted_at   timestamptz,
    UNIQUE (tenant_id, accession_no)
);
CREATE INDEX idx_study_accession ON study (tenant_id, accession_no);

-- ========= 2) Plantillas, formularios, informes =========
CREATE TABLE template
(
    id          uuid PRIMARY KEY     DEFAULT uuid_generate_v4(),
    tenant_id   uuid        NOT NULL REFERENCES tenant (id),
    code        text        NOT NULL,
    name        text        NOT NULL,
    scope       text        NOT NULL, -- 'RAD_REPORT' | 'CLINICAL_FORM'
    schema_json jsonb       NOT NULL, -- definición completa (secciones, campos)
    is_active   boolean     NOT NULL DEFAULT true,
    version     integer     NOT NULL DEFAULT 1,
    created_at  timestamptz NOT NULL DEFAULT now(),
    updated_at  timestamptz NOT NULL DEFAULT now(),
    deleted_at  timestamptz,
    UNIQUE (tenant_id, code, version)
);

-- (Opcional si prefieres tablas normalizadas para secciones/campos)
CREATE TABLE template_field
(
    id            uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id     uuid  NOT NULL REFERENCES tenant (id),
    template_id   uuid  NOT NULL REFERENCES template (id),
    path          text  NOT NULL,                       -- p.ej. "demographics.age"
    label         text  NOT NULL,
    data_type     text  NOT NULL,                       -- string, number, date, enum, boolean, text
    constraints   jsonb NOT NULL   DEFAULT '{}'::jsonb,
    mapping_hints jsonb NOT NULL   DEFAULT '{}'::jsonb, -- pistas para NLP (sinónimos, regex)
    UNIQUE (template_id, path)
);

CREATE TABLE report
(
    id              uuid PRIMARY KEY     DEFAULT uuid_generate_v4(),
    tenant_id       uuid        NOT NULL REFERENCES tenant (id),
    study_id        uuid REFERENCES study (id),
    template_id     uuid REFERENCES template (id),
    status          text        NOT NULL DEFAULT 'DRAFT', -- DRAFT|FINAL|AMENDED
    current_version integer     NOT NULL DEFAULT 1,
    signed_by_id    uuid REFERENCES provider (id),
    signed_at       timestamptz,
    meta            jsonb       NOT NULL DEFAULT '{}'::jsonb,
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now(),
    deleted_at      timestamptz
);
CREATE INDEX idx_report_study ON report (tenant_id, study_id);

CREATE TABLE report_version
(
    id             uuid PRIMARY KEY     DEFAULT uuid_generate_v4(),
    report_id      uuid        NOT NULL REFERENCES report (id),
    version_number integer     NOT NULL,
    content_json   jsonb       NOT NULL, -- campos estructurados + bloques free-text
    rendered_text  text,                 -- texto final plano si lo generas
    created_by_id  uuid REFERENCES user_account (id),
    created_at     timestamptz NOT NULL DEFAULT now(),
    UNIQUE (report_id, version_number)
);

CREATE TABLE form_submission
(
    id             uuid PRIMARY KEY     DEFAULT uuid_generate_v4(),
    tenant_id      uuid        NOT NULL REFERENCES tenant (id),
    template_id    uuid REFERENCES template (id),
    context_entity text        NOT NULL, -- 'encounter' | 'patient' | etc.
    context_id     uuid,
    payload        jsonb       NOT NULL, -- valores crudos de formulario
    created_by_id  uuid REFERENCES user_account (id),
    created_at     timestamptz NOT NULL DEFAULT now()
);

-- ========= 3) Dictado/ASR/NLP =========
CREATE TABLE audio_upload
(
    id             uuid PRIMARY KEY     DEFAULT uuid_generate_v4(),
    tenant_id      uuid        NOT NULL REFERENCES tenant (id),
    owner_user_id  uuid REFERENCES user_account (id),
    patient_id     uuid REFERENCES patient (id),
    study_id       uuid REFERENCES study (id),
    storage_uri    text        NOT NULL, -- s3://... o ruta
    content_type   text        NOT NULL, -- audio/wav; audio/mpeg...
    duration_sec   numeric(10, 2),
    sample_rate_hz integer,
    meta           jsonb       NOT NULL DEFAULT '{}'::jsonb,
    created_at     timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_audio_study ON audio_upload (tenant_id, study_id, created_at DESC);

CREATE TABLE transcription
(
    id         uuid PRIMARY KEY     DEFAULT uuid_generate_v4(),
    tenant_id  uuid        NOT NULL REFERENCES tenant (id),
    audio_id   uuid        NOT NULL REFERENCES audio_upload (id),
    engine     text        NOT NULL, -- whiperX, GCP, AWS Transcribe, etc.
    language   text        NOT NULL, -- es-ES, es-CO, en-US...
    text_raw   text        NOT NULL,
    text_norm  text,                 -- normalizado/puntuado
    confidence numeric(5, 4),
    meta       jsonb       NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_trans_audio ON transcription (audio_id);

CREATE TABLE extraction_session
(
    id               uuid PRIMARY KEY     DEFAULT uuid_generate_v4(),
    tenant_id        uuid        NOT NULL REFERENCES tenant (id),
    audio_id         uuid REFERENCES audio_upload (id),
    transcription_id uuid REFERENCES transcription (id),
    template_id      uuid REFERENCES template (id),
    status           text        NOT NULL DEFAULT 'PENDING', -- PENDING|RUNNING|DONE|FAILED
    result_json      jsonb,                                  -- valores de campos extraídos
    errors           jsonb,
    created_at       timestamptz NOT NULL DEFAULT now(),
    updated_at       timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE nlp_entity
(
    id            uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    extraction_id uuid  NOT NULL REFERENCES extraction_session (id),
    label         text  NOT NULL, -- PERSON, AGE, WEIGHT, SYMPTOM, DX, etc.
    value         text  NOT NULL,
    start_char    int,
    end_char      int,
    confidence    numeric(5, 4),
    meta          jsonb NOT NULL   DEFAULT '{}'::jsonb
);
CREATE INDEX idx_nlp_extraction ON nlp_entity (extraction_id);

CREATE TABLE nlp_field_mapping
(
    id                uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id         uuid  NOT NULL REFERENCES tenant (id),
    template_field_id uuid  NOT NULL REFERENCES template_field (id),
    entity_label      text  NOT NULL,                      -- cómo mapear label->campo
    priority          int   NOT NULL   DEFAULT 100,
    rules             jsonb NOT NULL   DEFAULT '{}'::jsonb -- regex, umbrales, normalizadores
);

-- ========= 4) Integración / mensajería =========
CREATE TABLE outbox_event
(
    id             bigserial PRIMARY KEY,
    tenant_id      uuid        NOT NULL REFERENCES tenant (id),
    aggregate_type text        NOT NULL, -- 'report', 'order', etc.
    aggregate_id   uuid        NOT NULL,
    event_type     text        NOT NULL, -- 'REPORT_FINALIZED', etc.
    payload        jsonb       NOT NULL,
    published      boolean     NOT NULL DEFAULT false,
    created_at     timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_outbox_pub ON outbox_event (tenant_id, published, created_at);

CREATE TABLE inbound_message
(
    id           bigserial PRIMARY KEY,
    tenant_id    uuid        NOT NULL REFERENCES tenant (id),
    source       text        NOT NULL,                    -- "HL7", "FHIR", "HCIS"
    content_type text        NOT NULL,                    -- 'application/hl7-v2', 'application/fhir+json'
    payload      text        NOT NULL,
    status       text        NOT NULL DEFAULT 'RECEIVED', -- RECEIVED|PROCESSED|FAILED
    errors       jsonb,
    created_at   timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE attachment
(
    id           uuid PRIMARY KEY     DEFAULT uuid_generate_v4(),
    tenant_id    uuid        NOT NULL REFERENCES tenant (id),
    entity_type  text        NOT NULL, -- 'report'|'study'|'patient'
    entity_id    uuid        NOT NULL,
    storage_uri  text        NOT NULL,
    content_type text,
    meta         jsonb       NOT NULL DEFAULT '{}'::jsonb,
    created_at   timestamptz NOT NULL DEFAULT now()
);

-- índices GIN (opcionales, buenos para JSONB)
CREATE INDEX IF NOT EXISTS idx_template_schema_json_gin ON template USING GIN (schema_json);
CREATE INDEX IF NOT EXISTS idx_report_version_content_gin ON report_version USING GIN (content_json);
CREATE INDEX IF NOT EXISTS idx_form_submission_payload_gin ON form_submission USING GIN (payload);
CREATE INDEX IF NOT EXISTS idx_outbox_payload_gin ON outbox_event USING GIN (payload);

COMMIT;
