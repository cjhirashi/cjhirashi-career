"""
Script para crear un nuevo usuario en la base de datos.
Útil para administración y testing.

Uso:
    python create_user.py --username john --email john@example.com --password secure123
"""
import asyncio
import argparse
import sys
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select
from models.user import User
from utils.security import hash_password
from config import settings


async def create_user(username: str, email: str, password: str):
    """
    Crea un nuevo usuario en la base de datos.

    Args:
        username: Nombre de usuario único
        email: Email único
        password: Contraseña en texto plano (será hasheada)
    """
    # Crear engine y session
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        try:
            # Verificar si el username ya existe
            result = await session.execute(
                select(User).where(User.username == username)
            )
            if result.scalar_one_or_none() is not None:
                print(f"Error: Username '{username}' ya existe")
                return False

            # Verificar si el email ya existe
            result = await session.execute(
                select(User).where(User.email == email)
            )
            if result.scalar_one_or_none() is not None:
                print(f"Error: Email '{email}' ya existe")
                return False

            # Crear usuario
            new_user = User(
                username=username,
                email=email,
                password_hash=hash_password(password)
            )

            session.add(new_user)
            await session.commit()
            await session.refresh(new_user)

            print(f"Usuario creado exitosamente:")
            print(f"  ID: {new_user.id}")
            print(f"  Username: {new_user.username}")
            print(f"  Email: {new_user.email}")
            print(f"  Created: {new_user.created_at}")

            return True

        except Exception as e:
            print(f"Error creando usuario: {e}")
            await session.rollback()
            return False

        finally:
            await engine.dispose()


def main():
    """Función principal del script."""
    parser = argparse.ArgumentParser(
        description="Crear un nuevo usuario en la base de datos MCP Tools API"
    )
    parser.add_argument(
        "--username",
        required=True,
        help="Nombre de usuario (único)"
    )
    parser.add_argument(
        "--email",
        required=True,
        help="Email del usuario (único)"
    )
    parser.add_argument(
        "--password",
        required=True,
        help="Contraseña del usuario (será hasheada con bcrypt)"
    )

    args = parser.parse_args()

    print("=" * 50)
    print("MCP Tools API - Create User Script")
    print("=" * 50)
    print(f"Username: {args.username}")
    print(f"Email: {args.email}")
    print(f"Database: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'N/A'}")
    print()

    # Ejecutar creación de usuario
    success = asyncio.run(create_user(args.username, args.email, args.password))

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
