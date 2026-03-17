export function Footer({ language }) {
  const currentYear = new Date().getFullYear();
  return (
    <footer className="py-12 border-t border-gray-200 dark:border-gray-800 bg-white dark:bg-black">
      <div className="max-w-7xl mx-auto px-6 md:px-12 lg:px-20">
        <div className="flex flex-col md:flex-row justify-between items-center gap-4">
          <p className="text-2xl font-black tracking-tighter text-black dark:text-white">
            BLOG
          </p>
          <p className="text-gray-500 text-sm">
            © {currentYear} · {language === "zh" ? "用 ❤️ 构建" : "Built with ❤️"}
          </p>
          <p className="text-xs text-gray-400 font-mono">
            {language === "zh" ? "基于 React + Magic UI" : "Powered by React + Magic UI"}
          </p>
        </div>
      </div>
    </footer>
  );
}
