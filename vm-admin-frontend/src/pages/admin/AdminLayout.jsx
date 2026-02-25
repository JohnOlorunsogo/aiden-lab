import { NavLink, Outlet, useLocation } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
  LayoutDashboard,
  Plus,
  Server,
  ChevronRight,
  ChevronLeft,
  Menu,
} from "lucide-react";
import { useState, useEffect } from "react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { ThemeToggle } from "@/components/theme-toggle";
import { useTheme } from "@/lib/theme";

const sidebarItems = [
  { path: "/admin", label: "Dashboard", icon: LayoutDashboard, end: true },
  { path: "/admin/vms/new", label: "Create VM", icon: Plus },
];

function MobileNav({ isOpen, onClose }) {
  const location = useLocation();
  const { theme } = useTheme();

  useEffect(() => {
    onClose();
  }, [location.pathname, onClose]);

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 md:hidden"
          />
          <motion.div
            initial={{ x: "-100%" }}
            animate={{ x: 0 }}
            exit={{ x: "-100%" }}
            transition={{ type: "spring", damping: 25, stiffness: 200 }}
            className="fixed top-0 left-0 bottom-0 w-[280px] bg-card/95 backdrop-blur-xl border-r border-border z-50 md:hidden"
          >
            <div className="flex flex-col h-full p-6">
              <div className="flex items-center justify-between mb-8">
                <NavLink to="/" className="flex items-center gap-3">
                  <img
                    src={theme === 'dark' ? '/Aiden lab Assets (Png & SVG)/White/Asset 9.svg' : '/Aiden lab Assets (Png & SVG)/Aiden Black/Asset 16.svg'}
                    alt="AIDEN Labs"
                    className="h-6 w-auto"
                  />
                </NavLink>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={onClose}
                  className="text-foreground/60"
                >
                  <ChevronLeft className="w-5 h-5" />
                </Button>
              </div>

              <div className="px-1 mb-8">
                <p className="text-[10px] text-primary/60 uppercase tracking-[0.25em] font-medium">
                  VM Management
                </p>
              </div>

              <nav className="flex flex-col gap-1 flex-1">
                {sidebarItems.map((item) => (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    end={item.end}
                    className={({ isActive }) =>
                      cn(
                        "flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-lg transition-all duration-200",
                        isActive
                          ? "bg-primary/10 text-primary"
                          : "text-foreground/60 hover:bg-foreground/5 hover:text-foreground",
                      )
                    }
                  >
                    <item.icon className="w-5 h-5" />
                    <span>{item.label}</span>
                  </NavLink>
                ))}
              </nav>

              <div className="pt-4 border-t border-border">
                <div className="flex items-center justify-between px-4">
                  <NavLink
                    to="/"
                    className="flex items-center gap-3 py-3 text-sm font-medium text-foreground/60 hover:text-foreground transition-all duration-200"
                  >
                    <ChevronRight className="w-5 h-5" />
                    <span>Back to Dashboard</span>
                  </NavLink>
                  <ThemeToggle className="text-foreground/60" />
                </div>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}

export default function AdminLayout() {
  const location = useLocation();
  const { theme } = useTheme();
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  return (
    <div className="flex min-h-screen bg-background">
      {/* Desktop Sidebar */}
      <aside className="fixed top-0 left-0 bottom-0 w-[280px] border-r border-border flex-col z-50 hidden md:flex">
        <div className="sidebar-pattern" />
        <div className="absolute inset-0 bg-card/80 backdrop-blur-xl" />

        <div className="relative z-10 flex flex-col h-full">
          <div className="flex items-center justify-between mb-10 px-6 pt-6">
            <NavLink to="/" className="flex items-center gap-3">
              <img
                src={theme === 'dark' ? '/Aiden lab Assets (Png & SVG)/White/Asset 9.svg' : '/Aiden lab Assets (Png & SVG)/Aiden Black/Asset 16.svg'}
                alt="AIDEN Labs"
                className="h-6 w-auto"
              />
            </NavLink>
            <ThemeToggle className="text-foreground/60 hover:text-foreground" />
          </div>

          <div className="px-6 mb-8">
            <p className="text-[10px] text-primary/60 uppercase tracking-[0.25em] font-medium">
              VM Management
            </p>
          </div>

          <nav className="flex flex-col gap-1 flex-1 px-3">
            {sidebarItems.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                end={item.end}
                className={({ isActive }) =>
                  cn(
                    "flex items-center gap-3 px-4 py-3 text-[13px] font-medium rounded-lg transition-all duration-200 group relative",
                    isActive
                      ? "text-primary"
                      : "text-foreground/60 hover:text-foreground",
                  )
                }
              >
                {({ isActive }) => (
                  <>
                    {isActive && (
                      <motion.div
                        layoutId="sidebar-active-admin"
                        className="absolute inset-0 bg-primary/10 rounded-lg"
                        transition={{
                          type: "spring",
                          bounce: 0.2,
                          duration: 0.6,
                        }}
                      />
                    )}
                    <item.icon
                      className={cn(
                        "w-4 h-4 relative z-10",
                        !isActive &&
                          "group-hover:scale-110 transition-transform",
                      )}
                    />
                    <span className="relative z-10">{item.label}</span>
                  </>
                )}
              </NavLink>
            ))}
          </nav>

          <div className="pt-4 px-6 border-t border-border">
            <NavLink
              to="/"
              className="flex items-center gap-3 px-4 py-3 text-[13px] font-medium text-foreground/60 hover:text-foreground transition-all duration-200 group"
            >
              <ChevronRight className="w-4 h-4 transition-transform duration-200 group-hover:-translate-x-1" />
              <span>Back to Dashboard</span>
            </NavLink>
          </div>
        </div>
      </aside>

      {/* Mobile Navigation */}
      <MobileNav
        isOpen={mobileNavOpen}
        onClose={() => setMobileNavOpen(false)}
      />

      {/* Mobile Header */}
      <header className="md:hidden fixed top-0 left-0 right-0 z-30 flex items-center justify-between p-4 bg-card/80 backdrop-blur-md border-b border-border">
        <div className="flex items-center gap-3">
          <NavLink to="/" className="flex items-center gap-3">
            <img
              src={theme === 'dark' ? '/Aiden lab Assets (Png & SVG)/White/Asset 9.svg' : '/Aiden lab Assets (Png & SVG)/Aiden Black/Asset 16.svg'}
              alt="AIDEN Labs"
              className="h-5 w-auto"
            />
          </NavLink>
        </div>
        <div className="flex items-center gap-2">
          <ThemeToggle className="text-foreground/60" />
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setMobileNavOpen(true)}
            className="text-foreground/60"
          >
            <Menu className="w-5 h-5" />
          </Button>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 md:ml-[280px]">
        <div className="px-4 md:px-8 pb-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
