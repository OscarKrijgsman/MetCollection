"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-09-25
"""
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
    CREATE EXTENSION IF NOT EXISTS pg_trgm;

    -- array_to_string is not IMMUTABLE, which a generated column requires.
    CREATE FUNCTION immutable_array_to_string(text[], text) RETURNS text
        LANGUAGE sql IMMUTABLE PARALLEL SAFE AS $$ SELECT array_to_string($1, $2) $$;

    CREATE TABLE era (
        id          serial PRIMARY KEY,
        name        text NOT NULL UNIQUE,
        slug        text NOT NULL UNIQUE,
        sort_order  int NOT NULL,
        is_special  boolean NOT NULL DEFAULT false
    );

    CREATE TABLE format (
        id    serial PRIMARY KEY,
        code  text NOT NULL UNIQUE,
        name  text NOT NULL
    );

    CREATE TABLE import_run (
        id           serial PRIMARY KEY,
        file_name    text NOT NULL,
        file_sha256  text NOT NULL,
        started_at   timestamptz NOT NULL DEFAULT now(),
        finished_at  timestamptz,
        added        int,
        updated      int,
        unchanged    int,
        missing      int,
        restored     int,
        warnings     jsonb NOT NULL DEFAULT '[]',
        changes      jsonb NOT NULL DEFAULT '{}'
    );

    CREATE TABLE item (
        id               text PRIMARY KEY,
        era_id           int NOT NULL REFERENCES era(id),
        format_id        int NOT NULL REFERENCES format(id),
        source_sheet     text NOT NULL,
        source_row       int NOT NULL,
        title            text NOT NULL,
        label            text,
        year             int,
        year_text        text,
        year_uncertain   boolean NOT NULL DEFAULT false,
        country          text,
        catalog_no       text,
        catalog_norm     text,
        barcode          text,
        matrix           text,
        made_in          text,
        description      text,
        additional_info  text,
        notes            text[] NOT NULL DEFAULT '{}',
        quantity         int NOT NULL DEFAULT 1,
        extra            jsonb NOT NULL DEFAULT '{}',
        content_hash     text NOT NULL,
        status           text NOT NULL DEFAULT 'active'
                         CHECK (status IN ('active', 'missing_from_excel')),
        search           tsvector GENERATED ALWAYS AS (to_tsvector('simple',
                             id || ' ' || title || ' ' ||
                             coalesce(label, '') || ' ' || coalesce(year_text, '') || ' ' ||
                             coalesce(country, '') || ' ' || coalesce(catalog_no, '') || ' ' ||
                             coalesce(catalog_norm, '') || ' ' || coalesce(barcode, '') || ' ' ||
                             coalesce(matrix, '') || ' ' || coalesce(made_in, '') || ' ' ||
                             coalesce(description, '') || ' ' || coalesce(additional_info, '') || ' ' ||
                             immutable_array_to_string(notes, ' '))) STORED,
        first_seen_import_id  int REFERENCES import_run(id),
        last_seen_import_id   int REFERENCES import_run(id),
        created_at       timestamptz NOT NULL DEFAULT now(),
        updated_at       timestamptz NOT NULL DEFAULT now()
    );

    CREATE INDEX item_search_idx ON item USING gin (search);
    CREATE INDEX item_catalog_norm_trgm ON item USING gin (catalog_norm gin_trgm_ops);
    CREATE INDEX item_barcode_trgm ON item USING gin (barcode gin_trgm_ops);
    CREATE INDEX item_matrix_trgm ON item USING gin (matrix gin_trgm_ops);
    CREATE INDEX item_title_trgm ON item USING gin (title gin_trgm_ops);
    CREATE INDEX item_era_idx ON item (era_id);
    CREATE INDEX item_format_idx ON item (format_id);
    CREATE INDEX item_year_idx ON item (year);
    CREATE INDEX item_country_idx ON item (country);
    CREATE INDEX item_label_idx ON item (label);

    -- Images reference the Excel ID. RESTRICT: an item with images is never removed silently.
    CREATE TABLE item_image (
        id          serial PRIMARY KEY,
        item_id     text NOT NULL REFERENCES item(id) ON DELETE RESTRICT,
        file_path   text NOT NULL,
        thumb_path  text,
        caption     text,
        sort_order  int NOT NULL DEFAULT 0,
        width       int,
        height      int,
        created_at  timestamptz NOT NULL DEFAULT now()
    );
    CREATE INDEX item_image_item_idx ON item_image (item_id, sort_order);

    CREATE TABLE concert (
        id         serial PRIMARY KEY,
        date       date NOT NULL,
        place      text,
        venue      text,
        country    text,
        with_kees  boolean NOT NULL DEFAULT false,
        with_whom  text
    );
    """)


def downgrade():
    op.execute("""
    DROP TABLE concert, item_image, item, import_run, format, era;
    DROP FUNCTION immutable_array_to_string(text[], text);
    """)
