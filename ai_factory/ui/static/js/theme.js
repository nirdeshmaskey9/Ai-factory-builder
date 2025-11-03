(() => {
  const THEME_KEY = 'jp_theme';
  const ACCENT_KEY = 'jp_accent';
  function apply(){
    const theme = localStorage.getItem(THEME_KEY) || 'dark';
    const accent = localStorage.getItem(ACCENT_KEY) || 'blue';
    document.documentElement.dataset.theme = theme;
    document.documentElement.dataset.accent = accent;
  }
  window.jpThemeToggle = function(){
    const cur = localStorage.getItem(THEME_KEY) || 'dark';
    const next = cur === 'dark' ? 'light' : 'dark';
    localStorage.setItem(THEME_KEY, next); apply();
  }
  window.jpAccentSet = function(a){ localStorage.setItem(ACCENT_KEY, a); apply(); }
  apply();
})();

