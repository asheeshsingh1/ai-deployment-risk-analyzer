function Header() {
    return (
        <header className="app-header">
        <div className="header-content">
            <div>
            <p className="eyebrow">Engineering Intelligence</p>
            <h1>Deployment Risk Analyzer</h1>
            </div>

            <div className="header-status">
            <span className="status-dot" />
            <span>Local</span>
            </div>
        </div>
        </header>
    );
}

export default Header;