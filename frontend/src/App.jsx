import { useState } from 'react';
import AdminPortal from '../admin/AdminPortal';
import UserPortal from '../user/UserPortal';

export default function App() {
  const [portal, setPortal] = useState('user');
  return <main className="app-shell">
    <header><div><span className="eyebrow">Urban Parcel Mapping</span><h1>Cadastral Intelligence</h1></div>
      <nav aria-label="Portal selector"><button className={portal === 'user' ? 'active' : ''} onClick={() => setPortal('user')}>User Portal</button><button className={portal === 'admin' ? 'active' : ''} onClick={() => setPortal('admin')}>Admin Portal</button></nav>
    </header>
    {portal === 'admin' ? <AdminPortal /> : <UserPortal />}
  </main>;
}
