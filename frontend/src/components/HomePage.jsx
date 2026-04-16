import { useUser } from '../contexts/UserContext';

function HomePage() {
  const { user } = useUser();

  return (
    <div className="home-container">
      <h1>Welcome, {user?.username}!</h1>
      <p>Your base application is up and running. Start building your features.</p>
    </div>
  );
}

export default HomePage;
