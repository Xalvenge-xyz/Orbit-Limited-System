class ThemeManager {
  constructor() {
    this.key = 'orbit_theme';
    this.current = localStorage.getItem(this.key) || 'dark';
    this.apply();
    const btn = document.getElementById('themeToggle');
    if (btn) btn.addEventListener('click', () => this.toggle());
  }
  apply() {
    document.documentElement.setAttribute('data-theme', this.current);
    // update charts if present
    if (window.chartManager && typeof window.chartManager.updateTheme === 'function') {
      window.chartManager.updateTheme();
    }
  }
  toggle() {
    this.current = this.current === 'dark' ? 'light' : 'dark';
    localStorage.setItem(this.key, this.current);
    this.apply();
  }
}
document.addEventListener('DOMContentLoaded', () => { window.themeManager = new ThemeManager(); });
