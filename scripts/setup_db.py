import asyncio
import asyncpg
import os

async def main():
    # Try connecting to default postgres database to create user/db
    # Assuming default user is 'postgres' or current user
    # We'll try 'postgres' first, then no user (current user)
    
    print("Attempting to connect to PostgreSQL...")
    
    conn = None
    try:
        # Try connecting to 'postgres' db with 'postgres' user
        conn = await asyncpg.connect('postgresql://postgres@localhost:5432/postgres')
        print("Connected as 'postgres'.")
    except Exception as e:
        print(f"Failed to connect as 'postgres': {e}")
        try:
            # Try connecting without user (uses current OS user)
            conn = await asyncpg.connect('postgresql://localhost:5432/postgres')
            print("Connected as current user.")
        except Exception as e2:
            print(f"Failed to connect as current user: {e2}")
            return

    if conn:
        try:
            # Check if user 'hector' exists
            user_exists = await conn.fetchval("SELECT 1 FROM pg_roles WHERE rolname='hector'")
            if not user_exists:
                print("Creating user 'hector'...")
                await conn.execute("CREATE USER hector WITH PASSWORD 'hector'")
            else:
                print("User 'hector' already exists.")

            # Check if database 'hector' exists
            db_exists = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname='hector'")
            if not db_exists:
                print("Creating database 'hector'...")
                # CREATE DATABASE cannot run in a transaction block, so we might need to close and reopen or use specific isolation level?
                # asyncpg connection is not in transaction by default unless we start one.
                # But CREATE DATABASE cannot be executed from a function/block? 
                # Actually asyncpg execute should work if not in transaction.
                await conn.execute("CREATE DATABASE hector OWNER hector")
            else:
                print("Database 'hector' already exists.")
                
        except Exception as e:
            print(f"Error during setup: {e}")
        finally:
            await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
