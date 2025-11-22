"""Version endpoint to verify deployment"""
from fastapi import APIRouter
import subprocess
import os

router = APIRouter()

def get_git_commit():
    """Get current git commit hash"""
    try:
        return subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).decode('ascii').strip()
    except Exception:
        return "unknown"

def get_git_branch():
    """Get current git branch"""
    try:
        return subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD']).decode('ascii').strip()
    except Exception:
        return "unknown"

@router.get("/version")
async def get_version():
    """Get backend version info to verify deployments"""
    return {
        "version": "1.0.0",
        "git_commit": get_git_commit(),
        "git_branch": get_git_branch(),
        "deployment_time": os.getenv("RAILWAY_DEPLOYMENT_TIME", "not_set"),
        "has_user_id_fallback": True,  # Marker for the cloud storage fix
        "allows_null_organization": True  # Marker for auth_dependency fix (commit 818b98a)
    }
