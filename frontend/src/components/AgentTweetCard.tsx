import { Card } from "@/components/ui/card";
import Image from "next/image";
import { Icons } from "@/components/ui/icons";

export interface AgentTweetCardProps {
  summary: string;
  avatarUrl?: string;
  name?: string;
  username?: string;
  socialUrl?: string;
}

export function AgentTweetCard({
  summary,
  avatarUrl = "/images.jpeg", // Place this image in your public/ directory or use a URL
  name = "Agent",
  username = "@agent",
  socialUrl = "https://21st.dev/"
}: AgentTweetCardProps) {
  return (
    <Card className="w-[1000px] h-auto p-5 relative bg-card border-border">
      <div className="flex items-center">
        <Image
          src={avatarUrl}
          alt={name}
          width={50}
          height={50}
          className="rounded-full"
        />
        <div className="flex flex-col pl-4">
          <span className="font-semibold text-base">{name}</span>
          <span className="text-sm text-muted-foreground">{username}</span>
        </div>
      </div>
      <div className="mt-5 mb-5">
        <p className="text-foreground font-medium">{summary}</p>
      </div>
      <button
        onClick={() => window.open(socialUrl, "_blank")?.focus()}
        className="absolute top-4 right-4 hover:opacity-80 transition-opacity"
      >
        <Icons.twitter className="h-4 w-4" aria-hidden="true" />
      </button>
    </Card>
  );
}
