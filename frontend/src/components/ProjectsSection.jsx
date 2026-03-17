import { BlurFade } from "./ui/blur-fade";
import { MagicCard } from "./ui/magic-card";
import { BorderBeam } from "./ui/border-beam";
import { PROJECTS } from "../data/projects";
import { Github, ExternalLink, Star } from "lucide-react";

const PROJECTS_CONTENT = {
  zh: {
    sectionLabel: "项目",
    title: "精选作品",
    allProjects: `共 ${PROJECTS.length} 个项目`,
  },
  en: {
    sectionLabel: "Projects",
    title: "Selected Works",
    allProjects: `${PROJECTS.length} Projects Total`,
  },
};

function ProjectCard({ project, language, delay }) {
  return (
    <BlurFade delay={delay} inView>
      <MagicCard className="group overflow-hidden h-full" gradientColor="#f3f4f6">
        <div className="relative overflow-hidden aspect-[16/9]">
          <img
            src={project.image}
            alt={language === "zh" ? project.title : project.titleEn}
            className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
          {project.featured && (
            <div className="absolute top-3 right-3 flex items-center gap-1 px-3 py-1 bg-yellow-400 text-black text-xs font-bold rounded-full">
              <Star size={10} fill="currentColor" />
              {language === "zh" ? "精选" : "Featured"}
            </div>
          )}
        </div>

        <div className="p-6">
          <h3 className="text-2xl font-black text-black dark:text-white mb-2 group-hover:opacity-70 transition-opacity">
            {language === "zh" ? project.title : project.titleEn}
          </h3>
          <p className="text-gray-600 dark:text-gray-400 text-sm leading-relaxed mb-4">
            {language === "zh" ? project.description : project.descriptionEn}
          </p>

          <div className="flex flex-wrap gap-2 mb-5">
            {project.tags.map((tag) => (
              <span
                key={tag}
                className="px-3 py-1 bg-gray-100 dark:bg-gray-900 text-gray-600 dark:text-gray-400 text-xs font-medium rounded-full"
              >
                {tag}
              </span>
            ))}
          </div>

          <div className="flex gap-3">
            {project.github && (
              <a
                href={project.github}
                className="flex items-center gap-2 px-4 py-2 border border-gray-200 dark:border-gray-800 rounded-full text-sm font-semibold text-gray-700 dark:text-gray-300 hover:border-black dark:hover:border-white hover:text-black dark:hover:text-white transition-all duration-200"
              >
                <Github size={14} />
                {language === "zh" ? "代码" : "Code"}
              </a>
            )}
            {project.demo && (
              <a
                href={project.demo}
                className="flex items-center gap-2 px-4 py-2 bg-black dark:bg-white text-white dark:text-black rounded-full text-sm font-semibold hover:opacity-80 transition-opacity"
              >
                <ExternalLink size={14} />
                {language === "zh" ? "演示" : "Demo"}
              </a>
            )}
          </div>
        </div>
        <BorderBeam size={300} duration={15} />
      </MagicCard>
    </BlurFade>
  );
}

export function ProjectsSection({ language }) {
  const content = PROJECTS_CONTENT[language];

  return (
    <section id="projects" className="py-24 md:py-32 bg-gray-50 dark:bg-gray-950">
      <div className="max-w-7xl mx-auto px-6 md:px-12 lg:px-20">
        <BlurFade delay={0.1} inView>
          <div className="mb-12">
            <p className="text-sm font-mono font-bold tracking-widest text-gray-400 uppercase mb-3">
              {content.sectionLabel}
            </p>
            <div className="w-full h-px bg-black dark:bg-white mb-6" />
            <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-6">
              <h2 className="text-5xl md:text-7xl font-black tracking-tighter text-black dark:text-white">
                {content.title}
              </h2>
              <p className="text-sm font-mono font-bold tracking-widest text-gray-400">
                {content.allProjects}
              </p>
            </div>
          </div>
        </BlurFade>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {PROJECTS.map((project, i) => (
            <ProjectCard
              key={project.id}
              project={project}
              language={language}
              delay={0.2 + i * 0.1}
            />
          ))}
        </div>
      </div>
    </section>
  );
}
