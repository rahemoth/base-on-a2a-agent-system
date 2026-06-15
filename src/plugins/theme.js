const THEMES = ['default', 'warm', 'cool', 'sunset', 'forest'];

export default function themePlugin({ settings }) {
  let theme = settings?.theme || 'default';

  function apply(themeName) {
    const root = document.documentElement;
    THEMES.forEach(t => root.classList.remove(`theme-${t}`));
    if (themeName !== 'default') {
      root.classList.add(`theme-${themeName}`);
    }
    theme = themeName;
  }

  return {
    init() {
      apply(theme);
    },

    // Expose via bus for UI control
    getTheme() {
      return theme;
    },

    setTheme(name) {
      if (THEMES.includes(name)) {
        apply(name);
      }
    },

    listThemes() {
      return [...THEMES];
    },
  };
}
