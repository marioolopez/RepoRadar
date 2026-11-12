"""
Crear tabla analisis
Revision ID: 5f407567253c
Revises: 1da75fbb4c30
Create Date: 2026-11-09 14:44:03.291606

"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


#identificadores de esta migración
revision: str = '5f407567253c'
down_revision: Union[str, Sequence[str], None] = '1da75fbb4c30'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    """"Aplica la migración. Crea la tabla 'analisis' en PostgreSQL"""

    op.create_table(
        'analisis',

        #identificador único de cada análisis
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        #id del proyecto que estamos analizando
        sa.Column('proyecto_id', sa.Integer(), nullable=False),
        #estado del análisis: pendiente, ejecutando, completado...
        sa.Column('estado', sa.String(length=20), server_default='pendiente', nullable=False),
        #fecha en la que se registra el análisis
        sa.Column('fecha_inicio', sa.DateTime(), server_default= sa.text('CURRENT_TIMESTAMP'), nullable=False),
        #fecha de finalización (puede estar vacía)
        sa.Column('fecha_fin', sa.DateTime(), nullable=True),
        #relacionamos el análisis con un proyecto existente
        sa.ForeignKeyConstraint(['proyecto_id'], ['proyectos.id']),
        #definimos la clave primaria
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """
    Revierte la migración.
    Elimina la tabla 'analisis'.
    """
    op.drop_table('analisis')