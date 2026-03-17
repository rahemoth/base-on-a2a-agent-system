import { useState, useEffect } from "react";
import { Moon, Sun, Globe, Menu, X } from "lucide-react";

const NAV_ITEMS = [
  { id: "hero", labelZh: "首页", labelEn: "Home" },
  { id: "about", labelZh: "关于", labelEn: "About" },
  { id: "blog", labelZh: "博客", labelEn: "Blog" },
  { id: "projects", labelZh: "项目", labelEn: "Projects" },
  { id: "timeline", labelZh: "时间线", labelEn: "Timeline" },
  { id: "contact", labelZh: "联系", labelEn: "Contact" },
];

export function Navbar({ activeSection, language, setLanguage, theme, setTheme }) {
  const [isScrolled, setIsScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => setIsScrolled(window.scrollY > 80);
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const scrollTo = (id) => {
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });
    setMobileMenuOpen(false);
  };

  return (
    <div
      className={`fixed top-0 left-0 right-0 z-50 flex justify-center transition-all duration-700 ${
        isScrolled ? "pt-4" : "pt-4"
      }`}
    >
      <nav
        className={`flex items-center justify-between transition-all duration-700 ease-out ${
          isScrolled
            ? "w-[92vw] md:w-auto gap-2 md:gap-8 bg-white/90 dark:bg-black/90 backdrop-blur-md border border-gray-200 dark:border-gray-800 rounded-full px-4 md:px-8 py-3 shadow-lg"
            : "w-[96vw] bg-transparent border-transparent shadow-none px-0 py-2"
        }`}
      >
        <button
          onClick={() => scrollTo("hero")}
          className="font-black tracking-tighter uppercase text-2xl md:text-3xl text-black dark:text-white transition-all duration-300 hover:opacity-70 shrink-0"
        >
          BLOG
        </button>

        <div className="hidden md:flex items-center gap-6">
          {NAV_ITEMS.map((item) => (
            <button
              key={item.id}
              onClick={() => scrollTo(item.id)}
              className={`text-base font-semibold uppercase tracking-wide transition-colors duration-200 relative group ${
                activeSection === item.id
                  ? "text-black dark:text-white"
                  : "text-gray-400 hover:text-black dark:hover:text-white"
              }`}
            >
              {language === "zh" ? item.labelZh : item.labelEn}
              <span
                className={`absolute -bottom-1 left-0 w-full h-[2px] bg-black dark:bg-white transform transition-transform duration-200 ${
                  activeSection === item.id ? "scale-x-100" : "scale-x-0 group-hover:scale-x-100"
                }`}
              />
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2">
          <div className="hidden md:block w-px h-6 bg-gray-200 dark:bg-gray-700 mx-1" />
          <button
            onClick={() => setLanguage(language === "zh" ? "en" : "zh")}
            className="flex items-center gap-1 px-2 py-1 rounded-full hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors text-black dark:text-white text-sm font-bold"
          >
            <Globe size={16} />
            {language === "zh" ? "EN" : "中"}
          </button>
          <button
            onClick={() => setTheme(theme === "light" ? "dark" : "light")}
            className="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors text-black dark:text-white"
          >
            {theme === "light" ? <Moon size={18} /> : <Sun size={18} />}
          </button>
          <button
            className="md:hidden p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors text-black dark:text-white"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            {mobileMenuOpen ? <X size={18} /> : <Menu size={18} />}
          </button>
        </div>
      </nav>

      {mobileMenuOpen && (
        <div className="absolute top-20 left-4 right-4 bg-white/95 dark:bg-black/95 backdrop-blur-md border border-gray-200 dark:border-gray-800 rounded-2xl p-4 shadow-xl">
          {NAV_ITEMS.map((item) => (
            <button
              key={item.id}
              onClick={() => scrollTo(item.id)}
              className={`w-full text-left py-3 px-4 text-lg font-semibold uppercase tracking-wide transition-colors rounded-xl ${
                activeSection === item.id
                  ? "text-black dark:text-white bg-gray-100 dark:bg-gray-900"
                  : "text-gray-500 hover:text-black dark:hover:text-white"
              }`}
            >
              {language === "zh" ? item.labelZh : item.labelEn}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
