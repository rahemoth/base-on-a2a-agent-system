import { useState } from "react";
import { BlurFade } from "./ui/blur-fade";
import { MagicCard } from "./ui/magic-card";
import { ShimmerButton } from "./ui/shimmer-button";
import { Mail, Github, Twitter, MapPin, Send, Check } from "lucide-react";

const CONTACT_CONTENT = {
  zh: {
    sectionLabel: "联系",
    title: "保持联系",
    description: "无论是项目合作、技术讨论，还是只是打个招呼，我都很乐意听到你的声音。",
    location: "中国 · 北京",
    email: "hello@example.com",
    formTitle: "发送消息",
    namePlaceholder: "你的名字",
    emailPlaceholder: "你的邮箱",
    messagePlaceholder: "你的消息...",
    send: "发送",
    sent: "已发送！",
  },
  en: {
    sectionLabel: "Contact",
    title: "Get In Touch",
    description: "Whether it's project collaboration, technical discussion, or just saying hi, I'd love to hear from you.",
    location: "Beijing, China",
    email: "hello@example.com",
    formTitle: "Send a Message",
    namePlaceholder: "Your name",
    emailPlaceholder: "Your email",
    messagePlaceholder: "Your message...",
    send: "Send",
    sent: "Sent!",
  },
};

export function ContactSection({ language }) {
  const content = CONTACT_CONTENT[language];
  const [sent, setSent] = useState(false);
  const [form, setForm] = useState({ name: "", email: "", message: "" });

  const handleSubmit = (e) => {
    e.preventDefault();
    setSent(true);
    setTimeout(() => setSent(false), 3000);
    setForm({ name: "", email: "", message: "" });
  };

  return (
    <section id="contact" className="py-24 md:py-32 bg-gray-50 dark:bg-gray-950">
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

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
          <BlurFade delay={0.2} inView>
            <div className="space-y-8">
              <p className="text-xl text-gray-600 dark:text-gray-300 leading-relaxed">
                {content.description}
              </p>

              <div className="space-y-4">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-full border-2 border-black dark:border-white flex items-center justify-center">
                    <MapPin size={20} className="text-black dark:text-white" />
                  </div>
                  <div>
                    <p className="text-sm text-gray-400 font-medium">
                      {language === "zh" ? "所在地" : "Location"}
                    </p>
                    <p className="text-lg font-bold text-black dark:text-white">
                      {content.location}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-full border-2 border-black dark:border-white flex items-center justify-center">
                    <Mail size={20} className="text-black dark:text-white" />
                  </div>
                  <div>
                    <p className="text-sm text-gray-400 font-medium">Email</p>
                    <a
                      href={`mailto:${content.email}`}
                      className="text-lg font-bold text-black dark:text-white hover:opacity-70 transition-opacity"
                    >
                      {content.email}
                    </a>
                  </div>
                </div>
              </div>

              <div className="flex gap-4">
                <a
                  href="https://github.com"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-2 px-5 py-3 border border-gray-200 dark:border-gray-800 rounded-full text-sm font-semibold text-gray-700 dark:text-gray-300 hover:border-black dark:hover:border-white hover:text-black dark:hover:text-white transition-all duration-200"
                >
                  <Github size={18} />
                  GitHub
                </a>
                <a
                  href="https://twitter.com"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-2 px-5 py-3 border border-gray-200 dark:border-gray-800 rounded-full text-sm font-semibold text-gray-700 dark:text-gray-300 hover:border-black dark:hover:border-white hover:text-black dark:hover:text-white transition-all duration-200"
                >
                  <Twitter size={18} />
                  Twitter
                </a>
              </div>
            </div>
          </BlurFade>

          <BlurFade delay={0.3} inView>
            <MagicCard className="p-8" gradientColor="#f3f4f6">
              <h3 className="text-2xl font-black text-black dark:text-white mb-6">
                {content.formTitle}
              </h3>
              <form onSubmit={handleSubmit} className="space-y-4">
                <input
                  type="text"
                  placeholder={content.namePlaceholder}
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  required
                  className="w-full px-4 py-3 border border-gray-200 dark:border-gray-800 rounded-xl bg-transparent text-black dark:text-white placeholder-gray-400 focus:outline-none focus:border-black dark:focus:border-white transition-colors"
                />
                <input
                  type="email"
                  placeholder={content.emailPlaceholder}
                  value={form.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
                  required
                  className="w-full px-4 py-3 border border-gray-200 dark:border-gray-800 rounded-xl bg-transparent text-black dark:text-white placeholder-gray-400 focus:outline-none focus:border-black dark:focus:border-white transition-colors"
                />
                <textarea
                  placeholder={content.messagePlaceholder}
                  value={form.message}
                  onChange={(e) => setForm({ ...form, message: e.target.value })}
                  required
                  rows={5}
                  className="w-full px-4 py-3 border border-gray-200 dark:border-gray-800 rounded-xl bg-transparent text-black dark:text-white placeholder-gray-400 focus:outline-none focus:border-black dark:focus:border-white transition-colors resize-none"
                />
                <ShimmerButton
                  type="submit"
                  background="rgba(0,0,0,1)"
                  className="w-full flex items-center justify-center gap-2 text-white"
                >
                  {sent ? (
                    <>
                      <Check size={18} />
                      {content.sent}
                    </>
                  ) : (
                    <>
                      <Send size={18} />
                      {content.send}
                    </>
                  )}
                </ShimmerButton>
              </form>
            </MagicCard>
          </BlurFade>
        </div>
      </div>
    </section>
  );
}
