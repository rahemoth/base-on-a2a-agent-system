import { BlurFade } from "./ui/blur-fade";
import { BorderBeam } from "./ui/border-beam";
import { TIMELINE } from "../data/timeline";
import { Briefcase, GraduationCap } from "lucide-react";

const TIMELINE_CONTENT = {
  zh: {
    sectionLabel: "时间线",
    title: "我的历程",
  },
  en: {
    sectionLabel: "Timeline",
    title: "My Journey",
  },
};

export function TimelineSection({ language }) {
  const content = TIMELINE_CONTENT[language];

  return (
    <section id="timeline" className="py-24 md:py-32 bg-white dark:bg-black">
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

        <div className="relative">
          <div className="absolute left-6 md:left-1/2 top-0 bottom-0 w-px bg-gray-200 dark:bg-gray-800 md:-translate-x-1/2" />

          <div className="space-y-12">
            {TIMELINE.map((item, index) => (
              <BlurFade key={index} delay={0.1 + index * 0.1} inView>
                <div
                  className={`relative flex items-start gap-8 ${
                    index % 2 === 0 ? "md:flex-row" : "md:flex-row-reverse"
                  }`}
                >
                  <div className="hidden md:block md:w-5/12" />

                  <div className="relative z-10 flex items-center justify-center w-12 h-12 rounded-full border-2 border-black dark:border-white bg-white dark:bg-black shrink-0 md:absolute md:left-1/2 md:-translate-x-1/2">
                    {item.type === "work" ? (
                      <Briefcase size={20} className="text-black dark:text-white" />
                    ) : (
                      <GraduationCap size={20} className="text-black dark:text-white" />
                    )}
                  </div>

                  <div className={`flex-1 md:w-5/12 pl-4 md:pl-0 ${index % 2 === 0 ? "md:pl-8" : "md:pr-8"}`}>
                    <div className="relative bg-white dark:bg-black border border-gray-200 dark:border-gray-800 rounded-2xl p-6 hover:border-black dark:hover:border-white transition-colors overflow-hidden">
                      <div className="flex items-center gap-3 mb-3">
                        <span className="text-sm font-mono font-bold text-gray-400 bg-gray-100 dark:bg-gray-900 px-3 py-1 rounded-full">
                          {item.year}
                        </span>
                        <span className={`text-xs font-semibold px-3 py-1 rounded-full ${
                          item.type === "work"
                            ? "bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-400"
                            : "bg-green-100 dark:bg-green-900 text-green-600 dark:text-green-400"
                        }`}>
                          {item.type === "work" ? (language === "zh" ? "工作" : "Work") : (language === "zh" ? "教育" : "Education")}
                        </span>
                      </div>
                      <h3 className="text-xl font-black text-black dark:text-white mb-1">
                        {language === "zh" ? item.title : item.titleEn}
                      </h3>
                      <p className="text-sm font-semibold text-gray-500 dark:text-gray-400 mb-3">
                        {language === "zh" ? item.institution : item.institutionEn}
                      </p>
                      <p className="text-gray-600 dark:text-gray-400 text-sm leading-relaxed">
                        {language === "zh" ? item.description : item.descriptionEn}
                      </p>
                      <BorderBeam size={150} duration={10} />
                    </div>
                  </div>
                </div>
              </BlurFade>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
