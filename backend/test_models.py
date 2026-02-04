"""Simple test script to verify SQLAlchemy models."""
import uuid
from src.core.database import SessionLocal
from src.user.model import User
from src.analysis.model import UserData

def test_models():
    """Test creating and querying User and UserData models."""
    db = SessionLocal()
    
    try:
        print("🧪 Testing SQLAlchemy models...\n")
        
        # 1. Create a user
        print("1️⃣ Creating a user...")
        user = User(
            id=str(uuid.uuid4()),
            user_name="테스트유저",
            height=175.5
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"✅ User created: {user}")
        print(f"   ID: {user.id}")
        print(f"   Name: {user.user_name}")
        print(f"   Height: {user.height}cm")
        print(f"   Created: {user.created_at}\n")
        
        # 2. Create user data
        print("2️⃣ Creating user data...")
        user_data = UserData(
            id=str(uuid.uuid4()),
            user_id=user.id,
            original_video_path="/storage/videos/test.mp4",
            overstride_overlay_path="/storage/overlays/test_overstride.mp4",
            overstride_avg=0.15,
            com_vertical_overlay_path="/storage/overlays/test_com.mp4",
            com_vertical_avg=0.05,
            tilt_overlay_path="/storage/overlays/test_tilt.mp4",
            tilt_avg=3.2,
            llm_feedback="전체적으로 양호한 러닝 폼입니다."
        )
        db.add(user_data)
        db.commit()
        db.refresh(user_data)
        print(f"✅ UserData created: {user_data}")
        print(f"   ID: {user_data.id}")
        print(f"   User ID: {user_data.user_id}")
        print(f"   Video: {user_data.original_video_path}")
        print(f"   Overstride avg: {user_data.overstride_avg}")
        print(f"   Feedback: {user_data.llm_feedback}\n")
        
        # 3. Query user with relationship
        print("3️⃣ Querying user with relationship...")
        queried_user = db.query(User).filter(User.id == user.id).first()
        print(f"✅ Found user: {queried_user.user_name}")
        print(f"   User data count: {len(queried_user.user_datas)}")
        for data in queried_user.user_datas:
            print(f"   - Data ID: {data.id}")
            print(f"     Overstride: {data.overstride_avg}\n")
        
        # 4. Query all user data for a user
        print("4️⃣ Querying all user data...")
        user_data_list = (
            db.query(UserData)
            .filter(UserData.user_id == user.id)
            .order_by(UserData.created_at.desc())
            .all()
        )
        print(f"✅ Found {len(user_data_list)} user data records\n")
        
        # 5. Test cascade delete
        print("5️⃣ Testing cascade delete...")
        db.delete(queried_user)
        db.commit()
        
        remaining = db.query(UserData).filter(UserData.user_id == user.id).count()
        print(f"✅ User deleted. Remaining user data: {remaining}")
        print(f"   (Should be 0 due to CASCADE DELETE)\n")
        
        print("🎉 All tests passed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    test_models()
