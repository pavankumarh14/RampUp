import asyncio
import os
import subprocess
import sys
from pathlib import Path

# Add the project root to the path so we can import our app modules
sys.path.insert(0, str(Path(__file__).parent))


async def main():
    print("🚀 Starting RampUp app...")

    # Step 1: Run Alembic migrations
    print("\n📊 Running Alembic migrations...")
    try:
        subprocess.run(
            ["uv", "run", "alembic", "-c", "app/alembic.ini", "upgrade", "head"],
            check=True,
            capture_output=False
        )
        print("✅ Migrations done!")
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        # Let the app still start if migrations fail, but log it
        pass

    # Step 2: Optionally load sample data
    load_samples = os.getenv("LOAD_SAMPLE_DATA", "true").lower() == "true"
    if load_samples:
        print("\n📄 Loading sample dataset...")
        try:
            # Import here after path is set
            from generate_sample_dataset import main as load_samples_main
            await load_samples_main()
            print("✅ Sample dataset loaded!")
        except Exception as e:
            print(f"❌ Failed to load sample data: {e}")
            pass

    # Step 3: Start the FastAPI server
    print("\n🌐 Starting FastAPI server...")
    server_cmd = [
        "uv", "run", "uvicorn", 
        "app.main:app", 
        "--host", "0.0.0.0", 
        "--port", "8000"
    ]
    os.execvp(server_cmd[0], server_cmd)


if __name__ == "__main__":
    asyncio.run(main())
