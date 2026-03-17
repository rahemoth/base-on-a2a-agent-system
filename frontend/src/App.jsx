import { useState, useEffect } from "react";
import { Navbar } from "./components/Navbar";
import { HeroSection } from "./components/HeroSection";
import { AboutSection } from "./components/AboutSection";
import { BlogSection } from "./components/BlogSection";
import { ProjectsSection } from "./components/ProjectsSection";
import { TimelineSection } from "./components/TimelineSection";
import { ContactSection } from "./components/ContactSection";
import { Footer } from "./components/Footer";
import "./styles/global.css";

const SECTIONS = ["hero", "about", "blog", "projects", "timeline", "contact"];

function App() {
  const [language, setLanguage] = useState("zh");
  const [theme, setTheme] = useState("light");
  const [activeSection, setActiveSection] = useState("hero");

  useEffect(() => {
    if (theme === "dark") {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  }, [theme]);

  useEffect(() => {
    const observers = SECTIONS.map((id) => {
      const el = document.getElementById(id);
      if (!el) return null;
      const observer = new IntersectionObserver(
        ([entry]) => {
          if (entry.isIntersecting) setActiveSection(id);
        },
        { threshold: 0.4 }
      );
      observer.observe(el);
      return observer;
    });
    return () => observers.forEach((o) => o?.disconnect());
  }, []);

  return (
    <div className="min-h-screen bg-white dark:bg-black transition-colors duration-300">
      <Navbar
        activeSection={activeSection}
        language={language}
        setLanguage={setLanguage}
        theme={theme}
        setTheme={setTheme}
      />
      <main>
        <HeroSection language={language} />
        <AboutSection language={language} />
        <BlogSection language={language} />
        <ProjectsSection language={language} />
        <TimelineSection language={language} />
        <ContactSection language={language} />
      </main>
      <Footer language={language} />
    </div>
  );
}

export default App;
