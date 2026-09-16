import { useState } from 'react';
import AdminPortal from '../admin/AdminPortal';
import UserPortal from '../user/UserPortal';

export default function App() {
  const [portal, setPortal] = useState('user');

  return <main className="app-shell">
    <header className="site-header">
      <button className="brand" onClick={() => setPortal('user')} aria-label="Open map explorer">
        <span className="brand-mark" aria-hidden="true"><i /><i /><i /></span>
        <span><small>PARCEL-XAI</small><strong>Field Atlas</strong></span>
      </button>
      <nav className="portal-switcher" aria-label="Portal selector">
        <button className={portal === 'user' ? 'active' : ''} onClick={() => setPortal('user')}>Explore map</button>
        <button className={portal === 'admin' ? 'active' : ''} onClick={() => setPortal('admin')}>Workspace</button>
      </nav>
      <div className="header-status"><span className="live-dot" />System online</div>
    </header>
    {portal === 'admin' ? <AdminPortal /> : <UserPortal />}
  </main>;
}
