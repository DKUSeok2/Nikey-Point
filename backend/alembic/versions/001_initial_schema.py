"""Initial schema - Simplified structure

Revision ID: 001
Revises: 
Create Date: 2026-02-04

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_name', sa.String(), nullable=False),
        sa.Column('height', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_users_user_name', 'users', ['user_name'])
    
    # Create user_datas table
    op.create_table(
        'user_datas',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        
        # 원본 영상
        sa.Column('original_video_path', sa.String(), nullable=False),
        
        # 오버스트라이드 분석
        sa.Column('overstride_overlay_path', sa.String(), nullable=True),
        sa.Column('overstride_avg', sa.Float(), nullable=True),
        
        # 무게중심 상하움직임 분석
        sa.Column('com_vertical_overlay_path', sa.String(), nullable=True),
        sa.Column('com_vertical_avg', sa.Float(), nullable=True),
        
        # 상체 기울기 분석
        sa.Column('tilt_overlay_path', sa.String(), nullable=True),
        sa.Column('tilt_avg', sa.Float(), nullable=True),
        
        # LLM 피드백
        sa.Column('llm_feedback', sa.Text(), nullable=True),
        
        # 타임스탬프
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_user_datas_user_id', 'user_datas', ['user_id'])
    op.create_index('ix_user_datas_created_at', 'user_datas', ['created_at'])


def downgrade() -> None:
    op.drop_index('ix_user_datas_created_at', table_name='user_datas')
    op.drop_index('ix_user_datas_user_id', table_name='user_datas')
    op.drop_table('user_datas')
    
    op.drop_index('ix_users_user_name', table_name='users')
    op.drop_table('users')
