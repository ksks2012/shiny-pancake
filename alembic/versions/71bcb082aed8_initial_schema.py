"""Initial schema

Revision ID: 71bcb082aed8
Revises: 
Create Date: 2025-05-20 15:56:15.356516

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '71bcb082aed8'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    """Upgrade schema."""
    # Update videos table
    with op.batch_alter_table('videos') as batch_op:
        batch_op.alter_column('title', type_=sa.String(), existing_nullable=False)
        batch_op.alter_column('type', type_=sa.String(), existing_nullable=False)
        batch_op.alter_column('date', type_=sa.String(), existing_nullable=True)
        batch_op.alter_column('status', type_=sa.String(), existing_nullable=True)
        batch_op.alter_column('description', type_=sa.Text(), existing_nullable=True)
        batch_op.alter_column('local_path', type_=sa.Text(), existing_nullable=True)

    # Update skills table (drop icon_url, update types)
    with op.batch_alter_table('skills') as batch_op:
        batch_op.alter_column('id', type_=sa.Integer(), nullable=False, existing_autoincrement=True)
        batch_op.alter_column('name', type_=sa.String(), existing_nullable=False)
        batch_op.drop_column('icon_url')

    # Update items table
    with op.batch_alter_table('items') as batch_op:
        batch_op.alter_column('id', type_=sa.Integer(), nullable=False, existing_autoincrement=True)
        batch_op.alter_column('name', type_=sa.String(), existing_nullable=False)
        batch_op.alter_column('size', type_=sa.String(), nullable=True)

    # Update video_skills table
    with op.batch_alter_table('video_skills') as batch_op:
        batch_op.alter_column('video_id', type_=sa.Integer(), nullable=False)
        batch_op.alter_column('skill_id', type_=sa.Integer(), nullable=False)

    # Update video_items table
    with op.batch_alter_table('video_items') as batch_op:
        batch_op.alter_column('video_id', type_=sa.Integer(), nullable=False)
        batch_op.alter_column('item_id', type_=sa.Integer(), nullable=False)

    # Update video_heroes table
    with op.batch_alter_table('video_heroes') as batch_op:
        batch_op.alter_column('video_id', type_=sa.Integer(), nullable=False)
        batch_op.alter_column('hero_name', type_=sa.String(), nullable=False)

    # Update skill_rarities table
    with op.batch_alter_table('skill_rarities') as batch_op:
        batch_op.alter_column('skill_id', type_=sa.Integer(), nullable=False)
        batch_op.alter_column('rarity', type_=sa.String(), nullable=True)

    # Update skill_types table
    with op.batch_alter_table('skill_types') as batch_op:
        batch_op.alter_column('skill_id', type_=sa.Integer(), nullable=False)
        batch_op.alter_column('type', type_=sa.String(), nullable=True)

    # Update skill_effects table
    with op.batch_alter_table('skill_effects') as batch_op:
        batch_op.alter_column('skill_id', type_=sa.Integer(), nullable=False)
        batch_op.alter_column('effect', type_=sa.String(), nullable=True)

    # Update skill_heroes table
    with op.batch_alter_table('skill_heroes') as batch_op:
        batch_op.alter_column('skill_id', type_=sa.Integer(), nullable=False)
        batch_op.alter_column('hero', type_=sa.String(), nullable=True)

    # Update item_rarities table
    with op.batch_alter_table('item_rarities') as batch_op:
        batch_op.alter_column('item_id', type_=sa.Integer(), nullable=False)
        batch_op.alter_column('rarity', type_=sa.String(), nullable=True)

    # Update item_types table
    with op.batch_alter_table('item_types') as batch_op:
        batch_op.alter_column('item_id', type_=sa.Integer(), nullable=False)
        batch_op.alter_column('type', type_=sa.String(), nullable=True)

    # Update item_effects table
    with op.batch_alter_table('item_effects') as batch_op:
        batch_op.alter_column('item_id', type_=sa.Integer(), nullable=False)
        batch_op.alter_column('effect', type_=sa.String(), nullable=True)

    # Update item_heroes table
    with op.batch_alter_table('item_heroes') as batch_op:
        batch_op.alter_column('item_id', type_=sa.Integer(), nullable=False)
        batch_op.alter_column('hero', type_=sa.String(), nullable=True)

    # Update enchantments table
    with op.batch_alter_table('enchantments') as batch_op:
        batch_op.alter_column('item_id', type_=sa.Integer(), nullable=False)
        batch_op.alter_column('enchantment_name', type_=sa.String(), nullable=False)
        batch_op.alter_column('enchantment_effect', type_=sa.String(), nullable=False)

def downgrade():
    """Downgrade schema."""
    # Note: SQLite may not support all downgrade operations
    # Recreate icon_url in skills
    with op.batch_alter_table('skills') as batch_op:
        batch_op.add_column(sa.Column('icon_url', sa.Text(), nullable=True))
        batch_op.alter_column('name', type_=sa.Text(), existing_nullable=False)
        batch_op.alter_column('id', type_=sa.Integer(), nullable=True, existing_autoincrement=True)

    # Revert videos table
    with op.batch_alter_table('videos') as batch_op:
        batch_op.alter_column('title', type_=sa.Text(), existing_nullable=False)
        batch_op.alter_column('type', type_=sa.Text(), existing_nullable=False)
        batch_op.alter_column('date', type_=sa.Text(), existing_nullable=True)
        batch_op.alter_column('status', type_=sa.Text(), existing_nullable=True)
        batch_op.alter_column('description', type_=sa.Text(), existing_nullable=True)
        batch_op.alter_column('local_path', type_=sa.Text(), existing_nullable=True)

    # Revert items table
    with op.batch_alter_table('items') as batch_op:
        batch_op.alter_column('id', type_=sa.Integer(), nullable=True, existing_autoincrement=True)
        batch_op.alter_column('name', type_=sa.Text(), existing_nullable=False)
        batch_op.alter_column('size', type_=sa.Text(), nullable=False)

    # Revert junction tables (set nullable=True where needed)
    with op.batch_alter_table('video_skills') as batch_op:
        batch_op.alter_column('video_id', type_=sa.Integer(), nullable=True)
        batch_op.alter_column('skill_id', type_=sa.Integer(), nullable=True)

    with op.batch_alter_table('video_items') as batch_op:
        batch_op.alter_column('video_id', type_=sa.Integer(), nullable=True)
        batch_op.alter_column('item_id', type_=sa.Integer(), nullable=True)

    with op.batch_alter_table('video_heroes') as batch_op:
        batch_op.alter_column('video_id', type_=sa.Integer(), nullable=True)
        batch_op.alter_column('hero_name', type_=sa.Text(), nullable=True)

    # Revert skill-related tables
    with op.batch_alter_table('skill_rarities') as batch_op:
        batch_op.alter_column('skill_id', type_=sa.Integer(), nullable=True)
        batch_op.alter_column('rarity', type_=sa.Text(), nullable=False)

    with op.batch_alter_table('skill_types') as batch_op:
        batch_op.alter_column('skill_id', type_=sa.Integer(), nullable=True)
        batch_op.alter_column('type', type_=sa.Text(), nullable=False)

    with op.batch_alter_table('skill_effects') as batch_op:
        batch_op.alter_column('skill_id', type_=sa.Integer(), nullable=True)
        batch_op.alter_column('effect', type_=sa.Text(), nullable=False)

    with op.batch_alter_table('skill_heroes') as batch_op:
        batch_op.alter_column('skill_id', type_=sa.Integer(), nullable=True)
        batch_op.alter_column('hero', type_=sa.Text(), nullable=False)

    # Revert item-related tables
    with op.batch_alter_table('item_rarities') as batch_op:
        batch_op.alter_column('item_id', type_=sa.Integer(), nullable=True)
        batch_op.alter_column('rarity', type_=sa.Text(), nullable=False)

    with op.batch_alter_table('item_types') as batch_op:
        batch_op.alter_column('item_id', type_=sa.Integer(), nullable=True)
        batch_op.alter_column('type', type_=sa.Text(), nullable=False)

    with op.batch_alter_table('item_effects') as batch_op:
        batch_op.alter_column('item_id', type_=sa.Integer(), nullable=True)
        batch_op.alter_column('effect', type_=sa.Text(), nullable=False)

    with op.batch_alter_table('item_heroes') as batch_op:
        batch_op.alter_column('item_id', type_=sa.Integer(), nullable=True)
        batch_op.alter_column('hero', type_=sa.Text(), nullable=False)

    with op.batch_alter_table('enchantments') as batch_op:
        batch_op.alter_column('item_id', type_=sa.Integer(), nullable=True)
        batch_op.alter_column('enchantment_name', type_=sa.Text(), nullable=False)
        batch_op.alter_column('enchantment_effect', type_=sa.Text(), nullable=False)