import asyncio
import os
import subprocess
import sys
from pathlib import Path

# Add the project root to the path so we can import our app modules
sys.path.insert(0, str(Path(__file__).parent))


def run_command(cmd_list):
    """Helper to run a command and print output/errors"""
    print(f"\n💻 Running command: {' '.join(cmd_list)}")
    result = subprocess.run(
        cmd_list,
        capture_output=True,
        text=True
    )
    print(f"📤 Command stdout:\n{result.stdout}")
    if result.stderr:
        print(f"⚠️ Command stderr:\n{result.stderr}")
    return result.returncode == 0


async def main():
    print("🚀 Starting RampUp app...")
    print(f"📋 Environment variables:")
    for key, value in sorted(os.environ.items()):
        if "KEY" in key or "PASSWORD" in key or "SECRET" in key:
            print(f"  {key}: [REDACTED]")
        else:
            print(f"  {key}: {value}")

    # Step 1: Run Alembic migrations
    print("\n📊 Running Alembic migrations...")
    migrations_ok = run_command([
        "alembic", 
        "-c", "app/alembic.ini", 
        "upgrade", "head"
    ])
    if migrations_ok:
        print("✅ Migrations done!")
    else:
        print("❌ Migration failed! Trying to continue anyway...")

    # Step 2: Optionally load sample data
    load_samples = os.getenv("LOAD_SAMPLE_DATA", "true").lower() == "true"
    reset_db = os.getenv("RESET_DB", "false").lower() == "true"
    if load_samples:
        print("\n📄 Loading sample dataset...")
        try:
            # Import here after path is set
            from generate_sample_dataset import main as load_samples_main
            await load_samples_main()
            print("✅ Sample dataset loaded!")
        except Exception as e:
            print(f"❌ Failed to load sample data: {e}")
            import traceback
            print("Stack trace:")
            traceback.print_exc()

    # Step 3: Start the FastAPI server
    print("\n🌐 Starting FastAPI server...")
    server_cmd = [
        "uvicorn", 
        "app.main:app", 
        "--host", "0.0.0.0", 
        "--port", "8000"
    ]
    print(f"💻 Running server command: {' '.join(server_cmd)}")
    os.execvp(server_cmd[0], server_cmd)


if __name__ == "__main__":
    asyncio.run(main())
