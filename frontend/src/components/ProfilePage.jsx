import { useUser } from '../contexts/UserContext';

function ProfilePage() {
  const { user } = useUser();

  return (
    <div className="profile-container">
      <div className="card">
        <h2>Profile</h2>
        <div className="profile-field">
          <span className="label">Username</span>
          <span>{user?.username}</span>
        </div>
        <div className="profile-field">
          <span className="label">Email</span>
          <span>{user?.email}</span>
        </div>
        <div className="profile-field">
          <span className="label">Member since</span>
          <span>
            {user?.created_at
              ? new Date(user.created_at).toLocaleDateString()
              : '—'}
          </span>
        </div>
      </div>
    </div>
  );
}

export default ProfilePage;
