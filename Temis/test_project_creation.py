#!/usr/bin/env python3
import sys
sys.path.append('C:\\Users\\User\\Ecosistema-Maxi\\Temis')

from backend.database import SessionLocal
from backend.models.user import User
from backend.models.project import Project, ProjectMember, ProjectMemberRole
from backend.models.phase import Phase, PhaseStatus, PHASE_NAMES

# Create session
db = SessionLocal()

try:
    # Get user
    user = db.query(User).first()
    if not user:
        print("❌ No user found")
        sys.exit(1)
    
    print(f"✅ User found: {user.email}")
    
    # Create project
    project = Project(
        name="Test Project",
        description="Testing project creation",
        created_by=user.id
    )
    db.add(project)
    db.flush()
    
    print(f"✅ Project created with ID: {project.id}")
    
    # Add owner
    member = ProjectMember(
        project_id=project.id,
        user_id=user.id,
        role=ProjectMemberRole.OWNER
    )
    db.add(member)
    
    print(f"✅ Owner added")
    
    # Create phases
    for phase_num in range(1, 8):
        phase = Phase(
            project_id=project.id,
            phase_number=phase_num,
            name=PHASE_NAMES[phase_num],
            status=PhaseStatus.NOT_STARTED
        )
        db.add(phase)
    
    print(f"✅ 7 phases created")
    
    # Commit
    db.commit()
    print(f"✅ COMMIT SUCCESSFUL!")
    
    # Verify
    count = db.query(Project).count()
    print(f"✅ Total projects in DB: {count}")
    
except Exception as e:
    print(f"❌ ERROR: {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc()
    db.rollback()
finally:
    db.close()
