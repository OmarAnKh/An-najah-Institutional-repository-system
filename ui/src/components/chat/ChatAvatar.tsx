import { User } from "lucide-react";
import { cn } from "@/lib/utils";
import logoSvg from "@/assets/logo.svg";

interface ChatAvatarProps {
  role: "user" | "assistant";
  className?: string;
}

export function ChatAvatar({ role, className }: ChatAvatarProps) {
  const isUser = role === "user";

  return (
    <div
      className={cn(
        "w-8 h-8 rounded-full flex items-center justify-center shrink-0 transition-transform duration-200 hover:scale-105",
        isUser
          ? "bg-gradient-to-br from-primary to-primary/80 text-primary-foreground shadow-sm"
          : "bg-secondary text-muted-foreground",
        className,
      )}
    >
      {isUser ? (
        <User className="w-4 h-4" />
      ) : (
        <img src={logoSvg} alt="Assistant" className="w-8 h-8 object-contain" />
      )}
    </div>
  );
}
