import { ArrowDown, Github, Mail, Twitter } from "lucide-react";
import { motion } from "framer-motion";
import { BlurFade } from "./ui/blur-fade";
import { WordRotate } from "./ui/word-rotate";
import { ShimmerButton } from "./ui/shimmer-button";
import { Meteors } from "./ui/meteors";

const HERO_CONTENT = {
  zh: {
    greeting: "你好，我是",
    roles: ["全栈工程师", "AI 探索者", "开源爱好者", "终身学习者"],
    description: "热爱构建有意义的产品，探索 AI 与人类的协作边界，分享技术与生活的点滴。",
    cta: "查看我的博客",
    contact: "与我联系",
  },
  en: {
    greeting: "Hi, I'm",
    roles: ["Full-Stack Engineer", "AI Explorer", "Open Source Fan", "Lifelong Learner"],
    description: "Passionate about building meaningful products, exploring the collaboration between AI and humans, and sharing insights about technology and life.",
    cta: "Read My Blog",
    contact: "Get In Touch",
  },
};

export function HeroSection({ language }) {
  const content = HERO_CONTENT[language];

  const scrollToBlog = () => {
    document.getElementById("blog")?.scrollIntoView({ behavior: "smooth" });
  };
  const scrollToContact = () => {
    document.getElementById("contact")?.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <section
      id="hero"
      className="relative min-h-screen flex flex-col justify-center overflow-hidden bg-white dark:bg-black pt-20"
    >
      <div className="absolute inset-0 overflow-hidden">
        <Meteors number={15} />
      </div>

      <div className="absolute inset-0 bg-[linear-gradient(to_right,#8882_1px,transparent_1px),linear-gradient(to_bottom,#8882_1px,transparent_1px)] bg-[size:64px_64px] dark:bg-[linear-gradient(to_right,#ffffff0a_1px,transparent_1px),linear-gradient(to_bottom,#ffffff0a_1px,transparent_1px)]" />

      <div className="relative max-w-7xl mx-auto px-6 md:px-12 lg:px-20 py-20">
        <div className="max-w-4xl">
          <BlurFade delay={0.1} inView>
            <p className="text-gray-500 dark:text-gray-400 text-lg md:text-xl font-medium mb-4 tracking-wide">
              {content.greeting}
            </p>
          </BlurFade>

          <BlurFade delay={0.2} inView>
            <h1 className="text-6xl md:text-8xl lg:text-[10rem] font-black tracking-tighter leading-none text-black dark:text-white mb-4">
              BLOG
            </h1>
          </BlurFade>

          <BlurFade delay={0.3} inView>
            <div className="flex items-center gap-3 mb-8">
              <span className="text-2xl md:text-4xl font-bold text-gray-600 dark:text-gray-300">
                {language === "zh" ? "我是一位" : "I'm a"}
              </span>
              <WordRotate
                words={content.roles}
                className="text-2xl md:text-4xl font-black text-black dark:text-white"
              />
            </div>
          </BlurFade>

          <BlurFade delay={0.4} inView>
            <p className="text-lg md:text-xl text-gray-600 dark:text-gray-300 max-w-2xl leading-relaxed mb-10">
              {content.description}
            </p>
          </BlurFade>

          <BlurFade delay={0.5} inView>
            <div className="flex flex-wrap gap-4">
              <ShimmerButton
                onClick={scrollToBlog}
                background="rgba(0,0,0,1)"
                className="text-white px-8 py-3 text-base font-semibold"
              >
                {content.cta}
              </ShimmerButton>
              <button
                onClick={scrollToContact}
                className="px-8 py-3 text-base font-semibold border-2 border-black dark:border-white text-black dark:text-white rounded-full hover:bg-black hover:text-white dark:hover:bg-white dark:hover:text-black transition-all duration-300"
              >
                {content.contact}
              </button>
            </div>
          </BlurFade>

          <BlurFade delay={0.6} inView>
            <div className="flex items-center gap-6 mt-10">
              <a href="https://github.com" target="_blank" rel="noopener noreferrer" className="text-gray-400 hover:text-black dark:hover:text-white transition-colors">
                <Github size={24} />
              </a>
              <a href="mailto:hello@example.com" className="text-gray-400 hover:text-black dark:hover:text-white transition-colors">
                <Mail size={24} />
              </a>
              <a href="https://twitter.com" target="_blank" rel="noopener noreferrer" className="text-gray-400 hover:text-black dark:hover:text-white transition-colors">
                <Twitter size={24} />
              </a>
            </div>
          </BlurFade>
        </div>

        <motion.div
          className="absolute bottom-10 left-1/2 -translate-x-1/2"
          animate={{ y: [0, 8, 0] }}
          transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
        >
          <ArrowDown className="text-gray-400" size={24} />
        </motion.div>
      </div>
    </section>
  );
}
