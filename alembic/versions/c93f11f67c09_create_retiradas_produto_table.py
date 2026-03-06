"""create_retiradas_produto_table

Revision ID: c93f11f67c09
Revises: 4c821097b713
Create Date: 2026-03-06 19:42:31.680221

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c93f11f67c09'
down_revision: Union[str, Sequence[str], None] = '4c821097b713'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Cria a tabela retiradas_produto."""
    
    # Cria a tabela retiradas_produto
    op.create_table(
        'retiradas_produto',
        
        # Colunas
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('sale_point_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('quantidade', sa.Float(), nullable=False),
        sa.Column('unidade', sa.String(length=10), nullable=False),
        sa.Column('observacao', sa.String(length=200), nullable=True),
        sa.Column('data', sa.DateTime(), nullable=True, 
                  server_default=sa.text('CURRENT_TIMESTAMP')),
        
        # Chaves estrangeiras
        sa.ForeignKeyConstraint(['sale_point_id'], ['sales_points.id'], 
                              ondelete='CASCADE', name='fk_retiradas_sale_point'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], 
                              ondelete='CASCADE', name='fk_retiradas_product'),
        
        # Chave primária
        sa.PrimaryKeyConstraint('id', name='pk_retiradas_produto')
    )
    
    # Cria índices para melhor performance nas consultas
    op.create_index('ix_retiradas_sale_point_id', 'retiradas_produto', ['sale_point_id'])
    op.create_index('ix_retiradas_product_id', 'retiradas_produto', ['product_id'])
    op.create_index('ix_retiradas_data', 'retiradas_produto', ['data'])
    
    # Nota: Não é necessário alterar as tabelas sales_points e products
    # pois as relações são apenas no nível do SQLAlchemy (back_populates)


def downgrade() -> None:
    """Remove a tabela retiradas_produto."""
    
    # Remove os índices (importante fazer antes de dropar a tabela)
    op.drop_index('ix_retiradas_data', table_name='retiradas_produto')
    op.drop_index('ix_retiradas_product_id', table_name='retiradas_produto')
    op.drop_index('ix_retiradas_sale_point_id', table_name='retiradas_produto')
    
    # Remove a tabela
    op.drop_table('retiradas_produto')