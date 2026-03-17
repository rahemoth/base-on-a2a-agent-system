import { useState } from "react";
import { BlurFade } from "./ui/blur-fade";
import { MagicCard } from "./ui/magic-card";
import { BorderBeam } from "./ui/border-beam";
import { BLOG_POSTS, BLOG_CATEGORIES } from "../data/blog-posts";
import { Calendar, Clock, ArrowRight, Tag } from "lucide-react";

const BLOG_CONTENT = {
  zh: {
    sectionLabel: "博客",
    title: "最新文章",
    all: "全部",
    categories: {
      "Development": "开发",
      "AI": "人工智能",
      "Life": "生活",
      "Design": "设计",
    },
  },
  en: {
    sectionLabel: "Blog",
    title: "Latest Posts",
    all: "All",
    categories: {
      "Development": "Development",
      "AI": "AI",
      "Life": "Life",
      "Design": "Design",
    },
  },
};

function BlogCard({ post, language, delay }) {
  return (
    <BlurFade delay={delay} inView>
      <MagicCard className="group overflow-hidden h-full" gradientColor="#f9fafb">
        <div className="relative overflow-hidden aspect-[16/9]">
          <img
            src={post.image}
            alt={language === "zh" ? post.title : post.titleEn}
            className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
          />
          <div className="absolute top-3 left-3">
            <span className="px-3 py-1 bg-black/80 text-white text-xs font-semibold rounded-full">
              {post.category}
            </span>
          </div>
        </div>
        <div className="p-6">
          <div className="flex items-center gap-4 text-gray-400 text-sm mb-3">
            <span className="flex items-center gap-1">
              <Calendar size={14} />
              {post.date}
            </span>
            <span className="flex items-center gap-1">
              <Clock size={14} />
              {post.readTime}
            </span>
          </div>
          <h3 className="text-xl font-bold text-black dark:text-white mb-3 line-clamp-2 group-hover:opacity-70 transition-opacity">
            {language === "zh" ? post.title : post.titleEn}
          </h3>
          <p className="text-gray-600 dark:text-gray-400 text-sm leading-relaxed line-clamp-2 mb-4">
            {language === "zh" ? post.excerpt : post.excerptEn}
          </p>
          <div className="flex flex-wrap gap-2 mb-4">
            {post.tags.slice(0, 3).map((tag) => (
              <span
                key={tag}
                className="flex items-center gap-1 px-2 py-1 bg-gray-100 dark:bg-gray-900 text-gray-600 dark:text-gray-400 text-xs rounded-md"
              >
                <Tag size={10} />
                {tag}
              </span>
            ))}
          </div>
          <button className="flex items-center gap-2 text-sm font-semibold text-black dark:text-white group-hover:gap-3 transition-all duration-300">
            {language === "zh" ? "阅读更多" : "Read More"}
            <ArrowRight size={16} />
          </button>
        </div>
        <BorderBeam size={250} duration={12} delay={9} />
      </MagicCard>
    </BlurFade>
  );
}

export function BlogSection({ language }) {
  const [activeCategory, setActiveCategory] = useState("All");
  const content = BLOG_CONTENT[language];

  const filteredPosts =
    activeCategory === "All"
      ? BLOG_POSTS
      : BLOG_POSTS.filter((p) => p.category === activeCategory);

  return (
    <section id="blog" className="py-24 md:py-32 bg-white dark:bg-black">
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
                {BLOG_POSTS.length} POSTS
              </p>
            </div>
          </div>
        </BlurFade>

        <BlurFade delay={0.2} inView>
          <div className="flex flex-wrap gap-3 mb-12">
            {BLOG_CATEGORIES.map((cat) => (
              <button
                key={cat}
                onClick={() => setActiveCategory(cat)}
                className={`px-5 py-2 rounded-full text-sm font-semibold transition-all duration-200 ${
                  activeCategory === cat
                    ? "bg-black dark:bg-white text-white dark:text-black"
                    : "border border-gray-200 dark:border-gray-800 text-gray-600 dark:text-gray-400 hover:border-black dark:hover:border-white hover:text-black dark:hover:text-white"
                }`}
              >
                {cat === "All" ? content.all : content.categories[cat] || cat}
              </button>
            ))}
          </div>
        </BlurFade>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredPosts.map((post, i) => (
            <BlogCard key={post.id} post={post} language={language} delay={0.1 + i * 0.05} />
          ))}
        </div>
      </div>
    </section>
  );
}
