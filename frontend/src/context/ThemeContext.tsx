import { createContext, useContext, useEffect, useState } from 'react';

type Theme = 'dark' | 'light' | 'cyberpunk';
type ThemeContextValue = { theme: Theme; setTheme: (theme: Theme) => void; cycleTheme: () => void };

const ThemeContext = createContext<ThemeContextValue | null>(null);
const themes: Theme[] = ['dark', 'light', 'cyberpunk'];

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setThemeState] = useState<Theme>(() => (localStorage.getItem('devorbit-theme') as Theme) || 'dark');
  const setTheme = (nextTheme: Theme) => { setThemeState(nextTheme); localStorage.setItem('devorbit-theme', nextTheme); };
  const cycleTheme = () => setTheme(themes[(themes.indexOf(theme) + 1) % themes.length]);
  useEffect(() => { document.documentElement.dataset.theme = theme; }, [theme]);
  return <ThemeContext.Provider value={{ theme, setTheme, cycleTheme }}>{children}</ThemeContext.Provider>;
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) throw new Error('useTheme must be used inside ThemeProvider');
  return context;
}
