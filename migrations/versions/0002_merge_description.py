"""fold additional_info and notes into description

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-27
"""
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

SEARCH = """to_tsvector('simple',
    id || ' ' || title || ' ' ||
    coalesce(label, '') || ' ' || coalesce(year_text, '') || ' ' ||
    coalesce(country, '') || ' ' || coalesce(catalog_no, '') || ' ' ||
    coalesce(catalog_norm, '') || ' ' || coalesce(barcode, '') || ' ' ||
    coalesce(matrix, '') || ' ' || coalesce(made_in, '') || ' ' ||
    coalesce(description, '')"""


def upgrade():
    op.execute(f"""
    UPDATE item SET description = nullif(concat_ws('; ', description, additional_info,
                                                   nullif(immutable_array_to_string(notes, '; '), '')), '')
    WHERE additional_info IS NOT NULL OR notes <> '{{}}';
    ALTER TABLE item DROP COLUMN search, DROP COLUMN additional_info, DROP COLUMN notes;
    ALTER TABLE item ADD COLUMN search tsvector GENERATED ALWAYS AS ({SEARCH})) STORED;
    CREATE INDEX item_search_idx ON item USING gin (search);
    """)


def downgrade():
    op.execute(f"""
    ALTER TABLE item DROP COLUMN search;
    ALTER TABLE item ADD COLUMN additional_info text, ADD COLUMN notes text[] NOT NULL DEFAULT '{{}}';
    ALTER TABLE item ADD COLUMN search tsvector GENERATED ALWAYS AS ({SEARCH} || ' ' ||
        coalesce(additional_info, '') || ' ' || immutable_array_to_string(notes, ' '))) STORED;
    CREATE INDEX item_search_idx ON item USING gin (search);
    """)
