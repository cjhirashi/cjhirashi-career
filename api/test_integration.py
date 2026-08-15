"""
Test de integración para la API MCP Tools.
Ejecuta pruebas automáticas de todos los endpoints principales.
"""
import asyncio
import httpx
import sys
from typing import Optional

API_URL = "http://localhost:8001"
USERNAME = "usuario"
PASSWORD = "password123"


class Colors:
    """ANSI color codes para output."""
    GREEN = '\033[0;32m'
    RED = '\033[0;31m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color


class APITester:
    """Tester de la API con httpx async."""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.token: Optional[str] = None
        self.client = httpx.AsyncClient(base_url=base_url, timeout=10.0)

    async def close(self):
        """Cierra el cliente HTTP."""
        await self.client.aclose()

    def print_test(self, step: str, name: str):
        """Imprime el nombre del test."""
        print(f"{Colors.BLUE}[{step}]{Colors.NC} {name}")

    def print_success(self, message: str):
        """Imprime mensaje de éxito."""
        print(f"{Colors.GREEN}✓ {message}{Colors.NC}")

    def print_error(self, message: str):
        """Imprime mensaje de error."""
        print(f"{Colors.RED}✗ {message}{Colors.NC}")

    async def test_health(self) -> bool:
        """Test de health check."""
        self.print_test("1/8", "Health Check")
        try:
            response = await self.client.get("/health")
            data = response.json()
            print(f"Response: {data}")

            if response.status_code == 200 and data.get("status") == "healthy":
                self.print_success("Health check passed")
                return True
            else:
                self.print_error("Health check failed")
                return False
        except Exception as e:
            self.print_error(f"Health check failed: {e}")
            return False

    async def test_login(self) -> bool:
        """Test de login."""
        self.print_test("2/8", "Login")
        try:
            response = await self.client.post(
                "/auth/login",
                json={"username": USERNAME, "password": PASSWORD}
            )
            data = response.json()

            if response.status_code == 200 and "access_token" in data:
                self.token = data["access_token"]
                self.print_success(f"Login successful, token: {self.token[:50]}...")
                return True
            else:
                self.print_error(f"Login failed: {data}")
                return False
        except Exception as e:
            self.print_error(f"Login failed: {e}")
            return False

    async def test_register(self) -> bool:
        """Test de registro de nuevo usuario."""
        self.print_test("3/8", "Register New User")
        try:
            # Intentar registrar un usuario único
            import random
            username = f"testuser_{random.randint(1000, 9999)}"
            email = f"{username}@test.com"

            response = await self.client.post(
                "/auth/register",
                json={
                    "username": username,
                    "email": email,
                    "password": "testpass123"
                }
            )
            data = response.json()

            if response.status_code == 201:
                self.print_success(f"User registered: {username}")
                return True
            else:
                self.print_error(f"Registration failed: {data}")
                return False
        except Exception as e:
            self.print_error(f"Registration failed: {e}")
            return False

    async def test_list_documents(self) -> bool:
        """Test de listado de documentos."""
        self.print_test("4/8", "List Documents")
        try:
            response = await self.client.get(
                "/documents",
                headers={"Authorization": f"Bearer {self.token}"}
            )
            data = response.json()
            print(f"Response: {data}")

            if response.status_code == 200 and "documents" in data:
                self.print_success(f"List documents passed, total: {data.get('total', 0)}")
                return True
            else:
                self.print_error(f"List documents failed: {data}")
                return False
        except Exception as e:
            self.print_error(f"List documents failed: {e}")
            return False

    async def test_create_document(self) -> Optional[int]:
        """Test de creación de documento."""
        self.print_test("5/8", "Create Document")
        try:
            response = await self.client.post(
                "/documents",
                headers={"Authorization": f"Bearer {self.token}"},
                json={
                    "type": "cv",
                    "title": "Integration Test CV",
                    "data": {
                        "nombre": "Test User",
                        "email": "test@example.com",
                        "telefono": "+34 600 000 000"
                    }
                }
            )
            data = response.json()
            print(f"Response: {data}")

            if response.status_code == 201 and "id" in data:
                doc_id = data["id"]
                self.print_success(f"Document created with ID: {doc_id}")
                return doc_id
            else:
                self.print_error(f"Document creation failed: {data}")
                return None
        except Exception as e:
            self.print_error(f"Document creation failed: {e}")
            return None

    async def test_get_document(self, doc_id: int) -> bool:
        """Test de obtención de documento."""
        self.print_test("6/8", "Get Document")
        try:
            response = await self.client.get(
                f"/documents/{doc_id}",
                headers={"Authorization": f"Bearer {self.token}"}
            )
            data = response.json()
            print(f"Response: {data}")

            if response.status_code == 200 and data.get("id") == doc_id:
                self.print_success("Get document passed")
                return True
            else:
                self.print_error(f"Get document failed: {data}")
                return False
        except Exception as e:
            self.print_error(f"Get document failed: {e}")
            return False

    async def test_update_document(self, doc_id: int) -> bool:
        """Test de actualización de documento."""
        self.print_test("7/8", "Update Document")
        try:
            response = await self.client.put(
                f"/documents/{doc_id}",
                headers={"Authorization": f"Bearer {self.token}"},
                json={
                    "title": "Updated Integration Test CV",
                    "data": {
                        "nombre": "Test User Updated",
                        "email": "test_updated@example.com"
                    }
                }
            )
            data = response.json()
            print(f"Response: {data}")

            if response.status_code == 200:
                self.print_success("Document updated")
                return True
            else:
                self.print_error(f"Document update failed: {data}")
                return False
        except Exception as e:
            self.print_error(f"Document update failed: {e}")
            return False

    async def test_delete_document(self, doc_id: int) -> bool:
        """Test de eliminación de documento."""
        self.print_test("8/8", "Delete Document")
        try:
            response = await self.client.delete(
                f"/documents/{doc_id}",
                headers={"Authorization": f"Bearer {self.token}"}
            )

            if response.status_code == 204:
                self.print_success("Document deleted")
                return True
            else:
                self.print_error(f"Document deletion failed: {response.text}")
                return False
        except Exception as e:
            self.print_error(f"Document deletion failed: {e}")
            return False


async def main():
    """Función principal de pruebas."""
    print("=" * 50)
    print("MCP Tools API - Integration Test Suite")
    print("=" * 50)
    print(f"API URL: {API_URL}")
    print()

    tester = APITester(API_URL)
    results = []

    try:
        # Ejecutar tests en orden
        results.append(await tester.test_health())
        results.append(await tester.test_login())

        if not tester.token:
            print(f"{Colors.RED}Cannot continue without token{Colors.NC}")
            await tester.close()
            sys.exit(1)

        results.append(await tester.test_register())
        results.append(await tester.test_list_documents())

        doc_id = await tester.test_create_document()
        if doc_id:
            results.append(True)
            results.append(await tester.test_get_document(doc_id))
            results.append(await tester.test_update_document(doc_id))
            results.append(await tester.test_delete_document(doc_id))
        else:
            results.extend([False, False, False, False])

        # Summary
        print()
        print("=" * 50)
        passed = sum(results)
        total = len(results)
        print(f"{Colors.GREEN if passed == total else Colors.RED}Results: {passed}/{total} tests passed{Colors.NC}")
        print("=" * 50)

        await tester.close()

        # Exit with appropriate code
        sys.exit(0 if passed == total else 1)

    except Exception as e:
        print(f"{Colors.RED}Test suite failed: {e}{Colors.NC}")
        await tester.close()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
