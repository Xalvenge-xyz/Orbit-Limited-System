class ChartManager {
  constructor() {
    this.instances = {};
  }
  destroy(key) {
    if (this.instances[key]) {
      this.instances[key].destroy();
      this.instances[key] = null;
    }
  }
  create(key, ctx, config) {
    this.destroy(key);
    this.instances[key] = new Chart(ctx, config);
    return this.instances[key];
  }
  updateTheme() {
    // re-render handled by pages if needed
  }
}
window.chartManager = new ChartManager();
window.ChartManager = ChartManager;
