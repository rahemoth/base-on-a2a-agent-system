import { BlurFade } from "./ui/blur-fade";
import { MagicCard } from "./ui/magic-card";
import { Marquee } from "./ui/marquee";
import { NumberTicker } from "./ui/number-ticker";
import { SKILLS } from "../data/timeline";

const ABOUT_CONTENT = {
  zh: {
    sectionLabel: "关于我",
    title: "构建·探索·分享",
    description1: "我是一名热衷于技术创新的全栈工程师，专注于构建优雅的用户界面和高效的后端系统。",
    description2: "在 AI 时代，我探索大语言模型与实际应用的结合，致力于打造真正有用的 AI 工具。同时，我热爱将技术学习历程记录成博客，与更多人分享。",
    stats: [
      { value: 3, suffix: "+", label: "年开发经验" },
      { value: 20, suffix: "+", label: "个项目完成" },
      { value: 50, suffix: "+", label: "篇博客文章" },
      { value: 10, suffix: "k+", label: "行代码提交" },
    ],
    skills: "技能栈",
  },
  en: {
    sectionLabel: "About Me",
    title: "Build · Explore · Share",
    description1: "I'm a full-stack engineer passionate about technological innovation, focused on building elegant user interfaces and efficient backend systems.",
    description2: "In the AI era, I explore the combination of large language models with practical applications, dedicated to creating truly useful AI tools. I also love documenting my learning journey in blog posts to share with others.",
    stats: [
      { value: 3, suffix: "+", label: "Years Experience" },
      { value: 20, suffix: "+", label: "Projects Done" },
      { value: 50, suffix: "+", label: "Blog Posts" },
      { value: 10, suffix: "k+", label: "Code Commits" },
    ],
    skills: "Skills",
  },
};

export function AboutSection({ language }) {
  const content = ABOUT_CONTENT[language];

  return (
    <section id="about" className="py-24 md:py-32 bg-gray-50 dark:bg-gray-950">
      <div className="max-w-7xl mx-auto px-6 md:px-12 lg:px-20">
        <BlurFade delay={0.1} inView>
          <div className="mb-16">
            <p className="text-sm font-mono font-bold tracking-widest text-gray-400 uppercase mb-3">
              {content.sectionLabel}
            </p>
            <div className="w-full h-px bg-black dark:bg-white mb-6" />
            <h2 className="text-5xl md:text-7xl font-black tracking-tighter text-black dark:text-white">
              {content.title}
            </h2>
          </div>
        </BlurFade>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 mb-16">
          <BlurFade delay={0.2} inView>
            <div className="space-y-6">
              <p className="text-xl text-gray-700 dark:text-gray-300 leading-relaxed">
                {content.description1}
              </p>
              <p className="text-xl text-gray-700 dark:text-gray-300 leading-relaxed">
                {content.description2}
              </p>
            </div>
          </BlurFade>

          <BlurFade delay={0.3} inView>
            <div className="grid grid-cols-2 gap-4">
              {content.stats.map((stat, index) => (
                <MagicCard key={index} className="p-6" gradientColor="#f3f4f6">
                  <div className="text-4xl font-black text-black dark:text-white mb-1">
                    <NumberTicker value={stat.value} />
                    <span>{stat.suffix}</span>
                  </div>
                  <p className="text-gray-500 dark:text-gray-400 text-sm font-medium">
                    {stat.label}
                  </p>
                </MagicCard>
              ))}
            </div>
          </BlurFade>
        </div>

        <BlurFade delay={0.4} inView>
          <div className="mt-10">
            <p className="text-sm font-mono font-bold tracking-widest text-gray-400 uppercase mb-6">
              {content.skills}
            </p>
            <Marquee pauseOnHover className="[--duration:30s]">
              {SKILLS.map((skill) => (
                <div
                  key={skill}
                  className="mx-3 px-5 py-2 border border-gray-200 dark:border-gray-800 rounded-full text-sm font-semibold text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-900 hover:border-black dark:hover:border-white transition-colors"
                >
                  {skill}
                </div>
              ))}
            </Marquee>
          </div>
        </BlurFade>
      </div>
    </section>
  );
}
