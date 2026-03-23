import { BarChart3, History, User, PanelLeftClose, PanelLeftOpen, LogOut } from "lucide-react";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { Separator } from "@/components/ui/separator";
import { useAuthStore } from "@/store/auth";

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

export function Sidebar({ collapsed, onToggle }: SidebarProps) {
  const logout = useAuthStore((s) => s.logout);
  const user = useAuthStore((s) => s.user);

  const iconBtn =
    "flex items-center justify-center w-full min-h-[44px] min-w-[44px] rounded-md text-slate-400 hover:text-slate-100 hover:bg-slate-700 transition-colors";

  const textBtn =
    "flex items-center gap-3 w-full px-3 min-h-[44px] rounded-md text-slate-400 hover:text-slate-100 hover:bg-slate-700 transition-colors text-sm";

  return (
    <TooltipProvider delay={300}>
      <aside
        className="flex flex-col bg-slate-800 border-r border-slate-700 transition-all duration-200 shrink-0"
        style={{ width: collapsed ? 64 : 240 }}
      >
        {/* Logo / wordmark */}
        <div className="flex items-center gap-3 px-4 py-4 h-14">
          <BarChart3 className="size-6 text-indigo-500 shrink-0" />
          {!collapsed && (
            <span className="text-[28px] font-semibold text-slate-100 leading-none">
              Stats-AI
            </span>
          )}
        </div>

        <Separator className="bg-slate-700" />

        {/* Navigation — History section */}
        <div className="flex-1 py-4">
          <div className="px-2 space-y-1">
            {collapsed ? (
              <Tooltip>
                <TooltipTrigger className={iconBtn} aria-label="History">
                  <History className="size-5" />
                </TooltipTrigger>
                <TooltipContent side="right">History</TooltipContent>
              </Tooltip>
            ) : (
              <button className={textBtn} aria-label="History">
                <History className="size-5 shrink-0" />
                <span>History</span>
              </button>
            )}
          </div>
        </div>

        <Separator className="bg-slate-700" />

        {/* Account info + logout */}
        <div className="py-3 px-2 space-y-1">
          {collapsed ? (
            <Tooltip>
              <TooltipTrigger
                className={iconBtn}
                aria-label={user?.email ?? "Account"}
              >
                <User className="size-5" />
              </TooltipTrigger>
              <TooltipContent side="right">{user?.email ?? "Account"}</TooltipContent>
            </Tooltip>
          ) : (
            <div className="flex items-center gap-3 px-3 py-2 rounded-md">
              <User className="size-5 text-slate-400 shrink-0" />
              <span className="text-sm text-slate-400 truncate flex-1">
                {user?.email ?? "Account"}
              </span>
            </div>
          )}

          {collapsed ? (
            <Tooltip>
              <TooltipTrigger
                className={`${iconBtn} hover:text-red-400`}
                onClick={logout}
                aria-label="Log out"
              >
                <LogOut className="size-5" />
              </TooltipTrigger>
              <TooltipContent side="right">Log out</TooltipContent>
            </Tooltip>
          ) : (
            <button
              onClick={logout}
              className={`${textBtn} hover:text-red-400`}
              aria-label="Log out"
            >
              <LogOut className="size-5 shrink-0" />
              <span>Log out</span>
            </button>
          )}
        </div>

        <Separator className="bg-slate-700" />

        {/* Collapse toggle */}
        <div className="p-2">
          {collapsed ? (
            <Tooltip>
              <TooltipTrigger
                className={iconBtn}
                onClick={onToggle}
                aria-label="Expand sidebar"
              >
                <PanelLeftOpen className="size-5" />
              </TooltipTrigger>
              <TooltipContent side="right">Expand sidebar</TooltipContent>
            </Tooltip>
          ) : (
            <button
              onClick={onToggle}
              aria-label="Collapse sidebar"
              className={textBtn}
            >
              <PanelLeftClose className="size-5 shrink-0" />
              <span>Collapse</span>
            </button>
          )}
        </div>
      </aside>
    </TooltipProvider>
  );
}
